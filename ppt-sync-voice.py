import os
from pptx import Presentation


def add_audio_slides(pptx_file, audio_dir="output", output_dir="output"):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Create the PowerPoint presentation object
    prs = Presentation(pptx_file)

    # List all mp3 files in the audio directory
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".mp3")]

    # Iterate over the audio files and create a slide for each one
    for i, audio_file in enumerate(audio_files):
        # Add a new slide with layout 5 (title and content)
        slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(slide_layout)

        # Add text for the audio description
        title = slide.shapes.title
        title.text = f"Audio Slide {i + 1}"

        # Add a placeholder icon for the audio file (or a description)
        slide.shapes.add_picture(
            "audio_icon.png", left=100, top=100, width=50, height=50
        )

        # You can also add a text box to describe the audio if needed
        textbox = slide.shapes.add_textbox(left=200, top=100, width=500, height=50)
        textbox.text = f"Audio File: {audio_file}"

        # You can further process the audio files here (copy them, etc.)

    # Define the path where the presentation will be saved
    output_pptx_file = os.path.join(output_dir, "output_presentation.pptx")
    prs.save(output_pptx_file)

    print(f"Presentation saved to: {output_pptx_file}")


# Call the function with the audio directory specified
add_audio_slides("Styled_Slides.pptx")
