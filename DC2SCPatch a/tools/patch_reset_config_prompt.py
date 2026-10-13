"""Build the reset confirmation from JSON using the return prompt's typography.

Run with Python + Pillow. Only option.mes and the reset panel inside
systemconfig_chip00.CRX are patched under id_Data. The original translated MES
and original sprite are backed up under reset_config_debug. The launcher syncs
the sprite when Language=1. No game process or DLL is accessed.

To change the wording, edit reset_config_prompt.json and run this script again.
If option.mes is reimported with the MES tool, rerun this script afterward to
avoid drawing the old fixed-cell text over the generated panel.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops, ImageDraw, ImageFont

from crx_image import decode, encode


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
DEBUG = TOOLS / 'reset_config_debug'
PANEL = (609, 217, 857, 345)
TEXT_AREA = (619, 237, 847, 287)


def tokenize(data):
    count = struct.unpack_from('<I', data)[0]
    base = count * 4 + 4
    assert count == 52 and data[base:base + 2] == b'\x69\x3b', 'Unexpected option.mes version'
    pos = base + 2
    tokens = []
    while pos < len(data):
        op = data[pos]
        if op < 0x29:
            end = pos + 3
        elif op < 0x4e:
            end = data.index(0, pos + (2 if op < 0x2f else 1)) + 1
        else:
            end = pos + 9
        assert end <= len(data), 'Truncated MES instruction'
        tokens.append((pos, data[pos:end]))
        pos = end
    return base, tokens


def suppress_script_caption(original):
    base, before = tokenize(original)
    captions = [(p, raw) for p, raw in before if raw[0] == 0x4d]
    assert len(captions) == 1, 'Expected one reset caption'
    pos, caption = captions[0]
    text = bytes((b + 32) & 255 for b in caption[1:-1]).decode('cp932')
    assert text.replace('\u3000', ' ') == 'Reset Config?', 'Unexpected caption; inspect before patching'
    assert original[pos - 27:pos] == (
        b'\x53' + struct.pack('<4H', 276, 236, 609, 217) +
        b'\x52' + struct.pack('<4H', 857, 345, 6, 1) +
        b'\x60' + struct.pack('<4H', 290, 266, 18, 7)
    ), 'Reset panel location changed'

    # Keep opcode 4D and its terminator; only remove the displayed characters.
    # Label offsets are relative to the version header, not the file start.
    removed = len(caption) - 2
    end = pos + len(caption)
    patched = bytearray(original[:pos] + b'\x4d\0' + original[end:])
    old_positions = {p: i for i, (p, _) in enumerate(before)}
    _, after = tokenize(patched)
    new_positions = {p: i for i, (p, _) in enumerate(after)}
    count = struct.unpack_from('<I', original)[0]
    shifted_labels = 0
    for index in range(count):
        slot = 4 + index * 4
        offset = struct.unpack_from('<I', original, slot)[0]
        old_target = base + offset
        assert old_target in old_positions, 'Label does not target an instruction'
        assert not pos < old_target < end, 'Label enters caption data'
        new_offset = offset - removed if old_target >= end else offset
        shifted_labels += new_offset != offset
        struct.pack_into('<I', patched, slot, new_offset)
        assert old_positions[old_target] == new_positions[base + new_offset], 'Label target changed'

    assert len(before) == len(after), 'Instruction count changed'
    for (old_pos, old_raw), (_, new_raw) in zip(before, after):
        assert new_raw == (b'\x4d\0' if old_pos == pos else old_raw), 'Non-caption instruction changed'
    return bytes(patched), len(before), count, shifted_labels


def build_sprite(original, text):
    sprite = decode(original)
    assert sprite.size == (1152, 752) and sprite.mode == 'RGB', 'Unexpected config sprite'
    scale = 4
    mask = Image.new('L', (248 * scale, 128 * scale))
    draw = ImageDraw.Draw(mask)
    font = ImageFont.load_default(size=30 * scale)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    assert right - left <= 220 * scale and bottom - top <= 44 * scale, 'Caption is too long'
    x = 124 * scale - (right - left) / 2 - left
    y = 45 * scale - (bottom - top) / 2 - top
    draw.text((x, y), text, fill=255, font=font)
    mask = mask.resize((248, 128), Image.Resampling.LANCZOS)
    patched = sprite.copy()
    patched.paste((255, 255, 255), PANEL[:2], mask)
    diff = ImageChops.difference(sprite, patched)
    bounds = diff.getbbox()
    assert bounds is not None
    diff.paste(0, TEXT_AREA)
    assert diff.getbbox() is None, 'Changed pixels outside the reset caption'
    encoded = encode(patched, original)
    assert encoded[:20] == original[:20], 'CRX metadata changed'
    assert decode(encoded).tobytes() == patched.tobytes(), 'CRX roundtrip failed'

    preview = patched.crop(PANEL)
    # These are the unchanged normal-state buttons copied by option.mes.
    preview.paste(sprite.crop((400, 217, 608, 249)), (20, 79))
    return encoded, preview, bounds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', type=Path, default=TOOLS / 'reset_config_prompt.json')
    args = parser.parse_args()
    entries = json.loads(args.json.read_text(encoding='utf-8-sig'))
    assert isinstance(entries, list) and len(entries) == 1
    text = entries[0]['message'].replace('\u3000', ' ').strip()
    assert text and all(32 <= ord(c) <= 126 for c in text), 'Expected one line of Latin text'
    DEBUG.mkdir(exist_ok=True)

    mes_path = ROOT / 'id_Data/MES/option.mes'
    sprite_path = ROOT / 'id_Data/GRP/SYSTEM/systemconfig_chip00.CRX'
    mes_backup = DEBUG / 'option.before_bitmap.mes'
    sprite_backup = DEBUG / 'systemconfig_chip00.original.CRX'
    current_mes = mes_path.read_bytes()
    original_mes = mes_backup.read_bytes() if mes_backup.exists() else current_mes
    original_sprite = (sprite_backup.read_bytes() if sprite_backup.exists() else
                       (ROOT / 'AdvData/GRP/SYSTEM/systemconfig_chip00.CRX').read_bytes())
    new_mes, instructions, labels, shifted = suppress_script_caption(original_mes)
    new_sprite, preview, bounds = build_sprite(original_sprite, text)
    assert current_mes in (original_mes, new_mes), 'option.mes changed since backup; inspect before replacing'

    manifest_path = DEBUG / 'installed.json'
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if sprite_path.exists():
        current_sprite = sprite_path.read_bytes()
        assert current_sprite in (original_sprite, new_sprite) or hashlib.sha256(current_sprite).hexdigest() == previous.get('sprite_sha256'), 'Unrecognized sprite patch'

    # All validation above finishes before either game data file is replaced.
    if not mes_backup.exists():
        mes_backup.write_bytes(original_mes)
    if not sprite_backup.exists():
        sprite_backup.write_bytes(original_sprite)
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    sprite_path.write_bytes(new_sprite)
    mes_path.write_bytes(new_mes)
    assert mes_path.read_bytes() == new_mes and sprite_path.read_bytes() == new_sprite
    preview.save(DEBUG / 'reset_config.preview.png')
    manifest = {
        'message': text,
        'mes_sha256': hashlib.sha256(new_mes).hexdigest(),
        'sprite_sha256': hashlib.sha256(new_sprite).hexdigest(),
        'changed_pixel_bounds': bounds,
        'instructions_preserved': instructions,
        'label_targets_preserved': labels,
        'relocated_labels': shifted,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    print('PASS: only caption payload/label relocation and reset caption pixels changed.')
    print('Runtime check remains: restart the launcher and inspect System Config > Reset.')


if __name__ == '__main__':
    main()
