@echo off
setlocal
set "choiceVsRoot="
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "choiceVsRoot=%%i"
if not defined choiceVsRoot (
    echo [ERROR] Visual Studio C++ tools were not found.
    exit /b 1
)
call "%choiceVsRoot%\VC\Auxiliary\Build\vcvarsamd64_x86.bat" >nul
if errorlevel 1 exit /b 1
if not exist "%~dp0choice_debug" mkdir "%~dp0choice_debug"
pushd "%~dp0choice_debug"
if errorlevel 1 exit /b 1
cl /nologo /EHsc /std:c++20 /utf-8 /O2 /MT /Fe:test_choice_layout.exe /Fo:test_choice_layout.obj ..\test_choice_layout.cpp user32.lib
if errorlevel 1 goto failed
test_choice_layout.exe ..\testdata\choices.cp932.txt
if errorlevel 1 goto failed
popd
exit /b 0

:failed
popd
exit /b 1
