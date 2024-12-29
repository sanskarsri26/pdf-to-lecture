from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import re


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
    # Define a set of professional color gradients
    gradients = [
        # Blue gradient
        (RGBColor(230, 240, 255), RGBColor(200, 220, 255)),
        # Light purple gradient
        (RGBColor(245, 240, 255), RGBColor(235, 225, 255)),
        # Mint gradient
        (RGBColor(240, 255, 250), RGBColor(225, 245, 240)),
        # Warm gray gradient
        (RGBColor(250, 248, 245), RGBColor(240, 238, 235)),
    ]
    return gradients[slide_number % len(gradients)]


def add_styled_slide(presentation, title, content, slide_number, total_slides):
    slide_layout = presentation.slide_layouts[1]
    slide = presentation.slides.add_slide(slide_layout)

    # Set gradient background
    background = slide.background
    fill = background.fill
    fill.solid()
    top_color, bottom_color = get_gradient_colors(slide_number, total_slides)
    fill.fore_color.rgb = top_color

    # Add a subtle accent bar on the left
    left_bar = slide.shapes.add_shape(
        1, Inches(0.5), Inches(0.5), Inches(0.1), Inches(6.5)  # Rectangle
    )
    left_bar.fill.solid()
    left_bar.fill.fore_color.rgb = RGBColor(100, 120, 200)  # Accent color
    left_bar.line.fill.background()  # No outline

    # Style title
    title_shape = slide.shapes.title
    title_shape.text = title
    title_frame = title_shape.text_frame
    title_frame.clear()  # Clear default formatting

    # Add title with custom formatting
    p = title_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RGBColor(40, 60, 100)  # Dark blue
    p.alignment = PP_ALIGN.LEFT

    # Style content
    body_shape = slide.placeholders[1]
    body_shape.text = content
    body_frame = body_shape.text_frame

    # Format content paragraphs
    for paragraph in body_frame.paragraphs:
        paragraph.font.size = Pt(20)
        paragraph.font.color.rgb = RGBColor(60, 60, 60)  # Dark gray
        paragraph.space_before = Pt(12)
        paragraph.space_after = Pt(12)
        paragraph.alignment = PP_ALIGN.LEFT

    # Add slide number
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


# Create the presentation
input_text_file = "M3-NFA-L1-NondeterminismByAnalogy-handout_response.txt"
output_pptx_file = "Styled_Slides.pptx"
create_styled_presentation(input_text_file, output_pptx_file)
