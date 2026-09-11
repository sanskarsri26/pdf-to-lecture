import io
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber


class PDFProcessingError(Exception):
    """Base exception for PDF extraction failures."""


class PDFTooLongError(PDFProcessingError):
    """Raised when the uploaded PDF exceeds the configured page limit."""


class NoExtractableTextError(PDFProcessingError):
    """Raised when the PDF has no extractable text."""


@dataclass
class ExtractedDocument:
    text: str
    page_count: int
    pages: List[str]
    ocr_pages: List[int]
    warnings: List[str]

    @property
    def used_ocr(self) -> bool:
        return bool(self.ocr_pages)


def clean_pdf_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(
    pdf_path: Path,
    max_pages: int = 30,
    enable_ocr: Optional[bool] = None,
) -> ExtractedDocument:
    enable_ocr = _env_flag("ENABLE_OCR", default=True) if enable_ocr is None else enable_ocr
    min_text_chars = _env_int("OCR_MIN_TEXT_CHARS", default=40)
    ocr_dpi = _env_int("OCR_DPI", default=200)
    ocr_lang = os.getenv("OCR_LANG", "eng")
    warnings: List[str] = []

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            page_count = len(pdf.pages)
            if page_count > max_pages:
                raise PDFTooLongError(
                    f"PDF has {page_count} pages. The MVP limit is {max_pages} pages."
                )

            pages: List[str] = []
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                pages.append(clean_pdf_text(page_text))
    except PDFProcessingError:
        raise
    except Exception as exc:
        raise PDFProcessingError(f"Could not read PDF: {exc}") from exc

    ocr_pages: List[int] = []
    pages_needing_ocr = _pages_needing_ocr(pages, min_text_chars=min_text_chars)
    if pages_needing_ocr and enable_ocr:
        ocr_text, ocr_warnings = _ocr_pdf_pages(
            pdf_path=pdf_path,
            page_indexes=pages_needing_ocr,
            dpi=ocr_dpi,
            lang=ocr_lang,
        )
        warnings.extend(ocr_warnings)

        for page_index, page_text in ocr_text.items():
            if len(page_text) > len(pages[page_index]):
                pages[page_index] = page_text
                ocr_pages.append(page_index + 1)
    elif pages_needing_ocr and not enable_ocr:
        warnings.append("OCR is disabled; scanned or image-only pages may be skipped.")

    text = clean_pdf_text("\n\n".join(page for page in pages if page))
    if not text:
        detail = " ".join(warnings)
        suffix = f" {detail}" if detail else ""
        raise NoExtractableTextError(
            "No extractable text was found. OCR requires a readable scanned PDF and the "
            f"Tesseract system binary to be installed.{suffix}"
        )

    return ExtractedDocument(
        text=text,
        page_count=page_count,
        pages=pages,
        ocr_pages=ocr_pages,
        warnings=warnings,
    )


def _pages_needing_ocr(pages: List[str], min_text_chars: int) -> List[int]:
    return [
        index
        for index, page_text in enumerate(pages)
        if len(page_text.strip()) < min_text_chars
    ]


def _ocr_pdf_pages(
    pdf_path: Path,
    page_indexes: List[int],
    dpi: int,
    lang: str,
) -> Tuple[Dict[int, str], List[str]]:
    if not page_indexes:
        return {}, []

    try:
        import fitz
        import pytesseract
        from PIL import Image
    except Exception as exc:
        return {}, [
            "OCR dependencies are unavailable. Install PyMuPDF, pytesseract, Pillow, "
            f"and the Tesseract system binary. Details: {exc}"
        ]

    extracted: Dict[int, str] = {}
    warnings: List[str] = []
    zoom = max(dpi, 72) / 72

    try:
        with fitz.open(str(pdf_path)) as document:
            for page_index in page_indexes:
                try:
                    page = document.load_page(page_index)
                    pixmap = page.get_pixmap(
                        matrix=fitz.Matrix(zoom, zoom),
                        alpha=False,
                    )
                    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                    page_text = pytesseract.image_to_string(image, lang=lang)
                    cleaned_text = clean_pdf_text(page_text)
                    if cleaned_text:
                        extracted[page_index] = cleaned_text
                    else:
                        warnings.append(f"OCR found no text on page {page_index + 1}.")
                except Exception as exc:
                    warnings.append(f"OCR failed on page {page_index + 1}: {exc}")
    except Exception as exc:
        warnings.append(f"OCR could not open PDF for rendering: {exc}")

    return extracted, warnings


def _env_flag(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.lower() not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default
