import convertapi
import os

# Set your API credentials
convertapi.api_credentials = "secret_WMk7Jyse4l1HvlFv"

# Convert the PPTX to JPG
result = convertapi.convert("jpg", {"File": "Styled_Slides.pptx"}, from_format="pptx")

# Create the 'slidees' directory if it doesn't exist
output_dir = "slides"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save and rename each slide with a custom name
for i, file in enumerate(result.files):
    # Custom name for each slide (e.g., slide_1.jpg, slide_2.jpg, etc.)
    custom_name = f"slide_{i + 1}.jpg"

    # Save the slide with the custom name
    file.save(os.path.join(output_dir, custom_name))

print("Slides have been successfully converted and renamed.")
