from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from textwrap import wrap


# Function to parse the text content and extract slides
def parse_text_to_slides(file_path):
    slides = []
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Split by each slide block
    slide_blocks = content.split("**Slide ")

    for block in slide_blocks:
        if not block.strip():
            continue

        # Extract title and content
        title_start = block.find("**Slide Title**:") + len("**Slide Title**:")
        explanation_start = block.find("**Detailed Explanation**:")

        title = (
            block[title_start:explanation_start].strip()
            if explanation_start > -1
            else None
        )
        explanation = (
            block[explanation_start + len("**Detailed Explanation**:") :].strip()
            if explanation_start > -1
            else None
        )

        if title and explanation:
            slides.append((title, explanation))

    return slides


# Function to wrap text for better display
def wrap_text(text, max_line_length=80):
    """
    Wrap text to ensure it fits within the slide content box.
    """
    wrapped_lines = []
    for paragraph in text.split("\n"):
        wrapped_lines.extend(wrap(paragraph, max_line_length))
    return "\n".join(wrapped_lines)


# Function to add a slide with enhanced formatting
def add_styled_slide(presentation, title, content):
    slide_layout = presentation.slide_layouts[1]  # Title and Content layout
    slide = presentation.slides.add_slide(slide_layout)

    # Set slide background color
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(240, 240, 240)  # Light gray background

    # Style the title
    title_placeholder = slide.shapes.title
    title_placeholder.text = title
    title_placeholder.text_frame.paragraphs[0].font.bold = True
    title_placeholder.text_frame.paragraphs[0].font.size = Pt(36)
    title_placeholder.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102)

    # Style the content with wrapped text
    wrapped_content = wrap_text(content, max_line_length=80)
    content_placeholder = slide.placeholders[1]
    content_placeholder.text = wrapped_content

    for paragraph in content_placeholder.text_frame.paragraphs:
        paragraph.font.size = Pt(18)
        paragraph.font.color.rgb = RGBColor(0, 0, 0)
        paragraph.space_after = Pt(10)  # Add spacing between paragraphs


# Main function to create PowerPoint from a text file with enhanced formatting
def create_styled_presentation(file_path, output_pptx):
    slides = parse_text_to_slides(file_path)
    presentation = Presentation()

    for title, content in slides:
        add_styled_slide(presentation, title, content)

    presentation.save(output_pptx)
    print(f"Presentation saved as '{output_pptx}'")


# Input text file and output PowerPoint file
input_text_file = "test.txt"  # Replace with your text file
output_pptx_file = "Styled_Slides.pptx"

# Create the presentation
create_styled_presentation(input_text_file, output_pptx_file)
