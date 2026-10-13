# Teks dialog Load dan Save

Sumber teks: `../load_save_prompts.json`.
Generator: `../patch_load_save_prompts.py` (Python + Pillow).

Untuk mengganti kalimat, edit `message` di JSON tersebut, lalu jalankan dari
PowerShell di folder game:

```powershell
python '.\DC2SCMesTextTool_GUI - Copy\DC4Patch a\tools\patch_load_save_prompts.py'
```

Font putih dan posisi tengah mengikuti dialog Mau Kembali dan Reset Config.
Ukuran dasar 30 piksel, otomatis diperkecil jika kalimat terlalu panjang;
Muat Permainan? memakai 28 piksel, Simpan Disini? memakai 30 piksel.

Kedua skrip semula memuat `common_load_chip00.CRX`. Generator mengarahkan
SAVE ke `common_save_chip00.CRX`, yang sprite aslinya identik. Dengan begitu,
masing-masing panel mempunyai kalimat sendiri. Referensi itu sama panjang,
slot gambar tetap sama, dan posisi panel maupun tombol tidak berubah.

Berkas hasil pemasangan:

- `id_Data/MES/LOAD.mes`
- `id_Data/MES/SAVE.mes`
- `id_Data/GRP/SYSTEM/common_load_chip00.CRX`
- `id_Data/GRP/SYSTEM/common_save_chip00.CRX`

Teks opcode 4D dikosongkan agar teks lama tidak bertumpuk dengan gambar.
Ekspor ulang MES hasil patch karena itu tidak memuat kalimat konfirmasi.
Setelah impor ulang MES terjemahan semula, jalankan generator ini kembali.
Jika MES telah mengalami perubahan lain, generator menolak menimpanya;
periksa dan sesuaikan generator/cadangan sebelum menerapkan patch kembali.

Generator memeriksa seluruh instruksi dan tujuan label, referensi sprite
khusus SAVE, piksel di luar area teks, metadata CRX, dan hasil encode/decode.
Cadangan sebelum patch, hash hasil, serta rincian pemeriksaan disimpan di
folder ini. `load_save.preview.png` adalah pratinjau aset, bukan screenshot
game. EXE, DLL, dan berkas save pemain tidak diubah.

Untuk memeriksa hasil di game, tutup game dan buka ulang DC2SCLauncher.exe
dengan Language=1. Tampilkan konfirmasi load dan save; tombol No dapat
digunakan untuk membatalkan tanpa memuat atau menyimpan data.

Untuk membatalkan patch saat game sudah ditutup:

1. Salin `LOAD.before_bitmap.mes` dan `SAVE.before_bitmap.mes` ke
   `id_Data/MES/LOAD.mes` dan `id_Data/MES/SAVE.mes`.
2. Salin `common_load_chip00.original.CRX` dan
   `common_save_chip00.original.CRX` ke nama tanpa `.original` di
   `id_Data/GRP/SYSTEM`.
3. Restart launcher agar sprite cadangan disinkronkan kembali ke AdvData.
