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

DEFAULT_PORT = 50555
DEFAULT_MESSAGE = "Oldimga kir"
SENDER_NAME = "Direktor Sardor"


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
    """Anvarga xabar yuboradi. (True, 'OK') yoki (False, xato) qaytaradi."""
    payload = json.dumps({"message": message, "sender": sender}).encode("utf-8")
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

            text, sender = DEFAULT_MESSAGE, addr[0]
            payload = data.decode("utf-8", errors="replace").strip()
            if payload:
                try:
                    obj = json.loads(payload)
                    text = obj.get("message", DEFAULT_MESSAGE)
                    sender = obj.get("sender", addr[0])
                except (ValueError, AttributeError):
                    text = payload
            try:
                conn.sendall(b"OK")
            except OSError:
                pass
            print(f"[+] Chaqiruv keldi: '{text}'  (yuboruvchi: {sender})")
            msg_queue.put((text, sender))


def _show_popup(text, sender):
    """Diqqatni tortadigan qizil pop-up oyna (asosiy oqimda chaqirilsin)."""
    import tkinter as tk

    root = tk.Tk()
    root.title("CHAQIRUV")
    root.attributes("-topmost", True)
    root.configure(bg="#b30000")
    root.resizable(False, False)

    w, h = 460, 260
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//3}")

    try:
        root.bell()
    except Exception:
        pass

    frame = tk.Frame(root, bg="#b30000")
    frame.pack(expand=True, fill="both", padx=20, pady=20)
    tk.Label(frame, text="📢  " + text, font=("Arial", 28, "bold"),
             fg="white", bg="#b30000").pack(pady=(10, 6))
    tk.Label(frame, text=f"Yuboruvchi: {sender}", font=("Arial", 13),
             fg="#ffe0e0", bg="#b30000").pack(pady=(0, 18))
    btn = tk.Button(frame, text="Tushunarli — Kelaman", font=("Arial", 14, "bold"),
                    bg="white", fg="#b30000", activebackground="#f0f0f0",
                    relief="flat", padx=20, pady=8, command=root.destroy)
    btn.pack()
    root.after(100, lambda: (root.focus_force(), btn.focus_set()))
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
                text, sender = msg_queue.get_nowait()
                _show_popup(text, sender)
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
def run_direktor(prefill_ip=""):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title("Direktor — Anvarni chaqirish")
    root.configure(bg="#1e3d59")
    root.resizable(False, False)
    w, h = 420, 320
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
                                                                     pady=(6, 0))
    root.bind("<Return>", lambda e: on_send())
    root.mainloop()


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
