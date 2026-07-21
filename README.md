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

1. Har bir hodim kompyuterida dastur **kutish rejimida** ishlab turadi.
2. Direktor xabar matnini yozadi, kimlarга yuborishни belgilaydi (yoki
   **"Hammasini"**) va **YUBORISH** tugmasini bosadi.
3. Har bir belgilangan hodim ekranида pop-up chiqadi (ovoz bilan).
4. Hodim **"✅ Hop, boraman"**, **"👍 Qabul qilindi"** yoki **"⏳ Keyinroq"**
   tugmasini bosadi.
5. Javob direktorга qaytadi va ro'yxatда o'sha hodim yonида ko'rinadi.

### Portlar

| Port    | Yo'nalish            | Vazifasi                          |
|---------|----------------------|-----------------------------------|
| `50555` | Direktor → Hodim     | xabar (masalan "Oldimga kir")     |
| `50556` | Hodim → Direktor     | javob (masalan "Hop, boraman")    |

Firewall (Windows Defender) so'rasa, ikkala portга ham ruxsat bering.

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

### Hodimlar ro'yxati — `hodimlar.json`

Direktor tomonда hodimlar ro'yxati `hodimlar.json` faylда (dastur yonида)
saqlanadi. Uni **direktor oynасидан "➕ Qo'shish"** tugmasi bilan to'ldirsangiz
bo'ladi, yoki qo'lда tahrirlаса bo'ladi:

```json
[
  { "ism": "Anvar",   "ip": "192.168.1.50" },
  { "ism": "Dilnoza", "ip": "192.168.1.51" },
  { "ism": "Jasur",   "ip": "192.168.1.52" }
]
```

Har bir hodim o'z **IP manzilини** kutish rejimидаги oynаda (yoki terminalда)
ko'radi va direktorга aytadi. IP manzilni bilish:
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
- `.github/workflows/build-exe.yml` — `.exe`ni avtomatik yasaydi.
- `anvar_listener.py` + `direktor_call.py` — **oddiy 1↔1 variant** (faqat
  bitta hodim bilan). Agar ko'p hodim kerak bo'lsa, `chaqiruv.py` dan
  foydalaning.
- `README.md` — shu qo'llanma.
