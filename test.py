import google.generativeai as genai

# Configure API Key
genai.configure(api_key="AIzaSyCSqsv69biM6pCAkPGEDh9XRM5WpVBraf4")

# Initialize the generative model
model = genai.GenerativeModel("gemini-1.5-flash")

# Define the prompt
prompt = """
Create a professional lecture on Natural Language Processing (NLP), designed for a 1-hour session, including slides and detailed speaker notes. The presentation should cover:

- Introduction to NLP: definition, importance, and real-world applications.
- How NLP Works: breaking down key components like tokenization, parsing, and semantics.
- Core Techniques: overview of machine learning, deep learning, and transformer models in NLP.
- Real-World Challenges: handling ambiguity, context, and large datasets.
- Future of NLP: trends like multilingual models, real-time processing, and ethical considerations.

Output Format:
- A title for each slide.
- The content of each slide (bullet points or visuals).
- A concise script for the speaker, specifying what to say for each slide (timed so that the session runs for approximately 1 hour).

Keep the speaker's script engaging and concise, with enough depth to hold the audience's attention. Allocate about 2–5 minutes per slide based on content complexity. Highlight where visuals or animations should be included.
"""

# Generate content
response = model.generate_content(prompt)

# Display the generated content
print(response)
