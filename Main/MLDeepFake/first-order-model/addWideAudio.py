from moviepy.editor import *
videoclip = VideoFileClip("result.mp4")
audioclip = AudioFileClip("resources/Wideaudio.mp3")

new_audioclip = CompositeAudioClip([audioclip])
videoclip.audio = new_audioclip
videoclip.write_videofile("finalWideResult.mp4")