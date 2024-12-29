from pathlib import Path
import pyttsx3
import re
import google.generativeai as genai

# Configure the API key
genai.configure(api_key="AIzaSyCSqsv69biM6pCAkPGEDh9XRM5WpVBraf4")

# Initialize the model
model = genai.GenerativeModel("gemini-1.5-flash")


def get_text_from_file(file_path):
    """Read text content from a file"""
    return Path(file_path).read_text()


def generate_response(text_content, prompt_template):
    """Generate response using Gemini API with a specific prompt"""
    try:
        # Combine prompt template with text content
        full_prompt = f"{prompt_template}\n\nText Content:\n{text_content}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"


# Example usage
file_path = "output.txt"
text_content = get_text_from_file(file_path)

# Define your specific prompt
prompt_template = "Here is a detailed breakdown of my lecture slides on the concept. I want you to create a speaker script for each slide. The script should focus on what I should say during the lecture, keeping it clear, engaging, and concise. Each slide's explanation should last at least 1 minute and 30 seconds, ensuring the audience fully grasps the key points. Use the provided slide details to craft a professional and engaging delivery."


response = generate_response(text_content, prompt_template)

# Save the response to voice.txt
with open('voice.txt', 'w', encoding='utf-8') as file:
    file.write(response)