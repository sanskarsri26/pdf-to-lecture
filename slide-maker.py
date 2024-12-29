import re
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.line import LineFormat


class SlideTheme:
    def __init__(self):
        # Color schemes
        self.color_schemes = [
            {
                "background": (240, 248, 255),  # Light blue
                "title": (47, 84, 150),  # Dark blue
                "body": (60, 60, 60),  # Dark gray
                "accent": (65, 105, 225),  # Royal blue
            },
            {
                "background": (255, 245, 238),  # Seashell
                "title": (139, 69, 19),  # Saddle brown
                "body": (60, 60, 60),  # Dark gray
                "accent": (210, 105, 30),  # Chocolate
            },
            {
                "background": (240, 255, 240),  # Honeydew
                "title": (34, 139, 34),  # Forest green
                "body": (60, 60, 60),  # Dark gray
                "accent": (60, 179, 113),  # Medium sea green
            },
        ]

        # Typography
        self.title_font = {"name": "Calibri", "size": Pt(44), "bold": True}

        self.body_font = {"name": "Calibri", "size": Pt(24), "bold": False}

        # Spacing
        self.margins = {
            "top": Inches(0.5),
            "left": Inches(0.5),
            "right": Inches(0.5),
            "bottom": Inches(0.5),
        }


def extract_slides(content):
    """
    Extract slides from content using various patterns.
    Returns a list of (title, content) tuples.
    """
    slides = []

    # Pattern 1: Matches "Slide N:" or "Slide N." format
    pattern1 = r"(?:Slide\s+\d+[:.])(.*?)(?=Slide\s+\d+[:.]|$)"
    # Pattern 2: Matches blocks separated by double newlines
    pattern2 = r"\n\n+(.*?)\n\n+|$"
    # Pattern 3: Matches content between markdown-style headers
    pattern3 = r"#(.*?)(?=#|$)"

    # Try different patterns to split content into slides
    patterns = [pattern1, pattern2, pattern3]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.DOTALL)
        potential_slides = [
            match.group(1).strip() for match in matches if match.group(1).strip()
        ]

        if potential_slides:
            for slide_content in potential_slides:
                title = None
                content = slide_content

                # Try to find title patterns
                title_patterns = [
                    r"\*\*(?:Slide\s+Title|Title)\*\*:\s*(.*?)(?:\n|$)",
                    r"Title:\s*(.*?)(?:\n|$)",
                    r"^([^:\n]+):(?:\s*\n|$)",
                    r"^([^\n]+)(?:\n|$)",
                ]

                for t_pattern in title_patterns:
                    title_match = re.search(
                        t_pattern, slide_content, re.IGNORECASE | re.MULTILINE
                    )
                    if title_match:
                        title = title_match.group(1).strip()
                        content = re.sub(
                            t_pattern,
                            "",
                            slide_content,
                            1,
                            re.IGNORECASE | re.MULTILINE,
                        ).strip()
                        break

                if not title:
                    title = (
                        content.split("\n")[0][:50] + "..."
                        if len(content.split("\n")[0]) > 50
                        else content.split("\n")[0]
                    )
                    content = "\n".join(content.split("\n")[1:])

                content = re.sub(r"\*\*Detailed Explanation\*\*:\s*", "", content)
                content = re.sub(r"\*\*.*?\*\*", "", content)

                if title and content.strip():
                    slides.append((title.strip(), content.strip()))

            if slides:
                break

    return slides


def add_decorative_elements(slide, theme, scheme_index):
    """Add decorative elements to the slide"""
    # Add accent bar on the left
    accent_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.2), Inches(0.5), Inches(0.1), Inches(6.5)
    )
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = RGBColor(
        *theme.color_schemes[scheme_index]["accent"]
    )
    accent_bar.line.fill.background()

    # Add subtle footer line
    footer_line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.2), Inches(7.0), Inches(12.9), Inches(0.02)
    )
    footer_line.fill.solid()
    footer_line.fill.fore_color.rgb = RGBColor(
        *theme.color_schemes[scheme_index]["accent"]
    )
    footer_line.line.fill.background()


def apply_slide_formatting(
    slide, title, content, theme, scheme_index, slide_number, total_slides
):
    """Apply formatting to a slide"""
    # Set background
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(*theme.color_schemes[scheme_index]["background"])

    # Add decorative elements
    add_decorative_elements(slide, theme, scheme_index)

    # Format title
    title_shape = slide.shapes.title
    title_shape.text = title
    title_frame = title_shape.text_frame

    # Apply title formatting
    p = title_frame.paragraphs[0]
    p.font.size = theme.title_font["size"]
    p.font.bold = theme.title_font["bold"]
    p.font.name = theme.title_font["name"]
    p.font.color.rgb = RGBColor(*theme.color_schemes[scheme_index]["title"])
    p.alignment = PP_ALIGN.LEFT

    # Format content
    body_shape = slide.placeholders[1]
    body_shape.text = content

    # Apply content formatting
    for paragraph in body_shape.text_frame.paragraphs:
        paragraph.font.size = theme.body_font["size"]
        paragraph.font.bold = theme.body_font["bold"]
        paragraph.font.name = theme.body_font["name"]
        paragraph.font.color.rgb = RGBColor(*theme.color_schemes[scheme_index]["body"])
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.space_before = Pt(12)
        paragraph.space_after = Pt(12)

    # Add slide number
    slide_number_box = slide.shapes.add_textbox(
        Inches(12.3), Inches(7.1), Inches(0.5), Inches(0.3)
    )
    number_text = slide_number_box.text_frame
    number_text.paragraphs[0].text = f"{slide_number}/{total_slides}"
    number_text.paragraphs[0].font.size = Pt(12)
    number_text.paragraphs[0].font.color.rgb = RGBColor(
        *theme.color_schemes[scheme_index]["body"]
    )
    number_text.paragraphs[0].alignment = PP_ALIGN.RIGHT


def create_styled_presentation(input_text, output_pptx):
    """Create a styled PowerPoint presentation from input text"""
    # Get slides content
    slides_content = extract_slides(input_text)

    if not slides_content:
        print("No slides were parsed!")
        return

    print(f"Total slides parsed: {len(slides_content)}")

    # Create presentation
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    # Initialize theme
    theme = SlideTheme()

    # Create slides
    total_slides = len(slides_content)
    for i, (title, content) in enumerate(slides_content, 1):
        print(f"Generating slide {i} of {total_slides}")

        # Add slide
        slide_layout = presentation.slide_layouts[1]
        slide = presentation.slides.add_slide(slide_layout)

        # Apply formatting
        scheme_index = (i - 1) % len(theme.color_schemes)
        apply_slide_formatting(
            slide, title, content, theme, scheme_index, i, total_slides
        )

    # Save presentation
    presentation.save(output_pptx)
    print(f"Created presentation with {total_slides} slides")


def clean_content(content):
    """Clean the content by removing empty bullet points and asterisks"""
    # Remove standalone asterisks
    content = re.sub(r"^\s*\*+\s*$", "", content, flags=re.MULTILINE)

    # Remove lines that only contain bullet points with no text
    content = re.sub(r"^\s*[•\-\*]\s*$", "", content, flags=re.MULTILINE)

    # Remove any remaining asterisks
    content = content.replace("*", "")

    # Remove empty lines
    lines = [line for line in content.split("\n") if line.strip()]

    # Join the lines back together
    return "\n".join(lines)


def extract_slides(content):
    """
    Extract slides from content using various patterns.
    Returns a list of (title, content) tuples.
    """
    slides = []

    # Pattern 1: Matches "Slide N:" or "Slide N." format
    pattern1 = r"(?:Slide\s+\d+[:.])(.*?)(?=Slide\s+\d+[:.]|$)"
    # Pattern 2: Matches blocks separated by double newlines
    pattern2 = r"\n\n+(.*?)\n\n+|$"
    # Pattern 3: Matches content between markdown-style headers
    pattern3 = r"#(.*?)(?=#|$)"

    # Try different patterns to split content into slides
    patterns = [pattern1, pattern2, pattern3]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.DOTALL)
        potential_slides = [
            match.group(1).strip() for match in matches if match.group(1).strip()
        ]

        if potential_slides:
            for slide_content in potential_slides:
                title = None
                content = slide_content

                # Try to find title patterns
                title_patterns = [
                    r"\*\*(?:Slide\s+Title|Title)\*\*:\s*(.*?)(?:\n|$)",
                    r"Title:\s*(.*?)(?:\n|$)",
                    r"^([^:\n]+):(?:\s*\n|$)",
                    r"^([^\n]+)(?:\n|$)",
                ]

                for t_pattern in title_patterns:
                    title_match = re.search(
                        t_pattern, slide_content, re.IGNORECASE | re.MULTILINE
                    )
                    if title_match:
                        title = title_match.group(1).strip()
                        content = re.sub(
                            t_pattern,
                            "",
                            slide_content,
                            1,
                            re.IGNORECASE | re.MULTILINE,
                        ).strip()
                        break

                if not title:
                    title = (
                        content.split("\n")[0][:50] + "..."
                        if len(content.split("\n")[0]) > 50
                        else content.split("\n")[0]
                    )
                    content = "\n".join(content.split("\n")[1:])

                # Clean the content
                content = clean_content(content)

                # Remove "Detailed Explanation" marker
                content = re.sub(r"Detailed Explanation:\s*", "", content)

                if title and content.strip():
                    # Clean the title as well
                    title = clean_content(title)
                    slides.append((title.strip(), content.strip()))

            if slides:
                break

    return slides

def main():
    try:
        with open("output.txt", "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        content = """
        Slide 1:
        Title: Introduction
        This is the first slide content.

        Slide 2:
        Title: Main Points
        These are the main points of the presentation.
        """

    create_styled_presentation(content, "Styled_Slides.pptx")


if __name__ == "__main__":
    main()
