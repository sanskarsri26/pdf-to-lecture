import fitz  # PyMuPDF for PDF processing
import base64
import io
import httpx


# Function to extract images from a PDF file
def extract_images_from_pdf(pdf_path):
    images = []
    doc = fitz.open(pdf_path)  # Open the PDF file
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Load each page
        image_list = page.get_images(full=True)  # Get all images on the page

        for img_index, img in enumerate(image_list):
            xref = img[0]  # Get the xref of the image
            base_image = doc.extract_image(xref)  # Extract the image
            image_bytes = base_image["image"]  # Get the image bytes
            images.append(image_bytes)
    return images


# Function to convert image to Base64 (no saving to disk)
def image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")


# Function to send image to Gemini API
def send_image_to_gemini(image_bytes, prompt, api_key):
    # Convert the image bytes to base64
    image_base64 = image_to_base64(image_bytes)

    # Define the API URL for Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }

    # Prepare the payload without mime_type and data in parts[1]
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},  # Adding text prompt
                    {"image": image_base64},  # Directly adding the image base64 encoded
                ]
            }
        ]
    }

    # Send the request to the Gemini API
    response = httpx.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()  # Return the response if successful
    else:
        return f"Error: {response.status_code} - {response.text}"  # Error handling


# Function to handle multiple images from PDF
def send_multiple_images_from_pdf(pdf_path, prompt, api_key):
    images = extract_images_from_pdf(pdf_path)
    responses = []

    for image in images:
        response = send_image_to_gemini(image, prompt, api_key)
        responses.append(response)

    return responses


# Example function to call for a single image from PDF
def main():
    api_key = "AIzaSyCSqsv69biM6pCAkPGEDh9XRM5WpVBraf4"
    pdf_path = input(
        "Enter the full path to the PDF file: "
    )  # Ask user for PDF file path
    prompt = "Describe the content of the images in this PDF."

    response = send_multiple_images_from_pdf(pdf_path, prompt, api_key)
    print(response)


if __name__ == "__main__":
    main()
