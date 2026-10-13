"""Build the Indonesian return-dialog sprite without editing the game EXE/DLL.

Run with Python + Pillow. The launcher syncs id_Data/GRP to AdvData on startup
when DC2SCPatch.ini has Language=1. Original pixels are preserved in this tool's
prompt_debug directory so the asset can also be rebuilt after startup sync.
"""

from pathlib import Path
import hashlib

from PIL import Image, ImageChops, ImageDraw, ImageFont

from crx_image import decode, encode


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
DEBUG = TOOLS / 'prompt_debug'
TEXT = 'Mau Kembali?'


def main():
    DEBUG.mkdir(exist_ok=True)
    original_path = ROOT / 'AdvData/GRP/SYSTEM/yn_chip01.CRX'
    blank_path = ROOT / 'AdvData/GRP/SYSTEM/yn_chip00.CRX'
    backup = DEBUG / 'yn_chip01.original.CRX'
    original_bytes = backup.read_bytes() if backup.exists() else original_path.read_bytes()
    original = decode(original_bytes)
    blank = decode(blank_path.read_bytes())
    # These two stock sprites differ only in the Japanese return prompt.
    assert ImageChops.difference(original, blank).getbbox() == (241, 32, 401, 58)
    if not backup.exists():
        backup.write_bytes(original_bytes)

    patched = original.copy()
    japanese_bounds = (241, 32, 401, 58)
    patched.paste(blank.crop(japanese_bounds), japanese_bounds)

    # Pillow's bundled font avoids system-font dependencies. Render only the
    # text mask at 4x resolution; preserve all other sprite pixels exactly.
    scale = 4
    mask = Image.new('L', (patched.width * scale, patched.height * scale))
    draw = ImageDraw.Draw(mask)
    font = ImageFont.load_default(size=30 * scale)
    left, top, right, bottom = draw.textbbox((0, 0), TEXT, font=font)
    x = 332 * scale - (right - left) / 2 - left
    y = 45 * scale - (bottom - top) / 2 - top
    draw.text((x, y), TEXT, fill=255, font=font)
    mask = mask.resize(patched.size, Image.Resampling.LANCZOS)
    patched.paste((255, 255, 255), (0, 0), mask)

    allowed = (218, 20, 446, 70)
    diff = ImageChops.difference(original, patched)
    diff.paste(0, allowed)
    assert diff.getbbox() is None, 'Changes escaped the prompt text area'

    encoded = encode(patched, original_bytes)
    result = decode(encoded)
    assert result.tobytes() == patched.tobytes(), 'CRX roundtrip mismatch'
    assert encoded[:20] == original_bytes[:20], 'CRX metadata changed'
    destination = ROOT / 'id_Data/GRP/SYSTEM/yn_chip01.CRX'
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != encoded:
            raise FileExistsError(f'Refusing to overwrite a different patch: {destination}')
    else:
        destination.write_bytes(encoded)
    assert decode(destination.read_bytes()).tobytes() == patched.tobytes()
    result.save(DEBUG / 'yn_chip01.indonesian.png')
    result.crop((208, 0, 456, 128)).save(DEBUG / 'return_prompt.preview.png')
    print(f'Installed: {destination}')
    print(f'SHA256: {hashlib.sha256(encoded).hexdigest()}')
    print('PASS: CRX metadata, decoded pixels, and unchanged frame/buttons')
    print('Runtime check: restart DC2SCLauncher.exe with Language=1 and open the return dialog.')


if __name__ == '__main__':
    main()
