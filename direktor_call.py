#!/usr/bin/env python3
"""
Direktor (Sardor) kompyuterida ishga tushiriladigan dastur (yuboruvchi).

Vazifasi:
  - Bir tugma bosilishi bilan Anvar kompyuteriga xabar yuboradi.
  - Anvar ekranida "Oldimga kir" pop-up oynasi chiqadi.
  - Telefon yoki SMS ishlatilmaydi — faqat mahalliy tarmoq (LAN).

Ikki xil ishlatish mumkin:

1) Grafik oyna (tugmali):
     python3 direktor_call.py --gui

2) Terminaldan bitta buyruq bilan (tugmasiz):
     python3 direktor_call.py --to 192.168.1.50
     python3 direktor_call.py --to 192.168.1.50 --message "Oldimga kir"

  --to      : Anvar kompyuterining IP manzili (anvar_listener.py ko'rsatadi)
  --port    : Anvar tinglayotgan port (default: 50555)
  --message : Yuboriladigan matn (default: "Oldimga kir")
"""

import argparse
import json
import socket

DEFAULT_PORT = 50555
DEFAULT_MESSAGE = "Oldimga kir"
SENDER_NAME = "Direktor Sardor"


def send_call(host, port, message, sender=SENDER_NAME, timeout=5):
    """
    Anvar kompyuteriga xabar yuboradi.
    Muvaffaqiyatli bo'lsa (True, None), aks holda (False, xato matni) qaytaradi.
    """
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


def run_cli(args):
    if not args.to:
        print("Xato: Anvar IP manzilini --to bilan ko'rsating. Masalan:")
        print("  python3 direktor_call.py --to 192.168.1.50")
        return 1

    print(f"[>] Anvarga yuborilmoqda: {args.to}:{args.port} — '{args.message}'")
    ok, info = send_call(args.to, args.port, args.message)
    if ok:
        print("[✓] Yuborildi! Anvar ekranida pop-up chiqdi.")
        return 0
    else:
        print(f"[✗] Yuborilmadi. Sabab: {info}")
        print("    Tekshiring: Anvar kompyuterida anvar_listener.py ishlab turibdimi?")
        print("    IP manzil va port to'g'rimi? Bir tarmoqdamisiz?")
        return 1


def run_gui(args):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title("Direktor — Anvarni chaqirish")
    root.configure(bg="#1e3d59")
    root.resizable(False, False)

    w, h = 420, 320
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//3}")

    frame = tk.Frame(root, bg="#1e3d59")
    frame.pack(expand=True, fill="both", padx=24, pady=20)

    tk.Label(frame, text="Anvarni chaqirish", font=("Arial", 20, "bold"),
             fg="white", bg="#1e3d59").pack(pady=(0, 16))

    tk.Label(frame, text="Anvar IP manzili:", font=("Arial", 11),
             fg="#cfe0ee", bg="#1e3d59").pack(anchor="w")
    ip_entry = tk.Entry(frame, font=("Arial", 12))
    ip_entry.insert(0, args.to or "192.168.1.")
    ip_entry.pack(fill="x", pady=(2, 10))

    tk.Label(frame, text="Xabar matni:", font=("Arial", 11),
             fg="#cfe0ee", bg="#1e3d59").pack(anchor="w")
    msg_entry = tk.Entry(frame, font=("Arial", 12))
    msg_entry.insert(0, args.message)
    msg_entry.pack(fill="x", pady=(2, 14))

    status = tk.Label(frame, text="", font=("Arial", 10),
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
        ok, info = send_call(host, args.port, message)
        if ok:
            status.config(text="✓ Yuborildi! Anvar ekranida chiqdi.", fg="#9be89b")
        else:
            status.config(text="✗ Yuborilmadi", fg="#ff8a8a")
            messagebox.showerror(
                "Xatolik",
                "Xabar yuborilmadi.\n\nSabab: " + info +
                "\n\nTekshiring:\n• Anvar kompyuterida anvar_listener.py ishlaptimi?\n"
                "• IP manzil to'g'rimi?\n• Bir tarmoqdamisiz?",
            )

    send_btn = tk.Button(frame, text="📢  CHAQIRISH", font=("Arial", 16, "bold"),
                         bg="#e63946", fg="white", activebackground="#c92d3a",
                         relief="flat", padx=20, pady=12, command=on_send)
    send_btn.pack(fill="x", pady=(6, 0))

    root.bind("<Return>", lambda e: on_send())
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Direktor — Anvarni chaqirish")
    parser.add_argument("--to", help="Anvar kompyuterining IP manzili")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Anvar porti (default: {DEFAULT_PORT})")
    parser.add_argument("--message", default=DEFAULT_MESSAGE,
                        help=f"Xabar matni (default: '{DEFAULT_MESSAGE}')")
    parser.add_argument("--gui", action="store_true",
                        help="Grafik (tugmali) oynani ochish")
    args = parser.parse_args()

    if args.gui or not args.to:
        # IP berilmagan bo'lsa ham qulaylik uchun GUI ochamiz
        if not args.gui and not args.to:
            print("[i] IP berilmadi — grafik oyna ochilmoqda "
                  "(terminaldan ishlatish uchun --to bilan IP bering).")
        run_gui(args)
        return 0
    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
