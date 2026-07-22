#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# chaqiruv dasturi - ichki tarmoqda xabar yuborish uchun
# telefon/sms ishlatmaymiz, hammasi wifi orqali
# ochib rolni tanlaysan: direktor yoki hodim
#
# portlar:
PORT = 50555          # xabar shu portga boradi
JAVOB_PORT = 50556    # hodim javobi shu yerga qaytadi
QIDIRUV_PORT = 50557  # udp, avtomatik topish uchun

import socket
import json
import threading
import time
import queue
import sys, os

DEF_MSG = "Oldimga kir"

# ===== DIREKTOR PAROLI =====
# MUHIM: exe yasashдан oldин buni O'ZGARTIRING va maxfiy saqlang!
# Faqat shu parolни bilган odam direktor rejimига kira olади.
# (Hodimlar bunи bilмаса, direktor nomidan xabar yubora olмайди.)
DIREKTOR_PAROL = "parol123"

# tez ishlatiladigan xabarlar (direktor tugmadan tanlaydi)
tayyor_xabarlar = [
    "Oldimga kir",
    "Yig'ilish boshlandi, zalga keling",
    "Tushlik vaqti",
    "Ish tugadi, borsalar bo'ladi",
]

# direktor tomonда topilgan hodimlar shu yerga yig'iladi (udp orqali)
# ip -> {ism, ip, vaqt}
topilgan = {}
topilgan_lock = threading.Lock()


def mening_ip():
    # o'zimning lokal ip manzilim
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    s.close()
    return ip


def komp_nomi():
    try:
        return socket.gethostname()
    except:
        return "hodim"


# fayl qayerda tursin (py va exe uchun)
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

HODIMLAR_FAYL = os.path.join(APP_DIR, "hodimlar.json")


# rol qayerga saqlanadi (%APPDATA%\Chaqiruv, yozishga ruxsat bor)
def _cfg_papka():
    d = os.environ.get("APPDATA")
    if not d:
        d = APP_DIR
    p = os.path.join(d, "Chaqiruv")
    try:
        os.makedirs(p, exist_ok=True)
    except:
        p = APP_DIR
    return p

ROL_FAYL = os.path.join(_cfg_papka(), "rol.cfg")


def rolni_oqi():
    # bu komp qaysi rolда? 'hodim' / 'direktor' / None
    try:
        f = open(ROL_FAYL, "r", encoding="utf-8")
        r = f.read().strip().lower()
        f.close()
        if r in ("hodim", "direktor"):
            return r
    except:
        pass
    return None


def rolni_saqla(r):
    try:
        f = open(ROL_FAYL, "w", encoding="utf-8")
        f.write(r)
        f.close()
    except:
        print("rolni saqlab bo'lmadi")


def hodimlarni_oqi():
    # qo'lda kiritilgan hodimlar json dan
    if os.path.exists(HODIMLAR_FAYL):
        try:
            f = open(HODIMLAR_FAYL, "r", encoding="utf-8")
            data = json.load(f)
            f.close()
            res = []
            for x in data:
                ip = str(x.get("ip", "")).strip()
                ism = str(x.get("ism", "")).strip()
                if ip != "":
                    res.append({"ism": ism or ip, "ip": ip})
            return res
        except:
            return []
    return []


def hodimlarni_saqla(royxat):
    try:
        f = open(HODIMLAR_FAYL, "w", encoding="utf-8")
        json.dump(royxat, f, ensure_ascii=False, indent=2)
        f.close()
    except:
        print("saqlab bo'lmadi :(")


# ========================= XABAR YUBORISH =========================
def xabar_yubor(ip, matn):
    # bitta hodimga xabar. (True/False, info) qaytaradi
    paket = json.dumps({
        "message": matn,
        "sender": "Direktor",
        "sender_ip": mening_ip(),
    })
    try:
        s = socket.create_connection((ip, PORT), timeout=5)
        s.sendall(paket.encode("utf-8"))
        s.shutdown(socket.SHUT_WR)
        try:
            s.settimeout(5)
            javob = s.recv(16)
        except socket.timeout:
            javob = b""
        s.close()
        return True, javob.decode("utf-8", "replace")
    except Exception as e:
        return False, str(e)


def javob_yubor(ip, matn):
    # hodim -> direktor (masalan "Hop boraman")
    paket = json.dumps({"confirm": matn, "from": komp_nomi()})
    try:
        s = socket.create_connection((ip, JAVOB_PORT), timeout=5)
        s.sendall(paket.encode("utf-8"))
        s.shutdown(socket.SHUT_WR)
        s.close()
        return True
    except:
        return False


# ========================= HODIM TOMONI =========================
def qabul_listener(sock, q):
    # xabar kelsa navbatga qo'yamiz, keyin gui popup chiqaradi
    while True:
        try:
            conn, addr = sock.accept()
        except OSError:
            break
        data = b""
        conn.settimeout(5)
        try:
            while True:
                b = conn.recv(1024)
                if not b:
                    break
                data += b
                if len(data) > 60000:
                    break
        except socket.timeout:
            pass

        matn = DEF_MSG
        kim = addr[0]
        kim_ip = addr[0]
        try:
            o = json.loads(data.decode("utf-8", "replace"))
            matn = o.get("message", DEF_MSG)
            kim = o.get("sender", addr[0])
            kim_ip = o.get("sender_ip", addr[0])
        except:
            # oddiy matn ham bo'lishi mumkin
            t = data.decode("utf-8", "replace").strip()
            if t:
                matn = t
        try:
            conn.sendall(b"OK")
        except:
            pass
        conn.close()
        print("xabar keldi:", matn, "(", kim, ")")
        q.put((matn, kim, kim_ip))


def ozini_elon_qil(stop):
    # udp broadcast - direktor bizni avtomatik ko'rsin
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    ma_lumot = json.dumps({"tip": "elon", "ism": komp_nomi(), "ip": mening_ip()})
    while not stop.is_set():
        try:
            s.sendto(ma_lumot.encode("utf-8"), ("255.255.255.255", QIDIRUV_PORT))
            # ba'zi tarmoqda 255.255.255.255 ishlamaydi, shu uchun buni ham:
            s.sendto(ma_lumot.encode("utf-8"), ("<broadcast>", QIDIRUV_PORT))
        except:
            pass
        time.sleep(3)
    s.close()


def popup(parent, matn, kim, kim_ip):
    # DIQQAT: bu Toplevel (bola oyna), Tk() emas! Aks holda ikkinchi
    # Tk() ochilib, birinchi popupdan keyin tinglash to'xtab qolardi.
    import tkinter as tk
    r = tk.Toplevel(parent)
    r.title("YANGI XABAR")
    r.attributes("-topmost", True)
    r.configure(bg="#b30000")
    r.resizable(False, False)
    w, h = 520, 340
    sw = r.winfo_screenwidth(); sh = r.winfo_screenheight()
    r.geometry("%dx%d+%d+%d" % (w, h, (sw-w)//2, (sh-h)//3))
    try:
        r.bell()
    except:
        pass

    fr = tk.Frame(r, bg="#b30000")
    fr.pack(expand=True, fill="both", padx=22, pady=18)
    tk.Label(fr, text="📢  " + matn, font=("Arial", 24, "bold"), fg="white",
             bg="#b30000", wraplength=470, justify="center").pack(pady=(6, 4))
    tk.Label(fr, text="Yuboruvchi: " + str(kim), font=("Arial", 13),
             fg="#ffe0e0", bg="#b30000").pack(pady=(0, 10))

    holat = tk.Label(fr, text="", font=("Arial", 11, "bold"), fg="#fff2b0",
                     bg="#b30000")
    holat.pack(pady=(0, 8))

    qator = tk.Frame(fr, bg="#b30000")
    qator.pack()

    def javob_ber(t):
        holat.config(text="yuborilmoqda...", fg="#fff2b0")
        r.update_idletasks()
        ok = javob_yubor(kim_ip, t)
        if ok:
            holat.config(text="✓ direktorga yuborildi", fg="#c8f7c8")
        else:
            holat.config(text="yuborib bo'lmadi", fg="#ffd0d0")
        r.after(700, r.destroy)

    tk.Button(qator, text="✅  Hop, boraman", font=("Arial", 15, "bold"),
              bg="white", fg="#0a7d0a", relief="flat", padx=16, pady=9,
              command=lambda: javob_ber("Hop, boraman")).pack(side="left", padx=5)
    tk.Button(qator, text="👍  Qabul qilindi", font=("Arial", 13), bg="#0a5d9c",
              fg="white", relief="flat", padx=14, pady=9,
              command=lambda: javob_ber("Qabul qilindi")).pack(side="left", padx=5)
    tk.Button(qator, text="⏳  Keyinroq", font=("Arial", 13), bg="#7a0000",
              fg="white", relief="flat", padx=14, pady=9,
              command=lambda: javob_ber("Band edim, keyinroq")).pack(side="left", padx=5)

    r.after(100, lambda: (r.focus_force()))
    # mainloop CHAQIRILMAYDI - asosiy oyna (hodim_rejim) allaqachon
    # mainloop'da ishlayapti, popup shunчaki uning ustida chiqadi.


def hodim_rejim():
    import tkinter as tk
    # tcp - xabar qabul qilish
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", PORT))
    sock.listen(5)

    ip = mening_ip()
    print("=" * 50)
    print("  HODIM - kutish rejimi")
    print("  komp:", komp_nomi(), " ip:", ip, " port:", PORT)
    print("  to'xtatish: Ctrl+C")
    print("=" * 50)

    q = queue.Queue()
    threading.Thread(target=qabul_listener, args=(sock, q), daemon=True).start()

    # udp elon (avtomatik topish)
    stop = threading.Event()
    threading.Thread(target=ozini_elon_qil, args=(stop,), daemon=True).start()

    # hodim rejimi FONDA ishlaydi - oyna ko'rinmaydi.
    # faqat direktor xabar yuborganda pop-up chiqadi.
    r = tk.Tk()
    r.title("Chaqiruv")
    r.withdraw()   # oynani yashiramiz

    def tekshir():
        try:
            while True:
                matn, kim, kim_ip = q.get_nowait()
                popup(r, matn, kim, kim_ip)   # r = asosiy (yashirin) oyna
        except queue.Empty:
            pass
        r.after(300, tekshir)

    r.after(300, tekshir)
    try:
        r.mainloop()
    finally:
        stop.set()
        sock.close()


# eski nomlar ham ishlashi uchun
run_hodim = hodim_rejim
run_anvar = hodim_rejim


# ========================= DIREKTOR TOMONI =========================
def javob_listener(sock, q):
    # hodimlardan javob keladi
    while True:
        try:
            conn, addr = sock.accept()
        except OSError:
            break
        data = b""
        conn.settimeout(5)
        try:
            while True:
                b = conn.recv(1024)
                if not b:
                    break
                data += b
                if len(data) > 60000:
                    break
        except socket.timeout:
            pass
        conn.close()
        matn = "javob"
        kim = addr[0]
        try:
            o = json.loads(data.decode("utf-8", "replace"))
            matn = o.get("confirm", matn)
            kim = o.get("from", addr[0])
        except:
            pass
        print("javob:", matn, "(", kim, "/", addr[0], ")")
        q.put((matn, kim, addr[0]))


def qidiruv_listener(stop):
    # udp - hodimlarning elonini eshitamiz
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("", QIDIRUV_PORT))
    except OSError as e:
        print("qidiruv portini ochib bo'lmadi:", e)
        return
    s.settimeout(1)
    myip = mening_ip()
    while not stop.is_set():
        try:
            data, addr = s.recvfrom(2048)
        except socket.timeout:
            continue
        except OSError:
            break
        try:
            o = json.loads(data.decode("utf-8", "replace"))
        except:
            continue
        if o.get("tip") != "elon":
            continue
        ip = o.get("ip", addr[0])
        if ip == myip:
            continue  # o'zimni qo'shmayman
        ism = o.get("ism", ip)
        with topilgan_lock:
            topilgan[ip] = {"ism": ism, "ip": ip, "vaqt": time.time()}
    s.close()


def direktor_rejim(prefill=""):
    import tkinter as tk
    from tkinter import messagebox

    hodimlar = hodimlarni_oqi()
    if prefill and not any(h["ip"] == prefill for h in hodimlar):
        hodimlar.insert(0, {"ism": prefill, "ip": prefill})

    # javob kutish (tcp)
    jq = queue.Queue()
    jsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    jsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    javob_ok = True
    try:
        jsock.bind(("0.0.0.0", JAVOB_PORT))
        jsock.listen(8)
        threading.Thread(target=javob_listener, args=(jsock, jq), daemon=True).start()
    except OSError as e:
        javob_ok = False
        print("javob port band:", e)

    # avtomatik topish (udp)
    stop = threading.Event()
    threading.Thread(target=qidiruv_listener, args=(stop,), daemon=True).start()

    natija_q = queue.Queue()  # (ip, ok/err)

    r = tk.Tk()
    r.title("Direktor - xabar yuborish")
    r.configure(bg="#1e3d59")
    r.minsize(560, 620)
    sw = r.winfo_screenwidth(); sh = r.winfo_screenheight()
    w, h = 580, 700
    r.geometry("%dx%d+%d+%d" % (w, h, (sw-w)//2, max(0, (sh-h)//4)))

    top = tk.Frame(r, bg="#1e3d59")
    top.pack(expand=True, fill="both", padx=18, pady=12)

    tk.Label(top, text="📢 Tashkilotga xabar", font=("Arial", 20, "bold"),
             fg="white", bg="#1e3d59").pack(anchor="w")

    # xabar matni
    tk.Label(top, text="Xabar:", font=("Arial", 11), fg="#cfe0ee",
             bg="#1e3d59").pack(anchor="w", pady=(8, 2))
    msg_box = tk.Text(top, font=("Arial", 12), height=3, wrap="word")
    msg_box.insert("1.0", DEF_MSG)
    msg_box.pack(fill="x")

    pr = tk.Frame(top, bg="#1e3d59")
    pr.pack(fill="x", pady=(5, 3))
    tk.Label(pr, text="Tayyor:", font=("Arial", 10), fg="#9fb8cc",
             bg="#1e3d59").pack(side="left", padx=(0, 4))

    def qoy(t):
        msg_box.delete("1.0", "end")
        msg_box.insert("1.0", t)

    for p in tayyor_xabarlar:
        nom = p if len(p) <= 16 else p[:15] + "…"
        tk.Button(pr, text=nom, font=("Arial", 9), bg="#2c5578", fg="white",
                  relief="flat", padx=6, pady=2,
                  command=lambda t=p: qoy(t)).pack(side="left", padx=2)

    # kimga
    hd = tk.Frame(top, bg="#1e3d59")
    hd.pack(fill="x", pady=(10, 2))
    tk.Label(hd, text="Kimga (🟢=onlayn, avtomatik topilgan):", font=("Arial", 11),
             fg="#cfe0ee", bg="#1e3d59").pack(side="left")
    hammasi_var = tk.IntVar(value=1)

    def hammasini():
        v = hammasi_var.get()
        for ip in qatorlar:
            qatorlar[ip]["var"].set(v)

    tk.Checkbutton(hd, text="Hammasi", variable=hammasi_var, command=hammasini,
                   font=("Arial", 10), fg="#cfe0ee", bg="#1e3d59",
                   selectcolor="#12263a", activebackground="#1e3d59",
                   activeforeground="white").pack(side="right")

    # skrol ro'yxat
    box = tk.Frame(top, bg="#12263a", height=200)
    box.pack(fill="both", expand=True, pady=(2, 6))
    box.pack_propagate(False)
    kanvas = tk.Canvas(box, bg="#12263a", highlightthickness=0)
    skr = tk.Scrollbar(box, orient="vertical", command=kanvas.yview)
    ich = tk.Frame(kanvas, bg="#12263a")
    ich.bind("<Configure>", lambda e: kanvas.configure(scrollregion=kanvas.bbox("all")))
    kanvas.create_window((0, 0), window=ich, anchor="nw", width=520)
    kanvas.configure(yscrollcommand=skr.set)
    kanvas.pack(side="left", fill="both", expand=True)
    skr.pack(side="right", fill="y")

    qatorlar = {}   # ip -> {var, nom_lbl, holat_lbl, online}

    def bitta_qator(ism, ip):
        f = tk.Frame(ich, bg="#12263a")
        f.pack(fill="x", padx=6, pady=2)
        var = tk.IntVar(value=1)
        tk.Checkbutton(f, variable=var, bg="#12263a", selectcolor="#1e3d59",
                       activebackground="#12263a").pack(side="left")
        nom = tk.Label(f, text="⚪ " + ism + "  (" + ip + ")", font=("Arial", 11),
                       fg="white", bg="#12263a", width=28, anchor="w")
        nom.pack(side="left")
        hol = tk.Label(f, text="—", font=("Arial", 10), fg="#9fb8cc",
                       bg="#12263a", anchor="w")
        hol.pack(side="left", fill="x", expand=True)
        qatorlar[ip] = {"var": var, "nom_lbl": nom, "holat_lbl": hol,
                        "ism": ism, "online": False}

    # boshida qo'lda kiritilganlarni qo'yamiz
    for h in hodimlar:
        if h["ip"] not in qatorlar:
            bitta_qator(h["ism"], h["ip"])

    # qo'lda qo'shish
    qq = tk.Frame(top, bg="#1e3d59")
    qq.pack(fill="x", pady=(2, 6))
    tk.Label(qq, text="Qo'lda:", font=("Arial", 10), fg="#9fb8cc",
             bg="#1e3d59").pack(side="left")
    ism_e = tk.Entry(qq, font=("Arial", 10), width=12)
    ism_e.pack(side="left", padx=(4, 3))
    ip_e = tk.Entry(qq, font=("Arial", 10), width=14)
    ip_e.pack(side="left", padx=3)
    ip_e.insert(0, "IP")

    def qol_qosh():
        ip = ip_e.get().strip()
        ism = ism_e.get().strip()
        if ip == "" or ip == "IP":
            messagebox.showwarning("e'tibor", "IP kiriting")
            return
        if ip not in qatorlar:
            bitta_qator(ism or ip, ip)
        hodimlar.append({"ism": ism or ip, "ip": ip})
        hodimlarni_saqla(hodimlar)
        ism_e.delete(0, "end"); ip_e.delete(0, "end")

    tk.Button(qq, text="➕", font=("Arial", 10), bg="#2a9d8f", fg="white",
              relief="flat", padx=8, command=qol_qosh).pack(side="left", padx=3)

    # yuborish
    def bitta_yubor(ip, matn):
        ok, info = xabar_yubor(ip, matn)
        natija_q.put((ip, ok))

    def yubor():
        matn = msg_box.get("1.0", "end").strip()
        if matn == "":
            messagebox.showwarning("e'tibor", "xabar bo'sh")
            return
        tanlangan = [ip for ip in qatorlar if qatorlar[ip]["var"].get()]
        if len(tanlangan) == 0:
            messagebox.showwarning("e'tibor", "hech kim tanlanmadi")
            return
        for ip in tanlangan:
            qatorlar[ip]["holat_lbl"].config(text="yuborilmoqda...", fg="#ffd966")
            threading.Thread(target=bitta_yubor, args=(ip, matn), daemon=True).start()

    tk.Button(top, text="📢  YUBORISH", font=("Arial", 16, "bold"), bg="#e63946",
              fg="white", relief="flat", pady=12, command=yubor).pack(fill="x",
                                                                       pady=(4, 4))

    izoh = ("Hodimlar avtomatik topiladi. Javoblar shu ro'yxatda ko'rinadi."
            if javob_ok else "⚠ Javob porti band, javob ko'rinmasligi mumkin.")
    tk.Label(top, text=izoh, font=("Arial", 9), fg="#9fb8cc", bg="#1e3d59",
             wraplength=520).pack(anchor="w")

    def tekshir():
        # yuborish natijalari
        try:
            while True:
                ip, ok = natija_q.get_nowait()
                if ip in qatorlar:
                    if ok:
                        qatorlar[ip]["holat_lbl"].config(text="✓ yuborildi", fg="#9be89b")
                    else:
                        qatorlar[ip]["holat_lbl"].config(text="✗ ulanmadi", fg="#ff8a8a")
        except queue.Empty:
            pass
        # javoblar
        try:
            while True:
                matn, kim, ip = jq.get_nowait()
                if ip in qatorlar:
                    qatorlar[ip]["holat_lbl"].config(text="✅ " + matn, fg="#7CFC8A")
                else:
                    # ro'yxatda yo'q edi, qo'shib qo'yamiz
                    bitta_qator(kim, ip)
                    qatorlar[ip]["holat_lbl"].config(text="✅ " + matn, fg="#7CFC8A")
                try:
                    r.bell()
                except:
                    pass
        except queue.Empty:
            pass
        # avtomatik topilganlarni ro'yxatga qo'shish + onlayn belgisi
        with topilgan_lock:
            hozir = time.time()
            for ip in list(topilgan.keys()):
                t = topilgan[ip]
                if ip not in qatorlar:
                    bitta_qator(t["ism"], ip)
                    if hammasi_var.get() == 0:
                        qatorlar[ip]["var"].set(0)
                online = (hozir - t["vaqt"]) < 8
                q = qatorlar[ip]
                if online != q["online"]:
                    q["online"] = online
                    belgi = "🟢 " if online else "⚪ "
                    q["nom_lbl"].config(text=belgi + q["ism"] + "  (" + ip + ")")
        r.after(500, tekshir)

    r.after(500, tekshir)
    try:
        r.mainloop()
    finally:
        stop.set()
        try:
            jsock.close()
        except:
            pass


# eski nom
run_direktor = direktor_rejim


# ========================= ROL TANLASH =========================
def tanlov():
    import tkinter as tk
    r = tk.Tk()
    r.title("CHAQIRUV")
    r.configure(bg="#12263a")
    r.resizable(False, False)
    w, h = 400, 340
    sw = r.winfo_screenwidth(); sh = r.winfo_screenheight()
    r.geometry("%dx%d+%d+%d" % (w, h, (sw-w)//2, (sh-h)//3))
    fr = tk.Frame(r, bg="#12263a")
    fr.pack(expand=True, fill="both", padx=28, pady=26)
    tk.Label(fr, text="CHAQIRUV tizimi", font=("Arial", 22, "bold"), fg="white",
             bg="#12263a").pack(pady=(0, 6))
    tk.Label(fr, text="Bu kompyuterda kim ishlaydi?", font=("Arial", 12),
             fg="#9fb8cc", bg="#12263a").pack(pady=(0, 6))
    tk.Label(fr, text="DIQQAT: tanlov bir marta! Keyin o'zgarmaydi.\n"
                      "Direktor uchun parol so'raladi.",
             font=("Arial", 9), fg="#e8a33d", bg="#12263a",
             justify="center").pack(pady=(0, 16))

    natija = {"r": None}

    def tanla(x):
        natija["r"] = x
        r.destroy()

    tk.Button(fr, text="👔  Men DIREKTORMAN\n(xabar yuboraman)",
              font=("Arial", 14, "bold"), bg="#e63946", fg="white", relief="flat",
              pady=12, command=lambda: tanla("direktor")).pack(fill="x", pady=(0, 14))
    tk.Button(fr, text="🧑‍💼  Men HODIMMAN\n(xabar kutaman)",
              font=("Arial", 14, "bold"), bg="#2a9d8f", fg="white", relief="flat",
              pady=12, command=lambda: tanla("hodim")).pack(fill="x")

    r.mainloop()
    return natija["r"]


def direktor_kirish():
    # direktor rejimiga faqat parol bilan kiriladi
    import tkinter as tk
    from tkinter import simpledialog, messagebox
    root = tk.Tk()
    root.withdraw()
    p = simpledialog.askstring("Direktor paroli", "Parolni kiriting:",
                               show="*", parent=root)
    if p is None:
        root.destroy()
        return False
    if p == DIREKTOR_PAROL:
        root.destroy()
        return True
    messagebox.showerror("Xato", "Parol noto'g'ri! Direktor rejimi ochilmaydi.",
                         parent=root)
    root.destroy()
    return False


def main():
    a = sys.argv[1:]
    rol = a[0].lower() if len(a) > 0 else None

    # terminaldan to'g'ridan-to'g'ri (masalan avtostart 'hodim')
    if rol in ("hodim", "anvar", "h"):
        rolni_saqla("hodim")
        hodim_rejim()
        return
    if rol in ("direktor", "d"):
        if not direktor_kirish():
            return
        p = a[1] if len(a) > 1 else ""
        direktor_rejim(p)
        return

    # argument yo'q -> avval saqlangan rolni qaraymiz
    saqlangan = rolni_oqi()
    if saqlangan == "hodim":
        # bu komp hodim - boshqa hech narsa so'ramaymiz, fonda ishlaymiz
        hodim_rejim()
        return
    if saqlangan == "direktor":
        if not direktor_kirish():
            return
        direktor_rejim()
        return

    # birinchi marta ochilyapti - rol tanlanadi
    x = tanlov()
    if x == "hodim":
        rolni_saqla("hodim")   # endi bu komp doim hodim
        hodim_rejim()
    elif x == "direktor":
        if not direktor_kirish():
            return
        rolni_saqla("direktor")
        direktor_rejim()
    else:
        print("hech nima tanlanmadi")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nto'xtatildi")
