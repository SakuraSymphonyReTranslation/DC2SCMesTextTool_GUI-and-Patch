// ADV32's immediate menu renderer is separate from the HSXF4 dialogue path.
// Addresses and signatures verified with IDA against DC2SC.EXE, base 0x400000.
// Use private glyph copies: the engine's shared glyph caches remain untouched.
static int (__cdecl *Real_NativeChoiceText)(int, int, int, const char *, int) = nullptr;
static int (__cdecl *Real_NativeChoiceWidget)(int *, const char *) = nullptr;
static UINT (__cdecl *NativeChoiceRaster)(char *, const unsigned char *, int) = nullptr;
static int (__cdecl *NativeChoiceBlit)(int, int, const char *, int, int) = nullptr;

struct ChoiceRowBounds {
  int left = 0; int right = 0; bool active = false;
  int top = 0; int bottom = 0;
  bool replayTitle = false;
};
static thread_local ChoiceRowBounds g_choiceRowBounds;

// The clipping rectangle can be only a few pixels wide during a sakura redraw.
// Get stable layout bounds from the owning 880-byte UI row instead.
static ChoiceRowBounds FindChoiceRowBounds(const int *part) {
  BYTE *base = (BYTE *)GetModuleHandleW(nullptr);
  const int tableRvas[] = {0x636FC, 0x63700};
  const int countRvas[] = {0x5B1490, 0x590340};
  for (int t = 0; t < 2; ++t) {
    BYTE *rows = *(BYTE **)(base + tableRvas[t]);
    int count = *(int *)(base + countRvas[t]);
    uintptr_t address = (uintptr_t)part;
    if (count <= 0 || count > 128 || !rows || address < (uintptr_t)rows ||
        address >= (uintptr_t)rows + count * 880) continue;
    int *row = (int *)(rows + ((address - (uintptr_t)rows) / 880) * 880);
    if (!IsReadablePtr(row, 28)) continue;
    if (row[3] >= 0 && row[5] <= 800 && row[5] - row[3] >= 100 &&
        row[6] - row[4] >= 28 && row[6] - row[4] <= 160 &&
        part[1] >= row[4] && part[1] < row[6])
      return {row[3], row[5], true, row[4], row[6], false};
  }
  return {};
}

static int __cdecl Hook_NativeChoiceWidget(int *part, const char *text) {
  if (g_fontManager.GetLanguage() == 0 || !part || !IsReadablePtr(part, 32) ||
      !text || !IsReadablePtr(text, 2))
    return Real_NativeChoiceWidget(part, text);
  bool choice = (unsigned char)text[0] == 0x81 && (unsigned char)text[1] == 0x9B;
  bool smallText = text[0] == '@' && text[1] == 's';
  if (!choice && !smallText) return Real_NativeChoiceWidget(part, text);
  ChoiceRowBounds bounds = FindChoiceRowBounds(part);
  if (!bounds.active) return Real_NativeChoiceWidget(part, text);
  if (!choice) {
    // Replay cards have a thumbnail, then one small title above a date line.
    // Match the card and title geometry, leaving dates and other small UI alone.
    if (bounds.left < 240 || bounds.right > 780 ||
        bounds.right - bounds.left < 200 || bounds.right - bounds.left > 280 ||
        bounds.bottom - bounds.top < 40 || bounds.bottom - bounds.top > 80 ||
        part[0] - bounds.left < 60 || part[0] - bounds.left > 100 ||
        part[1] - bounds.top < 0 || part[1] - bounds.top > 16)
      return Real_NativeChoiceWidget(part, text);
    bounds.replayTitle = true;
  }
  int localPart[8];
  memcpy(localPart, part, sizeof(localPart));
  if (choice) localPart[0] = bounds.left + 12;
  ChoiceRowBounds previous = g_choiceRowBounds;
  g_choiceRowBounds = bounds;
  // Let the engine intersect the shifted text bounds with its dirty rectangle.
  // Only the local copy changes; the click targets and popup data stay intact.
  int result = Real_NativeChoiceWidget(localPart, text);
  g_choiceRowBounds = previous;
  return result;
}

struct NativeChoiceGlyph {
  char pixels[28 * 28] = {};
  int left = 28;
  int width = 0;
};

static NativeChoiceGlyph GetNativeChoiceGlyph(UINT sjis) {
  static std::map<UINT, NativeChoiceGlyph> cache;
  auto found = cache.find(sjis);
  if (found != cache.end())
    return found->second;
  unsigned char text[3] = {};
  if (sjis > 255) {
    text[0] = (unsigned char)(sjis >> 8);
    text[1] = (unsigned char)sjis;
  } else {
    text[0] = (unsigned char)sjis;
  }
  NativeChoiceGlyph glyph;
  bool previous = g_nativeChoiceRaster;
  g_nativeChoiceRaster = true;
  NativeChoiceRaster(glyph.pixels, text, 28);
  g_nativeChoiceRaster = previous;
  int right = -1;
  for (int y = 0; y < 28; ++y)
    for (int x = 0; x < 28; ++x)
      if (glyph.pixels[y * 28 + x]) {
        if (x < glyph.left) glyph.left = x;
        if (x > right) right = x;
      }
  if (right >= glyph.left)
    glyph.width = right - glyph.left + 1;
  cache.emplace(sjis, glyph);
  return glyph;
}

static int __cdecl Hook_NativeChoiceText(int x, int y, int lineStep,
                                        const char *text, int style) {
  uintptr_t base = (uintptr_t)GetModuleHandleW(nullptr);
  // Only explicit choices and recognized replay title widgets qualify.
  // Popup captions, dates and textbox calls retain their original settings.
  if (!g_choiceRowBounds.active || g_fontManager.GetLanguage() == 0 || !text || !IsReadablePtr(text, 2))
    return Real_NativeChoiceText(x, y, lineStep, text, style);
  bool replay = g_choiceRowBounds.replayTitle;
  if (!replay && ((unsigned char)text[0] != 0x81 || (unsigned char)text[1] != 0x9B))
    return Real_NativeChoiceText(x, y, lineStep, text, style);
  if (replay && (text[0] != '@' || text[1] != 's'))
    return Real_NativeChoiceText(x, y, lineStep, text, style);

  std::vector<UINT> chars;
  bool latin = false;
  int length = replay ? 2 : 0;
  for (; length < 1024;) {
    if (!IsReadablePtr(text + length, 1))
      break;
    unsigned char ch = (unsigned char)text[length];
    if (!ch) break;
    if (ch < 0x20 || ch == '@')
      return Real_NativeChoiceText(x, y, lineStep, text, style);
    UINT code = ch;
    int step = 1;
    if ((ch >= 0x81 && ch <= 0x9F) || (ch >= 0xE0 && ch <= 0xFC)) {
      if (!IsReadablePtr(text + length, 2) || !text[length + 1])
        return Real_NativeChoiceText(x, y, lineStep, text, style);
      code = (ch << 8) | (unsigned char)text[length + 1];
      step = 2;
      wchar_t wide = 0;
      if (MultiByteToWideChar(932, 0, text + length, 2, &wide, 1) == 1 &&
          wide >= 0xFF01 && wide <= 0xFF5E)
        code = wide - 0xFEE0;
    }
    if (code == 0x8140 || code == '^' || code == '~') code = ' ';
    if ((code >= 'A' && code <= 'Z') || (code >= 'a' && code <= 'z')) latin = true;
    if (code != ' ' || (!chars.empty() && chars.back() != ' ')) chars.push_back(code);
    length += step;
  }
  if (!latin || length >= 1024)
    return Real_NativeChoiceText(x, y, lineStep, text, style);
  // Every marker gets exactly one compact gap, regardless of JSON spacing.
  if (!replay && chars.size() > 1 && chars[1] != ' ') chars.insert(chars.begin() + 1, ' ');
  while (!chars.empty() && chars.back() == ' ') chars.pop_back();

  std::vector<NativeChoiceGlyph> glyphs;
  int naturalWidth = 0;
  for (UINT code : chars) {
    NativeChoiceGlyph glyph;
    if (code != ' ') glyph = GetNativeChoiceGlyph(code);
    naturalWidth += code == ' ' ? 7 : glyph.width + 2;
    glyphs.push_back(glyph);
  }
  int start = x;
  int available = g_choiceRowBounds.right - start - (replay ? 8 : 12);
  if (available <= 0 || naturalWidth <= 0)
    return Real_NativeChoiceText(x, y, lineStep, text, style);
  int maxSize = replay ? 16 : 28;
  int size = min(maxSize, (28 * available) / naturalWidth);
  if (size < 1) size = 1;

  int advance = 0;
  for (size_t i = 0; i < chars.size(); ++i) {
    const auto &glyph = glyphs[i];
    int drawX = start + (advance * size) / 28;
    if (chars[i] != ' ' && glyph.width) {
      // Area resampling preserves the engine's 0..4 coverage values when a
      // long label needs to shrink to fit its actual menu clipping rectangle.
      std::vector<char> pixels(size * size, 0);
      for (int dy = 0; dy < size; ++dy)
        for (int dx = 0; dx < size; ++dx) {
          int sum = 0;
          for (int sy = dy * 28 / size; sy < ((dy + 1) * 28 + size - 1) / size; ++sy)
            for (int sx = dx * 28 / size; sx < ((dx + 1) * 28 + size - 1) / size; ++sx) {
              int wx = min((dx + 1) * 28, (sx + 1) * size) - max(dx * 28, sx * size);
              int wy = min((dy + 1) * 28, (sy + 1) * size) - max(dy * 28, sy * size);
              if (sx < glyph.width && sy < 28)
                sum += (unsigned char)glyph.pixels[sy * 28 + sx + glyph.left] * wx * wy;
            }
          pixels[dy * size + dx] = (char)((sum + 392) / 784);
        }
      int drawY = y + (maxSize - size) / 2;
      if (style & 0x80)
        NativeChoiceBlit(drawX + 1, drawY + 1, pixels.data(), (style & 0x3F) ? 0 : 9, size);
      NativeChoiceBlit(drawX, drawY, pixels.data(), style & 0x3F, size);
    }
    advance += chars[i] == ' ' ? 7 : glyph.width + 2;
  }
  *(int *)(base + 0x5BBCEC) = y;
  *(int *)(base + 0x61957C) = start + advance * size / 28;
  *(int *)(base + 0x5DECD8) = maxSize;
  *(int *)(base + 0x825FD8) = length;
  static LONG choiceCount = 0, replayCount = 0;
  LONG &count = replay ? replayCount : choiceCount;
  if (InterlockedIncrement(&count) <= 20)
    DiagLog("%s layout: x=%d->%d y=%d natural=%d available=%d size=%d bytes=%d style=%x", replay ? "Replay title" : "Choice", x, start, y, naturalWidth, available, size, length, style);
  return length;
}

static void AttachNativeChoiceLayout() {
  BYTE *base = (BYTE *)GetModuleHandleW(nullptr);
  const BYTE textSignature[] = {0x8B, 0x44, 0x24, 0x08, 0x53, 0x8B, 0x5C, 0x24, 0x08};
  const BYTE widgetSignature[] = {0x81, 0xEC, 0x04, 0x01, 0x00, 0x00, 0xA1, 0x90, 0x2F, 0x47, 0x00};
  const BYTE rasterSignature[] = {0x83, 0xEC, 0x28, 0x53, 0x8B, 0x0D, 0xCC, 0xD7, 0x97, 0x00};
  const BYTE blitSignature[] = {0x83, 0xEC, 0x10, 0x8B, 0x4C, 0x24, 0x14, 0x8B, 0x54, 0x24, 0x24};
  if (memcmp(base + 0x1A3A0, textSignature, sizeof(textSignature)) != 0 ||
      memcmp(base + 0x1DDC0, widgetSignature, sizeof(widgetSignature)) != 0 ||
      memcmp(base + 0x6F80, rasterSignature, sizeof(rasterSignature)) != 0 ||
      memcmp(base + 0xD820, blitSignature, sizeof(blitSignature)) != 0) {
    DiagLog("Choice layout skipped: unsupported executable signatures");
    return;
  }
  NativeChoiceRaster = (decltype(NativeChoiceRaster))(base + 0x6F80);
  NativeChoiceBlit = (decltype(NativeChoiceBlit))(base + 0xD820);
  Real_NativeChoiceText = (decltype(Real_NativeChoiceText))(base + 0x1A3A0);
  Real_NativeChoiceWidget = (decltype(Real_NativeChoiceWidget))(base + 0x1DDC0);
  DetourAttach(&(PVOID &)Real_NativeChoiceText, Hook_NativeChoiceText);
  DetourAttach(&(PVOID &)Real_NativeChoiceWidget, Hook_NativeChoiceWidget);
  DiagLog("Native choice/replay layout v3 attached at RVA 0x1A3A0/0x1DDC0 (stable row bounds)");
}
