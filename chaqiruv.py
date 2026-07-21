#!/usr/bin/env python3
"""
CHAQIRUV — Tashkilot ichki xabar tizimi (telefon/SMS'siz, bitta fayl)
====================================================================

Bitta fayl. Barcha kompyuterларга shu bir faylni qo'ying va ishga tushiring:

    python3 chaqiruv.py

Ochilgan oynada rolni tanlaysiz:
  • "Men HODIMMAN"    -> kutish rejimi. Xabar kelganда ekranда pop-up chiqadi
                         (masalan "Oldimga kir" yoki boshqa istalgan matn).
                         "Hop, boraman" tugmasi bilan javob qaytaradi.
  • "Men DIREKTORMAN" -> hodimlar ro'yxatidan kimlarга yuborishни belgilaysiz
                         (yoki "Hammasini"), istalgan xabar matnини yozasiz va
                         YUBORISH tugmasini bosasiz. Har bir hodim ekranида
                         pop-up chiqadi, javoblar ro'yxatда ko'rinadi.

Aloqa faqat mahalliy tarmoq (LAN/Wi-Fi) orqali. Internet, telefon, SMS
kerak emas. Qo'shimcha kutubxona shart emas — faqat Python 3 (tkinter,
socket standart kutubxonada mavjud).

Hodimlar ro'yxati `hodimlar.json` faylда saqlanadi (dastur yonида). Uni
direktor oynасидан qo'shsa/o'chirsa bo'ladi yoki qo'lда tahrirlаса bo'ladi.

Terminaldan to'g'ridan-to'g'ri ham:
    python3 chaqiruv.py hodim
    python3 chaqiruv.py direktor
"""

import json
import os
import queue
import socket
import sys
import threading

DEFAULT_PORT = 50555             # Direktor -> Hodim (xabar)
CONFIRM_PORT = DEFAULT_PORT + 1  # Hodim -> Direktor (javob/tasdiq)
DEFAULT_MESSAGE = "Oldimga kir"
SENDER_NAME = "Direktor"

# Tez-tez ishlatiladigan tayyor xabarlar (direktor bir bosishда tanlaydi)
PRESET_MESSAGES = [
    "Oldimga kir",
    "Yig'ilish boshlandi, zalga keling",
    "Tushlik vaqti",
    "Ish tugadi, uyга borishingiz mumkin",
]


# ---------------------------------------------------------------------------
# Fayl joylashuvi (oddiy .py va PyInstaller .exe ikkovi uchun)
# ---------------------------------------------------------------------------
def base_dir():
    if getattr(sys, "frozen", False):          # PyInstaller .exe
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


HODIMLAR_FILE = os.path.join(base_dir(), "hodimlar.json")


def load_hodimlar():
    """hodimlar.json dan ro'yxatni o'qiydi. Bo'lmasa namuna yaratadi."""
    if os.path.exists(HODIMLAR_FILE):
        try:
            with open(HODIMLAR_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            result = []
            for item in data:
                ism = str(item.get("ism", "")).strip()
                ip = str(item.get("ip", "")).strip()
                if ip:
                    result.append({"ism": ism or ip, "ip": ip})
            return result
        except (ValueError, OSError):
            pass
    # Namuna ro'yxat
    namuna = [
        {"ism": "Anvar (namuna)", "ip": "192.168.1.50"},
        {"ism": "Dilnoza (namuna)", "ip": "192.168.1.51"},
    ]
    save_hodimlar(namuna)
    return namuna


def save_hodimlar(hodimlar):
    try:
        with open(HODIMLAR_FILE, "w", encoding="utf-8") as f:
            json.dump(hodimlar, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Tarmoq yordamchilari
# ---------------------------------------------------------------------------
def get_local_ip():
    """Kompyuterning tarmoqdagi IP manzilini aniqlaydi (LAN uchun)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def get_hostname():
    try:
        return socket.gethostname()
    except Exception:
        return "hodim"


def send_call(host, port, message, sender=SENDER_NAME, timeout=5):
    """Bitta hodimга xabar yuboradi. (True, 'OK') yoki (False, xato) qaytaradi.

    Payload ичіга direktorning IP'si (sender_ip) qo'shiladi — hodim
    javob tugmasini bosганда shu manzilga tasdiq qaytaradi.
    """
    payload = json.dumps({
        "message": message,
        "sender": sender,
        "sender_ip": get_local_ip(),
    }).encode("utf-8")
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(payload)
            s.shutdown(socket.SHUT_WR)
            try:
                s.settimeout(timeout)
                reply = s.recv(16)
            except socket.timeout:
                reply = b""
        return True, reply.decode("utf-8", errors="replace")
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return False, str(e)


def send_confirm(host, port, text, who=None, timeout=5):
    """Hodimdan direktorga javob yuboradi (masalan 'Hop, boraman')."""
    if who is None:
        who = get_hostname()
    payload = json.dumps({"confirm": text, "from": who}).encode("utf-8")
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(payload)
            s.shutdown(socket.SHUT_WR)
        return True, None
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# HODIM tomoni (qabul qiluvchi + pop-up)
# ---------------------------------------------------------------------------
def _listener_thread(sock, msg_queue):
    while True:
        try:
            conn, addr = sock.accept()
        except OSError:
            break
        with conn:
            data = b""
            conn.settimeout(5)
            try:
                while True:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    if len(data) > 65536:
                        break
            except socket.timeout:
                pass

            text, sender, sender_ip = DEFAULT_MESSAGE, addr[0], addr[0]
            payload = data.decode("utf-8", errors="replace").strip()
            if payload:
                try:
                    obj = json.loads(payload)
                    text = obj.get("message", DEFAULT_MESSAGE)
                    sender = obj.get("sender", addr[0])
                    sender_ip = obj.get("sender_ip", addr[0])
                except (ValueError, AttributeError):
                    text = payload
            try:
                conn.sendall(b"OK")
            except OSError:
                pass
            print(f"[+] Xabar keldi: '{text}'  (yuboruvchi: {sender})")
            msg_queue.put((text, sender, sender_ip))


def _show_popup(text, sender, sender_ip):
    """Diqqatni tortadigan qizil pop-up oyna (asosiy oqimda chaqirilsin).

    Javob tugmasi bosilganда direktorga (sender_ip:CONFIRM_PORT) tasdiq
    yuboriladi va oynada natija ko'rsatiladi.
    """
    import tkinter as tk

    root = tk.Tk()
    root.title("YANGI XABAR")
    root.attributes("-topmost", True)
    root.configure(bg="#b30000")
    root.resizable(False, False)

    w, h = 520, 340
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//3}")

    try:
        root.bell()
    except Exception:
        pass

    frame = tk.Frame(root, bg="#b30000")
    frame.pack(expand=True, fill="both", padx=22, pady=18)
    tk.Label(frame, text="📢  " + text, font=("Arial", 24, "bold"),
             fg="white", bg="#b30000", wraplength=470,
             justify="center").pack(pady=(6, 4))
    tk.Label(frame, text=f"Yuboruvchi: {sender}", font=("Arial", 13),
             fg="#ffe0e0", bg="#b30000").pack(pady=(0, 10))

    status = tk.Label(frame, text="", font=("Arial", 11, "bold"),
                      fg="#fff2b0", bg="#b30000")
    status.pack(pady=(0, 8))

    btn_row = tk.Frame(frame, bg="#b30000")
    btn_row.pack()

    def confirm(answer):
        """Javobni direktorga yuboradi va oynani yopadi."""
        status.config(text="Yuborilmoqda...", fg="#fff2b0")
        root.update_idletasks()
        ok, err = send_confirm(sender_ip, CONFIRM_PORT, answer)
        if ok:
            status.config(text="✓ Direktorga yuborildi", fg="#c8f7c8")
        else:
            status.config(text="Direktorga yetkazib bo'lmadi", fg="#ffd0d0")
        root.after(700, root.destroy)

    yes_btn = tk.Button(btn_row, text="✅  Hop, boraman",
                        font=("Arial", 15, "bold"),
                        bg="white", fg="#0a7d0a", activebackground="#eaffea",
                        relief="flat", padx=16, pady=9,
                        command=lambda: confirm("Hop, boraman"))
    yes_btn.pack(side="left", padx=5)

    tk.Button(btn_row, text="👍  Qabul qilindi", font=("Arial", 13),
              bg="#0a5d9c", fg="white", activebackground="#084b7d",
              relief="flat", padx=14, pady=9,
              command=lambda: confirm("Qabul qilindi")).pack(side="left", padx=5)

    tk.Button(btn_row, text="⏳  Keyinroq", font=("Arial", 13),
              bg="#7a0000", fg="white", activebackground="#5c0000",
              relief="flat", padx=14, pady=9,
              command=lambda: confirm("Band edim, keyinroq")).pack(side="left",
                                                                   padx=5)

    root.after(100, lambda: (root.focus_force(), yes_btn.focus_set()))
    root.mainloop()


def run_hodim(port=DEFAULT_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(5)

    local_ip = get_local_ip()
    print("=" * 52)
    print("  HODIM — xabarni kutish rejimi")
    print("=" * 52)
    print(f"  Kompyuter nomi:                {get_hostname()}")
    print(f"  IP manzil (direktorga ayting): {local_ip}")
    print(f"  Port:                          {port}")
    print("  Xabar kelishi bilan pop-up oyna chiqadi.")
    print("  To'xtatish uchun: Ctrl + C")
    print("=" * 52)

    msg_queue = queue.Queue()
    threading.Thread(target=_listener_thread, args=(sock, msg_queue),
                     daemon=True).start()

    import tkinter as tk

    root = tk.Tk()
    root.title("Hodim — kutish rejimi")
    root.configure(bg="#1e3d59")
    root.resizable(False, False)
    w, h = 440, 210
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//3}")
    fr = tk.Frame(root, bg="#1e3d59")
    fr.pack(expand=True, fill="both", padx=20, pady=20)
    tk.Label(fr, text="✅ Xabarni kutmoqda...", font=("Arial", 18, "bold"),
             fg="white", bg="#1e3d59").pack(pady=(6, 12))
    tk.Label(fr, text=f"Kompyuter: {get_hostname()}",
             font=("Arial", 12), fg="#cfe0ee", bg="#1e3d59").pack()
    tk.Label(fr, text=f"Sizning IP: {local_ip}   (port {port})",
             font=("Arial", 12), fg="#cfe0ee", bg="#1e3d59").pack()
    tk.Label(fr, text="Bu oynani yopmang. Direktorga IP manzilingizni ayting.",
             font=("Arial", 10), fg="#9fb8cc", bg="#1e3d59",
             wraplength=380).pack(pady=(12, 0))

    def poll():
        try:
            while True:
                text, sender, sender_ip = msg_queue.get_nowait()
                _show_popup(text, sender, sender_ip)
        except queue.Empty:
            pass
        root.after(300, poll)

    root.after(300, poll)
    try:
        root.mainloop()
    finally:
        sock.close()


# Eski nom bilan chaqirilsa ham ishlashi uchun
run_anvar = run_hodim


# ---------------------------------------------------------------------------
# DIREKTOR tomoni (ko'p hodimga yuboruvchi GUI)
# ---------------------------------------------------------------------------
def _confirm_listener(sock, confirm_queue):
    """Hodimlardan kelgan javoblarni qabul qiladi (matn, kim, ip)."""
    while True:
        try:
            conn, addr = sock.accept()
        except OSError:
            break
        with conn:
            data = b""
            conn.settimeout(5)
            try:
                while True:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    if len(data) > 65536:
                        break
            except socket.timeout:
                pass
            text, who = "javob keldi", addr[0]
            payload = data.decode("utf-8", errors="replace").strip()
            if payload:
                try:
                    obj = json.loads(payload)
                    text = obj.get("confirm", text)
                    who = obj.get("from", addr[0])
                except (ValueError, AttributeError):
                    text = payload
            print(f"[+] Javob: '{text}'  ({who} / {addr[0]})")
            confirm_queue.put((text, who, addr[0]))


def run_direktor(prefill_ip=""):
    import tkinter as tk
    from tkinter import messagebox

    hodimlar = load_hodimlar()
    if prefill_ip and not any(h["ip"] == prefill_ip for h in hodimlar):
        hodimlar.insert(0, {"ism": prefill_ip, "ip": prefill_ip})

    # Javoblarni kutish uchun fon listener'i
    confirm_queue = queue.Queue()
    csock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    csock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    confirm_active = True
    try:
        csock.bind(("0.0.0.0", CONFIRM_PORT))
        csock.listen(8)
        threading.Thread(target=_confirm_listener, args=(csock, confirm_queue),
                         daemon=True).start()
    except OSError as e:
        confirm_active = False
        print(f"[!] Javob portини ochib bo'lmadi ({CONFIRM_PORT}): {e}")

    result_queue = queue.Queue()   # (ip, 'sent'|'err', info)

    root = tk.Tk()
    root.title("Direktor — tashkilotga xabar yuborish")
    root.configure(bg="#1e3d59")
    root.minsize(560, 600)
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 580, 680
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{max(0,(sh - h)//4)}")

    outer = tk.Frame(root, bg="#1e3d59")
    outer.pack(expand=True, fill="both", padx=18, pady=14)

    tk.Label(outer, text="📢 Tashkilotga xabar", font=("Arial", 20, "bold"),
             fg="white", bg="#1e3d59").pack(anchor="w")

    # --- Xabar matni ---
    tk.Label(outer, text="Xabar matni:", font=("Arial", 11),
             fg="#cfe0ee", bg="#1e3d59").pack(anchor="w", pady=(10, 2))
    msg_text = tk.Text(outer, font=("Arial", 12), height=3, wrap="word")
    msg_text.insert("1.0", DEFAULT_MESSAGE)
    msg_text.pack(fill="x")

    preset_row = tk.Frame(outer, bg="#1e3d59")
    preset_row.pack(fill="x", pady=(6, 4))
    tk.Label(preset_row, text="Tayyor:", font=("Arial", 10),
             fg="#9fb8cc", bg="#1e3d59").pack(side="left", padx=(0, 4))

    def set_msg(t):
        msg_text.delete("1.0", "end")
        msg_text.insert("1.0", t)

    for p in PRESET_MESSAGES:
        short = p if len(p) <= 18 else p[:16] + "…"
        tk.Button(preset_row, text=short, font=("Arial", 9),
                  bg="#2c5578", fg="white", activebackground="#37678f",
                  relief="flat", padx=6, pady=2,
                  command=lambda t=p: set_msg(t)).pack(side="left", padx=2)

    # --- Kimga yuborish (hodimlar ro'yxati) ---
    head = tk.Frame(outer, bg="#1e3d59")
    head.pack(fill="x", pady=(10, 2))
    tk.Label(head, text="Kimga yuborish:", font=("Arial", 11),
             fg="#cfe0ee", bg="#1e3d59").pack(side="left")

    all_var = tk.IntVar(value=1)

    def toggle_all():
        val = all_var.get()
        for r in rows:
            r["var"].set(val)

    tk.Checkbutton(head, text="Hammasini belgilash", variable=all_var,
                   command=toggle_all, font=("Arial", 10), fg="#cfe0ee",
                   bg="#1e3d59", selectcolor="#12263a",
                   activebackground="#1e3d59",
                   activeforeground="white").pack(side="right")

    # Skrollanadigan ro'yxat
    list_wrap = tk.Frame(outer, bg="#12263a", height=180)
    list_wrap.pack(fill="both", expand=True, pady=(2, 6))
    list_wrap.pack_propagate(False)
    canvas = tk.Canvas(list_wrap, bg="#12263a", highlightthickness=0)
    scrollbar = tk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg="#12263a")
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw", width=520)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    rows = []          # har biri: {ism, ip, var, status_lbl}
    ip_to_row = {}

    def rebuild_rows():
        for child in inner.winfo_children():
            child.destroy()
        rows.clear()
        ip_to_row.clear()
        for h in hodimlar:
            row_fr = tk.Frame(inner, bg="#12263a")
            row_fr.pack(fill="x", padx=6, pady=2)
            var = tk.IntVar(value=1)
            cb = tk.Checkbutton(row_fr, variable=var, bg="#12263a",
                                selectcolor="#1e3d59",
                                activebackground="#12263a")
            cb.pack(side="left")
            tk.Label(row_fr, text=f"{h['ism']}  ({h['ip']})",
                     font=("Arial", 11), fg="white", bg="#12263a",
                     width=26, anchor="w").pack(side="left")
            st = tk.Label(row_fr, text="—", font=("Arial", 10),
                          fg="#9fb8cc", bg="#12263a", anchor="w")
            st.pack(side="left", fill="x", expand=True)
            row = {"ism": h["ism"], "ip": h["ip"], "var": var, "status_lbl": st}
            rows.append(row)
            ip_to_row[h["ip"]] = row

    rebuild_rows()

    # --- Yangi hodim qo'shish ---
    add_fr = tk.Frame(outer, bg="#1e3d59")
    add_fr.pack(fill="x", pady=(2, 6))
    tk.Label(add_fr, text="Yangi hodim:", font=("Arial", 10),
             fg="#9fb8cc", bg="#1e3d59").pack(side="left")
    name_e = tk.Entry(add_fr, font=("Arial", 10), width=12)
    name_e.pack(side="left", padx=(4, 3))
    name_e.insert(0, "Ism")
    ip_e = tk.Entry(add_fr, font=("Arial", 10), width=14)
    ip_e.pack(side="left", padx=3)
    ip_e.insert(0, "IP manzil")

    def add_hodim():
        ism = name_e.get().strip()
        ip = ip_e.get().strip()
        if not ip or ip == "IP manzil":
            messagebox.showwarning("E'tibor", "IP manzilни kiriting.")
            return
        hodimlar.append({"ism": ism or ip, "ip": ip})
        save_hodimlar(hodimlar)
        rebuild_rows()
        name_e.delete(0, "end"); ip_e.delete(0, "end")

    tk.Button(add_fr, text="➕ Qo'shish", font=("Arial", 10),
              bg="#2a9d8f", fg="white", activebackground="#238377",
              relief="flat", padx=8, command=add_hodim).pack(side="left", padx=3)

    # --- Yuborish tugmasi ---
    def send_one(row, message):
        ok, info = send_call(row["ip"], DEFAULT_PORT, message)
        result_queue.put((row["ip"], "sent" if ok else "err", info))

    def on_send():
        message = msg_text.get("1.0", "end").strip()
        if not message:
            messagebox.showwarning("E'tibor", "Xabar matni bo'sh.")
            return
        selected = [r for r in rows if r["var"].get()]
        if not selected:
            messagebox.showwarning("E'tibor", "Hech kim belgilanmagan.")
            return
        for r in selected:
            r["status_lbl"].config(text="yuborilmoqda...", fg="#ffd966")
            threading.Thread(target=send_one, args=(r, message),
                             daemon=True).start()

    tk.Button(outer, text="📢  YUBORISH", font=("Arial", 16, "bold"),
              bg="#e63946", fg="white", activebackground="#c92d3a",
              relief="flat", pady=12, command=on_send).pack(fill="x", pady=(4, 4))

    info_txt = ("Javoblar yuqoridagi ro'yxatда har bir hodim yonида ko'rinadi."
                if confirm_active
                else "⚠ Javob porti band — javoblar ko'rinmasligi mumkin.")
    tk.Label(outer, text=info_txt, font=("Arial", 9),
             fg="#9fb8cc", bg="#1e3d59", wraplength=520).pack(anchor="w")

    # --- Natija va javoblarni yangilash ---
    def poll():
        # Yuborish natijalari
        try:
            while True:
                ip, kind, info = result_queue.get_nowait()
                row = ip_to_row.get(ip)
                if row:
                    if kind == "sent":
                        row["status_lbl"].config(text="✓ yuborildi", fg="#9be89b")
                    else:
                        row["status_lbl"].config(text="✗ ulanmadi", fg="#ff8a8a")
        except queue.Empty:
            pass
        # Hodim javoblari
        try:
            while True:
                text, who, ip = confirm_queue.get_nowait()
                row = ip_to_row.get(ip)
                if row:
                    row["status_lbl"].config(text=f"✅ {text}", fg="#7CFC8A")
                else:
                    # Ro'yxatda yo'q hodim ham javob bergan bo'lishi mumkin
                    print(f"[i] Ro'yxatda yo'q javob: {who} ({ip}): {text}")
                try:
                    root.bell()
                except Exception:
                    pass
        except queue.Empty:
            pass
        root.after(300, poll)

    root.after(300, poll)
    try:
        root.mainloop()
    finally:
        try:
            csock.close()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Rol tanlash oynasi (dastur shu bilan boshlanadi)
# ---------------------------------------------------------------------------
def run_chooser():
    import tkinter as tk

    root = tk.Tk()
    root.title("CHAQIRUV — rolni tanlang")
    root.configure(bg="#12263a")
    root.resizable(False, False)
    w, h = 400, 340
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//3}")

    fr = tk.Frame(root, bg="#12263a")
    fr.pack(expand=True, fill="both", padx=28, pady=26)
    tk.Label(fr, text="CHAQIRUV tizimi", font=("Arial", 22, "bold"),
             fg="white", bg="#12263a").pack(pady=(0, 6))
    tk.Label(fr, text="Bu kompyuterda kim ishlaydi?", font=("Arial", 12),
             fg="#9fb8cc", bg="#12263a").pack(pady=(0, 22))

    choice = {"role": None}

    def pick(role):
        choice["role"] = role
        root.destroy()

    tk.Button(fr, text="👔  Men DIREKTORMAN\n(xabar yuboraman)",
              font=("Arial", 14, "bold"), bg="#e63946", fg="white",
              activebackground="#c92d3a", relief="flat", pady=12,
              command=lambda: pick("direktor")).pack(fill="x", pady=(0, 14))
    tk.Button(fr, text="🧑‍💼  Men HODIMMAN\n(xabar kutaman)",
              font=("Arial", 14, "bold"), bg="#2a9d8f", fg="white",
              activebackground="#238377", relief="flat", pady=12,
              command=lambda: pick("hodim")).pack(fill="x")

    root.mainloop()
    return choice["role"]


# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    role = args[0].lower() if args else None

    if role in ("hodim", "anvar", "h", "a"):
        run_hodim()
        return
    if role in ("direktor", "d"):
        prefill = args[1] if len(args) > 1 else ""
        run_direktor(prefill)
        return

    chosen = run_chooser()
    if chosen == "hodim":
        run_hodim()
    elif chosen == "direktor":
        run_direktor()
    else:
        print("Rol tanlanmadi. Chiqildi.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[i] To'xtatildi.")
