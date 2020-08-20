from moviepy.editor import *
videoclip = VideoFileClip("result.mp4")
audioclip = AudioFileClip("resources/audio.mp3")

new_audioclip = CompositeAudioClip([audioclip])
videoclip.audio = new_audioclip
videoclip.write_videofile("finalResult.mp4")