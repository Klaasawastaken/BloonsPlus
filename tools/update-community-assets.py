"""Render the compact Discord artwork for sharing outside the website."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / 'docs/assets/discord-banner.png'
W, H = 1280, 210
image = Image.new('RGB', (W, H), '#214336')
draw = ImageDraw.Draw(image)
for y in range(H):
    t = y / H
    draw.line((0, y, W, y), fill=(int(31 + 13*t), int(64 + 17*t), int(52 + 13*t)))
# Small track and balloons echo the vector version.
draw.arc((735, -58, 895, 242), 30, 290, fill='#7da480', width=13)
for x, y, radius, fill in ((1023, 94, 36, '#ef987e'), (1110, 142, 27, '#f4c878'), (1187, 67, 21, '#8eb9b4')):
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=fill)
    draw.line((x, y+radius, x+4, y+radius+17), fill='#c4d2b8', width=2)
font_dir = Path('C:/Windows/Fonts')
def font(name, size):
    path = font_dir / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()
draw.text((54, 36), 'BLOONS+ COMMUNITY', fill='#b9d2bf', font=font('segoeuib.ttf', 16))
draw.text((54, 74), 'Join the next round.', fill='#f6f8ed', font=font('segoeuib.ttf', 47))
draw.text((55, 150), 'Routes, help and updates in our Discord.', fill='#bdd3c5', font=font('segoeui.ttf', 20))
draw.rounded_rectangle((1013, 156, 1207, 192), radius=17, fill='#f2aa8e')
draw.text((1036, 165), 'JOIN DISCORD', fill='#243c35', font=font('segoeuib.ttf', 15))
image.save(OUT, optimize=True)
print(OUT)
