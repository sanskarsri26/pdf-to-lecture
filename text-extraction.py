import os
import base64
import httpx
from pdf2image import convert_from_path
from PIL import Image
import io
import google.generativeai as genai
from pptx import Presentation

# Configure API Key
genai.configure(api_key="AIzaSyCSqsv69biM6pCAkPGEDh9XRM5WpVBraf4")

# Initialize the generative model
model = genai.GenerativeModel("gemini-1.5-flash")


# Function to process a single PDF or all PDFs in a directory
def process_pdfs(input_path):
    # Check if the input is a directory
    if os.path.isdir(input_path):
        print(f"Processing all PDFs in the directory: {input_path}")
        # Iterate through all the files in the directory
        for filename in os.listdir(input_path):
            if filename.endswith(".pdf"):  # Check if the file is a PDF
                pdf_path = os.path.join(input_path, filename)
                print(f"Processing PDF file: {pdf_path}")
                process_pdf(pdf_path)
    elif os.path.isfile(input_path) and input_path.endswith(".pdf"):
        # If it's a single PDF file, process it directly
        print(f"Processing single PDF file: {input_path}")
        process_pdf(input_path)
    else:
        print(
            "Invalid input. Please provide a valid PDF file or directory containing PDFs."
        )


# Function to process each PDF and convert it to images
def process_pdf(pdf_path):
    # Convert the PDF into a list of images (one per page)
    images = convert_from_path(pdf_path)

    # List to store encoded images in base64 as text
    encoded_images = []

    # Iterate through all the images (pages) and convert to base64
    for i, image in enumerate(images):
        print(f"Processing page {i+1} of {pdf_path}...")
        encoded_image = encode_image_to_base64(image)
        encoded_images.append(encoded_image)

    # Send all the images as a single request to Gemini API
    result = send_images_to_gemini(encoded_images)

    if result:
        print(f"Result: {result}")
        create_presentation(result)


# Function to convert an image to Base64 encoding
def encode_image_to_base64(image: Image.Image):
    # Convert the image to a byte stream
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    # Encode the image to Base64
    encoded_image = base64.b64encode(img_byte_arr).decode("utf-8")
    return encoded_image


# Function to send the list of images (encoded as Base64) to the Gemini API
def send_images_to_gemini(encoded_images):
    prompt = """
    Please act as a knowledgeable professor with deep expertise in explaining complex concepts across various subjects. For each slide, provide the following:

    1. **Slide Title**: The main title of the slide.
    2. **Detailed Explanation**: A 4-6 line explanation of the topic. This should include:
    - A concise but thorough description of the concept.
    - Important details that should not be missed, ensuring that the explanation is comprehensive for someone learning the topic.
    - Examples where relevant, or brief analogies that could help clarify complex ideas.

    The slides should follow a **logical flow** so that each slide builds on the previous one. The content should be clear, detailed, and aimed at educating someone who may not be familiar with the topic, ensuring that no important details are omitted.

    ### Example Breakdown for One Slide:
    - **Slide Title**: Introduction to Nondeterminism (or any other subject, e.g., "Photosynthesis in Plants")
    - **Detailed Explanation**:
    "Nondeterminism is a concept where multiple possible outcomes or paths exist for a given process or decision. Unlike deterministic systems, where there is only one path to follow, nondeterminism allows for exploration of all possible options. This concept is useful in various fields, including computer science, philosophy, and even economics, to model situations where outcomes are not predetermined."

    This approach will ensure that every slide is rich with detail and the content is focused on educating the audience, similar to how a professor would explain the topic in a lecture.


    """

    try:
        parts = []
        parts.append({"text": prompt})

        # Add images with size check
        for i, encoded_image in enumerate(encoded_images):
            # Check if we're not exceeding Gemini's limits
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


# Function to create a PowerPoint presentation from Gemini's output
def create_presentation(gemini_response):
    presentation = Presentation()

    # Split the Gemini response by slides (assumed format)
    slides = gemini_response.split(
        "\n\n"
    )  # Assuming each slide is separated by new lines

    for slide in slides:
        lines = slide.strip().split("\n")
        if len(lines) > 1:
            slide_title = lines[0].replace("Slide Title:", "").strip()
            slide_explanation = (
                "\n".join(lines[1:]).replace("Detailed Explanation:", "").strip()
            )

            # Create a new slide with a title and content
            slide_layout = presentation.slide_layouts[1]  # Title and Content layout
            slide_object = presentation.slides.add_slide(slide_layout)

            # Set slide title
            title = slide_object.shapes.title
            title.text = slide_title

            # Set slide content
            content = slide_object.shapes.placeholders[1]
            content.text = slide_explanation

    # Save the PowerPoint file
    presentation.save("presentation.pptx")
    print("PowerPoint presentation saved as 'presentation.pptx'.")


# Take the file path or directory path as input
input_path = input("Enter the file or directory path containing PDF files: ")

# Process the provided input path
process_pdfs(input_path)
