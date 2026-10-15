# Choice and Scene Replay layout tests

Run `tools\build_choice_test.cmd` from Windows with Visual Studio C++ tools installed. The script builds the test executable in the ignored `tools/choice_debug` directory and runs it against `choices.cp932.txt`.

The fixture contains all 110 Latin choice labels audited across 41 scenario files. The test includes the production `src/choice_layout.h` and uses a deterministic glyph rasterizer and a clipped framebuffer to check:

- Choice bounds and leading padding.
- Long Scene Replay titles fitting inside their cards.
- Identical output from full redraws and reconstruction using 19-pixel strips.
- Unchanged source widget geometry and native fallback for dates and popups.

This checks layout and redraw logic; it does not replace visual verification of the game's glyphs or effects.

To audit an installed Indonesian translation separately, use Python 3 with exported original JSON files under `<GAME_DIR>/AdvData/JSON` and imported MES files under `<GAME_DIR>/id_Data/MES`:

```powershell
python tools/audit_choice_layout.py --game-dir "<GAME_DIR>" --translated-dir "<TRANSLATED_JSON_DIR>"
```

The default audit is read-only for JSON/MES and writes a report under `tools/choice_debug`. `--baseline` accepts an optional JSON mapping of game-relative file paths to SHA256 hashes for checking protected files. `--apply` backs up and repairs missing choice markers in matching translated JSON/MES files; it validates instruction counts and jump targets.
