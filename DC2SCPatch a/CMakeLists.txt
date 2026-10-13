cmake_minimum_required(VERSION 3.15)
project(DC2SCPatch)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
set(CMAKE_CXX_STANDARD 20)

if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "Error: Building for x64, but x86 expected. Use x86 Native Tools Command Prompt.")
endif()

# Detours library
set(DETOURS_DIR "${CMAKE_SOURCE_DIR}/Detours/src")
include_directories(${DETOURS_DIR})

add_library(detours STATIC
    ${DETOURS_DIR}/detours.cpp
    ${DETOURS_DIR}/modules.cpp
    ${DETOURS_DIR}/disasm.cpp
    ${DETOURS_DIR}/image.cpp
    ${DETOURS_DIR}/creatwth.cpp
    ${DETOURS_DIR}/disolx86.cpp
)

# ============================================================================
# DC2SCPatch.dll - The actual patch (injected by launcher)
# ============================================================================
add_library(DC2SCPatch SHARED
    src/dc2scpatch.cpp
)

target_link_libraries(DC2SCPatch PRIVATE 
    detours
    gdi32
    user32
    advapi32
    comdlg32
    shlwapi
    shell32
    ole32
)

set_target_properties(DC2SCPatch PROPERTIES
    LINK_FLAGS "/DYNAMICBASE:NO"
    OUTPUT_NAME "DC2SCPatch"
)

# ============================================================================
# DC2SCLauncher.exe - Starts the game with Japanese locale and injects DC2SCPatch.dll
# ============================================================================
add_executable(DC2SCLauncher WIN32
    src/launcher.cpp
    src/launcher.rc
)

target_include_directories(DC2SCLauncher PRIVATE src)

target_link_libraries(DC2SCLauncher PRIVATE
    user32
    advapi32
)

set_target_properties(DC2SCLauncher PROPERTIES
    OUTPUT_NAME "DC2SCLauncher"
)
