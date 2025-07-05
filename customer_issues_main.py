#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Customer Issues Management System - Main Application
نظام إدارة مشاكل العملاء - التطبيق الرئيسي

Version: 5.0.0
Author: AI Assistant
Date: December 2024
"""

# Version information
VERSION = "5.0.1"

import sys
from error_handler import handle_error
import os
import logging
import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import shutil
import platform
import time


# إعداد المسارات بحيث يعمل البرنامج بشكل صحيح كملف exe أو كود بايثون
if getattr(sys, 'frozen', False):
    # إذا كان البرنامج يعمل كملف exe
    CURRENT_DIR = os.path.dirname(sys.executable)
else:
    # إذا كان يعمل كملف بايثون عادي
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

# إعداد نظام السجلات
def setup_logging():
    """إعداد نظام السجلات"""
    log_dir = os.path.join(CURRENT_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f'customer_issues_{datetime.now().strftime("%Y%m%d")}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # حذف ملفات log القديمة (الاحتفاظ بآخر 5 فقط)
    log_files = [f for f in os.listdir(log_dir) if f.startswith('customer_issues_') and f.endswith('.log')]
    if len(log_files) > 5:
        log_files.sort()
        for old_log in log_files[:-5]:
            try:
                os.remove(os.path.join(log_dir, old_log))
            except Exception:
                pass

def check_requirements():
    """فحص المتطلبات الأساسية"""
    logging.info("فحص متطلبات النظام...")
    
    # فحص إصدار Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        error_msg = f"يتطلب النظام Python 3.7 أو أحدث. الإصدار الحالي: {python_version.major}.{python_version.minor}"
        logging.error(error_msg)
        messagebox.showerror("خطأ في المتطلبات", error_msg)
        return False
    
    # فحص المكتبات المطلوبة
    required_modules = ['tkinter', 'sqlite3', 'datetime', 'shutil', 'platform']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        error_msg = f"المكتبات التالية مفقودة: {', '.join(missing_modules)}"
        logging.error(error_msg)
        messagebox.showerror("خطأ في المتطلبات", error_msg)
        return False
    
    logging.info("✅ تم فحص جميع المتطلبات بنجاح")
    return True

def create_backup():
    """إنشاء نسخة احتياطية"""
    try:
        backup_dir = os.path.join(CURRENT_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        db_path = os.path.join(CURRENT_DIR, 'customer_issues_enhanced.db')
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f'customer_issues_backup_{timestamp}.db')
            shutil.copy2(db_path, backup_path)
            logging.info(f"تم إنشاء نسخة احتياطية: {backup_path}")
            # تنظيف النسخ القديمة (الاحتفاظ بـ 5 نسخ فقط)
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith('customer_issues_backup_')]
            if len(backup_files) > 5:
                backup_files.sort()
                for old_backup in backup_files[:-5]:
                    old_path = os.path.join(backup_dir, old_backup)
                    os.remove(old_path)
                    logging.info(f"تم حذف النسخة الاحتياطية القديمة: {old_backup}")
            # إشعار المستخدم بنجاح النسخ الاحتياطي (يظهر فقط عند النسخ اليدوي وليس عند بدء التشغيل)
            if not getattr(create_backup, 'silent', False):
                messagebox.showinfo("نسخ احتياطي", "تم إنشاء نسخة احتياطية بنجاح.")
        return True
    except Exception as e:
        handle_error("خطأ في إنشاء النسخة الاحتياطية", e)
        return False

def initialize_system():
    """تهيئة النظام"""
    logging.info("بدء تهيئة النظام...")
    
    # إنشاء المجلدات الأساسية
    dirs_to_create = ['files', 'backups', 'reports', 'logs']
    for dir_name in dirs_to_create:
        dir_path = os.path.join(CURRENT_DIR, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        logging.info(f"تم إنشاء/فحص المجلد: {dir_path}")
    
    # إنشاء نسخة احتياطية
    # عند بدء التشغيل، لا تظهر رسالة النسخ الاحتياطي
    create_backup.silent = True
    create_backup()
    create_backup.silent = False
    
    # تهيئة قاعدة البيانات
    try:
        from customer_issues_database import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.init_database()
        # إضافة مستخدم admin الثابت إذا لم يكن موجودًا
        try:
            with sqlite3.connect(os.path.join(CURRENT_DIR, 'customer_issues_enhanced.db')) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM employees WHERE performance_number = 1")
                exists = cursor.fetchone()[0]
                if not exists:
                    cursor.execute("INSERT INTO employees (name, position, performance_number, created_date, is_active) VALUES (?, ?, ?, ?, 1)",
                                   ("admin", "مدير النظام", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
        except Exception as admin_err:
            handle_error("خطأ في إضافة مستخدم admin", admin_err, show_messagebox=True)
        # تأكد من وجود عمود performance_number في كل تشغيل
        try:
            with sqlite3.connect(os.path.join(CURRENT_DIR, 'customer_issues_enhanced.db')) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(employees)")
                columns = [row[1] for row in cursor.fetchall()]
                perf_col = None
                for row in cursor.execute("PRAGMA table_info(employees)"):
                    if row[1] == 'performance_number':
                        perf_col = row
                # إذا العمود غير موجود أو ليس INTEGER/UNIQUE، أعد بناء الجدول
                need_migration = False
                if not perf_col:
                    need_migration = True
                elif perf_col[2].upper() != 'INTEGER':
                    need_migration = True
                # ترحيل الجدول إذا لزم الأمر
                if need_migration:
                    logging.info("يتم ترحيل جدول الموظفين لجعل رقم الأداء INT وفريد...")
                    # إنشاء جدول مؤقت
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS employees_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            position TEXT,
                            performance_number INTEGER UNIQUE NOT NULL,
                            created_date TEXT,
                            is_active INTEGER DEFAULT 1
                        )
                    ''')
                    # جلب كل الموظفين القدامى
                    cursor.execute("SELECT id, name, position, created_date, is_active FROM employees")
                    old_emps = cursor.fetchall()
                    # توليد أرقام أداء صحيحة متفردة
                    used_numbers = set()
                    next_perf = 1001
                    for emp in old_emps:
                        emp_id, name, position, created_date, is_active = emp
                        # حاول استخراج رقم صحيح من performance_number القديم إن وجد
                        perf_num = None
                        try:
                            cursor.execute("SELECT performance_number FROM employees WHERE id=?", (emp_id,))
                            val = cursor.fetchone()
                            if val and val[0]:
                                try:
                                    perf_num = int(val[0])
                                except:
                                    perf_num = None
                        except:
                            perf_num = None
                        # إذا لم يوجد أو غير صالح، أعطه رقم جديد متفرد
                        while perf_num is None or perf_num in used_numbers:
                            perf_num = next_perf
                            next_perf += 1
                        used_numbers.add(perf_num)
                        cursor.execute("INSERT INTO employees_new (name, position, performance_number, created_date, is_active) VALUES (?, ?, ?, ?, ?)",
                                       (name, position, perf_num, created_date, is_active))
                    conn.commit()
                    # حذف الجدول القديم وإعادة تسمية الجديد
                    cursor.execute("DROP TABLE employees")
                    cursor.execute("ALTER TABLE employees_new RENAME TO employees")
                    conn.commit()
        except Exception as alter_err:
            handle_error("خطأ في معالجة عمود رقم الأداء", alter_err, show_messagebox=True)
        logging.info("✅ تم تهيئة قاعدة البيانات بنجاح")
    except Exception as e:
        handle_error("خطأ في تهيئة قاعدة البيانات", e, show_messagebox=True)
        return False
    
    logging.info("✅ تم تهيئة النظام بنجاح")
    return True

def show_splash_screen():
    """عرض شاشة البداية"""
    splash = tk.Toplevel()
    splash.title("نظام إدارة مشاكل العملاء v5.0.1")
    splash.geometry("600x400")
    splash.resizable(False, False)
    
    # توسيط النافذة
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - (600 // 2)
    y = (splash.winfo_screenheight() // 2) - (400 // 2)
    splash.geometry(f"600x400+{x}+{y}")
    
    # إزالة أزرار النافذة
    splash.overrideredirect(True)
    
    # الخلفية
    main_frame = tk.Frame(splash, bg='#2c3e50', padx=20, pady=20)
    main_frame.pack(fill='both', expand=True)
    
    # العنوان الرئيسي
    title_label = tk.Label(
        main_frame,
        text="نظام إدارة مشاكل العملاء",
        font=('Arial', 24, 'bold'),
        fg='white',
        bg='#2c3e50'
    )
    title_label.pack(pady=(40, 10))
    
    # العنوان الفرعي
    subtitle_label = tk.Label(
        main_frame,
        text="Customer Issues Management System",
        font=('Arial', 14),
        fg='#bdc3c7',
        bg='#2c3e50'
    )
    subtitle_label.pack(pady=(0, 30))
    
    # الإصدار
    version_label = tk.Label(
        main_frame,
        text="الإصدار 5.0.1 - النسخة المحسنة",
        font=('Arial', 12),
        fg='#3498db',
        bg='#2c3e50'
    )
    version_label.pack(pady=(0, 5))

    # اسم المطور تحت الإصدار
    dev_name_label = tk.Label(
        main_frame,
        text="مصطفى اسماعيل",
        font=('Arial', 12, 'bold'),
        fg='#e67e22',
        bg='#2c3e50'
    )
    dev_name_label.pack(pady=(0, 15))
    
    # معلومات النظام
    info_text = """
    نظام شامل لإدارة مشاكل وشكاوى عملاء شركات الغاز
    
    ✓ إدارة بيانات العملاء والمشاكل
    ✓ تتبع المراسلات مع الترقيم المزدوج
    ✓ رفع وإدارة المرفقات
    ✓ بحث متقدم وتقارير شاملة
    ✓ نسخ احتياطية تلقائية
    """
    
    info_label = tk.Label(
        main_frame,
        text=info_text,
        font=('Arial', 10),
        fg='#ecf0f1',
        bg='#2c3e50',
        justify='center'
    )
    info_label.pack(pady=20)
    
    # شريط التحميل
    progress_frame = tk.Frame(main_frame, bg='#2c3e50')
    progress_frame.pack(pady=(20, 10))
    
    progress_label = tk.Label(
        progress_frame,
        text="جاري تحميل النظام...",
        font=('Arial', 10),
        fg='#95a5a6',
        bg='#2c3e50'
    )
    progress_label.pack()
    
    # معلومات المطور
    dev_label = tk.Label(
        main_frame,
        text="تطوير: مساعد الذكي الاصطناعي - 2024",
        font=('Arial', 8),
        fg='#7f8c8d',
        bg='#2c3e50'
    )
    dev_label.pack(side='bottom', pady=(20, 0))
    
    # تحديث النافذة
    splash.update()
    
    return splash

def main():
    """الوظيفة الرئيسية"""
    # إعداد نظام السجلات
    setup_logging()
    
    logging.info("=" * 50)
    logging.info("بدء تشغيل نظام إدارة مشاكل العملاء v5.0.1")
    logging.info(f"نظام التشغيل: {platform.system()} {platform.release()}")
    logging.info(f"إصدار Python: {sys.version}")
    logging.info("=" * 50)
    
    # إنشاء نافذة root مخفية
    root = tk.Tk()
    root.withdraw()
    
    try:
        # عرض شاشة البداية
        splash = show_splash_screen()
        splash.update()

        # فحص المتطلبات
        if not check_requirements():
            splash.destroy()
            return 1

        # تهيئة النظام
        splash.update()
        if not initialize_system():
            splash.destroy()
            return 1

        # استيراد وتشغيل الواجهة الرئيسية
        splash.update()
        time.sleep(5)  # عرض splash screen لمدة 3 ثواني
        try:
            from customer_issues_window import EnhancedMainWindow

            # إغلاق شاشة البداية
            splash.destroy()

            # إظهار النافذة الرئيسية
            root.destroy()  # Destroy the hidden root window

            # تطبيق النافذة الرئيسية
            app = EnhancedMainWindow()

            logging.info("✅ تم تشغيل النظام بنجاح")

            # بدء حلقة الأحداث الرئيسية
            app.run()

        except ImportError as e:
            handle_error("خطأ في استيراد الواجهة الرئيسية", e, show_messagebox=True)
            return 1

    except Exception as e:
        handle_error("خطأ عام في النظام", e, show_messagebox=True)
        return 1

    finally:
        # إنشاء نسخة احتياطية عند الإغلاق بدون أي رسالة أو تفاعل مع الواجهة
        create_backup.silent = True
        create_backup()
        create_backup.silent = False
        logging.info("تم إغلاق النظام")
        logging.info("=" * 50)

if __name__ == "__main__":
    # تهيئة قاعدة البيانات وإنشاء الجداول والمستخدم admin قبل أي واجهة
    from customer_issues_database import DatabaseManager
    db_path = os.path.join(CURRENT_DIR, 'customer_issues_enhanced.db')
    db_manager = DatabaseManager(db_name=db_path)
    db_manager.init_database()
    # إضافة مستخدم admin إذا لم يكن موجودًا
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees WHERE performance_number = 1")
        exists = cursor.fetchone()[0]
        if not exists:
            cursor.execute("INSERT INTO employees (name, position, performance_number, created_date, is_active) VALUES (?, ?, ?, ?, 1)",
                           ("admin", "مدير النظام", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB INIT ERROR] {e}")

    # شاشة الدخول بعد شاشة السبلاش
    def start_main_app(user_id, user_name, performance_number):
        sys.exit(main())

    from login_window import LoginWindow


    # عرض شاشة السبلاش أولاً مع حماية المؤقتات من أخطاء after
    import tkinter as tk
    splash_root = tk.Tk()
    splash_root.withdraw()
    splash = show_splash_screen()
    splash.update()


    # --- إدارة مؤقتات after splash بشكل آمن ---
    splash_timer = None
    splash_root_timer = None

    def safe_destroy(widget, timer_id=None):
        try:
            if timer_id and widget and widget.winfo_exists():
                widget.after_cancel(timer_id)
        except Exception:
            pass
        try:
            if widget and widget.winfo_exists():
                widget.destroy()
        except Exception:
            pass

    def destroy_splash():
        safe_destroy(splash, splash_timer)

    def destroy_splash_root():
        safe_destroy(splash_root, splash_root_timer)

    splash_timer = splash.after(2000, destroy_splash)
    splash_root_timer = splash_root.after(2200, destroy_splash_root)
    try:
        splash_root.mainloop()
    except Exception:
        pass

    # بعد السبلاش، أظهر شاشة الدخول
    LoginWindow(db_path, on_success=start_main_app)