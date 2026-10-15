"""Audit every original/translated choice, repair omitted markers only.

Default is read-only; --apply backs up and repairs the JSON and matching MES.
Other MES instructions and label target instruction indices must stay identical.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unicodedata

sys.dont_write_bytecode = True
from patch_load_save_prompts import tokenize

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
DEBUG = TOOLS / 'choice_debug'


def canonical(text):
    text = unicodedata.normalize('NFKC', text).replace('~', ' ').replace('^', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return '○ ' + text[1:].strip() if text.startswith('○') else text


def decode(raw):
    return bytes((x + 32) & 255 for x in raw[1:-1]).decode('cp932')


def backup(path, group, output):
    dest = output / 'before' / group / path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(path.read_bytes())


def repair_mes(data, replacements):
    count = struct.unpack_from('<I', data)[0]
    base, before = tokenize(data, count)
    result = bytearray(data[:base + 2])
    reloc = {}
    for pos, raw in before:
        reloc[pos] = len(result)
        result.extend(replacements.get(pos, raw))
    for i in range(count):
        old = base + struct.unpack_from('<I', data, 4 + i * 4)[0]
        struct.pack_into('<I', result, 4 + i * 4, reloc[old] - base)
    _, after = tokenize(result, count)
    assert len(before) == len(after)
    old_indices = {p: i for i, (p, _) in enumerate(before)}
    new_indices = {p: i for i, (p, _) in enumerate(after)}
    for (pos, raw), (_, new) in zip(before, after):
        assert new == replacements.get(pos, raw)
    for i in range(count):
        old = base + struct.unpack_from('<I', data, 4 + i * 4)[0]
        new = base + struct.unpack_from('<I', result, 4 + i * 4)[0]
        assert old_indices[old] == new_indices[new]
    return bytes(result), {'instructions': len(before), 'label_targets': count}


def run(root, translated_dir, output, baseline=None, apply=False):
    choices, repairs, checks = [], [], []
    originals = sorted((root / 'AdvData/JSON').glob('*.json'))
    if not originals:
        raise ValueError('No original JSON files found under --game-dir/AdvData/JSON')
    if not translated_dir.is_dir():
        raise ValueError('--translated-dir does not exist')
    for op in originals:
        original = json.loads(op.read_text(encoding='utf-8-sig'))
        rows = [i for i, e in enumerate(original) if e.get('message', '').lstrip().startswith('○')]
        if not rows:
            continue
        tp = translated_dir / op.name
        translated = json.loads(tp.read_text(encoding='utf-8-sig'))
        assert len(original) == len(translated), op.name
        jp_before = tp.read_text(encoding='utf-8-sig')
        jp_after = jp_before
        mes = root / 'id_Data/MES' / op.with_suffix('.mes').name
        data = mes.read_bytes()
        _, tokens = tokenize(data, struct.unpack_from('<I', data)[0])
        texts = [(p, r, decode(r)) for p, r in tokens if r[0] in (0x4c, 0x4d)]
        replacements = {}
        expected = collections.Counter()
        for i in rows:
            text = translated[i]['message']
            label = canonical(text)
            if not label.startswith('○'):
                fixed = '○ ' + text.lstrip()
                old_json = json.dumps(text, ensure_ascii=False)
                new_json = json.dumps(fixed, ensure_ascii=False)
                assert jp_after.count(old_json) == 1
                jp_after = jp_after.replace(old_json, new_json)
                candidates = [(p, r) for p, r, s in texts if canonical(s) == label]
                assert len(candidates) == 1, (op.name, i, 'ambiguous missing marker')
                pos, raw = candidates[0]
                stored = canonical(fixed).replace(' ', '\u3000').encode('cp932')
                encrypted = bytes((x - 32) & 255 for x in stored)
                assert 0 not in encrypted
                replacements[pos] = raw[:1] + encrypted + b'\0'
                label = canonical(fixed)
                repairs.append({'file': op.name, 'index': i, 'label': label})
            expected[label] += 1
            assert re.search('[A-Za-z]', label), (op.name, i, 'non-Latin choice')
            assert '@' not in label and '\n' not in text
            assert len(label.replace(' ', '\u3000').encode('cp932')) < 1024
            choices.append({'file': op.name, 'index': i, 'text': label})
        if replacements:
            patched, validated = repair_mes(data, replacements)
            checks.append({'file': mes.name, **validated})
        else:
            patched = data
        _, final = tokenize(patched, struct.unpack_from('<I', patched)[0])
        actual = collections.Counter(canonical(decode(r)) for _, r in final
                                     if r[0] in (0x4c, 0x4d) and canonical(decode(r)).startswith('○'))
        assert actual == expected, (op.name, actual - expected, expected - actual)
        if apply and replacements:
            backup(tp, 'JSON_Translated', output)
            backup(mes, 'MES', output)
            # Preserve all formatting outside the two exact string replacements.
            tp.write_bytes(jp_after.encode('utf-8'))
            mes.write_bytes(patched)
    protected = json.loads(baseline.read_text()) if baseline else {}
    protected_result = {}
    for name, expected in protected.items():
        if 'SaveData' in name:
            continue  # Game legitimately updates system progress on launch/exit.
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        assert actual == expected, ('protected file changed', name)
        protected_result[name] = True
    report = {'original_json_files': len(originals), 'translated_json_files': len(list(translated_dir.glob('*.json'))),
              'choices': len(choices), 'choice_files': len(set(c['file'] for c in choices)),
              'repair_candidates': repairs, 'applied': apply, 'mes_validation': checks,
              'protected_files_unchanged': protected_result, 'labels': choices}
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / ('applied_choices.json' if apply else 'choice_audit.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('labels', 'protected_files_unchanged')}, ensure_ascii=True))
    print('Protected files unchanged:', len(protected_result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--game-dir', type=Path, default=ROOT)
    parser.add_argument('--translated-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=DEBUG)
    parser.add_argument('--baseline', type=Path, help='Optional JSON of protected paths and SHA256 hashes')
    args = parser.parse_args()
    run(args.game_dir, args.translated_dir, args.output_dir, args.baseline, args.apply)
