"""Build separate load/save confirmation panels from JSON.

Run with Python + Pillow. Installs under id_Data; the launcher synchronizes
graphics on startup with Language=1. Backups and previews are saved in
load_save_prompt_debug. No game process, EXE, or DLL is accessed.
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
DEBUG = TOOLS / 'load_save_prompt_debug'
PANEL = (208, 144, 456, 272)
TEXT_AREA = (218, 164, 446, 214)
RESOURCE = b'\x33system\\common_load_chip00\0'
SPECS = {
    'LOAD': (18, 'Muat Permainan?', 'common_load_chip00'),
    'SAVE': (19, 'Simpan Disini?', 'common_save_chip00'),
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def tokenize(data, expected_labels):
    count = struct.unpack_from('<I', data)[0]
    base = count * 4 + 4
    assert count == expected_labels and data[base:base + 2] == b'\x69\x3b', 'Unexpected MES version'
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


def patch_script(original, dialog):
    expected_labels, expected_caption, sprite_name = SPECS[dialog]
    base, before = tokenize(original, expected_labels)
    captions = [(p, r) for p, r in before if r[0] == 0x4d]
    assert len(captions) == 1, 'Expected one confirmation caption'
    pos, caption = captions[0]
    text = bytes((b + 32) & 255 for b in caption[1:-1]).decode('cp932')
    assert text.replace('\u3000', ' ') == expected_caption, 'Unexpected original caption'
    assert original[pos - 27:pos] == (
        b'\x53' + struct.pack('<4H', 276, 236, 208, 144) +
        b'\x52' + struct.pack('<4H', 456, 272, 8, 1) +
        b'\x60' + struct.pack('<4H', 293, 260, 24, 7)
    ), 'Confirmation panel location changed'

    resources = [(p, r) for p, r in before if r == RESOURCE]
    assert len(resources) == 1, 'Expected one common load panel resource'
    replacements = {pos: b'\x4d\0'}
    if dialog == 'SAVE':
        # Both stock scripts use common_load. Give SAVE its identical, unused
        # stock save sprite so load and save can carry different captions.
        replacement = b'\x33system\\' + sprite_name.encode('ascii') + b'\0'
        assert len(replacement) == len(RESOURCE)
        replacements[resources[0][0]] = replacement

    patched = bytearray(original[:base + 2])
    relocated_positions = {}
    for old_pos, raw in before:
        relocated_positions[old_pos] = len(patched)
        patched.extend(replacements.get(old_pos, raw))

    shifted_labels = 0
    for index in range(expected_labels):
        slot = 4 + index * 4
        old_offset = struct.unpack_from('<I', original, slot)[0]
        old_target = base + old_offset
        assert old_target in relocated_positions, 'Label does not target an instruction'
        new_offset = relocated_positions[old_target] - base
        struct.pack_into('<I', patched, slot, new_offset)
        shifted_labels += old_offset != new_offset

    _, after = tokenize(patched, expected_labels)
    assert len(before) == len(after), 'Instruction count changed'
    for (old_pos, old_raw), (_, new_raw) in zip(before, after):
        assert new_raw == replacements.get(old_pos, old_raw), 'Unexpected instruction change'
    old_indices = {p: i for i, (p, _) in enumerate(before)}
    new_indices = {p: i for i, (p, _) in enumerate(after)}
    for index in range(expected_labels):
        old_target = base + struct.unpack_from('<I', original, 4 + index * 4)[0]
        new_target = base + struct.unpack_from('<I', patched, 4 + index * 4)[0]
        assert old_indices[old_target] == new_indices[new_target], 'Label target changed'
    return bytes(patched), {
        'instructions_preserved': len(before),
        'label_targets_preserved': expected_labels,
        'relocated_labels': shifted_labels,
        'caption_bytes_removed': len(caption) - 2,
        'sprite_reference_changed': dialog == 'SAVE',
    }


def build_sprite(original, text):
    sprite = decode(original)
    assert sprite.size == (456, 272) and sprite.mode == 'RGB', 'Unexpected panel sprite'
    scale = 4
    mask = Image.new('L', (248 * scale, 128 * scale))
    draw = ImageDraw.Draw(mask)
    # Match the return/reset font; reduce long captions only enough to fit.
    for font_size in range(30, 19, -1):
        font = ImageFont.load_default(size=font_size * scale)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        if right - left <= 220 * scale and bottom - top <= 44 * scale:
            break
    else:
        raise ValueError('Caption is too long for the confirmation panel')
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
    assert diff.getbbox() is None, 'Changed pixels outside the caption area'
    encoded = encode(patched, original)
    assert encoded[:20] == original[:20], 'CRX metadata changed'
    assert decode(encoded).tobytes() == patched.tobytes(), 'CRX roundtrip failed'

    preview = patched.crop(PANEL)
    # Normal Yes/No buttons: destination (296,315), panel origin (276,236).
    buttons = sprite.crop((0, 144, 208, 176))
    red, green, blue = ImageChops.difference(
        buttons, Image.new('RGB', buttons.size, (255, 0, 255))
    ).split()
    button_mask = ImageChops.lighter(ImageChops.lighter(red, green), blue).point(lambda v: 255 if v else 0)
    preview.paste(buttons, (20, 79), button_mask)
    return encoded, preview, font_size, bounds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', type=Path, default=TOOLS / 'load_save_prompts.json')
    args = parser.parse_args()
    entries = json.loads(args.json.read_text(encoding='utf-8-sig'))
    assert isinstance(entries, list) and len(entries) == 2
    messages = {entry['dialog']: entry['message'].replace('\u3000', ' ').strip() for entry in entries}
    assert set(messages) == set(SPECS), 'Expected LOAD and SAVE entries'
    assert all(text and all(32 <= ord(c) <= 126 for c in text) for text in messages.values()), 'Expected one line of Latin text'
    manifest_path = DEBUG / 'installed.json'
    previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    prepared = []
    for dialog, (_, _, sprite_name) in SPECS.items():
        mes_path = ROOT / 'id_Data/MES' / (dialog + '.mes')
        sprite_path = ROOT / 'id_Data/GRP/SYSTEM' / (sprite_name + '.CRX')
        mes_backup = DEBUG / (dialog + '.before_bitmap.mes')
        sprite_backup = DEBUG / (sprite_name + '.original.CRX')
        current_mes = mes_path.read_bytes()
        original_mes = mes_backup.read_bytes() if mes_backup.exists() else current_mes
        original_sprite = (sprite_backup.read_bytes() if sprite_backup.exists() else
                           (ROOT / 'AdvData/GRP/SYSTEM' / (sprite_name + '.CRX')).read_bytes())
        new_mes, checks = patch_script(original_mes, dialog)
        new_sprite, preview, font_size, bounds = build_sprite(original_sprite, messages[dialog])
        assert current_mes in (original_mes, new_mes), f'{dialog}.mes changed since backup; inspect before replacing'
        if sprite_path.exists():
            current_sprite = sprite_path.read_bytes()
            assert current_sprite in (original_sprite, new_sprite) or sha256(current_sprite) == previous.get(dialog, {}).get('sprite_sha256'), f'Unrecognized {dialog} sprite patch'
        prepared.append({
            'dialog': dialog, 'mes_path': mes_path, 'sprite_path': sprite_path,
            'mes_backup': mes_backup, 'sprite_backup': sprite_backup,
            'original_mes': original_mes, 'original_sprite': original_sprite,
            'new_mes': new_mes, 'new_sprite': new_sprite, 'preview': preview,
            'manifest': {
                'message': messages[dialog], 'font_size': font_size,
                'sprite': sprite_name + '.CRX',
                'mes_sha256': sha256(new_mes), 'sprite_sha256': sha256(new_sprite),
                'original_mes_sha256': sha256(original_mes),
                'original_sprite_sha256': sha256(original_sprite),
                'changed_pixel_bounds': bounds, **checks,
            },
        })

    # The stock load/save sprites must be identical before splitting references.
    assert prepared[0]['original_sprite'] == prepared[1]['original_sprite'], 'Stock panels differ; inspect before separating SAVE'
    # Finish validation of both dialogs before replacing any game data.
    DEBUG.mkdir(exist_ok=True)
    for item in prepared:
        for kind in ('mes', 'sprite'):
            if not item[kind + '_backup'].exists():
                item[kind + '_backup'].write_bytes(item['original_' + kind])
    for item in prepared:
        for kind in ('sprite', 'mes'):
            destination = item[kind + '_path']
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(item['new_' + kind])
            assert destination.read_bytes() == item['new_' + kind]
        item['preview'].save(DEBUG / (item['dialog'].lower() + '.preview.png'))
    combined = Image.new('RGB', (512, 128), (245, 245, 245))
    for index, item in enumerate(prepared):
        combined.paste(item['preview'], (index * 264, 0))
    combined.save(DEBUG / 'load_save.preview.png')
    manifest = {item['dialog']: item['manifest'] for item in prepared}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    print('PASS: caption pixels, empty script captions, SAVE resource separation, and label targets verified.')
    print('Runtime check remains: restart the launcher with Language=1 and inspect both confirmations.')


if __name__ == '__main__':
    main()
