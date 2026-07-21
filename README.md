# Direktor → Anvar chaqiruv tizimi (telefon/SMS'siz)

Direktor Sardor yordamchisi Anvarni **telefon yoki SMS ishlatmasdan** chaqirishi
uchun oddiy dastur. Direktor kompyuteridan tugma bosilganda, Anvar kompyuterida
ekranda **"Oldimga kir"** degan pop-up oyna paydo bo'ladi.

Aloqa faqat mahalliy tarmoq (LAN / Wi-Fi) orqali amalga oshadi — internet,
telefon raqami yoki SMS kerak emas. Qo'shimcha dastur o'rnatish shart emas,
faqat **Python 3** bo'lsa yetarli (tkinter va socket standart kutubxonada).

## Qanday ishlaydi (sxema)

```
   Direktor kompyuteri                     Anvar kompyuteri
  ┌────────────────────┐                 ┌────────────────────┐
  │  direktor_call.py  │                 │ anvar_listener.py  │
  │  [ CHAQIRISH ] ────┼── LAN/tarmoq ──►│  (kutish rejimi)   │
  │                    │   xabar (TCP)   │                    │
  └────────────────────┘                 │   ┌──────────────┐ │
                                         │   │ 📢 Oldimga  │ │
                                         │   │    kir       │ │  ← pop-up
                                         │   └──────────────┘ │
                                         └────────────────────┘
```

1. Anvar kompyuterida `anvar_listener.py` ishlab turadi va xabarni kutadi.
2. Direktor `direktor_call.py` dagi **CHAQIRISH** tugmasini bosadi.
3. Xabar tarmoq orqali Anvar kompyuteriga boradi.
4. Anvar ekranida darhol **"Oldimga kir"** pop-up oynasi chiqadi (ovoz bilan).

## O'rnatish

Ikkala kompyuter ham **bir tarmoqda** (bir Wi-Fi / bir LAN) bo'lishi shart.
Python 3 o'rnatilgan bo'lishi kerak:

```bash
python3 --version
```

## Ishlatish

### 1-qadam — Anvar kompyuterida

```bash
python3 anvar_listener.py
```

Dastur o'z **IP manzilini** ko'rsatadi, masalan:

```
  IP manzil (direktorga ayting): 192.168.1.50
  Port:                          50555
```

Bu IP manzilni direktorga ayting. Dastur doim ochiq turishi kerak.

### 2-qadam — Direktor kompyuterida

**Grafik (tugmali) rejim** — tavsiya etiladi:

```bash
python3 direktor_call.py --gui
```

Ochilgan oynaga Anvar IP manzilini (`192.168.1.50`) kiriting va
**CHAQIRISH** tugmasini bosing.

**Yoki bitta buyruq bilan (terminaldan):**

```bash
python3 direktor_call.py --to 192.168.1.50
```

Xabar matnini o'zgartirish:

```bash
python3 direktor_call.py --to 192.168.1.50 --message "Oldimga kir"
```

## Sozlamalar

| Parametr     | Tavsif                                  | Default        |
|--------------|-----------------------------------------|----------------|
| `--to`       | Anvar kompyuteri IP manzili             | —              |
| `--port`     | Port raqami (ikkalasida bir xil bo'lsin)| `50555`        |
| `--message`  | Yuboriladigan matn                      | `Oldimga kir`  |
| `--gui`      | Direktorda grafik oynani ochish         | —              |

Portni o'zgartirsangiz, ikkala tomonda ham bir xil bo'lishi kerak:

```bash
# Anvar
python3 anvar_listener.py --port 50600
# Direktor
python3 direktor_call.py --to 192.168.1.50 --port 50600
```

## Muammolarni bartaraf etish

- **"Yuborilmadi" xatosi** — Anvar kompyuterida `anvar_listener.py` ishlab
  turganini, IP manzil va port to'g'riligini tekshiring.
- **Kompyuterlar bir-birini "ko'rmayapti"** — ikkalasi bir tarmoqda ekaniga
  ishonch hosil qiling. Firewall (Windows Defender) `50555`-portga ruxsat
  berishi kerak bo'lishi mumkin.
- **IP manzilni bilish**:
  - Windows: `ipconfig`
  - Linux / macOS: `ip addr` yoki `ifconfig`

## Fayllar

- `anvar_listener.py` — Anvar tomoni (qabul qiluvchi, pop-up chiqaradi).
- `direktor_call.py` — Direktor tomoni (yuboruvchi, tugmali oyna yoki CLI).
- `README.md` — shu qo'llanma.
