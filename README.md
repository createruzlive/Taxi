# CHAQIRUV — tashkilot ichki xabar tizimi (telefon/SMS'siz)

Direktor **telefon yoki SMS ishlatmasdan**, o'z kompyuteridан tashkilotdagi
bir yoki bir nechta (yoki hamma) hodimga **istalgan xabarни** yuboradi.
Xabar hodim kompyuterida ekranда pop-up oyna bo'lib chiqadi (masalan
**"Oldimga kir"**, **"Yig'ilish boshlandi"** yoki boshqa istalgan matn), va
hodim **"Hop, boraman"** tugmasi bilan javob qaytaradi.

Aloqa faqat mahalliy tarmoq (LAN / Wi-Fi) orqali — internet, telefon raqami
yoki SMS kerak emas. Qo'shimcha dastur o'rnatish shart emas, faqat **Python 3**
bo'lsa yetarli (tkinter va socket standart kutubxonada).

## Qanday ishlaydi (sxema)

```
                          ┌───────────────► Hodim 1  →  📢 pop-up  → "Hop, boraman"
   Direktor kompyuteri    │
  ┌────────────────────┐  │
  │  📢 YUBORISH  ──────┼──┼───────────────► Hodim 2  →  📢 pop-up  → "Qabul qilindi"
  │  (ko'p tanlov)     │  │   LAN (TCP)
  └────────────────────┘  │
        ▲                 └───────────────► Hodim 3  →  📢 pop-up  → "Keyinroq"
        │
        └── javoblar har bir hodim yonида ro'yxatда ko'rinadi
```

1. Har bir hodim kompyuterida dastur **kutish rejimida** ishlab turadi va
   o'zini tarmoqqа **avtomatik e'lon qiladi**.
2. Direktor oynасида hodimlar **o'zi paydo bo'ladi** (🟢 = onlayn) — IP'ни
   qo'lда yozish shart emas.
3. Direktor xabar matnини yozadi, kimlarга yuborishни belgilaydi (yoki
   **"Hammasi"**) va **YUBORISH** tugmasини bosadi.
4. Har bir belgilangan hodim ekранида pop-up chiqadi (ovoz bilan).
5. Hodim **"✅ Hop, boraman"**, **"👍 Qabul qilindi"** yoki **"⏳ Keyinroq"**
   tugmasини bosadi.
6. Javob direktorга qaytadi va ro'yxатда o'sha hodim yonида ko'rinadi.

### Avtomatik topish

Hodim kompyuteri ishga tushsa, har 3 soniyада tarmoqqа o'zини (ism + IP)
UDP orqali e'lon qiladi. Direktor bu e'lonларни eshitib, hodimni ro'yxатga
avtomatik qo'shadi va **🟢 onlayn** deб belgilaydi. Ya'ni direktor odatда
hech qanday IP kiritмаyди — hamma o'zи chiqadi. (Boshqa tarmoqдаги yoki
o'chиq kompyuterни istasангиз, **"Qo'lда"** orqali IP bilan qo'shса bo'ladi.)

### Portlar

| Port    | Turi | Yo'nalish            | Vazifasi                       |
|---------|------|----------------------|--------------------------------|
| `50555` | TCP  | Direktor → Hodim     | xabar (masalan "Oldimga kir")  |
| `50556` | TCP  | Hodim → Direktor     | javob (masalan "Hop, boraman") |
| `50557` | UDP  | Hodim → Direktor     | avtomatik topish (e'lon)       |

Firewall (Windows Defender) so'rasa, uchала portга ham ruxsat bering.

## Ishlatish — bitta fayl (`chaqiruv.py`)

Barcha kompyuterларга xuddi shu bir faylni qo'ying va oching:

```bash
python3 chaqiruv.py
```

Ochilgan oynada rolni tanlaysiz:

- **👔 Men DIREKTORMAN** → xabar yuborish oynasi ochiladi:
  - Xabar matnини yozasiz (yoki tayyorlaridan tanlaysiz).
  - Hodimlar ro'yxatidан kimlarга yuborishни belgilaysiz (yoki "Hammasini").
  - **YUBORISH** — har bir hodim ekранида pop-up chiqadi, javoblar ro'yxatда
    ko'rinadi.
- **🧑‍💼 Men HODIMMAN** → kutish rejimi; xabar kelганда pop-up chiqadi va
  javob tugmalari bilan javob berasiz.

Terminaldan to'g'ridan-to'g'ri ham:

```bash
python3 chaqiruv.py hodim       # har bir hodim kompyuterida
python3 chaqiruv.py direktor    # direktor kompyuterida
```

### Qo'lда qo'shish — `hodimlar.json`

Ko'p hollarда hech nima kiritmaysiz — hodimlar avtomatik topiladi. Lekin
o'chиq yoki boshqa tarmoqdagi kompyuterni oldindan qo'shib qo'ymoqchi
bo'lsangiz, direktor oynasидаги **"Qo'lда"** maydoniga ism + IP yozib
**➕** tugmasini bosasiz. Bular `hodimlar.json` faylида saqlanadi:

```json
[
  { "ism": "Anvar", "ip": "192.168.1.50" },
  { "ism": "Jasur", "ip": "192.168.1.52" }
]
```

IP manzilni bilish (kerak bo'lsa):
- Windows: `ipconfig`
- Linux / macOS: `ip addr` yoki `ifconfig`

## `.exe` fayl yasash (Python o'rnatilmagan kompyuter uchun)

Agar kompyuterларда Python bo'lmasa, `chaqiruv.py` dan mustaqil
`Chaqiruv.exe` yasab olsa bo'ladi — uni ikki marta bosib ishlatiladi.
`hodimlar.json` fayli `.exe` yonида turishi kerak.

**A) Windows kompyuterда o'zingiz yasash:**

`build_exe.bat` faylini ikki marta bosing (PyInstaller'ni o'rnatib,
`dist\Chaqiruv.exe` yasaydi). Buyruq qo'lда:

```bat
pip install pyinstaller
pyinstaller --onefile --windowed --name Chaqiruv chaqiruv.py
```

**B) Windows kompyuterисiz — GitHub orqali avtomatik:**

Repozitoriyada `.github/workflows/build-exe.yml` bor. GitHub'да:
1. Repozitoriya → **Actions** bo'limi
2. **"Chaqiruv.exe yasash"** → **Run workflow**
3. Tugagach, **Artifacts** ostidан **Chaqiruv-exe** ni yuklab oling.

## Muammolarni bartaraf etish

- **Hodim yonида "✗ ulanmadi"** — o'sha hodim kompyuterида dastur "kutish
  rejimи"да ochiqmi, IP manzil to'g'rimi, bir tarmoqdamisiz — tekshiring.
- **Javob ko'rinmayapti** — hodim tomonда `50556`-portга (Direktor kompyuteriга
  kirish) firewall to'sqinlik qilmayotganini tekshiring.
- **Kompyuterlar bir-birини "ko'rmayapti"** — hammasi bir Wi-Fi/LAN da ekaniга
  ishonch hosil qiling.

## Fayllar

- `chaqiruv.py` — **asosiy** bitta faylли dastur (direktor + hodim, ko'p
  tanlovли yuborish, javoblar, hodimlar ro'yxati). `.exe` shundан yasaladi.
- `hodimlar.json` — hodimlar ro'yxati (dastur avtomatik yaratadi).
- `build_exe.bat` — Windows'да `Chaqiruv.exe` yasash skripti.
- `avtostart_ornat.bat` — hodim kompyuterида dasturни Windows bilan avtomatik
  ishга tushirадиган qilади (Startup'га yorлиq qo'yади).
- `EXE_QOLLANMA.md` — `.exe` yasash bo'yicha to'liq qadamба-qadam qo'llanma.
- `.github/workflows/build-exe.yml` — `.exe`ni avtomatik yasaydi.
- `anvar_listener.py` + `direktor_call.py` — **oddiy 1↔1 variant** (faqat
  bitta hodim bilan). Agar ko'p hodim kerak bo'lsa, `chaqiruv.py` dan
  foydalaning.
- `README.md` — shu qo'llanma.
