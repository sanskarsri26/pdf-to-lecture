from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
import re


def parse_text_to_slides(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Split into individual slide sections
    slide_sections = content.split("\n\n**Slide ")

    slides = []
    # Skip the first split as it's the introduction text
    for section in slide_sections[1:]:
        try:
            # Extract the main slide title line
            first_line_end = section.find("\n")
            if first_line_end == -1:
                continue

            # Find the actual title and content markers
            title_marker = section.find("* **Slide Title**:")
            content_marker = section.find("* **Detailed Explanation**:")

            if title_marker != -1 and content_marker != -1:
                # Extract the title text
                title_start = title_marker + len("* **Slide Title**:")
                title_end = section.find("\n", title_start)
                title = section[title_start:title_end].strip()

                # Extract the content text
                content_start = content_marker + len("* **Detailed Explanation**:")
                next_section = section.find("\n\n**Slide", content_start)
                if next_section == -1:
                    content = section[content_start:].strip()
                else:
                    content = section[content_start:next_section].strip()

                # Clean up any remaining markdown
                title = re.sub(r"\*+", "", title)
                content = re.sub(r"\*+", "", content)

                slides.append((title, content))
                print(f"Parsed slide: {title[:30]}...")  # Debug print

        except Exception as e:
            print(f"Error parsing slide section: {str(e)}")
            continue

    return slides


def add_styled_slide(presentation, title, content):
    # Use a layout with title and content
    slide_layout = presentation.slide_layouts[1]
    slide = presentation.slides.add_slide(slide_layout)

    # Set background
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(255, 255, 255)

    # Add and style title
    title_shape = slide.shapes.title
    title_shape.text = title
    title_frame = title_shape.text_frame
    for paragraph in title_frame.paragraphs:
        paragraph.font.size = Pt(44)
        paragraph.font.bold = True
        paragraph.font.color.rgb = RGBColor(0, 0, 0)
        paragraph.alignment = 1  # Center alignment

    # Add and style content
    body_shape = slide.placeholders[1]
    body_shape.text = content
    body_frame = body_shape.text_frame

    # Format the content text
    for paragraph in body_frame.paragraphs:
        paragraph.font.size = Pt(20)
        paragraph.font.color.rgb = RGBColor(0, 0, 0)
        paragraph.space_before = Pt(12)
        paragraph.space_after = Pt(12)


def create_styled_presentation(file_path, output_pptx):
    slides = parse_text_to_slides(file_path)

    if not slides:
        print("No slides were parsed!")
        return

    presentation = Presentation()

    # Set slide size to 16:9
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    # Create each slide
    for title, content in slides:
        add_styled_slide(presentation, title, content)

    presentation.save(output_pptx)
    print(f"Created presentation with {len(slides)} slides")


# Create the presentation
input_text_file = "test.txt"
output_pptx_file = "Slides.pptx"
create_styled_presentation(input_text_file, output_pptx_file)
