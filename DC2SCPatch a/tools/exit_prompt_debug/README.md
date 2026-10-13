# Dialog Ingin keluar?

Sumber teks: `../exit_prompt.json`.
Generator: `../patch_exit_prompt.py` (Windows + Python + Pillow).

Tampilan mengikuti contoh DC2TY yang sudah dikonfirmasi berhasil di chat
`01a11b39-04c5-7ed3-944f-05726ca34447`: spasi normal, lebar huruf proporsional,
batas lebar 216 piksel, dan pusat teks (400,278). Bentuk huruf pada sampel dan
ukuran bitmap yang tercatat (144 x 24 piksel) cocok dengan MS PGothic regular
28 piksel, sehingga generator memakai font tersebut.
Generator memakai pengukuran dan rasterisasi GDI mengikuti pola contoh,
melalui konteks font di memori tanpa membaca atau mengendalikan layar.

DC2SC menyimpan hasilnya dalam aset khusus `id_Data/GRP/SYSTEM/yn_exit00.CRX`.
Empat referensi `yn_chip00` pada `id_Data/MES/title_01.mes` diarahkan ke aset
khusus tersebut. Isi satu teks konfirmasi lama dikosongkan untuk mencegah
penumpukan. Jumlah instruksi, tujuan lompatan, koordinat panel, tombol,
dan instruksi Yes/No tetap dipertahankan. Sprite kosong `yn_chip00.CRX`,
dialog lain, EXE, DLL, dan berkas save pemain tidak diubah.

Untuk mengganti kalimat, edit nilai `message` di JSON, lalu jalankan dari
PowerShell di folder game:

```powershell
python '.\DC2SCMesTextTool_GUI - Copy\DC4Patch a\tools\patch_exit_prompt.py'
```

Jika mengimpor ulang MES terjemahan semula, jalankan generator kembali.
Jika MES telah mengalami perubahan lain, generator akan menolak menimpanya;
periksa perubahan tersebut sebelum memperbarui cadangan/generator.

`exit.preview.png` merupakan pratinjau aset, bukan screenshot game.
`installed.json` mencatat hash pemasangan, ukuran teks, dan hasil pemeriksaan.
Untuk mengecek runtime, restart DC2SCLauncher.exe dengan Language=1, buka
Game End, lalu gunakan No untuk menutup konfirmasi.

Cadangan sebelum patch:

- `title_01.before_exit_bitmap.mes`: skrip terjemahan semula.
- `yn_chip00.original.CRX`: sprite kosong sumber pembuatan panel.

Untuk membatalkan, tutup game dan salin `title_01.before_exit_bitmap.mes`
kembali ke `id_Data/MES/title_01.mes`. Setelah restart launcher, skrip memakai
sprite kosong asli lagi; `yn_exit00.CRX` tidak lagi dirujuk dan boleh dibiarkan.
