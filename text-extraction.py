import os
import base64
import httpx
from pdf2image import convert_from_path
from PIL import Image
import io
import google.generativeai as genai

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

    # Iterate through all the images (pages) and send to Gemini API
    for i, image in enumerate(images):
        print(f"Processing page {i+1} of {pdf_path}...")
        result = send_image_to_gemini(image)
        print(f"Result for page {i+1}: {result}")


# Function to send an image (encoded as Base64) to the Gemini API
def send_image_to_gemini(image: Image.Image):
    # Convert the image to a byte stream
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    # Encode the image to Base64
    encoded_image = base64.b64encode(img_byte_arr).decode("utf-8")

    # Define the prompt you want to use
    prompt = """
    Please analyze the attachment and create a series of slides based on the content. For each slide, break down the key concepts, explanations, and visual elements. Send the slides as images in byte-encoded form (Base64). Each slide should be designed with a clean, professional layout, containing bullet points, diagrams, and any other necessary visual aids to enhance understanding. The slides should follow a logical sequence and be easy to understand for someone learning the subject.

    Once the analysis is done, send each slide as an image in bytes encoded form (Base64) along with the content and description.
    """
    # Send the request with the image (Base64 encoded) and text
    response = model.generate_content(
        [{"mime_type": "image/jpeg", "data": encoded_image}, prompt]
    )

    return response.text


# Take the file path or directory path as input
input_path = input("Enter the file or directory path containing PDF files: ")

# Process the provided input path
process_pdfs(input_path)
