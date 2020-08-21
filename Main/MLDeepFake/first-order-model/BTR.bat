set videoDriver=%1
set audioDriver=%2
python demo.py  --config config/vox-adv-256.yaml --driving_video %videoDriver% --source_image resources/BaseIMG.png --checkpoint resources/vox-adv-cpk.pth.tar --relative --adapt_scale
python audioAdd.py --audio %audioDriver% --video result.mp4