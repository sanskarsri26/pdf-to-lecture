from moviepy.editor import *

# Create a simple video clip
clip = ColorClip(
    size=(640, 480), color=(255, 0, 0), duration=2
)  # Red screen, 2 seconds long

# Write to a file
clip.write_videofile("test_video.mp4", fps=24)
