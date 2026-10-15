@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1

echo [1/2] Generating Visual Studio 2022 solution in build...
cmake --fresh -S . -B build -G "Visual Studio 17 2022" -A Win32
if errorlevel 1 goto failed

echo [2/2] Building Release / Win32...
cmake --build build --config Release --parallel
if errorlevel 1 goto failed

echo.
echo [SUCCESS] Solution: build\DC2SCPatch.sln
echo Output: build\Release\DC2SCLauncher.exe and build\Release\DC2SCPatch.dll
echo Copy both files to the game folder to install the new build.
popd
exit /b 0

:failed
echo [ERROR] Build failed. Check the messages above.
popd
exit /b 1
