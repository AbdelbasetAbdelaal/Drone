import os
from PIL import Image

src_dir = r"C:\Users\DELL\.gemini\antigravity\brain\cc3f7da3-8200-4c07-bc28-068b705d12b5"
dest_dir = r"d:\AI_Projects\drone_hunter\assets"
os.makedirs(dest_dir, exist_ok=True)

files = {
    "cyberpunk_bg_1784892626156.jpg": "bg.jpg",
    "building_sprite_1784892634992.jpg": "building.png",
    "player_drone_1784892644984.jpg": "drone.png",
    "enemy_rover_1784892652591.jpg": "rover.png"
}

def remove_white_bg(img_path, out_path):
    img = Image.open(img_path).convert("RGBA")
    data = img.getdata()
    new_data = []
    for item in data:
        # If pixel is bright white, make it transparent
        if item[0] > 235 and item[1] > 235 and item[2] > 235:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    img.save(out_path, "PNG")

for src, dst in files.items():
    in_path = os.path.join(src_dir, src)
    out_path = os.path.join(dest_dir, dst)
    if dst == "bg.jpg":
        # Just copy the background, don't remove white
        Image.open(in_path).save(out_path)
    else:
        remove_white_bg(in_path, out_path)
    print(f"Processed {dst}")
