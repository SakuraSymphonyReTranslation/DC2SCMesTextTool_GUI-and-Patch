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
5. Translated scripts are installed separately into `<GAME_DIR>\id_Data\MES` or `<GAME_DIR>\eng_data\MES` according to your `DC2SCPatch.ini` configuration (`Language=1` for Indonesian, `Language=2` for English, `Language=0` for original Japanese).

The tested reference executable has SHA256:

```text
cb1a9cdcd8c60b310fc7cdc4dab0bf544cd6d160853e8fa99afa92074d4039e4
```

## Runtime Patch Features

- **DVD Check Bypass:** AdvSys32 DVD check is bypassed via drive letter spoofing, allowing the game to boot on modern Windows 10/11 and Linux (Wine/Proton) systems without optical CD/DVD drives.
- **File Redirection:** Redirects `.mes` script requests to `id_Data\MES` (or `eng_data\MES`) without modifying original `AdvData` game archives.
- **Font & Dialogue Scaling:** Font rendering and character width ratios configured via `DC2SCPatch.ini` (`DialogueRenderScale=74`, `DialogueAdvanceScale=62`, `DialogueSpaceScale=24`).
- **Choice Layout:** Latin choice labels use compact spacing around `○` and between words, with automatic scaling for long labels.
- **Sakura Redraws:** Layout uses stable choice box bounds, so text remains visible when sakura effects redraw a small part of the screen.
- **Scene Replay Titles:** Latin titles automatically shrink to fit their cards, with a maximum normal size of 16 pixels. Size is calculated from the displayed text; changing a title through JSON/MES import does not require rebuilding the DLL. Preserve the small-text marker `@s` if it appears in exported text.
- **Prompt Patchers:** Scripts in `tools/` provide patchers for bitmap system confirmation prompts (Save, Load, Exit).

Choice and replay title layout applies in translation modes (`Language=1` or `2`). Replay date lines, popup sizes, and textbox settings are unchanged by this layout. Restart the game through the launcher after replacing MES files or the DLL.

## Building the Patch (C++)

Use **Visual Studio 2022** with the **Desktop development with C++** workload, a Windows SDK, and **CMake 3.24 or newer**.

1. Open `build/DC2SCPatch.sln`.
2. Select the **Release** configuration and **Win32** platform.
3. Select **Build → Build Solution** (`Ctrl+Shift+B`).

Build output is written to `build/Release/DC2SCLauncher.exe` and `build/Release/DC2SCPatch.dll`. The `build/Released` directory holds the distribution package and is not updated automatically by compilation.

The repository includes the entire `build` directory, including the solution, projects, cache, and compiled files. CMake caches and projects contain paths from the computer that generated them. **After cloning or moving the source**, run the following commands from `DC2SCPatch a` to regenerate the solution for your location and toolchain:

```batch
cmake --fresh -S . -B build -G "Visual Studio 17 2022" -A Win32
cmake --build build --config Release --parallel
```

Or run the script that performs the same configuration and build:

```batch
build.bat
```

Copy the built launcher and DLL to `<GAME_DIR>` to use them. Choice and replay layout source is in `src/choice_layout.h`; run its layout tests with `tools/build_choice_test.cmd`.
