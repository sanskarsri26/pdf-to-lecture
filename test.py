import google.generativeai as genai

genai.configure(api_key="AIzaSyCSqsv69biM6pCAkPGEDh9XRM5WpVBraf4")
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Create a lecture on NLPs with slides")
print(response.text)
