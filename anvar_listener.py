#!/usr/bin/env python3
"""
Anvar kompyuterida ishga tushiriladigan dastur (qabul qiluvchi / listener).

Vazifasi:
  - Tarmoq (LAN) orqali direktor kompyuteridan kelgan xabarni kutadi.
  - Xabar kelganda ekranda "Oldimga kir" degan pop-up oyna chiqaradi.
  - Telefon yoki SMS umuman ishlatilmaydi — faqat mahalliy tarmoq.

Ishga tushirish (Anvar kompyuterida):
  python3 anvar_listener.py
  python3 anvar_listener.py --port 50555   # portni o'zgartirish

Anvar o'z IP manzilini bilishi kerak (direktorga aytish uchun):
  - Windows:  ipconfig
  - Linux/Mac: ip addr  yoki  ifconfig
Dastur ishga tushganda IP manzil terminalда ham ko'rsatiladi.
"""

import argparse
import json
import queue
import socket
import threading

DEFAULT_PORT = 50555
CONFIRM_PORT = DEFAULT_PORT + 1   # Anvar -> Direktor (tasdiq)
DEFAULT_MESSAGE = "Oldimga kir"
ANVAR_NAME = "Anvar"


def get_local_ip():
    """Kompyuterning tarmoqdagi IP manzilini aniqlaydi (LAN uchun)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Haqiqiy ulanish bo'lmaydi, faqat marshrutни aniqlash uchun
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def send_confirm(host, port, text, who=ANVAR_NAME, timeout=5):
    """Anvardan direktorga tasdiq yuboradi (masalan 'Hop, boraman')."""
    import json as _json
    payload = _json.dumps({"confirm": text, "from": who}).encode("utf-8")
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(payload)
            s.shutdown(socket.SHUT_WR)
        return True, None
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return False, str(e)


def show_popup(text, sender, sender_ip):
    """
    tkinter yordamida diqqatni tortadigan pop-up oyna chiqaradi.
    Bu funksiya asosiy (main) oqimda chaqirilishi kerak — GUI shu talab qiladi.
    """
    import tkinter as tk

    root = tk.Tk()
    root.title("CHAQIRUV")

    # Oynani hamma narsadan ustun (topmost) qilib ekran markaziga qo'yamiz
    root.attributes("-topmost", True)
    root.configure(bg="#b30000")
    root.resizable(False, False)

    w, h = 480, 320
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 3
    root.geometry(f"{w}x{h}+{x}+{y}")

    # Diqqatni tortish uchun ovoz (bo'lsa)
    try:
        root.bell()
    except Exception:
        pass

    frame = tk.Frame(root, bg="#b30000")
    frame.pack(expand=True, fill="both", padx=20, pady=18)

    tk.Label(
        frame,
        text="📢  " + text,
        font=("Arial", 28, "bold"),
        fg="white",
        bg="#b30000",
    ).pack(pady=(6, 4))

    tk.Label(
        frame,
        text=f"Yuboruvchi: {sender}",
        font=("Arial", 13),
        fg="#ffe0e0",
        bg="#b30000",
    ).pack(pady=(0, 10))

    status = tk.Label(frame, text="", font=("Arial", 11, "bold"),
                      fg="#fff2b0", bg="#b30000")
    status.pack(pady=(0, 8))

    btn_row = tk.Frame(frame, bg="#b30000")
    btn_row.pack()

    def confirm(answer):
        """Tasdiqni direktorga yuboradi va oynani yopadi."""
        status.config(text="Yuborilmoqda...", fg="#fff2b0")
        root.update_idletasks()
        ok, _ = send_confirm(sender_ip, CONFIRM_PORT, answer)
        status.config(
            text="✓ Direktorga yuborildi" if ok else "Direktorga yetkazib bo'lmadi",
            fg="#c8f7c8" if ok else "#ffd0d0",
        )
        root.after(700, root.destroy)

    yes_btn = tk.Button(
        btn_row, text="✅  Hop, boraman", font=("Arial", 15, "bold"),
        bg="white", fg="#0a7d0a", activebackground="#eaffea",
        relief="flat", padx=18, pady=9,
        command=lambda: confirm("Hop, boraman"),
    )
    yes_btn.pack(side="left", padx=6)

    tk.Button(
        btn_row, text="⏳  Band edim, keyinroq", font=("Arial", 13),
        bg="#7a0000", fg="white", activebackground="#5c0000",
        relief="flat", padx=14, pady=9,
        command=lambda: confirm("Band edim, keyinroq boraman"),
    ).pack(side="left", padx=6)

    # Oyna paydo bo'lganда fokusni oladi
    root.after(100, lambda: (root.focus_force(), yes_btn.focus_set()))
    root.mainloop()


def listener_thread(sock, msg_queue):
    """Fon oqimda ulanishlarni qabul qiladi va xabarlarni navbatga qo'yadi."""
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
                    if len(data) > 65536:  # xavfsizlik chegarasi
                        break
            except socket.timeout:
                pass

            text = DEFAULT_MESSAGE
            sender = addr[0]
            sender_ip = addr[0]
            payload = data.decode("utf-8", errors="replace").strip()
            if payload:
                try:
                    obj = json.loads(payload)
                    text = obj.get("message", DEFAULT_MESSAGE)
                    sender = obj.get("sender", addr[0])
                    sender_ip = obj.get("sender_ip", addr[0])
                except (ValueError, AttributeError):
                    text = payload  # oddiy matn ham qabul qilinadi

            # Direktorga "yetkazildi" javobini yuboramiz
            try:
                conn.sendall(b"OK")
            except OSError:
                pass

            print(f"[+] Chaqiruv keldi: '{text}'  (yuboruvchi: {sender})")
            msg_queue.put((text, sender, sender_ip))


def main():
    parser = argparse.ArgumentParser(description="Anvar chaqiruv qabul qiluvchi")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Tinglash porti (default: {DEFAULT_PORT})")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Tinglash manzili (default: 0.0.0.0 — barcha interfeyslar)")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.host, args.port))
    sock.listen(5)

    local_ip = get_local_ip()
    print("=" * 52)
    print("  ANVAR — chaqiruvni kutish rejimi")
    print("=" * 52)
    print(f"  IP manzil (direktorga ayting): {local_ip}")
    print(f"  Port:                          {args.port}")
    print("  Xabar kelishi bilan pop-up oyna chiqadi.")
    print("  To'xtatish uchun: Ctrl + C")
    print("=" * 52)

    msg_queue = queue.Queue()
    t = threading.Thread(target=listener_thread, args=(sock, msg_queue), daemon=True)
    t.start()

    # GUI (tkinter) asosiy oqimда ishlashi shart, shuning uchun pop-up'ларни
    # shu yerda navbatдан olib ko'rsatamiz.
    try:
        while True:
            text, sender, sender_ip = msg_queue.get()  # xabar kelguncha kutadi
            show_popup(text, sender, sender_ip)
    except KeyboardInterrupt:
        print("\n[i] To'xtatildi.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
