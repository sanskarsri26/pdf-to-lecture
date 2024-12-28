from pptx import Presentation
from pptx.util import Inches, Pt

# Create a PowerPoint presentation object
presentation = Presentation()


# Function to add a slide with a title and content
def add_slide(title, content):
    slide_layout = presentation.slide_layouts[1]  # Use layout 1 for title and content
    slide = presentation.slides.add_slide(slide_layout)

    title_placeholder = slide.shapes.title
    content_placeholder = slide.shapes.placeholders[1]

    title_placeholder.text = title
    content_placeholder.text = content


# Slide 1: Title Slide
add_slide(
    "Nondeterminism by Analogy", "Arizona State University logo (insert logo here)"
)

# Slide 2: Outline
add_slide(
    "Outline",
    "1. Navigating a maze (Determinism)\n2. Navigating a maze (Nondeterminism)\n3. Routing packets on the Internet\n4. Planning moves in Chess\n5. Why Nondeterminism?\n6. Summary and Acknowledgements\n7. References and Thank You",
)

# Slide 3: Navigating a Maze (Determinism)
add_slide(
    "Navigating a Maze: Determinism",
    "Deterministic strategy: always take the left-most path\n"
    "Maze 1 (unsolvable with this strategy) and Maze 2 (solvable)\n"
    "Determinism deals with 'what must be'",
)

# Slide 4: Navigating a Maze (Nondeterminism)
add_slide(
    "Navigating a Maze: Nondeterminism",
    "Nondeterminism explores all paths\n"
    "Same mazes as Slide 3, but now all paths are explored\n"
    "Determinism deals with 'what can happen'",
)

# Slide 5: Routing Packets on the Internet
add_slide(
    "Routing Packets on the Internet",
    "A network diagram illustrating possible routes from source (src) to destination (dst)\n"
    "Nodes: circles\nArrows: possible routes",
)

# Slide 6: Planning Moves in Chess
add_slide(
    "Planning Moves in Chess",
    "A game tree showing possible moves for white and black\n"
    "Branching possibilities of chess moves",
)

# Slide 7: Why Nondeterminism?
add_slide(
    "Why Nondeterminism?",
    "Explores the power and uncertainty aspects of nondeterminism\n"
    "Discusses whether it exists in the real world",
)

# Slide 8: Summary and Acknowledgements
add_slide(
    "Summary and Acknowledgements",
    "Summary of analogies used\nSpecial thanks to contributors",
)

# Slide 9: References and Thank You
add_slide(
    "References and Thank You",
    "References: ChessCoach source\nThank you for your attention!",
)

# Save the PowerPoint file
ppt_filename = "Nondeterminism_by_Analogy.pptx"
presentation.save(ppt_filename)

print(f"Presentation saved as {ppt_filename}")
