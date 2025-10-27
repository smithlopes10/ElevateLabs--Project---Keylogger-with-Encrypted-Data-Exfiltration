# client_app.py
import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime
import base64, json, os, threading, requests, time
from encrpt import encrypt_bytes
from pynput import keyboard
from pynput.keyboard import Controller as KController

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
SERVER_URL = "http://127.0.0.1:5000/upload"

class ConsentLoggerApp:
    def __init__(self, root):
        self.root = root
        root.title("ConsentLogger — Ethical PoC (pynput safe)")
        self.logging = False
        self.lock = threading.Lock()

        notice = ("Ethical notice: This app records ONLY text typed into this window's box, "
                  "and only when logging is ON (Start Logging). Use only on machines you own.")
        tk.Label(root, text=notice, wraplength=560, justify="left").pack(padx=10, pady=(10,5))

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(padx=10, pady=5, anchor="w")
        self.start_btn = tk.Button(btn_frame, text="Start Logging", command=self.start_logging)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = tk.Button(btn_frame, text="Stop Logging", command=self.stop_logging, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        self.send_btn = tk.Button(btn_frame, text="Send Unsents", command=self.send_all_unsent)
        self.send_btn.pack(side="left", padx=5)
        self.delete_btn = tk.Button(btn_frame, text="Delete All Logs", command=self.delete_all_logs)
        self.delete_btn.pack(side="left", padx=5)
        self.simulate_btn = tk.Button(btn_frame, text="Simulate Typing (Test)", command=self.simulate_typing)
        self.simulate_btn.pack(side="left", padx=5)

        # Textbox
        tk.Label(root, text="Type here (ONLY this box is recorded when logging is ON):").pack(anchor="w", padx=10)
        self.text = scrolledtext.ScrolledText(root, width=80, height=18)
        self.text.pack(padx=10, pady=5)
        self.text.bind("<Key>", self.on_key)  # captures keys only inside this widget

        self.status = tk.StringVar(value="Idle")
        tk.Label(root, textvariable=self.status).pack(anchor="w", padx=10, pady=(0,10))

        # Start pynput GlobalHotKeys in background thread (safe: toggles only)
        threading.Thread(target=self.start_hotkeys, daemon=True).start()

    def start_logging(self):
        with self.lock:
            self.logging = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.set("Logging: ON")

    def stop_logging(self):
        with self.lock:
            self.logging = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.set("Logging: OFF")

    def on_key(self, event):
        with self.lock:
            if not self.logging:
                return
        key = event.keysym
        char = event.char
        timestamp = datetime.utcnow().isoformat()
        entry = {"timestamp": timestamp, "keysym": key, "char": char, "context": self.get_snippet()}
        self.save_encrypted_entry(entry)
        self.status.set(f"Logged at {timestamp}")

    def get_snippet(self, chars=60):
        content = self.text.get("1.0", "end-1c")
        return content[-chars:]

    def save_encrypted_entry(self, entry_dict):
        raw = json.dumps(entry_dict).encode("utf-8")
        token = encrypt_bytes(raw)
        b64 = base64.b64encode(token).decode()
        ts = entry_dict["timestamp"].replace(":", "-")
        filename = os.path.join(LOG_DIR, f"log_{ts}.b64")
        with open(filename, "w") as f:
            f.write(b64)
        # try to send in background
        threading.Thread(target=self.try_send_file, args=(filename,), daemon=True).start()

    def try_send_file(self, filepath):
        try:
            with open(filepath, "r") as f:
                b64 = f.read()
            payload = {"timestamp": os.path.basename(filepath), "data": b64}
            resp = requests.post(SERVER_URL, json=payload, timeout=5)
            if resp.ok:
                sent_path = filepath + ".sent"
                os.rename(filepath, sent_path)
                print(f"Sent {filepath} -> {sent_path}")
        except Exception as e:
            print("Send failed:", e)

    def send_all_unsent(self):
        for fname in os.listdir(LOG_DIR):
            if fname.endswith(".b64"):
                self.try_send_file(os.path.join(LOG_DIR, fname))
        messagebox.showinfo("Send", "Triggered send for unsent logs (check server).")

    def delete_all_logs(self):
        for fname in os.listdir(LOG_DIR):
            os.remove(os.path.join(LOG_DIR, fname))
        messagebox.showinfo("Delete", "All logs deleted.")

    def simulate_typing(self):
        # Simulate typing into the app's text box for testing using pynput Controller.
        # This produces input that will be recorded when logging is ON.
        def worker():
            kb = KController()
            # focus the text widget — user must click it first; we give 2 seconds
            self.status.set("Simulating typing in 2s: focus the app's text box now")
            time.sleep(2)
            # type a test sentence
            kb.type("Simulated test input: The quick brown fox jumps over the lazy dog.\n")
            self.status.set("Simulation complete")
        threading.Thread(target=worker, daemon=True).start()

    def start_hotkeys(self):
        # Safe usage: only toggles logging. Hotkeys: Ctrl+Shift+S (start), Ctrl+Shift+X (stop)
        def on_start():
            print("[hotkey] start requested")
            self.root.after(0, self.start_logging)
        def on_stop():
            print("[hotkey] stop requested")
            self.root.after(0, self.stop_logging)
        hotkeys = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+s': on_start,
            '<ctrl>+<shift>+x': on_stop
        })
        with hotkeys:
            hotkeys.join()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConsentLoggerApp(root)
    root.mainloop()
