#!/usr/bin/env python3
"""
CHAQIRUV — Direktor <-> Anvar (telefon/SMS'siz, bitta fayl)
============================================================

Bitta fayl. Ikkala kompyuterга ham shu bir faylni qo'ying va ishga tushiring:

    python3 chaqiruv.py

Ochilgan oynada rolni tanlaysiz:
  • "Men ANVARMAN"    -> kutish rejimi. Chaqiruv kelganda "Oldimga kir"
                         degan pop-up oyna chiqadi.
  • "Men DIREKTORMAN" -> Anvar IP manzilini kiritib, CHAQIRISH tugmasini
                         bosasiz. Anvar ekranida pop-up chiqadi.

Aloqa faqat mahalliy tarmoq (LAN/Wi-Fi) orqali. Internet, telefon, SMS
kerak emas. Qo'shimcha kutubxona shart emas — faqat Python 3 (tkinter,
socket standart kutubxonada mavjud).

Xohlasangiz, terminalдан to'g'ridan-to'g'ri ham:
    python3 chaqiruv.py anvar
    python3 chaqiruv.py direktor
    python3 chaqiruv.py direktor 192.168.1.50
"""

import json
import queue
import socket
import sys
import threading

DEFAULT_PORT = 50555          # Direktor -> Anvar (chaqiruv)
CONFIRM_PORT = DEFAULT_PORT + 1  # Anvar -> Direktor (tasdiq)
DEFAULT_MESSAGE = "Oldimga kir"
SENDER_NAME = "Direktor Sardor"
ANVAR_NAME = "Anvar"


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


def send_call(host, port, message, sender=SENDER_NAME, timeout=5):
    """Anvarga xabar yuboradi. (True, 'OK') yoki (False, xato) qaytaradi.

    Payload ichiga direktorning IP'si (sender_ip) ham qo'shiladi — Anvar
    "Hop, boraman" tugmasini bosganда shu manzilga tasdiq qaytaradi.
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


def send_confirm(host, port, text, who=ANVAR_NAME, timeout=5):
    """Anvardan direktorga tasdiq yuboradi (masalan 'Hop, boraman')."""
    payload = json.dumps({"confirm": text, "from": who}).encode("utf-8")
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(payload)
            s.shutdown(socket.SHUT_WR)
        return True, None
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# ANVAR tomoni (qabul qiluvchi + pop-up)
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
            print(f"[+] Chaqiruv keldi: '{text}'  (yuboruvchi: {sender})")
            msg_queue.put((text, sender, sender_ip))


def _show_popup(text, sender, sender_ip):
    """Diqqatni tortadigan qizil pop-up oyna (asosiy oqimda chaqirilsin).

    "Hop, boraman" tugmasi bosilganда direktorga (sender_ip:CONFIRM_PORT)
    tasdiq yuboriladi va oynada natija ko'rsatiladi.
    """
    import tkinter as tk

    root = tk.Tk()
    root.title("CHAQIRUV")
    root.attributes("-topmost", True)
    root.configure(bg="#b30000")
    root.resizable(False, False)

    w, h = 480, 320
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//3}")

    try:
        root.bell()
    except Exception:
        pass

    frame = tk.Frame(root, bg="#b30000")
    frame.pack(expand=True, fill="both", padx=20, pady=18)
    tk.Label(frame, text="📢  " + text, font=("Arial", 28, "bold"),
             fg="white", bg="#b30000").pack(pady=(6, 4))
    tk.Label(frame, text=f"Yuboruvchi: {sender}", font=("Arial", 13),
             fg="#ffe0e0", bg="#b30000").pack(pady=(0, 10))

    status = tk.Label(frame, text="", font=("Arial", 11, "bold"),
                      fg="#fff2b0", bg="#b30000")
    status.pack(pady=(0, 8))

    btn_row = tk.Frame(frame, bg="#b30000")
    btn_row.pack()

    def confirm(answer):
        """Tasdiqni direktorga yuboradi va oynani yopadi."""
        status.config(text="Yuborilmoqda...", fg="#fff2b0")
        root.update_idletasks()
        ok, err = send_confirm(sender_ip, CONFIRM_PORT, answer)
        if ok:
            status.config(text="✓ Direktorga yuborildi", fg="#c8f7c8")
        else:
            # Direktor javob kutmayotgan bo'lsa ham Anvarni to'smaymiz
            status.config(text="Direktorga yetkazib bo'lmadi", fg="#ffd0d0")
        root.after(700, root.destroy)

    yes_btn = tk.Button(btn_row, text="✅  Hop, boraman",
                        font=("Arial", 15, "bold"),
                        bg="white", fg="#0a7d0a", activebackground="#eaffea",
                        relief="flat", padx=18, pady=9,
                        command=lambda: confirm("Hop, boraman"))
    yes_btn.pack(side="left", padx=6)

    busy_btn = tk.Button(btn_row, text="⏳  Band edim, keyinroq",
                         font=("Arial", 13),
                         bg="#7a0000", fg="white", activebackground="#5c0000",
                         relief="flat", padx=14, pady=9,
                         command=lambda: confirm("Band edim, keyinroq boraman"))
    busy_btn.pack(side="left", padx=6)

    root.after(100, lambda: (root.focus_force(), yes_btn.focus_set()))
    root.mainloop()


def run_anvar(port=DEFAULT_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(5)

    local_ip = get_local_ip()
    print("=" * 52)
    print("  ANVAR — chaqiruvni kutish rejimi")
    print("=" * 52)
    print(f"  IP manzil (direktorga ayting): {local_ip}")
    print(f"  Port:                          {port}")
    print("  Xabar kelishi bilan pop-up oyna chiqadi.")
    print("  To'xtatish uchun: Ctrl + C")
    print("=" * 52)

    msg_queue = queue.Queue()
    threading.Thread(target=_listener_thread, args=(sock, msg_queue),
                     daemon=True).start()

    # Kutish oynasi — foydalanuvchi tirik ekanini ko'rsatib turadi va
    # xabar kelganda pop-up chiqaradi (GUI asosiy oqimда bo'lishi shart).
    import tkinter as tk

    root = tk.Tk()
    root.title("Anvar — kutish rejimi")
    root.configure(bg="#1e3d59")
    root.resizable(False, False)
    w, h = 420, 200
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//3}")
    fr = tk.Frame(root, bg="#1e3d59")
    fr.pack(expand=True, fill="both", padx=20, pady=20)
    tk.Label(fr, text="✅ Chaqiruvni kutmoqda...", font=("Arial", 18, "bold"),
             fg="white", bg="#1e3d59").pack(pady=(6, 12))
    tk.Label(fr, text=f"Sizning IP: {local_ip}   (port {port})",
             font=("Arial", 12), fg="#cfe0ee", bg="#1e3d59").pack()
    tk.Label(fr, text="Bu oynani yopmang. Direktorga IP manzilingizni ayting.",
             font=("Arial", 10), fg="#9fb8cc", bg="#1e3d59",
             wraplength=360).pack(pady=(12, 0))

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


# ---------------------------------------------------------------------------
# DIREKTOR tomoni (yuboruvchi GUI)
# ---------------------------------------------------------------------------
def _confirm_listener(sock, confirm_queue):
    """Anvardan kelgan tasdiqni (masalan 'Hop, boraman') qabul qiladi."""
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
            print(f"[+] Anvar javobi: '{text}'  ({who})")
            confirm_queue.put((text, who))


def run_direktor(prefill_ip=""):
    import tkinter as tk
    from tkinter import messagebox

    # Anvar tasdiqini kutish uchun fon listener'ini ishga tushiramiz.
    # (Port band bo'lsa ham dastur ishlashда davom etadi — faqat tasdiq
    #  ko'rinmaydi.)
    confirm_queue = queue.Queue()
    csock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    csock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    confirm_active = True
    try:
        csock.bind(("0.0.0.0", CONFIRM_PORT))
        csock.listen(5)
        threading.Thread(target=_confirm_listener, args=(csock, confirm_queue),
                         daemon=True).start()
    except OSError as e:
        confirm_active = False
        print(f"[!] Tasdiq portини ochib bo'lmadi ({CONFIRM_PORT}): {e}")

    root = tk.Tk()
    root.title("Direktor — Anvarni chaqirish")
    root.configure(bg="#1e3d59")
    root.resizable(False, False)
    w, h = 420, 400
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//3}")

    fr = tk.Frame(root, bg="#1e3d59")
    fr.pack(expand=True, fill="both", padx=24, pady=20)
    tk.Label(fr, text="Anvarni chaqirish", font=("Arial", 20, "bold"),
             fg="white", bg="#1e3d59").pack(pady=(0, 16))

    tk.Label(fr, text="Anvar IP manzili:", font=("Arial", 11),
             fg="#cfe0ee", bg="#1e3d59").pack(anchor="w")
    ip_entry = tk.Entry(fr, font=("Arial", 12))
    ip_entry.insert(0, prefill_ip or "192.168.1.")
    ip_entry.pack(fill="x", pady=(2, 10))

    tk.Label(fr, text="Xabar matni:", font=("Arial", 11),
             fg="#cfe0ee", bg="#1e3d59").pack(anchor="w")
    msg_entry = tk.Entry(fr, font=("Arial", 12))
    msg_entry.insert(0, DEFAULT_MESSAGE)
    msg_entry.pack(fill="x", pady=(2, 14))

    status = tk.Label(fr, text="", font=("Arial", 10),
                      fg="#ffd966", bg="#1e3d59")
    status.pack(pady=(4, 6))

    def on_send():
        host = ip_entry.get().strip()
        message = msg_entry.get().strip() or DEFAULT_MESSAGE
        if not host:
            status.config(text="IP manzilini kiriting!", fg="#ff8a8a")
            return
        status.config(text="Yuborilmoqda...", fg="#ffd966")
        root.update_idletasks()
        ok, info = send_call(host, DEFAULT_PORT, message)
        if ok:
            status.config(text="✓ Yuborildi! Anvar ekranida chiqdi.", fg="#9be89b")
        else:
            status.config(text="✗ Yuborilmadi", fg="#ff8a8a")
            messagebox.showerror(
                "Xatolik",
                "Xabar yuborilmadi.\n\nSabab: " + info +
                "\n\nTekshiring:\n• Anvarда dastur 'kutish rejimi'да ochiqmi?\n"
                "• IP manzil to'g'rimi?\n• Bir tarmoqdamisiz?",
            )

    tk.Button(fr, text="📢  CHAQIRISH", font=("Arial", 16, "bold"),
              bg="#e63946", fg="white", activebackground="#c92d3a",
              relief="flat", padx=20, pady=12, command=on_send).pack(fill="x",
                                                                     pady=(6, 10))

    # Anvar javobi shu yerda chiqadi
    tk.Frame(fr, bg="#345", height=1).pack(fill="x", pady=(4, 8))
    tk.Label(fr, text="Anvar javobi:", font=("Arial", 11),
             fg="#cfe0ee", bg="#1e3d59").pack(anchor="w")
    reply_lbl = tk.Label(
        fr,
        text=("— (kutilmoqda)" if confirm_active
              else "⚠ Javob porti band — tasdiq ko'rinmaydi"),
        font=("Arial", 13, "bold"),
        fg="#9fb8cc", bg="#1e3d59", wraplength=360, justify="left",
    )
    reply_lbl.pack(anchor="w", pady=(2, 0))

    def poll_confirm():
        try:
            while True:
                text, who = confirm_queue.get_nowait()
                reply_lbl.config(text=f"✅ {who}: {text}", fg="#9be89b")
                try:
                    root.bell()
                except Exception:
                    pass
        except queue.Empty:
            pass
        root.after(300, poll_confirm)

    root.after(300, poll_confirm)
    root.bind("<Return>", lambda e: on_send())
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

    tk.Button(fr, text="👔  Men DIREKTORMAN\n(chaqiraman)",
              font=("Arial", 14, "bold"), bg="#e63946", fg="white",
              activebackground="#c92d3a", relief="flat", pady=12,
              command=lambda: pick("direktor")).pack(fill="x", pady=(0, 14))
    tk.Button(fr, text="🧑‍💼  Men ANVARMAN\n(kutaman)",
              font=("Arial", 14, "bold"), bg="#2a9d8f", fg="white",
              activebackground="#238377", relief="flat", pady=12,
              command=lambda: pick("anvar")).pack(fill="x")

    root.mainloop()
    return choice["role"]


# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    role = args[0].lower() if args else None

    # Terminaldan to'g'ridan-to'g'ri rol berilgan bo'lsa
    if role in ("anvar", "a"):
        run_anvar()
        return
    if role in ("direktor", "d"):
        prefill = args[1] if len(args) > 1 else ""
        run_direktor(prefill)
        return

    # Aks holda — grafik rol tanlash oynasi
    chosen = run_chooser()
    if chosen == "anvar":
        run_anvar()
    elif chosen == "direktor":
        run_direktor()
    else:
        print("Rol tanlanmadi. Chiqildi.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[i] To'xtatildi.")
