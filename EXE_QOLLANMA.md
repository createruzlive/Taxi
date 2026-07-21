# `Chaqiruv.exe` yasash — to'liq qo'llanma

Bu qo'llanma `chaqiruv.py` dasturidan mustaqil **`Chaqiruv.exe`** fayl yasashni
o'rgatadi. Tayyor `.exe` ni **Python o'rnatilmagan** kompyuterларда ham ikki
marta bosib ishlatsa bo'ladi.

Ikkita yo'l bor:
- **1-usul** — Windows kompyuterда o'zingiz yasaysiz (eng oddiy).
- **2-usul** — Windows bo'lmasa, GitHub avtomatik yasaydi.

---

## 1-usul: Windows kompyuterда yasash

### Nima kerak
- **Windows** kompyuter.
- **Python 3** o'rnatilgan bo'lishi kerak. Agar yo'q bo'lsa,
  <https://python.org/downloads> dan yuklab o'rnating va o'rnatishда
  **"Add Python to PATH"** katakchасини belgilang (juda muhim!).

Python borligini tekshirish — `cmd` (buyruq satri) ochib:

```bat
python --version
```

`Python 3.xx.x` chiqsa — hammasi joyида.

### A) Eng oson — `build_exe.bat` ni bosish

1. Loyiha papkасини oching (ичида `chaqiruv.py` va `build_exe.bat` bor).
2. **`build_exe.bat`** faylini **ikki marta bosing**.
3. Oyna ochilиб o'zi hammасини qiladi: PyInstaller'ни o'rnatади va exe yasайди.
4. Tugagач, tayyor fayl **`dist\Chaqiruv.exe`** da bo'ladi.

### B) Qo'lда (buyruq bilan)

`cmd` ни loyiha papkасида ochib, ketma-ket:

```bat
pip install pyinstaller
pyinstaller --onefile --windowed --name Chaqiruv chaqiruv.py
```

Natija: **`dist\Chaqiruv.exe`**.

Bayroqlarни ma'носи:
- `--onefile` — hammасини bitta `.exe` ga jamlайди.
- `--windowed` — dastur ochilganда ortиқcha qora konsol oynаси chiqмайди.
- `--name Chaqiruv` — fayl nomи `Chaqiruv.exe` bo'lади.

---

## 2-usul: GitHub orqали avtomatik (Windows shart emas)

Agar sizда Windows kompyuter bo'lмаса, GitHub o'zи Windows'да yasаб berади.

1. GitHub'да repozitoriyани oching.
2. Yuqoридаги **Actions** bo'limигa o'ting.
3. Chapдан **"Chaqiruv.exe yasash"** ni tanlаб, o'ngда **Run workflow** →
   yana **Run workflow** ни bosing.
4. Bir-ikki daqiqа kutinг (yashил ✓ paydo bo'lса tayyor).
5. O'shа ishни ochib, pastдаги **Artifacts** bo'limидан **`Chaqiruv-exe`**
   ni yuklаб oling (ичида `Chaqiruv.exe` bor).

> Eslatма: bu har safar `chaqiruv.py` o'zгарса avtomatik ham ishga tushади.

---

## `.exe` ni ishlаtиш va tarqатиш

1. `Chaqiruv.exe` ни har bir kompyuterга (direktor va hodimларга) nusxаланг.
2. Ikki marta bosиб oching — ochilганда **rol tanlаш** oynаси chiqади
   ("Direktor" yoki "Hodim").
3. Har bir hodim kompyuterида **"Hodim"** ни tanlаб, oynани ochиқ qoldирасиз.
4. Direktor **"Direktor"** ни tanlайди — hodimlar ro'yxатda avtomatik chiqади.

### `hodimlar.json` haqида
Odatда kerak emas (hodimlar avtomatik topiladi). Lekин qo'лда qo'shган
hodimларингиз bo'lса, `hodimlar.json` fayli **`Chaqiruv.exe` bilan bir
papkада** turиши kerak.

---

## Avtomatik ishga tushirish (hodimlar uchun)

Hodimlar har kuni qo'lda ochishni unutmasligi uchun, kompyuter yoqilganда
dastur o'zi "Hodim" rejimida ishga tushsin. Buning uchun **hodim
kompyuterida bir marta** `avtostart_ornat.bat` ni bosing — u yorliqni
Windows'ning Startup papkasiga qo'yadi (`Chaqiruv.exe hodim`).

O'chirish kerak bo'lsa: **Win+R** → `shell:startup` → ochilgan papkadan
"Chaqiruv" yorlig'ini o'chiring.

> `avtostart_ornat.bat` ni `Chaqiruv.exe` bilan bir papkada saqlang
> (yoki `dist\` yonida).

## Tez-tez uchrايдиган muammolar

**Antivirus / Windows Defender exe'ни o'chirса yoki ogohlantirса.**
PyInstaller bilan yasалган yangi exe'ларни antiviruslар ba'zан "notaниш"
deб belgилайди (bu *false positive* — aslида xavfsiz). Yechим:
- Faylни "ishonchли" (allow / whitelist) ro'yxатga qo'shинг, yoki
- O'z tashkilотингизда imzоланган (code signing) exe ishlатинг.

**"python topilmadi" xatоси (1-usul).**
Python o'rnатилмаган yoki PATH'га qo'shилмаган. Python'ни qайta o'rnатиб,
**"Add Python to PATH"** ни belgилаng.

**Exe ochилади-yu, xabar bormayди.**
Firewall to'саётган bo'лиши mumкин. Windows so'rasа, dasturга tarmоққа
kirишга **ruxsat bering**. Kerак portlar: `50555`, `50556` (TCP) va
`50557` (UDP). Barchа kompyuter bir tarmoqda (bir Wi-Fi) bo'лиши shart.

**Exe hajми katta (~7-10 MB).**
Bu normаль — ичига Python'ning o'zи ham jamlаngan, shuning uchun boshqа
kompyuterда Python kerак bo'лмайди.

---

## (Ixtiyorий) exe'ga o'z belgиси (ikonка) qo'yиш

Agar `.ico` faylингиз bo'лса:

```bat
pyinstaller --onefile --windowed --name Chaqiruv --icon=belgi.ico chaqiruv.py
```
