# Main script
import subprocess

# Run first script
subprocess.run(["python", "text-extraction.py"])

# Run second script
subprocess.run(["python", "slide-maker.py"])

subprocess.run(["python", "voice-generation.py"])

subprocess.run(["python", "extract-image-from-ppt.py"])

subprocess.run(["python", "sync.py"])
