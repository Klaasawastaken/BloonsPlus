"""Build matching vector and Discord-upload banner assets, and install methods."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent.parent
assets = root / 'docs/assets'
svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="360" viewBox="0 0 1280 360" role="img" aria-labelledby="title desc"><title id="title">The Bloons+ community</title><desc id="desc">Join our Discord. Better runs start together.</desc><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#172d27"/><stop offset="1" stop-color="#243d35"/></linearGradient><linearGradient id="coral" x2="1" y2="1"><stop stop-color="#ffb198"/><stop offset="1" stop-color="#ed725d"/></linearGradient></defs><rect width="1280" height="360" rx="30" fill="url(#bg)"/><circle cx="1100" cy="180" r="210" fill="none" stroke="#456357"/><circle cx="1100" cy="180" r="145" fill="none" stroke="#456357"/><circle cx="1100" cy="180" r="90" fill="#2b483e"/><g transform="translate(1036 116) scale(2)"><rect width="64" height="64" rx="20" fill="url(#coral)"/><path d="M31 13c-10 0-17 7-17 17 0 9 6 16 14 19l-3 5h12l-3-5c8-3 14-10 14-19 0-10-7-17-17-17Z" fill="#fff"/><circle cx="45" cy="41" r="12" fill="#253b3d"/><path d="M45 36v10m-5-5h10" stroke="#fff" stroke-width="3" stroke-linecap="round"/></g><circle cx="935" cy="130" r="9" fill="#f5aa8b"/><circle cx="1220" cy="242" r="6" fill="#b7d5c1"/><text x="58" y="69" fill="#b7d5c1" font-family="Segoe UI,Arial,sans-serif" font-size="15" font-weight="600" letter-spacing="3">BLOONS+ / COMMUNITY</text><text x="56" y="153" fill="#f4f6ef" font-family="Segoe UI,Arial,sans-serif" font-size="55" font-weight="700" letter-spacing="-2">Better runs start together.</text><text x="59" y="203" fill="#b7c9bf" font-family="Segoe UI,Arial,sans-serif" font-size="21">Share strategies. Find help. See what’s next.</text><rect x="58" y="252" width="216" height="52" rx="16" fill="#f5aa8b"/><text x="83" y="285" fill="#253d36" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">Join the Discord ↗</text><text x="300" y="284" fill="#b7c9bf" font-family="Segoe UI,Arial,sans-serif" font-size="16">bloonsplus.com</text></svg>'''
(assets/'discord-banner.svg').write_text(svg,encoding='utf-8')
im = Image.new('RGB',(1280,360),'#172d27'); d = ImageDraw.Draw(im)
for radius in (210,145): d.ellipse((1100-radius,180-radius,1100+radius,180+radius),outline='#456357',width=1)
d.ellipse((1010,90,1190,270),fill='#2b483e')
d.rounded_rectangle((1036,116,1164,244),radius=40,fill='#ef987e')
d.ellipse((1064,142,1132,214),fill='#ffffff')
d.polygon([(1088,208),(1080,224),(1108,224),(1100,208)],fill='white')
d.ellipse((1102,174,1150,222),fill='#253b3d')
d.line((1126,187,1126,209),fill='white',width=6);d.line((1115,198,1137,198),fill='white',width=6)
fontdir=Path('C:/Windows/Fonts')
def font(size,bold=False): return ImageFont.truetype(str(fontdir/('segoeuib.ttf' if bold else 'segoeui.ttf')),size)
d.text((58,45),'BLOONS+ / COMMUNITY',font=font(16,True),fill='#b7d5c1')
d.text((56,99),'Better runs start together.',font=font(55,True),fill='#f4f6ef')
d.text((59,176),'Share strategies. Find help. See what’s next.',font=font(21),fill='#b7c9bf')
d.rounded_rectangle((58,252,274,304),radius=16,fill='#f5aa8b')
d.text((82,263),'Join the Discord',font=font(18,True),fill='#253d36')
d.text((300,263),'bloonsplus.com',font=font(16),fill='#b7c9bf')
im.save(assets/'discord-banner.png',optimize=True)

p=root/'docs/download/index.html';text=p.read_text(encoding='utf-8')
methods='''<section class="wrap section" id="installation-methods"><div class="section-heading"><div><div class="eyebrow">INSTALL YOUR WAY</div><h2>Choose your installation method.</h2></div></div><div class="requirements-grid"><article><span>RECOMMENDED</span><h3>Windows installer</h3><p>Download BloonsPlusSetup.exe above and run it. It installs the desktop app and its dependencies. Leave VM setup enabled to continue with the guided game setup.</p><a class="text-link" href="#start">Follow the installation steps →</a></article><article><span>EXISTING SETUP</span><h3>Connect your VM</h3><p>Already have a Bloons+ VM? Open Settings and continue setup. The app checks existing components and resumes missing steps. Use the VM update button to update its app.</p><a class="text-link" href="../wiki/vm-connection/">Connection troubleshooting →</a></article><article><span>DEVELOPERS</span><h3>Run from source</h3><p>Clone the repository, install the pinned dependencies and launch the desktop app. The repository includes the build instructions.</p><a class="text-link" href="https://github.com/Klaasawastaken/BloonsPlus/blob/main/docs/developer/GITHUB_SETUP.md">Source installation →</a></article></div></section>'''
if 'id="installation-methods"' not in text:
    text=text.replace('<section class="wrap section" id="start">',methods+'<section class="wrap section" id="start">')
p.write_text(text,encoding='utf-8')
