import fitz  # PyMuPDF
import base64
import os


# Function to extract text from the PDF
def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        return f"An error occurred while extracting text: {e}"


# Function to extract images and convert them to base64
def extract_images_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        image_list = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            img_list = page.get_images(full=True)

            for img_index, img in enumerate(img_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Convert the image to base64
                encoded_image = base64.b64encode(image_bytes).decode("utf-8")
                image_list.append(encoded_image)

        return image_list
    except Exception as e:
        return f"An error occurred while extracting images: {e}"


# Commented out API portion
# Function to send data to the Gemini API
# def send_to_gemini_api(text, images=None):
#     url = "https://gemini-api-endpoint"  # Replace with Gemini API endpoint
#     headers = {
#         "Authorization": "Bearer YOUR_API_KEY",  # Replace with your API key
#         "Content-Type": "application/json",
#     }
#     data = {
#         "text": text,
#         "images": images,  # Optional: Only include if you have image data
#     }
#     response = requests.post(url, json=data, headers=headers)
#     return response.json()


# Example usage
def main():
    # Take the full file path as input
    file_path = input("Enter the full path to the PDF file: ").strip()

    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    # Extract text from the PDF
    text = extract_text_from_pdf(file_path)
    print("\nExtracted Text:")
    print(text)

    # Extract images and encode them as base64
    images = extract_images_from_pdf(file_path)
    print("\nExtracted Images (Base64 encoded):")
    for idx, img in enumerate(images):
        print(
            f"Image {idx + 1}: {img[:50]}..."
        )  # Show the first 50 characters of base64 string

    # Commented out: Sending data to Gemini API (for now)
    # response = send_to_gemini_api(text, images)
    # print("\nAPI Response:")
    # print(response)


if __name__ == "__main__":
    main()
