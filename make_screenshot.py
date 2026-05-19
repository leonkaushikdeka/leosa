from PIL import Image, ImageDraw, ImageFont
import os

os.chdir("D:/active projects/leosa")

lines = [
    "$ pip install -r requirements.txt",
    "Successfully installed torch-2.12.0 torchvision-0.27.0",
    "Successfully installed ultralytics-8.4.51 ultralytics-thop-2.0.19",
    "",
    "$ python -c \"from ForensicSight_v2 import *\"",
    "ForensicSight v2.0 loaded successfully",
    "",
    "$ python --version",
    "Python 3.13.11",
]

img_w, img_h = 900, len(lines) * 24 + 80
img = Image.new("RGB", (img_w, img_h), "#1e1e2e")
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, img_w, 32], fill="#313244")
draw.text((15, 8), "ForensicSight v2.0 - D:\\active projects\\leosa", fill="#cdd6f4", font=ImageFont.load_default())

try:
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
except:
    font = ImageFont.load_default()

y = 42
for line in lines:
    if line.startswith("$"):
        draw.text((15, y), line, fill="#89b4fa", font=font)
    elif "successfully" in line.lower():
        draw.text((15, y), line, fill="#a6e3a1", font=font)
    else:
        draw.text((15, y), line, fill="#cdd6f4", font=font)
    y += 24

os.makedirs("screenshots", exist_ok=True)
img.save("screenshots/demo.png")
print("Screenshot saved")
