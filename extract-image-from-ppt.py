import convertapi

# Set your API credentials
convertapi.api_credentials = "secret_WMk7Jyse4l1HvlFv"

# Convert the PPTX to JPG
result = convertapi.convert("jpg", {"File": "Styled_Slides.pptx"}, from_format="pptx")

# Save the files in the 'slidees' directory
result.save_files("slides")

print("Slides have been successfully converted and saved.")
