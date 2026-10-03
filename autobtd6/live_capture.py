"""Capture the visible game client only, without moving or focusing the game."""
import io
import sys
import windowed_input

if not windowed_input.is_game_foreground():
    raise SystemExit('BTD6 is not visible in the guest desktop')
image = windowed_input.screenshot()
image.thumbnail((960, 540))
output = io.BytesIO()
image.convert('RGB').save(output, format='JPEG', quality=76)
sys.stdout.buffer.write(output.getvalue())
