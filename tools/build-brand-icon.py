"""Rasterize the website balloon mark into the Windows application icon."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent.parent
scale = 8
size = 64 * scale
image = Image.new('RGBA', (size, size))
mask = Image.new('L', image.size)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), 20 * scale, fill=255)
for y in range(size):
    for x in range(size):
        t = (x + y) / (2 * (size - 1))
        image.putpixel((x, y), tuple(round(a + (b - a) * t) for a, b in zip((255,177,152),(237,114,93))) + (mask.getpixel((x,y)),))
draw = ImageDraw.Draw(image)
points = [(31,13)]
def cubic(c1, c2, end):
    start = points[-1]
    for i in range(1,41):
        t = i/40; u = 1-t
        points.append(tuple(u**3*start[k] + 3*u*u*t*c1[k] + 3*u*t*t*c2[k] + t**3*end[k] for k in (0,1)))
cubic((21,13),(14,20),(14,30))
cubic((14,39),(20,46),(28,49))
points += [(25,54),(37,54),(34,49)]
cubic((42,46),(48,40),(48,30))
cubic((48,20),(41,13),(31,13))
draw.polygon([(round(x*scale), round(y*scale)) for x,y in points],fill=(255,255,255,240))
points = [(24,23)]
cubic((21,25),(20,28),(20,31))
draw.line([(int(x*scale),int(y*scale)) for x,y in points],fill='#ee816c',width=3*scale)
draw.ellipse((33*scale,29*scale,57*scale,53*scale),fill='#253b3d')
for a,b in [((45,36),(45,46)),((40,41),(50,41))]:
    draw.line(tuple(int(v*scale) for p in (a,b) for v in p),fill='white',width=3*scale)
    for x,y in (a,b):
        draw.ellipse(((x-1.5)*scale,(y-1.5)*scale,(x+1.5)*scale,(y+1.5)*scale),fill='white')
image.save(root/'bloonsplus.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('Built branded Windows icon.')
