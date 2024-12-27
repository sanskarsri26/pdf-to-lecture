from pptx import Presentation
from pptx.util import Inches, Pt

# Create a presentation object
prs = Presentation()

# Function to add a slide with a title and content
def add_slide(title, content):
    slide_layout = prs.slide_layouts[1]  # Using title and content layout
    slide = prs.slides.add_slide(slide_layout)
    title_placeholder = slide.shapes.title
    content_placeholder = slide.placeholders[1]

    title_placeholder.text = title
    content_placeholder.text = content


# Function to add a slide with bullet points
def add_bullet_slide(title, bullet_points):
    slide_layout = prs.slide_layouts[1]  # Using title and content layout
    slide = prs.slides.add_slide(slide_layout)
    title_placeholder = slide.shapes.title
    content_placeholder = slide.placeholders[1]

    title_placeholder.text = title

    # Creating bullet points
    tf = content_placeholder.text_frame
    tf.clear()  # Clears default text
    for point in bullet_points:
        p = tf.add_paragraph()
        p.text = point
        p.font.size = Pt(18)  # Adjust font size


# Add the title slide
slide_layout = prs.slide_layouts[0]  # Using title slide layout
slide = prs.slides.add_slide(slide_layout)
title = slide.shapes.title
subtitle = slide.placeholders[1]
title.text = "Natural Language Processing (NLP): A Deep Dive"
subtitle.text = "A Lecture in 3 Parts\n[Your Name/Institution]\n[Date]"

# Part 1: Introduction to NLP
add_slide(
    "What is NLP?",
    "NLP is a branch of AI that focuses on enabling computers to understand, interpret, and generate human language. "
    "It bridges the gap between human communication and computer understanding.",
)
add_bullet_slide(
    "Challenges in NLP",
    [
        "Ambiguity: Words and sentences can have multiple meanings.",
        "Context Dependence: Meaning is influenced by surrounding words and context.",
        "Variability: Language changes constantly.",
        "Data Sparsity: High-quality datasets are scarce for some languages.",
    ],
)
add_bullet_slide(
    "Key NLP Tasks",
    [
        "Text Classification: Sentiment analysis, spam detection.",
        "Machine Translation: Converting text from one language to another.",
        "Named Entity Recognition: Identifying people, places, organizations.",
        "Part-of-Speech Tagging: Assigning grammatical tags to words.",
        "Question Answering: Answering questions posed in natural language.",
        "Text Summarization: Creating concise summaries of texts.",
        "Dialogue Systems (Chatbots): Building systems that can engage in conversations.",
    ],
)
add_slide(
    "NLP Pipeline (Simplified)",
    "1. Text Preprocessing\n2. Feature Extraction\n3. Model Training\n4. Output/Prediction",
)

# Part 2: Techniques in NLP
add_bullet_slide(
    "Text Preprocessing",
    [
        "Tokenization: Breaking down text into individual words or sub-word units.",
        "Stop Word Removal: Removing common words that don't carry much meaning.",
        "Stemming/Lemmatization: Reducing words to their root form.",
        "Cleaning: Handling punctuation, special characters, and noise.",
    ],
)
add_bullet_slide(
    "Feature Extraction",
    [
        "Bag-of-Words (BoW): Representing text as a collection of words and their frequencies.",
        "TF-IDF: Weighing words based on their importance in the document.",
        "Word Embeddings (Word2Vec, GloVe, FastText): Representing words as dense vectors.",
        "Contextualized Embeddings (BERT, ELMo): Embeddings that consider the context of a word.",
    ],
)
add_bullet_slide(
    "Machine Learning Models in NLP",
    [
        "Naive Bayes: A probabilistic classifier used for text classification.",
        "Support Vector Machines (SVMs): Effective for text classification and NER.",
        "Recurrent Neural Networks (RNNs): Suitable for sequential data.",
        "Long Short-Term Memory (LSTM) networks: A type of RNN that addresses the vanishing gradient problem.",
        "Transformers (BERT, GPT): Powerful models based on the Transformer architecture.",
    ],
)
add_slide(
    "Deep Learning and NLP",
    "Deep learning has revolutionized NLP, leading to significant improvements in accuracy and performance.\n"
    "Neural networks, particularly recurrent and transformer networks, are widely used.\n"
    "Transfer learning and pre-trained models (like BERT) allow for faster training.",
)

# Part 3: Applications and Future of NLP
add_bullet_slide(
    "Real-World Applications",
    [
        "Chatbots and Virtual Assistants: Siri, Alexa, customer service bots.",
        "Machine Translation: Google Translate, DeepL.",
        "Sentiment Analysis: Monitoring social media, analyzing customer reviews.",
        "Medical Diagnosis Support: Analyzing patient records and medical literature.",
        "Legal Document Review: Automating the review of legal documents.",
        "Search Engines: Improving search relevance and understanding user queries.",
    ],
)
add_bullet_slide(
    "Ethical Considerations",
    [
        "Bias in Data and Models: Addressing biases that lead to unfair or discriminatory outcomes.",
        "Privacy Concerns: Protecting user data and ensuring responsible use of NLP technologies.",
        "Misinformation and Manipulation: Preventing the use of NLP for generating fake news.",
    ],
)
add_bullet_slide(
    "Future Directions",
    [
        "Multimodal NLP: Combining NLP with images and audio.",
        "Explainable NLP: Making NLP models more transparent and understandable.",
        "Low-Resource NLP: Developing NLP for languages with limited data.",
        "Improved Common Sense Reasoning: Enabling NLP systems to reason with common sense knowledge.",
    ],
)

# Add conclusion slide
add_slide(
    "Conclusion",
    "NLP is a rapidly evolving field with enormous potential. By addressing challenges and ethical considerations, "
    "we can create innovative and beneficial applications. Thank you.",
)

# Save the presentation
prs.save("NLP_Lecture.pptx")

print("Presentation created and saved as 'NLP_Lecture.pptx'.")
