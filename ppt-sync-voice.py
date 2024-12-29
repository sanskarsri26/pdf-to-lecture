import subprocess
import os


def run_applescript(script):
    process = subprocess.Popen(
        ["osascript", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = process.communicate()
    if err:
        print(f"Error: {err.decode()}")
    return out, err


def get_relative_audio_path(base_dir, output_dir, audio_filename):
    # Construct relative path for audio file inside 'output' directory
    return os.path.join(base_dir, output_dir, audio_filename)


# Path to the directory containing your PowerPoint file
base_dir = "/Users/sanskarsrivastava/Desktop/CSE/pdf-to-lecture"  # The base directory where your pptx file is located
pptx_file = "Styled_Slides.pptx"  # Your PowerPoint file name
output_dir = "output"  # Audio files are inside the 'output' directory

# AppleScript code to sync audio with slides (modified for relative paths)
applescript_code = f"""
tell application "Microsoft PowerPoint"
    set pptFile to "{base_dir}/{pptx_file}"
    open pptFile
    delay 2 -- wait for PowerPoint to load

    set slideCount to count of slides of active presentation
    repeat with i from 1 to slideCount
        -- Construct relative path to the audio file in the 'output' folder
        set audioFile to "{base_dir}/{output_dir}/slide_" & i & ".mp3"
        
        -- Insert the audio file into the slide
        tell slide i of active presentation
            -- Make new sound shape
            set audioShape to make new sound with properties {file name:audioFile}
            
            -- Set auto start and play sound properties
            set auto start of audioShape to true
            set play sound of audioShape to true
        end tell
    end repeat
end tell
"""


# Run the AppleScript from Python
out, err = run_applescript(applescript_code)
if err:
    print(f"Error: {err.decode()}")
else:
    print(f"Success: {out.decode()}")
