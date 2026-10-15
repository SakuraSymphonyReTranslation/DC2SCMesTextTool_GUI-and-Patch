// Regression harness for the production layout code, with a deterministic
// glyph source and a native-style dirty-rectangle blitter. Build for Win32.
#include <windows.h>
#include <map>
#include <vector>
#include <string>
#include <cstdio>
#include <cstdarg>
#include <stdexcept>
#include <fstream>

static BYTE *testBase;
static HMODULE TestModule(LPCWSTR) { return (HMODULE)testBase; }
struct TestFonts { int GetLanguage() { return 1; } } g_fontManager;
static thread_local bool g_nativeChoiceRaster = false;
static bool IsReadablePtr(const void *p, size_t) { return p != nullptr; }
static void DiagLog(const char *, ...) {}
static LONG DetourAttach(PVOID *, PVOID) { return 0; }
#define GetModuleHandleW TestModule
#include "../src/choice_layout.h"
#undef GetModuleHandleW

static RECT dirty;
static std::vector<unsigned char> framebuffer(800 * 600);
static int nativeFallbacks;

static void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

static UINT __cdecl Raster(char *out, const unsigned char *text, int size) {
  memset(out, 0, size * size);
  int width = text[0] >= 0x81 ? 22 : 4 + text[0] % 10;
  for (int y = 4; y < 25; ++y)
    for (int x = 2; x < width + 2; ++x)
      out[y * size + x] = ((x + y) % 5 == 0) ? 2 : 4;
  return width;
}

static int __cdecl Blit(int x, int y, const char *pixels, int color, int size) {
  int left = *(int *)(testBase + 0x838E5C);
  int right = *(int *)(testBase + 0x838E54);
  int top = *(int *)(testBase + 0x838E50);
  int bottom = *(int *)(testBase + 0x838E4C);
  for (int dy = 0; dy < size; ++dy)
    for (int dx = 0; dx < size; ++dx) {
      int px = x + dx, py = y + dy;
      if (px >= left && px < right && py >= top && py < bottom &&
          px >= 0 && px < 800 && py >= 0 && py < 600 && pixels[dy * size + dx])
        framebuffer[py * 800 + px] = (unsigned char)(1 + color * 5 + pixels[dy * size + dx]);
    }
  return 0;
}

static int __cdecl OriginalText(int, int, int, const char *, int) {
  ++nativeFallbacks;
  return 0;
}

static int __cdecl OriginalWidget(int *part, const char *text) {
  *(int *)(testBase + 0x838E5C) = max(part[0], (int)dirty.left);
  *(int *)(testBase + 0x838E54) = min(part[0] + 14 * (int)strlen(text), (int)dirty.right);
  *(int *)(testBase + 0x838E50) = max(part[1], (int)dirty.top);
  *(int *)(testBase + 0x838E4C) = min(part[1] + part[7], (int)dirty.bottom);
  return Hook_NativeChoiceText(part[0] + 1, part[1] + 1, 0, text, part[2]);
}

static int *SetupRow(bool replay) {
  int *row = (int *)(testBase + 0x10000);
  memset(row, 0, 880);
  row[3] = replay ? 252 : 136;
  row[4] = replay ? 116 : 200;
  row[5] = replay ? 498 : 616;
  row[6] = replay ? 168 : 240;
  int *part = (int *)((BYTE *)row + 52 + 4 * 44);
  part[0] = replay ? 330 : 182;
  part[1] = replay ? 122 : 204;
  part[2] = replay ? 1 : 0x87;
  part[7] = replay ? 17 : 29;
  *(BYTE **)(testBase + 0x636FC) = (BYTE *)row;
  *(int *)(testBase + 0x5B1490) = 1;
  return part;
}

static void CheckPartialRedraw(const std::string &text, bool replay) {
  int *part = SetupRow(replay);
  dirty = {0, 0, 800, 600};
  std::fill(framebuffer.begin(), framebuffer.end(), 0);
  int before = nativeFallbacks;
  Hook_NativeChoiceWidget(part, text.c_str());
  Require(nativeFallbacks == before, "label unexpectedly bypassed the layout");
  auto complete = framebuffer;
  int last = -1, first = 800;
  for (int y = 0; y < 600; ++y)
    for (int x = 0; x < 800; ++x)
      if (complete[y * 800 + x]) { last = max(last, x); first = min(first, x); }
  Require(last > first, "no rendered text");
  Require(last < (replay ? 490 : 604), "text overflowed the row");
  if (!replay) Require(first == 149, "choice leading padding changed");
  Require(part[0] == (replay ? 330 : 182), "source widget geometry was changed");
  // Reconstruct the frame from tiny moving strips, as the sakura compositor does.
  std::fill(framebuffer.begin(), framebuffer.end(), 0);
  for (int x = 0; x < 800; x += 19) {
    dirty = {x, 0, min(x + 19, 800), 600};
    Hook_NativeChoiceWidget(part, text.c_str());
  }
  Require(framebuffer == complete, "partial redraw changed or erased the text");
}

int main(int argc, char **argv) {
  testBase = (BYTE *)VirtualAlloc(nullptr, 0x900000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  Require(testBase != nullptr, "VirtualAlloc failed");
  NativeChoiceRaster = Raster;
  NativeChoiceBlit = Blit;
  Real_NativeChoiceText = OriginalText;
  Real_NativeChoiceWidget = OriginalWidget;
  try {
    Require(argc == 2, "pass the CP932 choice fixture path");
    std::ifstream input(argv[1], std::ios::binary);
    Require(input.good(), "fixture not found");
    int count = 0;
    std::string label;
    while (std::getline(input, label)) {
      if (!label.empty() && label.back() == '\r') label.pop_back();
      if (!label.empty()) { CheckPartialRedraw(label, false); ++count; }
    }
    Require(count == 110, "expected all 110 audited choices");
    CheckPartialRedraw("@sPesan Kenang-kenangan Kelas", true);
    CheckPartialRedraw("@sA very long scenario title that must stay inside its own replay card", true);
    int *date = SetupRow(true);
    date[1] = 149;
    int before = nativeFallbacks;
    Hook_NativeChoiceWidget(date, "@s03/14");
    Require(nativeFallbacks == before + 1, "date must use the native renderer");
    before = nativeFallbacks;
    Hook_NativeChoiceWidget(date, "Muat Permainan?");
    Require(nativeFallbacks == before + 1, "popup must use the native renderer");
    printf("PASS: %d choices + 2 replay titles, full/partial redraw parity, bounds, padding, date/popup isolation.\n", count);
  } catch (const std::exception &error) {
    fprintf(stderr, "FAIL: %s\n", error.what());
    return 1;
  }
  VirtualFree(testBase, 0, MEM_RELEASE);
  return 0;
}
