from moviepy.editor import *
import argparse, sys

parser=argparse.ArgumentParser()
parser.add_argument('--audio', help='Set audio source')
parser.add_argument('--video', help='Set video source')
args=parser.parse_args()

videoclip = VideoFileClip(args.video)
audioclip = AudioFileClip(args.audio)

new_audioclip = CompositeAudioClip([audioclip])
videoclip.audio = new_audioclip
videoclip.write_videofile("finalResult.mp4")