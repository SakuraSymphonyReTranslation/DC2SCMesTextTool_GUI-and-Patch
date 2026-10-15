"""Read-only IDA analysis of a private copy of the game executable."""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'choice_debug'
OUT.mkdir(exist_ok=True)
EXE = OUT / 'DC2SC.analysis.exe'
if not EXE.exists():
    shutil.copy2(HERE.parents[2] / 'DC2SC.EXE', EXE)

import idapro
rc = idapro.open_database(str(EXE), True)
if rc:
    raise RuntimeError(f'IDA open failed: {rc}')
import ida_funcs
import ida_hexrays
import ida_name
import idautils
import idc

result = {}
try:
    ida_hexrays.init_hexrays_plugin()
    if len(sys.argv) > 1:
        addresses = [int(x, 0) for x in sys.argv[1:]]
    else:
        addresses = [ea for ea, name in idautils.Names()
                     if any(s in name for s in ('TextOut', 'GlyphOutline', 'TextExtent'))]
    for ea in addresses:
        refs = list(idautils.XrefsTo(ea))
        functions = {ida_funcs.get_func(x.frm).start_ea for x in refs
                     if ida_funcs.get_func(x.frm)}
        own = ida_funcs.get_func(ea)
        if own:
            functions.add(own.start_ea)
        result[hex(ea)] = {
            'name': ida_name.get_name(ea),
            'xrefs': [hex(x.frm) for x in refs],
            'functions': {hex(f): str(ida_hexrays.decompile(f)) for f in sorted(functions)},
        }
    path = OUT / 'ida_latest.json'
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
finally:
    idapro.close_database(True)
