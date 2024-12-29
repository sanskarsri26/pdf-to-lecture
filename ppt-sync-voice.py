import pyttsx3
import re
from pptx import Presentation
from pathlib import Path
import time


class PresentationSyncer:
    def __init__(self):
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        # Set default voice properties
        self.engine.setProperty("rate", 150)  # Speaking rate
        self.engine.setProperty("volume", 0.9)  # Volume (0-1)

    def parse_script(self, script_content):
        """Parse the script content into sections by slides."""
        # Split content by slide markers
        slide_sections = []
        current_section = []

        for line in script_content.split("\n"):
            if line.strip().startswith("**Slide"):
                if current_section:
                    slide_sections.append("\n".join(current_section))
                current_section = []
            current_section.append(line)

        if current_section:
            slide_sections.append("\n".join(current_section))

        return slide_sections

    def clean_text(self, text):
        """Remove markdown formatting and parenthetical directions."""
        # Remove markdown formatting
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)

        # Remove parenthetical directions
        text = re.sub(r"\(.*?\)", "", text)

        # Remove slide headers
        text = re.sub(r"Slide \d+:.*?\n", "", text)

        return text.strip()

    def create_audio_segments(self, script_sections, output_dir):
        """Convert text sections to audio files."""
        audio_files = []
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        for i, section in enumerate(script_sections):
            # Clean the text
            clean_section = self.clean_text(section)

            # Create output filename
            audio_file = output_dir / f"slide_{i+1}.mp3"

            # Save audio file
            self.engine.save_to_file(clean_section, str(audio_file))
            self.engine.runAndWait()

            audio_files.append(audio_file)

        return audio_files

    def get_slide_durations(self, audio_files):
        """Get durations for each audio file (placeholder - needs audio library)."""
        # This is a placeholder - in a real implementation, you'd use a library
        # like librosa or mutagen to get actual audio durations
        durations = []
        for audio_file in audio_files:
            # Placeholder duration calculation
            with open(audio_file, "rb") as f:
                # This is just an example - real implementation would parse MP3 metadata
                duration = len(f.read()) / 16000  # Rough approximation
                durations.append(duration)
        return durations

    def create_timing_file(self, durations, output_file):
        """Create timing file for PowerPoint."""
        total_time = 0
        with open(output_file, "w") as f:
            for i, duration in enumerate(durations):
                f.write(f"{i+1},{total_time:.2f}\n")
                total_time += duration

    def process_presentation(self, script_file, pptx_file, output_dir):
        """Process the entire presentation."""
        # Read script content
        with open(script_file, "r") as f:
            script_content = f.read()

        # Parse script into sections
        script_sections = self.parse_script(script_content)

        # Create audio segments
        audio_files = self.create_audio_segments(script_sections, output_dir)

        # Get durations
        durations = self.get_slide_durations(audio_files)

        # Create timing file
        timing_file = Path(output_dir) / "timing.txt"
        self.create_timing_file(durations, timing_file)

        print(
            f"Processing complete. Audio files and timing file created in {output_dir}"
        )


def main():
    # Example usage
    syncer = PresentationSyncer()
    syncer.process_presentation(
        script_file="voice.txt", pptx_file="Styled_Slides.pptx", output_dir="output"
    )


if __name__ == "__main__":
    main()
