from gtts import gTTS  # Using gTTS instead of pyttsx3 for better performance
import re
from pptx import Presentation
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os
from tqdm import tqdm  # For progress bars


class PresentationSyncer:
    def __init__(self):
        self.language = "en"

    def parse_script(self, script_content):
        """Parse the script content into sections by slides."""
        sections = re.split(r"\*\*Slide \d+:", script_content)[
            1:
        ]  # More efficient splitting
        return [section.strip() for section in sections]

    def clean_text(self, text):
        """Remove markdown formatting and parenthetical directions."""
        # Combine multiple regex operations into one pass
        text = re.sub(r"\*\*|\*|\(.*?\)|Slide \d+:.*?\n", "", text)
        return text.strip()

    def create_audio_for_section(self, args):
        """Create audio file for a single section."""
        section, output_path, index = args
        clean_section = self.clean_text(section)

        try:
            tts = gTTS(text=clean_section, lang=self.language, slow=False)
            tts.save(str(output_path))
            return index, output_path
        except Exception as e:
            print(f"Error processing slide {index + 1}: {str(e)}")
            return index, None

    def create_audio_segments(self, script_sections, output_dir):
        """Convert text sections to audio files using parallel processing."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Prepare arguments for parallel processing
        audio_files = []
        args_list = []
        for i, section in enumerate(script_sections):
            audio_file = output_dir / f"slide_{i+1}.mp3"
            audio_files.append(audio_file)
            args_list.append((section, audio_file, i))

        # Process sections in parallel with progress bar
        print("Converting text to speech...")
        with ThreadPoolExecutor(
            max_workers=min(os.cpu_count(), len(script_sections))
        ) as executor:
            list(
                tqdm(
                    executor.map(self.create_audio_for_section, args_list),
                    total=len(args_list),
                    desc="Processing slides",
                )
            )

        return audio_files

    def process_presentation(self, script_file, output_dir):
        """Process the entire presentation."""
        # Read script content
        with open(script_file, "r", encoding="utf-8") as f:
            script_content = f.read()

        # Parse script into sections
        print("Parsing script...")
        script_sections = self.parse_script(script_content)

        # Create audio segments
        audio_files = self.create_audio_segments(script_sections, output_dir)

        print(f"\nProcessing complete. Audio files created in {output_dir}")
        return audio_files


def main():
    # Example usage
    syncer = PresentationSyncer()
    output_dir = "output"

    try:
        audio_files = syncer.process_presentation(
            script_file="voice.txt", output_dir=output_dir
        )
        print(f"\nSuccessfully created {len(audio_files)} audio files.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
