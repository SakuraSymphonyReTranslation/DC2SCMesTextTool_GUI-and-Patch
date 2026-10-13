"""Build the DC2SC exit panel with the confirmed DC2TY popup typography.

Windows + Python + Pillow. Uses an offscreen GDI font context only; it does not
open, inspect, or control game/desktop windows. Installs a dedicated CRX and
updates title_01.mes under id_Data. No EXE or DLL changes are needed.
"""

import argparse
import ctypes
from ctypes import wintypes as wt
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops

from crx_image import decode, encode
from patch_load_save_prompts import sha256, tokenize


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
DEBUG = TOOLS / 'exit_prompt_debug'
PANEL = (208, 0, 456, 128)
TEXT_AREA = (218, 16, 446, 70)
OLD_RESOURCE = b'\x33SYSTEM\\yn_chip00\0'
NEW_RESOURCE = b'\x33SYSTEM\\yn_exit00\0'
FONT_FACE = 'MS PGothic'


class Fixed(ctypes.Structure):
    _fields_ = [('fract', wt.WORD), ('value', ctypes.c_short)]


class Mat2(ctypes.Structure):
    _fields_ = [(name, Fixed) for name in ('eM11', 'eM12', 'eM21', 'eM22')]


class GlyphMetrics(ctypes.Structure):
    _fields_ = [('black_x', wt.UINT), ('black_y', wt.UINT),
                ('origin', wt.POINT), ('advance_x', ctypes.c_short),
                ('advance_y', ctypes.c_short)]


def render_label(text):
    """Match DC2TY's visible result using GDI metrics and 0..4 alpha.

    The confirmed sample's glyphs and 144x24 bitmap match MS PGothic at 28 px.
    Keep the reference's 216 px width limit and crop visible glyphs.
    Use GetGlyphOutline on an offscreen DC, without DLL hooks or screen access.
    """
    gdi = ctypes.WinDLL('gdi32', use_last_error=True)

    def function(name, result, arguments):
        fn = getattr(gdi, name)
        fn.restype, fn.argtypes = result, arguments
        return fn

    create_dc = function('CreateCompatibleDC', wt.HDC, [wt.HDC])
    delete_dc = function('DeleteDC', wt.BOOL, [wt.HDC])
    create_font = function('CreateFontW', wt.HFONT,
                           [ctypes.c_int] * 5 + [wt.DWORD] * 8 + [wt.LPCWSTR])
    select = function('SelectObject', wt.HGDIOBJ, [wt.HDC, wt.HGDIOBJ])
    delete_object = function('DeleteObject', wt.BOOL, [wt.HGDIOBJ])
    text_extent = function('GetTextExtentPoint32W', wt.BOOL,
                           [wt.HDC, wt.LPCWSTR, ctypes.c_int, ctypes.POINTER(wt.SIZE)])
    glyph_outline = function('GetGlyphOutlineW', wt.DWORD,
                             [wt.HDC, wt.UINT, wt.UINT, ctypes.POINTER(GlyphMetrics),
                              wt.DWORD, ctypes.c_void_p, ctypes.POINTER(Mat2)])
    text_face = function('GetTextFaceW', ctypes.c_int,
                         [wt.HDC, ctypes.c_int, wt.LPWSTR])
    dc = create_dc(None)
    if not dc:
        raise RuntimeError('Cannot create offscreen font context')
    matrix = Mat2()
    matrix.eM11.value = matrix.eM22.value = 1
    try:
        for size in range(28, 17, -1):
            # FW_NORMAL, ANSI_CHARSET, ANTIALIASED_QUALITY, regular weight.
            font = create_font(-size, 0, 0, 0, 400, 0, 0, 0, 0, 0, 0, 4, 0, FONT_FACE)
            if not font:
                raise RuntimeError('Cannot create popup font')
            previous = select(dc, font)
            try:
                face = ctypes.create_unicode_buffer(128)
                assert text_face(dc, len(face), face) and face.value == FONT_FACE, 'Expected popup font unavailable'
                extent = wt.SIZE()
                assert text_extent(dc, text, len(text), ctypes.byref(extent))
                if extent.cx > 216:
                    continue
                canvas = bytearray(256 * 64)
                for i, char in enumerate(text):
                    prefix = wt.SIZE()
                    if i:
                        assert text_extent(dc, text[:i], i, ctypes.byref(prefix))
                    metrics = GlyphMetrics()
                    length = glyph_outline(dc, ord(char), 6, ctypes.byref(metrics),
                                           0, None, ctypes.byref(matrix))
                    assert length != 0xffffffff and length <= 65536, 'Cannot measure glyph'
                    if not length:
                        continue
                    glyph = (ctypes.c_ubyte * length)()
                    result = glyph_outline(dc, ord(char), 6, ctypes.byref(metrics),
                                           length, glyph, ctypes.byref(matrix))
                    assert result != 0xffffffff, 'Cannot rasterize glyph'
                    stride = (metrics.black_x + 3) & ~3
                    assert stride * metrics.black_y <= length
                    for gy in range(metrics.black_y):
                        for gx in range(metrics.black_x):
                            x = 4 + prefix.cx + metrics.origin.x + gx
                            y = 40 - metrics.origin.y + gy
                            assert 0 <= x < 256 and 0 <= y < 64, 'Glyph exceeds canvas'
                            alpha = (glyph[gy * stride + gx] + 8) // 16
                            assert 0 <= alpha <= 4
                            canvas[y * 256 + x] = max(canvas[y * 256 + x], alpha)
                mask = Image.frombytes('L', (256, 64), bytes(canvas))
                bounds = mask.getbbox()
                if not bounds:
                    continue
                mask = mask.crop(bounds)
                if mask.width > 216 or mask.height > 28:
                    continue
                # Map native engine coverage levels to Pillow alpha coverage.
                return mask.point(lambda value: value * 255 // 4), size
            finally:
                select(dc, previous)
                delete_object(font)
    finally:
        delete_dc(dc)
    raise ValueError('Caption does not fit the exit panel')


def patch_script(original):
    base, before = tokenize(original, 27)
    captions = [(pos, raw) for pos, raw in before if raw[0] == 0x4d and len(raw) > 2]
    assert len(captions) == 1, 'Expected one nonempty title caption'
    pos, caption = captions[0]
    text = bytes((b + 32) & 255 for b in caption[1:-1]).decode('cp932')
    assert text.replace('\u3000', ' ') == 'Ingin Keluar?', 'Unexpected exit caption'
    assert original[pos - 27:pos] == (
        b'\x53' + struct.pack('<4H', 276, 236, 208, 0) +
        b'\x52' + struct.pack('<4H', 456, 128, 8, 1) +
        b'\x60' + struct.pack('<4H', 306, 266, 24, 7)
    ), 'Exit panel location changed'
    references = [p for p, raw in before if raw == OLD_RESOURCE]
    assert len(references) == 4 and len(OLD_RESOURCE) == len(NEW_RESOURCE)
    replacements = {p: NEW_RESOURCE for p in references}
    replacements[pos] = b'\x4d\0'
    patched = bytearray(original[:base + 2])
    positions = {}
    for old_pos, raw in before:
        positions[old_pos] = len(patched)
        patched.extend(replacements.get(old_pos, raw))
    shifted = 0
    for index in range(27):
        slot = 4 + index * 4
        old_offset = struct.unpack_from('<I', original, slot)[0]
        assert base + old_offset in positions, 'Label does not target an instruction'
        new_offset = positions[base + old_offset] - base
        struct.pack_into('<I', patched, slot, new_offset)
        shifted += new_offset != old_offset
    _, after = tokenize(patched, 27)
    assert len(before) == len(after)
    for (old_pos, old_raw), (_, new_raw) in zip(before, after):
        assert new_raw == replacements.get(old_pos, old_raw), 'Unexpected instruction change'
    old_indices = {p: i for i, (p, _) in enumerate(before)}
    new_indices = {p: i for i, (p, _) in enumerate(after)}
    for index in range(27):
        old_target = base + struct.unpack_from('<I', original, 4 + index * 4)[0]
        new_target = base + struct.unpack_from('<I', patched, 4 + index * 4)[0]
        assert old_indices[old_target] == new_indices[new_target], 'Label target changed'
    return bytes(patched), {
        'instruction_count_preserved': len(before), 'label_targets_preserved': 27,
        'relocated_labels': shifted, 'resource_references_changed': len(references),
        'caption_bytes_removed': len(caption) - 2,
    }


def build_sprite(original, text):
    sprite = decode(original)
    assert sprite.size == (456, 128) and sprite.mode == 'RGB'
    mask, font_size = render_label(text)
    # DC2TY's confirmed screen center is (400,278). DC2SC's panel is at
    # (276,236), so the matching local center is (124,42).
    local_x = (248 - mask.width) // 2
    local_y = 42 - mask.height // 2
    patched = sprite.copy()
    patched.paste((255, 255, 255), (208 + local_x, local_y), mask)
    diff = ImageChops.difference(sprite, patched)
    bounds = diff.getbbox()
    assert bounds is not None
    diff.paste(0, TEXT_AREA)
    assert diff.getbbox() is None, 'Changed pixels outside the exit caption'
    encoded = encode(patched, original)
    assert encoded[:20] == original[:20], 'CRX metadata changed'
    assert decode(encoded).tobytes() == patched.tobytes(), 'CRX roundtrip failed'
    return encoded, patched.crop(PANEL), {
        'font': FONT_FACE, 'font_size': font_size,
        'text_bitmap_size': list(mask.size), 'text_screen_center': [400, 278],
        'changed_pixel_bounds': bounds,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', type=Path, default=TOOLS / 'exit_prompt.json')
    args = parser.parse_args()
    entries = json.loads(args.json.read_text(encoding='utf-8-sig'))
    assert isinstance(entries, list) and len(entries) == 1
    text = entries[0]['message'].replace('\u3000', ' ').strip()
    assert text and all(32 <= ord(c) <= 126 for c in text), 'Expected one Latin caption'
    mes_path = ROOT / 'id_Data/MES/title_01.mes'
    sprite_path = ROOT / 'id_Data/GRP/SYSTEM/yn_exit00.CRX'
    mes_backup = DEBUG / 'title_01.before_exit_bitmap.mes'
    sprite_backup = DEBUG / 'yn_chip00.original.CRX'
    manifest_path = DEBUG / 'installed.json'
    previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    current_mes = mes_path.read_bytes()
    original_mes = mes_backup.read_bytes() if mes_backup.exists() else current_mes
    original_sprite = (sprite_backup.read_bytes() if sprite_backup.exists() else
                       (ROOT / 'AdvData/GRP/SYSTEM/yn_chip00.CRX').read_bytes())
    new_mes, script_checks = patch_script(original_mes)
    new_sprite, preview, image_checks = build_sprite(original_sprite, text)
    assert current_mes in (original_mes, new_mes), 'title_01.mes changed since backup; inspect before replacing'
    if sprite_path.exists():
        current_sprite = sprite_path.read_bytes()
        assert current_sprite == new_sprite or sha256(current_sprite) == previous.get('sprite_sha256'), 'Unrecognized exit sprite patch'
    # Complete validation before changing either installed game asset.
    DEBUG.mkdir(exist_ok=True)
    if not mes_backup.exists():
        mes_backup.write_bytes(original_mes)
    if not sprite_backup.exists():
        sprite_backup.write_bytes(original_sprite)
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    sprite_path.write_bytes(new_sprite)
    mes_path.write_bytes(new_mes)
    assert sprite_path.read_bytes() == new_sprite and mes_path.read_bytes() == new_mes
    preview.save(DEBUG / 'exit.preview.png')
    manifest = {
        'message': text, 'mes_sha256': sha256(new_mes),
        'sprite_sha256': sha256(new_sprite),
        'original_mes_sha256': sha256(original_mes),
        'original_sprite_sha256': sha256(original_sprite),
        **script_checks, **image_checks,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    print('PASS: script targets, dedicated panel references, caption-only pixels, and CRX roundtrip.')
    print('Runtime check remains: restart DC2SCLauncher.exe with Language=1 and open Game End.')


if __name__ == '__main__':
    main()
