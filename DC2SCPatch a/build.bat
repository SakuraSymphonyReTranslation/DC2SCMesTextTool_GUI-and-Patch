@echo off
echo ==========================================
echo Building DC2SC Patch (Launcher + DLL)
echo ==========================================

if not exist build_cmake mkdir build_cmake
cd build_cmake

echo [1/2] Configuring CMake...
cmake .. -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release
if %errorlevel% neq 0 (
    echo [ERROR] CMake failed.
    pause
    exit /b %errorlevel%
)

echo [2/2] Compiling...
nmake
if %errorlevel% neq 0 (
    echo [ERROR] Compilation failed.
    pause
    exit /b %errorlevel%
)

echo.
echo ==========================================
echo [SUCCESS] Build completed!
echo ==========================================
echo.
echo Output files:
echo   - build_cmake\DC2SCLauncher.exe
echo   - build_cmake\DC2SCPatch.dll
echo.
echo Installation:
echo   1. Copy BOTH files to the DC2SC game folder
echo   2. Run DC2SCLauncher.exe instead of DC2SC.EXE
echo.
pause
