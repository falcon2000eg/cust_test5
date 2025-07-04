import tkinter as tk
from tkinter import messagebox
import sqlite3
import os

class LoginWindow:
    def __init__(self, db_path, on_success):
        self.db_path = db_path
        self.on_success = on_success
        self.root = tk.Tk()
        self.root.title("تسجيل الدخول - نظام إدارة مشاكل العملاء")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f6fa")
        self.build_ui()
        self.center_window(400, 250)
        self.root.mainloop()

    def center_window(self, w, h):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def build_ui(self):
        frame = tk.Frame(self.root, bg="#f5f6fa", padx=30, pady=30)
        frame.pack(expand=True)
        tk.Label(frame, text="رقم الأداء:", font=("Arial", 14), bg="#f5f6fa").pack(anchor='e', pady=(0, 10))
        self.perf_var = tk.StringVar()
        perf_entry = tk.Entry(frame, textvariable=self.perf_var, font=("Arial", 14), width=20, justify='center')
        perf_entry.pack(pady=(0, 20))
        perf_entry.focus_set()
        tk.Button(frame, text="دخول", font=("Arial", 12, "bold"), bg="#27ae60", fg="white", width=12, command=self.try_login).pack(pady=10)
        self.root.bind('<Return>', lambda e: self.try_login())

    def try_login(self):
        perf = self.perf_var.get().strip()
        try:
            perf_int = int(perf)
        except Exception:
            messagebox.showerror("خطأ", "رقم الأداء يجب أن يكون عددًا صحيحًا.")
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if perf_int == 1:
                cursor.execute("SELECT id, name FROM employees WHERE performance_number = 1 LIMIT 1")
            else:
                cursor.execute("SELECT id, name FROM employees WHERE performance_number = ? AND is_active = 1", (perf_int,))
            row = cursor.fetchone()
            conn.close()
            if row:
                self.root.destroy()
                self.on_success(user_id=row[0], user_name=row[1], performance_number=perf_int)
            else:
                messagebox.showerror("خطأ في الدخول", "رقم الأداء غير صحيح أو الحساب غير نشط.")
        except Exception as e:
            messagebox.showerror("خطأ في النظام", f"حدث خطأ أثناء التحقق من الدخول:\n{e}")
