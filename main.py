import subprocess

# Take input from the user
user_input = "/Users/sanskarsrivastava/Downloads/M3-NFA-L1-NondeterminismByAnalogy-handout.pdf"

# Run first script with the user input as an argument
subprocess.run(["python", "text-extraction.py", user_input]) # Break the pdf into images and send to gemini to get the information on it

# Run the other scripts
subprocess.run(["python", "slide-maker.py"])    # the information from the gemini is used to create slides
subprocess.run(["python", "lecture-generation.py"]) # the slides are used to generate the lecture
subprocess.run(["python", "audio-generation.py"]) # the lecture is used to generate the audio
subprocess.run(["python", "extract-image-from-ppt.py"]) # the slides are used to extract images from the slides
subprocess.run(["python", "sync.py"])   # the images and audio are synced to create the final video
