# DC2SC MES Text Tool — GUI and CLI

[Bahasa Indonesia](README.md) | **English**

An importer/exporter for **D.C.II Spring Celebration ～Da Capo II～**.

This distribution supports **Da Capo 2 Spring Celebration** only (`dc2sc`, MES version `0x3B69`). The GUI, CLI, reference tables, patch, and launcher are specific to this game. The main patch source is `DC2SCPatch a/src/dc2scpatch.cpp`.

## Downloads and game folder

Download both packages from [GitHub Releases](https://github.com/SakuraSymphonyReTranslation/DC2SCMesTextTool_GUI-and-Patch/releases/latest):

- **DC2SCMesTextTool_GUI.rar**: MES ↔ JSON importer/exporter with a GUI and CLI. Includes Indonesian and English documentation.
- **Released_patch.rar**: launcher, patch DLL, INI configuration, and supporting runtime files.

`<GAME_DIR>` means **your game's installation folder**, which contains `DC2SC.EXE` and `AdvData`. It is a documentation placeholder: replace it with your actual game folder, without the `<` and `>` characters. No particular drive or installation path is required.

1. Close the game and back up any files that will be replaced, especially the executable and `DC2SCPatch.ini`.
2. Extract the contents of `Released_patch.rar` directly into `<GAME_DIR>`, so that `DC2SCLauncher.exe`, `DC2SCPatch.dll`, and `DC2SCPatch.ini` are next to `DC2SC.EXE`.
3. Run **`<GAME_DIR>\DC2SCLauncher.exe`** with `<GAME_DIR>` as the working directory. If you use a shortcut, set its **Start in** field to that folder.
4. Select the appropriate language in the patch settings (`Language=1` for Indonesian, `Language=0` for English). Place Indonesian MES files in `<GAME_DIR>\id_Data\MES`; for English, use `<GAME_DIR>\eng_data\MES`.

```text
<GAME_DIR>/
├── DC2SC.EXE
├── DC2SCLauncher.exe
├── DC2SCPatch.dll
├── DC2SCPatch.ini
├── LoaderDll.dll
├── LocaleEmulator.dll
├── AdvData/
└── id_Data/
    └── MES/
```

The two archives provide the tool and patch runtime; they do not include the complete translated scripts. The repository's source folder can be placed anywhere. The patch package is also available under `DC2SCPatch a/build/Released` in the source tree.

The tested reference executable has SHA256:

```text
cb1a9cdcd8c60b310fc7cdc4dab0bf544cd6d160853e8fa99afa92074d4039e4
```

## Opening the application

Extract `DC2SCMesTextTool_GUI.rar` to a folder of your choice and run `DC2SCMesTextTool_GUI.exe`. If you are using the source repository, run `bin\Release\net8.0-windows\DC2SCMesTextTool_GUI.exe`.
The ready-to-use package, `DC2SCMesTextTool_GUI.rar`, is in the same folder: `bin\Release\net8.0-windows\DC2SCMesTextTool_GUI.rar`.
The application requires the .NET 8 Desktop Runtime.

## Single File

**MES → JSON (export)**

1. Set **Input MES/JSON** to the original MES file.
2. Set **Output**, or leave it empty to create the JSON file next to the input.
3. Click **Export (MES -> JSON)**.

The default output extracts character names and dialogue according to the Circus MES format:

```json
[
  { "message": "Narration." },
  { "name": "Otome", "message": "「Character dialogue.」" }
]
```

Both the Single File and Batch tabs export using the format shown above. Export preserves text, Japanese/Indonesian names, and line breaks.

**JSON → MES (import)**

1. Set **Input MES/JSON** to the translated JSON file.
2. The original MES file is automatically located if present in the corresponding MES folder or next to the JSON file.
3. Choose an **Output** file different from the original MES file.
4. Set **Word Wrap**: the default is `70` in Single File, Batch, and the CLI; `0` preserves text and line breaks without reflowing them.
5. Click **Import (JSON -> MES)**.

The original template is required to preserve bytecode instructions, non-text tokens, and scenario label flow.

## Batch

- **Batch Export:** set **MES Folder** and **Output Folder**, then click **Batch Export (MES -> JSON)**.
- **Batch Import:** set **JSON Folder**, original **MES Folder**, and a different **Output Folder**, then click **Batch Import (JSON -> MES)**.
- File names must match: for example, `scene.json` uses `scene.mes` as template.
- Files are processed sequentially, and progress/status messages appear in the bottom log box.

## Layout and patch runtime

- **`DC2SCPatch.dll`** is automatically injected by `DC2SCLauncher.exe`.
- **DVD check bypass:** The AdvSys32 engine in DC2SC performs optical CD/DVD drive checks at startup. The patch spoofs the optical drive to allow seamless playback on modern PCs without optical drives (including Linux/Wine/Proton).
- **Font & Text Scaling:** Font rendering and Shift-JIS / Latin character scaling are configured via `DC2SCPatch.ini` (`DialogueRenderScale=74`, `DialogueAdvanceScale=62`, `DialogueSpaceScale=24`).
- **File Redirection:** Redirects MES script reads to `id_Data\MES` (or `eng_data\MES`) without overwriting original game archives in `AdvData`.
- **System Prompt Localization:** Utility scripts in `DC2SCPatch a/tools/` provide patchers for bitmap confirmation prompts (Save, Load, Exit).

Technical patch instructions are available in the [patch README](DC2SCPatch%20a/Readme_en.md).

## Validation and encoding

- DC2SC uses the **Shift-JIS (CP932)** encoding.
- Encrypted bytecode strings use XOR key `0x20`.
- MES labels are recalculated based on the Offset1 label table structure (`labelCount * 4 + 4`).
- Unsupported characters are validated to prevent garbled text or runtime crashes.

## CLI

From the executable folder:

```powershell
.\DC2SCMesTextTool_GUI.exe export "scene.mes" "scene.json"
.\DC2SCMesTextTool_GUI.exe import "scene.json" "original\scene.mes" "new\scene.mes" -w 70
.\DC2SCMesTextTool_GUI.exe batch-export "original_mes_folder" "json_output"
.\DC2SCMesTextTool_GUI.exe batch-import "json_folder" "original_mes_folder" "output_mes_folder" -w 70
```

`-w` sets the word wrap threshold (default: 70, `0` for no wrap). Drag-and-drop of `.mes` files onto the GUI window is also supported for quick export.

## Build

From the source repository root:

```powershell
dotnet build -c Release
```

Building the GUI requires the .NET 8 SDK. To build the C++ patch DLL and launcher, see the instructions in the [patch README](DC2SCPatch%20a/Readme_en.md).
