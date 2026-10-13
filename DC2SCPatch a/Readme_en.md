# DC2SC Patch — Installation and Build

[Bahasa Indonesia](README.md) | **English**

This patch and launcher are dedicated to **Da Capo 2 Spring Celebration** (`D.C.II Spring Celebration ～ダ・カーポII～`). Main source: `src/dc2scpatch.cpp`.

## Installation

Download `Released_patch.rar` from [Releases](https://github.com/SakuraSymphonyReTranslation/DC2SCMesTextTool_GUI-and-Patch/releases/latest), or use the package under `build/Released`.

`<GAME_DIR>` means the game installation folder containing `DC2SC.EXE` and `AdvData`. Replace this placeholder with your actual game folder path; no specific drive is required.

1. Close the game, backup any files that will be replaced, then extract the package into `<GAME_DIR>`.
2. Run **`<GAME_DIR>\DC2SCLauncher.exe`** with `<GAME_DIR>` as the working directory; shortcuts must specify that folder in **Start in**.
3. The launcher injects the patch DLL and initializes Japanese Locale Emulator, falling back to standard execution if LE loading fails.
4. The package includes `DC2SC.EXE`, `DC2SCLauncher.exe`, `DC2SCPatch.dll`, `DC2SCPatch.ini`, `LoaderDll.dll`, and `LocaleEmulator.dll`.
5. Translated scripts are installed separately into `<GAME_DIR>\id_Data\MES` or `<GAME_DIR>\eng_data\MES` according to your `DC2SCPatch.ini` configuration (`Language=1` for Indonesian).

The tested reference executable has SHA256:

```text
cb1a9cdcd8c60b310fc7cdc4dab0bf544cd6d160853e8fa99afa92074d4039e4
```

## Runtime Patch Features

- **DVD Check Bypass:** AdvSys32 DVD check is bypassed via drive letter spoofing, allowing the game to boot on modern Windows 10/11 and Linux (Wine/Proton) systems without optical CD/DVD drives.
- **File Redirection:** Redirects `.mes` script requests to `id_Data\MES` (or `eng_data\MES`) without modifying original `AdvData` game archives.
- **Font & Dialogue Scaling:** Font rendering and character width ratios configured via `DC2SCPatch.ini` (`DialogueRenderScale=74`, `DialogueAdvanceScale=62`, `DialogueSpaceScale=24`).
- **Prompt Patchers:** Scripts in `tools/` provide patchers for bitmap system confirmation prompts (Save, Load, Exit).

## Building the Patch (C++)

Use the x86 Native Tools Command Prompt for Visual Studio:

```batch
build.bat
```

Or manually using CMake:

```batch
mkdir build_cmake && cd build_cmake
cmake .. -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release
nmake
```

Output files: `DC2SCLauncher.exe` and `DC2SCPatch.dll`.
