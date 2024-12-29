import subprocess
import os


def get_audio_duration(audio_file):
    # Get the duration of the audio file in seconds
    command = ["ffmpeg", "-i", audio_file]
    result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    output = result.stderr.decode("utf-8")
    duration_line = next(
        (line for line in output.split("\n") if "Duration" in line), None
    )
    if duration_line:
        duration = duration_line.split(",")[0].split("Duration:")[1].strip()
        h, m, s = map(float, duration.split(":"))
        return h * 3600 + m * 60 + s
    return 0


image_dir = "slides"
audio_dir = "output"
output_video_file = "output_video.mp4"

# List of image and audio files
image_files = sorted([f for f in os.listdir(image_dir) if f.endswith((".jpg", ".png"))])
audio_files = sorted([f for f in os.listdir(audio_dir) if f.endswith(".mp3")])

# Ensure the number of images matches the number of audio files
if len(image_files) != len(audio_files):
    raise ValueError("Number of images and audio files must be the same.")

# Prepare image and audio file paths
image_file_paths = [os.path.join(image_dir, image) for image in image_files]
audio_file_paths = [os.path.join(audio_dir, audio) for audio in audio_files]

# Verify that audio files exist
for audio_file in audio_file_paths:
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

# Create the ffmpeg input arguments
input_files = []
for image_path in image_file_paths:
    input_files.extend(["-i", image_path])
for audio_path in audio_file_paths:
    input_files.extend(["-i", audio_path])

# Create filter_complex to trim images based on audio durations
filter_complex = ""
video_streams = []
audio_streams = []

# First, handle the video streams
for i in range(len(image_files)):
    audio_duration = get_audio_duration(audio_file_paths[i])
    filter_complex += f"[{i}:v]loop=loop=-1:size=1:start=0,trim=duration={audio_duration},setpts=PTS-STARTPTS,format=yuv420p[v{i}];"
    video_streams.append(f"[v{i}]")

# Remove trailing semicolon
filter_complex = filter_complex.rstrip(";")

# Add concat filter without segment mode
filter_complex += (
    f";{' '.join(video_streams)}concat=n={len(image_files)}:v=1:a=0[outv];"
)

# Add audio concatenation
filter_complex += f"{' '.join([f'[{i+len(image_files)}:a]' for i in range(len(audio_files))])}concat=n={len(audio_files)}:v=0:a=1[outa]"

# Update command with additional parameters
command = (
    [
        "ffmpeg",
        "-y",
    ]
    + input_files
    + [
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "[outa]",
        "-c:v",
        "libx264",
        "-vsync",
        "2",
        "-pix_fmt",
        "yuv420p",
        "-acodec",
        "aac",
        output_video_file,
    ]
)


# Run the command
subprocess.run(command)

print(f"Video created successfully: {output_video_file}")
