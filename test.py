import os
import base64
import httpx
from pdf2image import convert_from_path
from PIL import Image
import io
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import re


# Configure API Key for Gemini
genai.configure(api_key="AIzaSyCSqsv69biM6pCAkPGEDh9XRM5WpVBraf4")
model = genai.GenerativeModel("gemini-1.5-flash")


# First Script: Processing PDFs and Sending Images to Gemini
def process_pdfs(input_path):
    if os.path.isdir(input_path):
        print(f"Processing all PDFs in the directory: {input_path}")
        for filename in os.listdir(input_path):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(input_path, filename)
                print(f"Processing PDF file: {pdf_path}")
                process_pdf(pdf_path)
    elif os.path.isfile(input_path) and input_path.endswith(".pdf"):
        print(f"Processing single PDF file: {input_path}")
        process_pdf(input_path)
    else:
        print(
            "Invalid input. Please provide a valid PDF file or directory containing PDFs."
        )


def process_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    encoded_images = []

    for i, image in enumerate(images):
        print(f"Processing page {i+1} of {pdf_path}...")
        encoded_image = encode_image_to_base64(image)
        encoded_images.append(encoded_image)

    result = send_images_to_gemini(encoded_images)

    if result:
        print(f"Result: {result}")
        response_file = save_response_to_text(result, pdf_path)
        return response_file  # Return the generated text file path


def encode_image_to_base64(image: Image.Image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()
    encoded_image = base64.b64encode(img_byte_arr).decode("utf-8")
    return encoded_image


def send_images_to_gemini(encoded_images):
    prompt = """
    Please act as a knowledgeable professor with deep expertise in explaining complex concepts across various subjects. For each slide, provide the following:
    1. **Slide Title**: The main title of the slide.
    2. **Detailed Explanation**: A 4-6 line explanation of the topic.
    """

    try:
        parts = [{"text": prompt}]
        for i, encoded_image in enumerate(encoded_images):
            if i >= 16:  # Gemini typically has a limit on number of images
                print(f"Warning: Only processing first 16 images due to API limits")
                break
            parts.append(
                {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}}
            )
        response = model.generate_content(parts)
        return response.text
    except Exception as e:
        print(f"Error in send_images_to_gemini: {str(e)}")
        return None


def save_response_to_text(response, pdf_path):
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = f"{base_name}_response.txt"
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(response)
    print(f"API response saved as '{output_file}'.")
    return output_file  # Return the file path


# Second Script: Create Styled PowerPoint from Text File
def parse_text_to_slides(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    slide_sections = content.split("\n\n**Slide ")
    slides = []

    for section in slide_sections[1:]:
        try:
            title_marker = section.find("* **Slide Title**:")
            content_marker = section.find("* **Detailed Explanation**:")
            if title_marker != -1 and content_marker != -1:
                title_start = title_marker + len("* **Slide Title**:")
                title_end = section.find("\n", title_start)
                title = section[title_start:title_end].strip()

                content_start = content_marker + len("* **Detailed Explanation**:")
                next_section = section.find("\n\n**Slide", content_start)
                if next_section == -1:
                    content = section[content_start:].strip()
                else:
                    content = section[content_start:next_section].strip()

                title = re.sub(r"\*+", "", title)
                content = re.sub(r"\*+", "", content)

                slides.append((title, content))

        except Exception as e:
            print(f"Error parsing slide section: {str(e)}")
            continue

    return slides


def get_gradient_colors(slide_number, total_slides):
    gradients = [
        (RGBColor(230, 240, 255), RGBColor(200, 220, 255)),
        (RGBColor(245, 240, 255), RGBColor(235, 225, 255)),
        (RGBColor(240, 255, 250), RGBColor(225, 245, 240)),
        (RGBColor(250, 248, 245), RGBColor(240, 238, 235)),
    ]
    return gradients[slide_number % len(gradients)]


def add_styled_slide(presentation, title, content, slide_number, total_slides):
    slide_layout = presentation.slide_layouts[1]
    slide = presentation.slides.add_slide(slide_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    top_color, bottom_color = get_gradient_colors(slide_number, total_slides)
    fill.fore_color.rgb = top_color

    left_bar = slide.shapes.add_shape(
        1, Inches(0.5), Inches(0.5), Inches(0.1), Inches(6.5)
    )
    left_bar.fill.solid()
    left_bar.fill.fore_color.rgb = RGBColor(100, 120, 200)
    left_bar.line.fill.background()

    title_shape = slide.shapes.title
    title_shape.text = title
    title_frame = title_shape.text_frame
    title_frame.clear()

    p = title_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(40, 60, 100)
    p.alignment = PP_ALIGN.LEFT

    body_shape = slide.placeholders[1]
    body_shape.text = content
    body_frame = body_shape.text_frame

    for paragraph in body_frame.paragraphs:
        paragraph.font.size = Pt(20)
        paragraph.font.color.rgb = RGBColor(60, 60, 60)
        paragraph.space_before = Pt(12)
        paragraph.space_after = Pt(12)
        paragraph.alignment = PP_ALIGN.LEFT

    slide_number_shape = slide.shapes.add_textbox(
        Inches(12), Inches(7), Inches(0.5), Inches(0.3)
    )
    slide_number_text = slide_number_shape.text_frame
    p = slide_number_text.paragraphs[0]
    p.text = f"{slide_number + 1}"
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(100, 100, 100)
    p.alignment = PP_ALIGN.RIGHT


def create_styled_presentation(file_path, output_pptx):
    slides_content = parse_text_to_slides(file_path)

    if not slides_content:
        print("No slides were parsed!")
        return

    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    total_slides = len(slides_content)
    for i, (title, content) in enumerate(slides_content):
        add_styled_slide(presentation, title, content, i, total_slides)

    presentation.save(output_pptx)
    print(f"Created presentation with {total_slides} slides")


# Run the first script (process PDFs), generate text file, and create PowerPoint
input_path = input("Enter the file or directory path containing PDF files: ")
response_file = process_pdfs(input_path)  # Generate the response text file

if response_file:
    create_styled_presentation(response_file, "Styled_Slides.pptx")
