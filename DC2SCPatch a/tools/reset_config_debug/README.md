# Teks dialog Reset Config

Sumber teks: `../reset_config_prompt.json`.
Generator: `../patch_reset_config_prompt.py` (Python + Pillow).

Untuk mengganti teks, edit nilai `message` di JSON tersebut, lalu jalankan
generator dari PowerShell di folder game:

```powershell
python '.\DC2SCMesTextTool_GUI - Copy\DC4Patch a\tools\patch_reset_config_prompt.py'
```

Generator menggambar teks putih di tengah panel reset pada
`id_Data/GRP/SYSTEM/systemconfig_chip00.CRX`, dengan font dan ukuran yang sama
seperti dialog Mau Kembali. Teks opcode 4D pada `id_Data/MES/option.mes`
dikosongkan agar teks lama tidak bertumpuk. Karena itu, ekspor ulang MES hasil
patch tidak memuat kalimat reset: sumber teks untuk panel ini adalah JSON di
atas. Generator perlu dijalankan ulang setelah impor ulang MES biasa.

Perubahan ini khusus panel reset di menu System Config. Sprite bersama
`yn_chip00.CRX`, sprite Mau Kembali, EXE, dan DLL tidak diubah.

Pemeriksaan generator:

- Semua 1.416 instruksi tetap sama selain isi teks opcode 4D.
- Semua 52 label tetap menunjuk instruksi yang sama; 34 offset disesuaikan
  karena panjang teks berkurang 14 byte.
- Perubahan piksel hanya di area teks panel reset; tombol dan bingkai tetap.
- Hasil encode/decode CRX identik dengan piksel yang dibuat dan metadata tetap.

`reset_config.preview.png` adalah pratinjau aset, bukan tangkapan game.
Pemeriksaan runtime belum dilakukan. Restart launcher dengan Language=1,
lalu buka dialog reset dari System Config untuk memeriksa tampilannya.

Cadangan sebelum patch:

- `option.before_bitmap.mes`: skrip terjemahan semula, masih bertuliskan Reset Config?.
- `systemconfig_chip00.original.CRX`: sprite sebelum teks ditambahkan.

Untuk membatalkan saat game sudah ditutup, salin cadangan MES ke
`id_Data/MES/option.mes`, lalu salin cadangan CRX ke
`id_Data/GRP/SYSTEM/systemconfig_chip00.CRX`. Restart launcher agar sprite
cadangan disinkronkan kembali ke AdvData.

`installed.json` mencatat hash hasil pemasangan dan pemeriksaan terakhir.
