python demo.py  --config config/vox-adv-256.yaml --driving_video resources/meatbeat.mp4 --source_image resources/BaseIMG.png --checkpoint resources/vox-adv-cpk.pth.tar --relative --adapt_scale
python audioAdd.py --audio resources/meatbeat.mp3 --video result.mp4