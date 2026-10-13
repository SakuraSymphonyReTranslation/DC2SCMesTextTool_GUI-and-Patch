"""Read/write the CRXG v2 true-color assets used by DC2SC.

Format reference: ImageCRX.reference.cs (GARbro, morkt, MIT license).
Only the formats checked here are supported; other variants fail explicitly.
"""

import struct
import zlib
from pathlib import Path

from PIL import Image


def decode(data):
    magic, ox, oy, width, height, compression, flags, depth, mode = struct.unpack(
        '<4shhHHHHhH', data[:20]
    )
    if magic != b'CRXG' or compression != 2 or depth not in (0, 1):
        raise ValueError('Only CRXG v2 RGB/RGBA is supported')
    channels = 3 if depth == 0 else 4
    raw = zlib.decompress(data[24 if flags & 0x10 else 20:])
    stride = width * channels
    pixels = bytearray(stride * height)
    pos = 0
    for y in range(height):
        ctl = raw[pos]
        pos += 1
        dst = y * stride
        prev = dst - stride
        if ctl in (0, 1, 2, 3):
            if y == 0 and ctl != 0:
                raise ValueError('Invalid first-row predictor')
            row = raw[pos:pos + stride]
            if len(row) != stride:
                raise ValueError('Truncated row')
            pos += stride
            for x, value in enumerate(row):
                prediction = 0
                if ctl == 0 and x >= channels:
                    prediction = pixels[dst + x - channels]
                elif ctl == 1:
                    prediction = pixels[prev + x]
                elif ctl == 2 and x >= channels:
                    prediction = pixels[prev + x - channels]
                elif ctl == 3 and x < stride - channels:
                    prediction = pixels[prev + x + channels]
                pixels[dst + x] = (value + prediction) & 255
        elif ctl == 4:
            for c in range(channels):
                x = 0
                value = raw[pos]
                pos += 1
                while x < width:
                    pixels[dst + x * channels + c] = value
                    x += 1
                    if x == width:
                        break
                    next_value = raw[pos]
                    pos += 1
                    if next_value == value:
                        count = raw[pos]
                        pos += 1
                        if x + count > width:
                            raise ValueError('Invalid RLE run')
                        for _ in range(count):
                            pixels[dst + x * channels + c] = value
                            x += 1
                        if x < width:
                            value = raw[pos]
                            pos += 1
                    else:
                        value = next_value
        else:
            raise ValueError(f'Unknown row predictor: {ctl}')
    if pos != len(raw):
        raise ValueError('Unexpected trailing image data')
    if channels == 3:
        return Image.frombytes('RGB', (width, height), bytes(pixels), 'raw', 'BGR')
    if mode != 1:
        flip = 0 if mode == 2 else 255
        for p in range(0, len(pixels), 4):
            a, b, g, r = pixels[p:p + 4]
            pixels[p:p + 4] = bytes((b, g, r, a ^ flip))
    return Image.frombytes('RGBA', (width, height), bytes(pixels), 'raw', 'BGRA')


def encode(image, template):
    """Preserve header metadata; encode rows with the left-pixel predictor."""
    header = bytearray(template[:20])
    _, _, _, width, height, compression, flags, depth, mode = struct.unpack(
        '<4shhHHHHhH', header
    )
    if compression != 2 or depth not in (0, 1) or image.size != (width, height):
        raise ValueError('Unsupported template or mismatched dimensions')
    channels = 3 if depth == 0 else 4
    pixels = bytearray(image.convert('RGB' if channels == 3 else 'RGBA').tobytes(
        'raw', 'BGR' if channels == 3 else 'BGRA'
    ))
    if channels == 4 and mode != 1:
        flip = 0 if mode == 2 else 255
        for p in range(0, len(pixels), 4):
            b, g, r, a = pixels[p:p + 4]
            pixels[p:p + 4] = bytes((a ^ flip, b, g, r))
    stride = width * channels
    raw = bytearray()
    for y in range(height):
        row = pixels[y * stride:(y + 1) * stride]
        raw.append(0)
        raw.extend((value - (row[x - channels] if x >= channels else 0)) & 255
                   for x, value in enumerate(row))
    compressed = zlib.compress(raw, 9)
    return bytes(header) + (struct.pack('<I', len(compressed)) if flags & 0x10 else b'') + compressed


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    decode(args.source.read_bytes()).save(args.output)
