import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Menu
from datetime import datetime
import os
import json
from customer_issues_database import enhanced_db
from customer_issues_file_manager import FileManager
import sqlite3
import threading
import time

class EnhancedMainWindow:
    def __init__(self):
        self.root = tk.Tk()
        # --- لوحة الألوان الموحدة المحسنة ---
        self.colors = {
            'bg_main': '#f8f9fa',
            'bg_card': '#f0f6fa',
            'bg_light': '#ffffff',
            'header': '#2c3e50',
            'header_text': 'white',
            'button_save': '#27ae60',
            'button_delete': '#e74c3c',
            'button_action': '#3498db',
            'button_secondary': '#95a5a6',
            'button_warning': '#f39c12',
            'status_new': '#3498db',
            'status_inprogress': '#f39c12',
            'status_solved': '#27ae60',
            'status_closed': '#95a5a6',
            'text_main': '#222',
            'text_subtle': '#7f8c8d',
            'border_light': '#e0e0e0',
            'border_dark': '#bdc3c7',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'info': '#3498db',
        }
        self.root.title("نظام إدارة مشاكل العملاء - النسخة المحسنة")
        # جعل حجم النافذة الرئيسية مرن حسب دقة الشاشة
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        win_width = int(screen_width * 0.85)
        win_height = int(screen_height * 0.85)
        self.root.geometry(f"{win_width}x{win_height}")
        self.root.minsize(1000, 600)
        self.root.configure(bg=self.colors['bg_main'])
        
        # إعداد الخطوط أولاً
        self.setup_fonts()
        
        # دعم اتجاه RTL للواجهة بالكامل
        try:
            self.root.tk.call('tk', 'scaling', 1.2)
            self.root.option_add('*tearOff', False)
            self.root.option_add('*font', self.fonts['normal'])
            self.root.option_add('*justify', 'right')
            self.root.option_add('*Entry.justify', 'right')
            self.root.option_add('*Label.anchor', 'e')
            self.root.option_add('*Button.anchor', 'e')
            
            # إعداد نمط التبويبات للغة العربية
            style = ttk.Style()
            style.configure('TNotebook.Tab', anchor='e', justify='right', padding=[10, 5])
            style.configure('TNotebook', tabmargins=[2, 5, 2, 0])
        except Exception:
            pass

        # إنشاء قائمة منسدلة
        self.create_menu_bar()
        
        # إزالة Header ثابت لتوفير مساحة

        # إنشاء شريط الأدوات
        self.create_toolbar()

        # المتغيرات
        self.file_manager = FileManager()
        self.current_case_id = None
        self.cases_data = []
        self.filtered_cases = []
        self.basic_data_widgets = {}
        self.scrollable_frame = None
        self.original_received_date = None
        self.current_case_status = None
        self.created_years = []
        self.received_years = []
        self.notification_label = None
        self.loading_indicator = None
        self.is_loading = False
        self.pending_dashboard_case = None

        # ربط وظائف النظام
        try:
            from customer_issues_functions import EnhancedFunctions
            self.functions = EnhancedFunctions(self)
        except Exception as e:
            self.functions = None

        # إنشاء الواجهة
        self.create_main_layout()

        # إنشاء شريط الحالة
        self.create_status_bar()

        # تحميل البيانات الأولية بعد إنشاء كل عناصر الواجهة (لضمان وجود scrollable_frame)
        self.after_main_layout()

        # ربط أحداث الإغلاق
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ربط اختصارات لوحة المفاتيح محسنة
        self.bind_keyboard_shortcuts()

        # --- إضافة الإعدادات ---
        self.config_file = 'config.json'
        self.settings = self.load_settings()

    def create_menu_bar(self):
        """إنشاء قائمة منسدلة محسنة"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # قائمة الملف
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📄 الملف", menu=file_menu)
        file_menu.add_command(label="🆕 حالة جديدة", command=self.add_new_case, accelerator="Ctrl+N")
        file_menu.add_command(label="💾 حفظ", command=self.save_changes, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="🖨️ طباعة", command=self.print_case, accelerator="Ctrl+P")
        file_menu.add_command(label="📊 تصدير البيانات", command=self.export_cases_data)
        file_menu.add_separator()
        file_menu.add_command(label="⚙️ الإعدادات", command=self.show_settings_window)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 خروج", command=self.on_closing, accelerator="Ctrl+Q")
        
        # قائمة التحرير
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="✏️ التحرير", menu=edit_menu)
        edit_menu.add_command(label="📎 إضافة مرفق", command=self.add_attachment, accelerator="Ctrl+A")
        edit_menu.add_command(label="✉️ إضافة مراسلة", command=self.add_correspondence, accelerator="Ctrl+M")
        edit_menu.add_separator()
        edit_menu.add_command(label="🗑️ حذف الحالة", command=self.delete_case, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="👥 إدارة الموظفين", command=self.manage_employees)
        
        # قائمة العرض
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="👁️ العرض", menu=view_menu)
        view_menu.add_command(label="📋 جميع الحالات", command=self.show_all_cases_window)
        view_menu.add_separator()
        view_menu.add_command(label="🔄 تحديث البيانات", command=self.refresh_data, accelerator="F5")
        view_menu.add_command(label="🔍 تركيز على البحث", command=self.focus_search, accelerator="Ctrl+F")
        
        # قائمة المساعدة
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ المساعدة", menu=help_menu)
        help_menu.add_command(label="📖 دليل الاستخدام", command=self.show_help)
        help_menu.add_command(label="ℹ️ حول البرنامج", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="⌨️ اختصارات لوحة المفاتيح", command=self.show_shortcuts)

    def create_toolbar(self):
        """إنشاء شريط الأدوات محسن مع عناوين كبيرة وواضحة"""
        toolbar_frame = tk.Frame(self.root, bg=self.colors['bg_light'], height=90, relief='solid', bd=1)
        toolbar_frame.pack(fill='x', side='top')
        toolbar_frame.pack_propagate(False)
        
        # عنوان النظام في الجانب الأيمن
        title_frame = tk.Frame(toolbar_frame, bg=self.colors['bg_light'])
        title_frame.pack(side='right', fill='y', padx=15)
        
        title_label = tk.Label(title_frame, text="نظام إدارة مشاكل العملاء", 
                              font=self.fonts['subheader'], fg=self.colors['text_main'], 
                              bg=self.colors['bg_light'])
        title_label.pack(side='right', pady=10)
        
        version_label = tk.Label(title_frame, text="v5.0.1", 
                                font=self.fonts['small'], fg=self.colors['text_subtle'], 
                                bg=self.colors['bg_light'])
        version_label.pack(side='right', pady=(0, 10))
        
        # إطار للأزرار مع توزيع أفضل
        buttons_frame = tk.Frame(toolbar_frame, bg=self.colors['bg_light'])
        buttons_frame.pack(side='left', expand=True, fill='both', padx=10, pady=5)
        
        # أزرار شريط الأدوات مع عناوين وتصميم محسن
        buttons_data = [
            ("🆕", "حالة جديدة", self.add_new_case, self.colors['button_save'], "إضافة حالة جديدة للعميل"),
            ("💾", "حفظ", self.save_changes, self.colors['button_action'], "حفظ التغييرات"),
            ("🖨️", "طباعة", self.print_case, self.colors['button_secondary'], "طباعة تقرير الحالة"),
            ("🔄", "تحديث", self.refresh_data, self.colors['button_secondary'], "تحديث البيانات"),
            ("🗑️", "حذف", self.delete_case, self.colors['button_delete'], "حذف الحالة المحددة"),
            ("👥", "الموظفين", self.manage_employees, self.colors['button_warning'], "إدارة الموظفين"),
            ("⚙️", "إعدادات", self.show_settings_window, self.colors['button_secondary'], "إعدادات النظام"),
            ("❌", "خروج", self.on_closing, self.colors['button_delete'], "إغلاق النظام"),
        ]
        
        for icon, title, command, color, description in buttons_data:
            # إطار لكل زر مع عنوان
            btn_frame = tk.Frame(buttons_frame, bg=self.colors['bg_light'])
            btn_frame.pack(side='right', padx=5, pady=2)
            
            # الزر مع الأيقونة - الحجم الأصلي
            btn = tk.Button(btn_frame, text=icon, command=command,
                           font=('Arial', 16), bg=color, fg='white',
                           relief='flat', padx=15, pady=10, width=4,
                           cursor='hand2')
            btn.pack()
            
            # عنوان الزر - كبير وواضح فقط
            title_label = tk.Label(btn_frame, text=title, 
                                  font=self.fonts['subheader'], fg=self.colors['text_main'], 
                                  bg=self.colors['bg_light'], anchor='center')
            title_label.pack(pady=(2, 0))
            
            # إضافة tooltip محسن للزر والعنوان
            self.create_tooltip(btn, f"{title}\n{description}")
            self.create_tooltip(title_label, f"{title}\n{description}")
            
            # تأثيرات بصرية محسنة عند التمرير
            def on_enter(event, button=btn, original_color=color):
                button.config(bg=self.lighten_color(original_color, 0.3))
                button.config(relief='raised')
                
            def on_leave(event, button=btn, original_color=color):
                button.config(bg=original_color)
                button.config(relief='flat')
            
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
            title_label.bind('<Enter>', on_enter)
            title_label.bind('<Leave>', on_leave)
            
            # تأثير عند النقر
            def on_click(event, button=btn, original_color=color):
                button.config(bg=self.lighten_color(original_color, 0.5))
                self.root.after(100, lambda: button.config(bg=original_color))
            
            btn.bind('<Button-1>', on_click)
            title_label.bind('<Button-1>', lambda e: command())

    def create_status_bar(self):
        """إنشاء شريط الحالة محسن مع ساعة حقيقية"""
        self.status_bar = tk.Frame(self.root, bg=self.colors['header'], height=30)
        self.status_bar.pack(fill='x', side='bottom')
        self.status_bar.pack_propagate(False)
        
        # إطار للمعلومات مع توزيع أفضل
        info_frame = tk.Frame(self.status_bar, bg=self.colors['header'])
        info_frame.pack(fill='both', expand=True, padx=10, pady=2)
        
        # معلومات الحالة (يمين)
        status_frame = tk.Frame(info_frame, bg=self.colors['header'])
        status_frame.pack(side='right', fill='y')
        
        self.status_label = tk.Label(status_frame, text="✅ جاهز", 
                                    font=self.fonts['small'], fg='white', 
                                    bg=self.colors['header'])
        self.status_label.pack(side='right', padx=5)
        
        # عدد الحالات (وسط)
        cases_frame = tk.Frame(info_frame, bg=self.colors['header'])
        cases_frame.pack(side='right', fill='y', padx=20)
        
        self.cases_count_label = tk.Label(cases_frame, text="📋 جميع الحالات: 0", 
                                         font=self.fonts['small'], fg='white', 
                                         bg=self.colors['header'])
        self.cases_count_label.pack(side='right', padx=5)
        
        # الوقت والتاريخ (يسار)
        time_frame = tk.Frame(info_frame, bg=self.colors['header'])
        time_frame.pack(side='left', fill='y')
        
        self.time_label = tk.Label(time_frame, text="🕐 جاري التحميل...", 
                                  font=self.fonts['small'], fg='white', 
                                  bg=self.colors['header'])
        self.time_label.pack(side='left', padx=5)
        
        # بدء تحديث الوقت بعد إنشاء الواجهة بالكامل
        self.is_closing = False
        self.root.after(100, self.update_time)

    def update_time(self):
        """تحديث الوقت والتاريخ في شريط الحالة"""
        if getattr(self, 'is_closing', False):
            return
        try:
            if hasattr(self, 'time_label') and self.time_label and self.time_label.winfo_exists():
                current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                self.time_label.config(text=f"🕐 {current_time}")
        except Exception:
            pass  # تجاهل الأخطاء في تحديث الوقت
        # جدولة التحديث التالي
        try:
            if hasattr(self, 'root') and self.root and self.root.winfo_exists() and not getattr(self, 'is_closing', False):
                self.root.after(1000, self.update_time)
        except Exception:
            pass  # تجاهل الأخطاء في جدولة التحديث

    def bind_keyboard_shortcuts(self):
        """ربط اختصارات لوحة المفاتيح محسنة"""
        # اختصارات الملف
        self.root.bind('<Control-n>', lambda e: self.add_new_case())
        self.root.bind('<Control-s>', lambda e: self.save_changes())
        self.root.bind('<Control-p>', lambda e: self.print_case())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        
        # اختصارات التحرير
        self.root.bind('<Control-a>', lambda e: self.add_attachment())
        self.root.bind('<Control-m>', lambda e: self.add_correspondence())
        self.root.bind('<Delete>', lambda e: self.delete_case())
        
        # اختصارات العرض
        self.root.bind('<F5>', lambda e: self.refresh_data())
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        self.root.bind('<Control-r>', lambda e: self.refresh_data())
        
        # اختصارات التنقل
        self.root.bind('<Escape>', lambda e: self.clear_selection())
        self.root.bind('<Up>', lambda e: self._on_case_list_up(e))
        self.root.bind('<Down>', lambda e: self._on_case_list_down(e))
        
        # اختصارات إضافية
        self.root.bind('<Control-e>', lambda e: self.manage_employees())
        self.root.bind('<Control-l>', lambda e: self.show_all_cases_window())
        
        # منع اختصارات المتصفح
        self.root.bind('<Control-t>', lambda e: 'break')
        self.root.bind('<Control-w>', lambda e: 'break')
        self.root.bind('<F11>', lambda e: 'break')

    def focus_search(self):
        """تركيز على حقل البحث"""
        if hasattr(self, 'search_entry'):
            self.search_entry.focus_set()
            self.search_entry.select_range(0, tk.END)

    def clear_selection(self):
        """مسح التحديد الحالي"""
        if hasattr(self, 'attachments_tree'):
            self.attachments_tree.selection_remove(self.attachments_tree.selection())
        if hasattr(self, 'correspondences_tree'):
            self.correspondences_tree.selection_remove(self.correspondences_tree.selection())

    def lighten_color(self, color, factor=0.2):
        """تفتيح اللون"""
        # تحويل اللون من hex إلى RGB
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        # تفتيح اللون
        lightened = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
        
        # تحويل العودة إلى hex
        return '#{:02x}{:02x}{:02x}'.format(*lightened)

    def show_loading_indicator(self, message="جاري التحميل..."):
        """عرض مؤشر التحميل محسن"""
        if self.loading_indicator:
            self.hide_loading_indicator()
        
        self.is_loading = True
        
        # إنشاء نافذة التحميل
        self.loading_indicator = tk.Toplevel(self.root)
        self.loading_indicator.title("جاري التحميل")
        self.loading_indicator.geometry("400x200")
        self.loading_indicator.resizable(False, False)
        self.loading_indicator.transient(self.root)
        self.loading_indicator.grab_set()
        
        # توسيط النافذة
        self.loading_indicator.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (200 // 2)
        self.loading_indicator.geometry(f"400x200+{x}+{y}")
        
        # إزالة أزرار النافذة
        self.loading_indicator.overrideredirect(True)
        
        # الإطار الرئيسي
        main_frame = tk.Frame(self.loading_indicator, bg=self.colors['bg_main'], padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # أيقونة التحميل
        loading_icon = tk.Label(main_frame, text="⏳", font=('Arial', 48), 
                               bg=self.colors['bg_main'], fg=self.colors['button_action'])
        loading_icon.pack(pady=(0, 20))
        
        # رسالة التحميل
        message_label = tk.Label(main_frame, text=message, 
                                font=self.fonts['subheader'], 
                                bg=self.colors['bg_main'], fg=self.colors['text_main'])
        message_label.pack(pady=(0, 20))
        
        # شريط التقدم
        progress_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', 
                                           length=300, style='TProgressbar')
        self.progress_bar.pack()
        self.progress_bar.start(10)
        
        # نص إضافي
        info_label = tk.Label(main_frame, text="يرجى الانتظار...", 
                             font=self.fonts['small'], 
                             bg=self.colors['bg_main'], fg=self.colors['text_subtle'])
        info_label.pack()
        
        # تحديث النافذة
        self.loading_indicator.update()
    
    def hide_loading_indicator(self):
        """إخفاء مؤشر التحميل"""
        self.is_loading = False
        if self.loading_indicator:
            try:
                self.loading_indicator.destroy()
                self.loading_indicator = None
            except:
                pass

    def show_notification(self, message, duration=3000, notification_type="info"):
        """عرض إشعار محسن مع أنواع مختلفة وتصميم أفضل"""
        # إخفاء الإشعار السابق إذا كان موجوداً
        if self.notification_label:
            self.hide_notification()
        
        # تحديد الألوان والأيقونات حسب نوع الإشعار
        notification_config = {
            "success": {
                "bg": self.colors['success'],
                "icon": "✅",
                "title": "نجح"
            },
            "warning": {
                "bg": self.colors['warning'],
                "icon": "⚠️",
                "title": "تحذير"
            },
            "error": {
                "bg": self.colors['error'],
                "icon": "❌",
                "title": "خطأ"
            },
            "info": {
                "bg": self.colors['info'],
                "icon": "ℹ️",
                "title": "معلومات"
            }
        }
        
        config = notification_config.get(notification_type, notification_config["info"])
        
        # إنشاء إطار الإشعار مع تصميم محسن
        notification_frame = tk.Frame(self.root, bg=config['bg'], relief='solid', bd=2)
        notification_frame.place(relx=0.5, rely=0.15, anchor='center')
        
        # إطار المحتوى
        content_frame = tk.Frame(notification_frame, bg=config['bg'])
        content_frame.pack(padx=20, pady=15)
        
        # العنوان مع الأيقونة
        title_frame = tk.Frame(content_frame, bg=config['bg'])
        title_frame.pack(fill='x', pady=(0, 5))
        
        title_label = tk.Label(title_frame, 
                              text=f"{config['icon']} {config['title']}",
                              font=self.fonts['subheader'], fg='white', bg=config['bg'],
                              anchor='e')
        title_label.pack(side='right')
        
        # نص الإشعار
        self.notification_label = tk.Label(content_frame, 
                                          text=message,
                                          font=self.fonts['normal'], fg='white', bg=config['bg'],
                                          wraplength=400, justify='right')
        self.notification_label.pack()
        
        # إضافة تأثير ظهور تدريجي
        self.root.after(100, lambda: self._fade_in_notification(notification_frame))
        
        # إخفاء الإشعار بعد المدة المحددة
        self.root.after(duration, lambda: self._fade_out_notification(notification_frame))
    
    def _fade_in_notification(self, frame):
        """تأثير ظهور تدريجي للإشعار"""
        try:
            frame.lift()
            frame.focus_force()
        except:
            pass
    
    def _fade_out_notification(self, frame):
        """تأثير اختفاء تدريجي للإشعار"""
        try:
            frame.destroy()
            self.notification_label = None
        except:
            pass

    def show_help(self):
        """عرض دليل الاستخدام محسن"""
        help_text = """
📖 دليل استخدام نظام إدارة مشاكل العملاء

🎯 الوظائف الأساسية:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• إضافة حالة جديدة: Ctrl+N
• حفظ التغييرات: Ctrl+S
• طباعة التقرير: Ctrl+P
• إضافة مرفق: Ctrl+A
• إضافة مراسلة: Ctrl+M
• تحديث البيانات: F5 أو Ctrl+R
• حذف الحالة: Delete
• تركيز على البحث: Ctrl+F

🔍 البحث والفلترة:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• استخدم حقل البحث للبحث الشامل في جميع البيانات
• اختر نوع البحث المحدد:
  - اسم العميل
  - رقم المشترك
  - العنوان
  - تصنيف المشكلة
  - حالة المشكلة
  - اسم الموظف
• استخدم فلتر السنة لعرض الحالات حسب السنة
• اختر نوع التاريخ (تاريخ الورود أو تاريخ الإدخال)
• استخدم خيارات الترتيب لتنظيم النتائج

📁 إدارة المرفقات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• يمكن ربط الملفات الموجودة أو نسخها لمجلد مخصص
• استخدم النقر المزدوج لفتح المرفقات
• النقر بالزر الأيمن لعرض قائمة الخيارات
• إضافة وصف وموظف مسؤول لكل مرفق

✉️ إدارة المراسلات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• يتم ترقيم المراسلات تلقائياً
• يمكن تعديل محتوى المراسلات بالنقر المزدوج
• احذف المراسلات من قائمة الخيارات
• تتبع تاريخ المراسلات

⚙️ الإعدادات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• حدد مسار حفظ المرفقات المنسوخة
• يمكن تصدير البيانات بصيغة CSV
• إنشاء نسخ احتياطية تلقائية
• إدارة الموظفين في النظام

💡 نصائح للاستخدام:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• استخدم الاختصارات لتسريع العمل
• احفظ التغييرات بانتظام
• راجع سجل التعديلات لتتبع التغييرات
• استخدم الفلاتر للعثور على الحالات بسرعة
• تأكد من إدخال البيانات المطلوبة قبل الحفظ
        """
        
        self.show_info_dialog("📖 دليل الاستخدام", help_text)

    def show_about(self):
        """عرض معلومات البرنامج"""
        about_text = """
نظام إدارة مشاكل العملاء
Customer Issues Management System

الإصدار: 5.1
النسخة: النسخة المحسنة

المطور: مصطفى اسماعيل
التاريخ: ديسمبر 2024

المميزات:
✓ إدارة شاملة لبيانات العملاء والمشاكل
✓ نظام مراسلات متقدم مع الترقيم المزدوج
✓ إدارة المرفقات مع خيارات الربط والنسخ
✓ بحث متقدم وفلترة ذكية
✓ تقارير شاملة وإمكانية الطباعة
✓ نسخ احتياطية تلقائية
✓ واجهة مستخدم محسنة ومتجاوبة
✓ دعم كامل للغة العربية

التقنيات المستخدمة:
• Python 3.7+
• Tkinter للواجهة الرسومية
• SQLite لقاعدة البيانات
• نظام ملفات متقدم للمرفقات
        """
        
        self.show_info_dialog("حول البرنامج", about_text)

    def show_shortcuts(self):
        """عرض اختصارات لوحة المفاتيح محسنة"""
        shortcuts_text = """
⌨️ اختصارات لوحة المفاتيح

📄 الملف:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ctrl+N     - حالة جديدة
Ctrl+S     - حفظ التغييرات
Ctrl+P     - طباعة التقرير
Ctrl+Q     - خروج

✏️ التحرير:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ctrl+A     - إضافة مرفق
Ctrl+M     - إضافة مراسلة
Delete     - حذف الحالة المحددة
Ctrl+E     - إدارة الموظفين

👁️ العرض:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
F5         - تحديث البيانات
Ctrl+R     - تحديث البيانات
Ctrl+F     - تركيز على البحث
Ctrl+D     - لوحة التحكم
Ctrl+L     - عرض جميع الحالات

🔧 التنقل:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Escape     - مسح التحديد
↑          - الانتقال للحالة السابقة
↓          - الانتقال للحالة التالية

💡 نصائح:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• استخدم الاختصارات لتسريع العمل
• يمكن الجمع بين المفاتيح للوصول السريع
• جميع الاختصارات تعمل في أي مكان في التطبيق
        """
        
        self.show_info_dialog("⌨️ اختصارات لوحة المفاتيح", shortcuts_text)

    def hide_notification(self):
        """إخفاء الإشعار"""
        if self.notification_label:
            self.notification_label.master.destroy()
            self.notification_label = None

    def show_info_dialog(self, title, content):
        """عرض نافذة معلومات"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # توسيط النافذة
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        # العنوان
        title_label = tk.Label(dialog, text=title, 
                              font=self.fonts['header'], fg=self.colors['text_main'])
        title_label.pack(pady=(20, 10))
        
        # المحتوى مع سكرول
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        text_widget = tk.Text(text_frame, wrap='word', font=self.fonts['normal'],
                             bg=self.colors['bg_light'], relief='solid', bd=1)
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # إدخال المحتوى
        text_widget.insert('1.0', content)
        text_widget.config(state='disabled')
        
        # زر الإغلاق
        close_btn = tk.Button(dialog, text="إغلاق", command=dialog.destroy,
                             font=self.fonts['button'], bg=self.colors['button_action'], 
                             fg='white', padx=20, pady=5)
        close_btn.pack(pady=20)

    def load_settings(self):
        """تحميل الإعدادات من ملف JSON."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"attachments_path": ""} # قيمة افتراضية فارغة

    def save_settings(self):
        """حفظ الإعدادات في ملف JSON."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def show_settings_window(self):
        """عرض شاشة الإعدادات."""
        win = tk.Toplevel(self.root)
        win.title("الإعدادات")
        win.geometry("600x200")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="مسار حفظ المرفقات المنسوخة:", font=self.fonts['subheader']).pack(pady=(15, 5))

        path_frame = tk.Frame(win)
        path_frame.pack(fill='x', padx=20)

        path_var = tk.StringVar(value=self.settings.get('attachments_path', ''))
        path_entry = tk.Entry(path_frame, textvariable=path_var, font=self.fonts['normal'], state='readonly')
        path_entry.pack(side='left', fill='x', expand=True)

        def select_path():
            path = filedialog.askdirectory(title="اختر مجلد لحفظ المرفقات")
            if path:
                path_var.set(path)

        tk.Button(path_frame, text="اختيار...", command=select_path).pack(side='right', padx=(5, 0))

        def save_and_close():
            self.settings['attachments_path'] = path_var.get()
            self.save_settings()
            self.show_notification("تم حفظ الإعدادات بنجاح", notification_type="success")
            win.destroy()

        save_btn = tk.Button(win, text="حفظ وإغلاق", command=save_and_close, font=self.fonts['button'], bg='#27ae60', fg='white')
        save_btn.pack(pady=20)

    def after_main_layout(self):
        """تحميل البيانات الأولية بعد إنشاء كل عناصر الواجهة"""
        if hasattr(self, 'functions') and self.functions:
            self.functions.load_initial_data()
        else:
            self.load_initial_data()
        
        # تحميل الحالة المعلقة من لوحة التحكم إذا وجدت
        if hasattr(self, 'pending_dashboard_case') and self.pending_dashboard_case:
            self.root.after(200, lambda: self._load_pending_dashboard_case())
    
    def _load_pending_dashboard_case(self):
        """تحميل الحالة المعلقة من لوحة التحكم"""
        try:
            if hasattr(self, 'pending_dashboard_case') and self.pending_dashboard_case:
                case = self.pending_dashboard_case
                case_id = None
                
                if isinstance(case, dict):
                    case_id = case.get('id')
                elif isinstance(case, (list, tuple)) and len(case) > 0:
                    case_id = case[0]
                
                # البحث عن الحالة في البيانات المحملة
                target_case = None
                for c in self.cases_data:
                    current_id = None
                    if isinstance(c, dict):
                        current_id = c.get('id')
                    elif isinstance(c, (list, tuple)) and len(c) > 0:
                        current_id = c[0]
                    
                    if current_id == case_id:
                        target_case = c
                        break
                
                # إذا لم نجد الحالة في البيانات المحملة، استخدم البيانات الأصلية
                if not target_case:
                    target_case = case
                
                # تحميل الحالة
                self.load_case(target_case)
                
                # إشعار المستخدم بنجاح التحميل
                customer_name = target_case.get('customer_name', '') if isinstance(target_case, dict) else target_case[1] if len(target_case) > 1 else ''
                self.show_notification(f"تم تحميل حالة العميل: {customer_name}", notification_type="success")
                
                # مسح الحالة المعلقة
                delattr(self, 'pending_dashboard_case')
                
        except Exception as e:
            self.show_notification(f"خطأ في تحميل الحالة المعلقة: {str(e)}", notification_type="error")
            print(f"خطأ في تحميل الحالة المعلقة: {e}")
            import traceback
            traceback.print_exc()
            # مسح الحالة المعلقة في حالة الخطأ
            if hasattr(self, 'pending_dashboard_case'):
                delattr(self, 'pending_dashboard_case')
    
    def setup_fonts(self):
        """إعداد الخطوط العربية الاحترافية"""
        preferred_fonts = [
            ("Cairo", 1),
            ("Noto Kufi Arabic", 1),
            ("Amiri", 1),
            ("Arial", 0)
        ]
        def get_font(family, size, weight=None):
            for font_name, _ in preferred_fonts:
                try:
                    import tkinter.font as tkFont
                    f = tkFont.Font(family=font_name, size=size, weight=weight or 'normal')
                    return (font_name, size, weight) if weight else (font_name, size)
                except:
                    continue
            return ("Arial", size, weight) if weight else ("Arial", size)

        self.fonts = {
            'header': get_font(0, 18, 'bold'),
            'subheader': get_font(0, 13, 'bold'),
            'normal': get_font(0, 11),
            'small': get_font(0, 10),
            'button': get_font(0, 12, 'bold')
        }
    
    # تم إزالة create_fixed_header لتوفير مساحة
    
    def create_tooltip(self, widget, text):
        """إنشاء tooltip للعنصر - محسن وأكبر"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
            
            # تصميم محسن للـ tooltip
            label = tk.Label(tooltip, text=text, justify='right',
                           background="#2c3e50", relief='solid', borderwidth=2,
                           font=self.fonts['normal'], fg='white', padx=10, pady=8)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
            tooltip.bind('<Leave>', lambda e: hide_tooltip())
        
        widget.bind('<Enter>', show_tooltip)
    
    def refresh_data(self):
        """إعادة تحميل البيانات من قاعدة البيانات"""
        try:
            # فحص وجود عناصر الواجهة قبل التحديث
            if hasattr(self, 'status_label') and self.status_label and self.status_label.winfo_exists():
                self.status_label.config(text="جاري تحديث البيانات...")
            self.show_loading_indicator("جاري تحديث البيانات...")
            
            # تشغيل التحديث في خيط منفصل لتجنب تجميد الواجهة
            def update_data():
                try:
                    # تحديث البيانات الأساسية فقط
                    self.cases_data = enhanced_db.get_all_cases() if hasattr(enhanced_db, 'get_all_cases') else []
                    self.filtered_cases = self.cases_data.copy()
                    
                    # تحديث قائمة الحالات
                    self.update_cases_list()
                    
                    # تحديث شريط الحالة
                    try:
                        if hasattr(self, 'cases_count_label') and self.cases_count_label and self.cases_count_label.winfo_exists():
                            total_cases = len(self.cases_data)
                            self.cases_count_label.config(text=f"📋 جميع الحالات: {total_cases}")
                    except Exception:
                        pass
                    
                    # تحديث قوائم السنوات
                    self.received_years = sorted({str(case.get('received_date', '')).split('-')[0] for case in self.cases_data if case.get('received_date')}, reverse=True)
                    self.created_years = sorted({str(case.get('created_date', '')).split('-')[0] for case in self.cases_data if case.get('created_date')}, reverse=True)
                    
                    # تحديث خيارات السنة
                    self.update_year_filter_options()
                    
                    # تحديث التبويبات إذا كانت الحالة محملة
                    if self.current_case_id:
                        self.load_attachments()
                        self.load_correspondences()
                        self.load_audit_log()
                    
                    self.root.after(0, lambda: self.show_notification("تم إعادة تحميل البيانات بنجاح", notification_type="success"))
                    self.root.after(0, lambda: self.status_label.config(text="جاهز") if hasattr(self, 'status_label') and self.status_label and self.status_label.winfo_exists() else None)
                except Exception as e:
                    self.root.after(0, lambda e=e: self.show_notification(f"خطأ في إعادة تحميل البيانات: {str(e)}", notification_type="error"))
                    self.root.after(0, lambda e=e: messagebox.showerror("خطأ", f"فشل في إعادة تحميل البيانات:\n{e}"))
                finally:
                    self.root.after(0, self.hide_loading_indicator)
            
            threading.Thread(target=update_data, daemon=True).start()
            
        except Exception as e:
            self.hide_loading_indicator()
            self.show_notification(f"خطأ في إعادة تحميل البيانات: {str(e)}", notification_type="error")
            messagebox.showerror("خطأ", f"فشل في إعادة تحميل البيانات:\n{e}")
    
    def create_main_layout(self):
        """إنشاء التخطيط الرئيسي محسن مع استغلال أفضل للمساحات"""
        # الإطار الرئيسي - استغلال كامل للمساحة
        main_frame = tk.Frame(self.root, bg=self.colors['bg_main'])
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # اللوحة الجانبية (يمين) - عرض ثابت
        self.create_sidebar(main_frame)
        
        # فاصل رفيع
        separator = ttk.Separator(main_frame, orient='vertical')
        separator.pack(side='right', fill='y', padx=2)
        
        # منطقة العرض الرئيسية (يسار) - استغلال كامل للمساحة المتبقية
        self.create_main_display(main_frame)
    
    def create_sidebar(self, parent):
        """إنشاء اللوحة الجانبية محسنة مع استغلال أفضل للمساحة"""
        sidebar_frame = tk.Frame(parent, bg=self.colors['bg_card'], width=380, relief='raised', bd=1)
        sidebar_frame.pack(side='right', fill='y', padx=(0, 3))
        sidebar_frame.pack_propagate(False)
        
        # عنوان اللوحة الجانبية - أكثر إحكاما
        header_frame = tk.Frame(sidebar_frame, bg=self.colors['header'], height=40)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        header_label = tk.Label(header_frame, text="قائمة الحالات", 
                               font=self.fonts['subheader'], fg=self.colors['header_text'], bg=self.colors['header'], anchor='e', justify='right')
        header_label.pack(expand=True, anchor='e', padx=10)
        
        # زر العودة للشاشة الرئيسية - أكثر إحكاما
        back_btn = tk.Button(sidebar_frame, text="⬅️ العودة للشاشة الرئيسية", 
                            font=self.fonts['small'], command=self.show_dashboard, 
                            bg=self.colors['button_secondary'], fg='white', 
                            relief='flat', padx=10, pady=3)
        back_btn.pack(fill='x', padx=8, pady=(3, 0))
        
        # أزرار الإجراءات
        self.create_action_buttons(sidebar_frame)
        
        # أدوات البحث والفلترة - أكثر إحكاما
        self.create_search_filters(sidebar_frame)
        
        # قائمة الحالات - استغلال كامل للمساحة المتبقية
        self.create_cases_list(sidebar_frame)

    def create_action_buttons(self, parent):
        """إنشاء أزرار الإجراءات مع tooltips - إزالة الأزرار المزدوجة"""
        # إزالة جميع الأزرار المزدوجة من اللوحة الجانبية لأنها موجودة في شريط الأدوات
        # لا نحتاج لأي أزرار هنا لأن جميع الأزرار موجودة في شريط الأدوات
        pass
    
    def create_search_filters(self, parent):
        """إنشاء أدوات البحث والفلترة محسنة مع استغلال أفضل للمساحة"""
        filters_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        filters_frame.pack(fill='x', padx=8, pady=6)
        
        # فلترة السنة - أكثر إحكاما
        year_frame = tk.Frame(filters_frame, bg=self.colors['bg_light'])
        year_frame.pack(fill='x', pady=(0, 6))
        
        tk.Label(year_frame, text="السنة:", font=self.fonts['small'], bg=self.colors['bg_light']).pack(side='right')
        
        self.year_var = tk.StringVar(value="الكل")
        self.year_combo = ttk.Combobox(year_frame, textvariable=self.year_var, 
                                      state='readonly', width=8)
        self.year_combo.pack(side='right', padx=(3, 0))
        self.year_combo.bind('<<ComboboxSelected>>', self.perform_search)

        # اختيار نوع التاريخ - أكثر إحكاما
        self.date_field_var = tk.StringVar(value="received_date")
        self.date_field_combo = ttk.Combobox(year_frame, textvariable=self.date_field_var, 
                                             values=["تاريخ الورود", "تاريخ الإدخال"], 
                                             state='readonly', width=10)
        self.date_field_combo.pack(side='right', padx=(3, 0))
        self.date_field_combo.bind('<<ComboboxSelected>>', self.update_year_filter_options)
        self.date_field_map = {"تاريخ الورود": "received_date", "تاريخ الإدخال": "created_date"}
        
        # البحث المتقدم - أكثر إحكاما
        search_frame = tk.Frame(filters_frame, bg=self.colors['bg_light'])
        search_frame.pack(fill='x')
        
        tk.Label(search_frame, text="البحث:", font=self.fonts['small'], bg=self.colors['bg_light']).pack(anchor='e')
        
        # نوع البحث
        search_type_frame = tk.Frame(search_frame, bg=self.colors['bg_light'])
        search_type_frame.pack(fill='x', pady=(3, 0))
        
        self.search_type_var = tk.StringVar(value="شامل")
        self.search_type_combo = ttk.Combobox(search_type_frame, textvariable=self.search_type_var,
                                             state='readonly', width=15)
        self.search_type_combo['values'] = [
            "شامل", "اسم العميل", "رقم المشترك", "العنوان", 
            "تصنيف المشكلة", "حالة المشكلة", "اسم الموظف"
        ]
        self.search_type_combo.pack(fill='x')
        self.search_type_combo.bind('<<ComboboxSelected>>', self.on_search_type_change)
        
        # حقل البحث
        search_input_frame = tk.Frame(search_frame, bg=self.colors['bg_light'])
        search_input_frame.pack(fill='x', pady=(3, 0))
        
        self.search_value_var = tk.StringVar()
        self.search_entry = tk.Entry(search_input_frame, textvariable=self.search_value_var,
                                    font=self.fonts['small'])
        self.search_entry.pack(fill='x')
        self.search_entry.bind('<KeyRelease>', self.perform_search)
        
        # سيتم إنشاء الكومبو بوكس ديناميكياً حسب نوع البحث
        self.search_combo = None
        
        # إضافة قائمة ترتيب - أكثر إحكاما
        sort_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        sort_frame.pack(fill='x', padx=8, pady=(0, 6))
        tk.Label(sort_frame, text="ترتيب:", font=self.fonts['small'], bg=self.colors['bg_light']).pack(side='right')
        self.sort_var = tk.StringVar(value="السنة (تنازلي)")
        sort_options = ["السنة (تنازلي)", "السنة (تصاعدي)", "اسم العميل (أ-ي)", "اسم العميل (ي-أ)"]
        self.sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var, values=sort_options, state='readonly', width=15)
        self.sort_combo.pack(side='right', padx=(3, 0))
        self.sort_combo.bind('<<ComboboxSelected>>', self.apply_sorting)
    
    def create_cases_list(self, parent):
        """
        إنشاء قائمة الحالات محسنة مع استغلال أفضل للمساحة
        """
        list_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        list_frame.pack(fill='both', expand=True, padx=6, pady=6)
        
        list_canvas = tk.Canvas(list_frame, bg=self.colors['bg_light'], highlightthickness=0)
        style = ttk.Style()
        style.layout('AlwaysOn.TScrollbar',
            [('Vertical.Scrollbar.trough', {'children': [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})], 'sticky': 'ns'})]
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=list_canvas.yview, style='AlwaysOn.TScrollbar')
        self.scrollable_frame = tk.Frame(list_canvas, bg=self.colors['bg_light'])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        )
        # anchor='nw' حتى تظهر البطاقات بشكل صحيح
        list_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=scrollbar.set)
        list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.cases_canvas = list_canvas
        self.cases_scrollbar = scrollbar
        
        # دعم تمرير بالماوس
        def _on_mousewheel(event):
            list_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        list_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # دعم تمرير بالأسهم
        list_canvas.bind_all("<Up>", self._on_case_list_up)
        list_canvas.bind_all("<Down>", self._on_case_list_down)
        
        self.selected_case_index = 0
        self.case_card_widgets = []

    def add_case_card(self, case_data):
        """إضافة بطاقة حالة للقائمة مع تصميم محسن وتأثيرات تفاعلية"""
        try:
            # فحص وجود الإطار القابل للتمرير
            if not self.scrollable_frame or not self.scrollable_frame.winfo_exists():
                return
                
            # استخراج البيانات
            if isinstance(case_data, dict):
                case_id = case_data.get('id')
                customer_name = case_data.get('customer_name', 'بدون اسم')
                subscriber_number = case_data.get('subscriber_number', '')
                status = case_data.get('status', 'غير محدد')
                category_name = case_data.get('category_name', '')
                created_date = case_data.get('created_date', '')
                modified_by_name = case_data.get('modified_by_name', '')
            else:
                case_id, customer_name, subscriber_number, status, category_name, _, modified_by_name, created_date, _ = case_data
            
            # إنشاء إطار البطاقة مع تصميم محسن وأكثر إحكاما
            card_frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg_light'], 
                                 relief='solid', bd=1, padx=12, pady=8)
            card_frame.pack(fill='x', padx=6, pady=3)
            
            # لون الحدود حسب الحالة
            status_colors = {
                'جديدة': self.colors['status_new'],
                'قيد التنفيذ': self.colors['status_inprogress'],
                'تم حلها': self.colors['status_solved'],
                'مغلقة': self.colors['status_closed']
            }
            border_color = status_colors.get(status, self.colors['status_closed'])
            card_frame.configure(highlightbackground=border_color, highlightthickness=2)
            
            # إطار المحتوى الرئيسي
            content_frame = tk.Frame(card_frame, bg=self.colors['bg_light'])
            content_frame.pack(fill='both', expand=True)
            
            # رأس البطاقة مع اسم العميل
            header_frame = tk.Frame(content_frame, bg=self.colors['bg_light'])
            header_frame.pack(fill='x', pady=(0, 8))
            
            name_label = tk.Label(header_frame, text=customer_name, 
                                 font=self.fonts['subheader'], fg=self.colors['text_main'], 
                                 bg=self.colors['bg_light'])
            name_label.pack(side='right')
            
            # شارة الحالة في الجانب الأيسر
            status_badge = tk.Label(header_frame, text=status,
                                   font=self.fonts['small'], fg='white',
                                   bg=border_color, padx=10, pady=3, relief='flat')
            status_badge.pack(side='left')
            
            # تفاصيل الحالة
            details_frame = tk.Frame(content_frame, bg=self.colors['bg_light'])
            details_frame.pack(fill='x', pady=(0, 8))
            
            # رقم المشترك
            if subscriber_number:
                subscriber_frame = tk.Frame(details_frame, bg=self.colors['bg_light'])
                subscriber_frame.pack(fill='x', pady=2)
                
                subscriber_icon = tk.Label(subscriber_frame, text="📞", 
                                          font=self.fonts['small'], bg=self.colors['bg_light'])
                subscriber_icon.pack(side='right', padx=(0, 5))
                
                subscriber_label = tk.Label(subscriber_frame, text=f"رقم المشترك: {subscriber_number}", 
                                           font=self.fonts['normal'], fg=self.colors['text_subtle'], 
                                           bg=self.colors['bg_light'])
                subscriber_label.pack(side='right')
            
            # تصنيف المشكلة
            if category_name:
                category_frame = tk.Frame(details_frame, bg=self.colors['bg_light'])
                category_frame.pack(fill='x', pady=2)
                
                category_icon = tk.Label(category_frame, text="🏷️", 
                                        font=self.fonts['small'], bg=self.colors['bg_light'])
                category_icon.pack(side='right', padx=(0, 5))
                
                category_label = tk.Label(category_frame, text=f"التصنيف: {category_name}", 
                                         font=self.fonts['normal'], fg=self.colors['text_subtle'], 
                                         bg=self.colors['bg_light'])
                category_label.pack(side='right')
            
            # تاريخ الإنشاء
            if created_date:
                try:
                    date_obj = datetime.strptime(created_date, "%Y-%m-%d %H:%M:%S")
                    formatted_date = date_obj.strftime("%Y/%m/%d")
                    
                    date_frame = tk.Frame(details_frame, bg=self.colors['bg_light'])
                    date_frame.pack(fill='x', pady=2)
                    
                    date_icon = tk.Label(date_frame, text="📅", 
                                        font=self.fonts['small'], bg=self.colors['bg_light'])
                    date_icon.pack(side='right', padx=(0, 5))
                    
                    date_label = tk.Label(date_frame, text=f"تاريخ الإنشاء: {formatted_date}", 
                                         font=self.fonts['small'], fg=self.colors['text_subtle'], 
                                         bg=self.colors['bg_light'])
                    date_label.pack(side='right')
                except:
                    pass
            
            # آخر مُعدِّل
            if modified_by_name:
                modifier_frame = tk.Frame(details_frame, bg=self.colors['bg_light'])
                modifier_frame.pack(fill='x', pady=2)
                
                modifier_icon = tk.Label(modifier_frame, text="👤", 
                                        font=self.fonts['small'], bg=self.colors['bg_light'])
                modifier_icon.pack(side='right', padx=(0, 5))
                
                modifier_label = tk.Label(modifier_frame, text=f"آخر تعديل: {modified_by_name}", 
                                         font=self.fonts['small'], fg=self.colors['text_subtle'], 
                                         bg=self.colors['bg_light'])
                modifier_label.pack(side='right')
            
            # إضافة البطاقة للقائمة
            self.case_card_widgets.append(card_frame)
            
            # ربط حدث النقر
            def on_card_click(event, case_data=case_data):
                self.load_case(case_data)
                self._update_selected_case_index(case_data.get('id') if isinstance(case_data, dict) else case_data[0])
                self._highlight_selected_case_card()
            
            # ربط الأحداث للبطاقة الرئيسية
            card_frame.bind('<Button-1>', on_card_click)
            card_frame.bind('<Enter>', lambda e: self._on_card_hover_enter(e, card_frame))
            card_frame.bind('<Leave>', lambda e: self._on_card_hover_leave(e, card_frame))
            
            # جعل جميع العناصر الداخلية قابلة للنقر بشكل متكرر
            def bind_click_to_widget(widget):
                widget.bind('<Button-1>', on_card_click)
                widget.bind('<Enter>', lambda e: self._on_card_hover_enter(e, card_frame))
                widget.bind('<Leave>', lambda e: self._on_card_hover_leave(e, card_frame))
                
                # ربط الأحداث للعناصر الفرعية أيضاً
                for child in widget.winfo_children():
                    bind_click_to_widget(child)
            
            # تطبيق الربط على جميع العناصر الداخلية
            for child in card_frame.winfo_children():
                bind_click_to_widget(child)
        except Exception as e:
            # تجاهل الأخطاء في إضافة البطاقات
            pass
    
    def _on_card_hover_enter(self, event, card_frame):
        """تأثير عند دخول الماوس للبطاقة"""
        try:
            card_frame.config(relief='raised', bd=2)
            card_frame.config(bg=self.colors['bg_card'])
            
            # تغيير لون خلفية جميع العناصر الداخلية مع حماية شارة الحالة
            for child in card_frame.winfo_children():
                if isinstance(child, tk.Label):
                    # لا تغير لون شارة الحالة (التي لها خلفية ملونة)
                    if child.cget('bg') not in [self.colors['status_new'], self.colors['status_inprogress'], 
                                               self.colors['status_solved'], self.colors['status_closed']]:
                        child.config(bg=self.colors['bg_card'])
                elif isinstance(child, tk.Frame):
                    child.config(bg=self.colors['bg_card'])
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label):
                            # لا تغير لون شارة الحالة
                            if grandchild.cget('bg') not in [self.colors['status_new'], self.colors['status_inprogress'], 
                                                           self.colors['status_solved'], self.colors['status_closed']]:
                                grandchild.config(bg=self.colors['bg_card'])
        except Exception:
            pass
    
    def _on_card_hover_leave(self, event, card_frame):
        """تأثير عند خروج الماوس من البطاقة"""
        try:
            card_frame.config(relief='solid', bd=1)
            card_frame.config(bg=self.colors['bg_light'])
            
            # إعادة لون خلفية جميع العناصر الداخلية مع حماية شارة الحالة
            for child in card_frame.winfo_children():
                if isinstance(child, tk.Label):
                    # لا تغير لون شارة الحالة (التي لها خلفية ملونة)
                    if child.cget('bg') not in [self.colors['status_new'], self.colors['status_inprogress'], 
                                               self.colors['status_solved'], self.colors['status_closed']]:
                        child.config(bg=self.colors['bg_light'])
                elif isinstance(child, tk.Frame):
                    child.config(bg=self.colors['bg_light'])
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label):
                            # لا تغير لون شارة الحالة
                            if grandchild.cget('bg') not in [self.colors['status_new'], self.colors['status_inprogress'], 
                                                           self.colors['status_solved'], self.colors['status_closed']]:
                                grandchild.config(bg=self.colors['bg_light'])
        except Exception:
            pass
    
    def create_main_display(self, parent):
        """إنشاء منطقة العرض الرئيسية محسنة مع استغلال أفضل للمساحة"""
        # الإطار الرئيسي للعرض - استغلال كامل للمساحة
        display_frame = tk.Frame(parent, bg='#ffffff', relief='raised', bd=1)
        display_frame.pack(side='left', fill='both', expand=True)
        
        # رأس العرض - أكثر إحكاما
        self.create_display_header(display_frame)
        
        # أزرار العمليات - مساحة أقل
        self.create_display_buttons(display_frame)
        
        # نظام التبويبات - استغلال كامل للمساحة المتبقية
        self.create_tabs(display_frame)
    
    def create_display_header(self, parent):
        """إنشاء رأس العرض محسن مع استغلال أفضل للمساحة"""
        header_frame = tk.Frame(parent, bg=self.colors['header'], height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # اسم العميل - أكثر إحكاما
        self.customer_name_label = tk.Label(header_frame, text="اختر حالة من القائمة",
                                           font=self.fonts['subheader'], fg=self.colors['header_text'], bg=self.colors['header'])
        self.customer_name_label.pack(expand=True, pady=(8, 0))
        
        # الموظف المسؤول عن الحل - أكثر إحكاما
        self.solved_by_label = tk.Label(header_frame, text="",
                                       font=self.fonts['small'], fg=self.colors['text_subtle'], bg=self.colors['header'])
        self.solved_by_label.pack(pady=(0, 8))
    
    def create_display_buttons(self, parent):
        """إنشاء أزرار العمليات مع tooltips - إزالة الأزرار المزدوجة"""
        # إزالة الأزرار المزدوجة لأنها موجودة في شريط الأدوات
        # إزالة منطقة الأزرار تماماً لتوفير مساحة
        buttons_frame = tk.Frame(parent, bg=self.colors['bg_card'], height=10)
        buttons_frame.pack(fill='x')
        buttons_frame.pack_propagate(False)
        
        # إنشاء أزرار فارغة لتجنب أخطاء الكود (لن تستخدم)
        self.save_btn = tk.Button(buttons_frame, text="", command=lambda: None, state='disabled')
        self.print_btn = tk.Button(buttons_frame, text="", command=lambda: None, state='disabled')
        self.save_btn.pack_forget()  # إخفاء الزر
        self.print_btn.pack_forget()  # إخفاء الزر
    
    def create_tabs(self, parent):
        """إنشاء نظام التبويبات محسن مع استغلال أفضل للمساحة"""
        # إطار التبويبات - استغلال كامل للمساحة
        tabs_frame = tk.Frame(parent, bg='#ffffff')
        tabs_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # نوت بوك التبويبات مع اتجاه RTL
        self.notebook = ttk.Notebook(tabs_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # التبويبات - ترتيب عكسي للتوافق مع RTL
        self.create_reports_tab()
        self.create_audit_log_tab()
        self.create_correspondences_tab()
        self.create_attachments_tab()
        self.create_basic_data_tab()
        
        # تحديد تبويب البيانات الأساسية كافتراضي
        self.notebook.select(4)  # التبويب الأخير (البيانات الأساسية)

    def create_reports_tab(self):
        """إنشاء تبويب التقارير"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="التقارير")

        # عنوان رئيسي
        title = tk.Label(reports_frame, text="تقارير النظام", font=("Arial", 16, "bold"), fg="#2c3e50")
        title.pack(pady=20)

        # زر تصدير كل الحالات (Excel/CSV فقط)
        export_all_btn = tk.Button(reports_frame, text="تصدير كل الحالات (Excel/CSV)", font=("Arial", 12), bg="#3498db", fg="white", command=self.export_cases_data)
        export_all_btn.pack(pady=10)

        # زر تقرير إحصائي سريع
        stats_btn = tk.Button(reports_frame, text="تقرير إحصائي سريع", font=("Arial", 12), bg="#27ae60", fg="white", command=self.show_quick_stats_report)
        stats_btn.pack(pady=10)

        # منطقة عرض التقرير الإحصائي
        self.stats_report_label = tk.Label(reports_frame, text="", font=("Arial", 11), fg="#2c3e50", justify="right")
        self.stats_report_label.pack(pady=20)

    def show_quick_stats_report(self):
        """عرض تقرير إحصائي سريع في تبويب التقارير"""
        total_cases = len(self.cases_data)
        active_cases = len([case for case in self.cases_data if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) not in ['تم حلها', 'مغلقة']])
        solved_cases = len([case for case in self.cases_data if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) == 'تم حلها'])
        closed_cases = len([case for case in self.cases_data if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) == 'مغلقة'])
        stats_text = f"""
        إجمالي الحالات: {total_cases}\n
        الحالات النشطة: {active_cases}\n
        الحالات المحلولة: {solved_cases}\n
        الحالات المغلقة: {closed_cases}
        """
        self.stats_report_label.config(text=stats_text)
    
    def create_basic_data_tab(self):
        """إنشاء تبويب البيانات الأساسية بمحاذاة يمين"""
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text="البيانات الأساسية")

        # إطار للمحتوى مع سكرول
        canvas = tk.Canvas(basic_frame, bg=self.colors['bg_light'])
        style = ttk.Style()
        style.layout('AlwaysOn.TScrollbar',
            [('Vertical.Scrollbar.trough', {'children': [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})], 'sticky': 'ns'})]
        )
        scrollbar = ttk.Scrollbar(basic_frame, orient="vertical", command=canvas.yview, style='AlwaysOn.TScrollbar')
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_light'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # anchor='nw' حتى تظهر الحقول بشكل صحيح
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # الحقول - أكثر إحكاما
        fields_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_light'])
        fields_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # بيانات العميل
        customer_section = tk.LabelFrame(fields_frame, text="بيانات العميل", 
                                        font=self.fonts['subheader'], bg=self.colors['bg_light'], labelanchor='ne')
        customer_section.pack(fill='x', pady=(0, 20), ipady=10, ipadx=10)

        # اسم العميل
        self.create_field(customer_section, "اسم العميل:", "customer_name", row=0)

        # رقم المشترك
        self.create_field(customer_section, "رقم المشترك:", "subscriber_number", row=1)

        # رقم الهاتف
        self.create_field(customer_section, "رقم الهاتف:", "phone", row=2)

        # العنوان
        self.create_text_field(customer_section, "العنوان:", "address", row=3, height=3)

        # بيانات المشكلة
        problem_section = tk.LabelFrame(fields_frame, text="بيانات المشكلة", 
                                       font=self.fonts['subheader'], bg=self.colors['bg_light'], labelanchor='ne')
        problem_section.pack(fill='x', pady=(0, 20), ipady=10, ipadx=10)
        problem_section.pack_propagate(True)

        # تصنيف المشكلة
        category_combo = self.create_combo_field(problem_section, "تصنيف المشكلة:", "category", row=0)
        categories = enhanced_db.get_categories() if hasattr(enhanced_db, 'get_categories') else []
        if not categories:
            # إضافة تصنيفات افتراضية إذا كانت قاعدة البيانات فارغة
            default_cats = ["مياه", "صرف صحي", "عداد", "فاتورة", "شكاوى أخرى"]
            # for cat in default_cats:
            #     if hasattr(enhanced_db, 'add_category'):
            #         enhanced_db.add_category(cat)
            categories = enhanced_db.get_categories() if hasattr(enhanced_db, 'get_categories') else []
        category_names = [cat[1] for cat in categories]
        category_combo['values'] = category_names
        if category_names:
            category_combo.set(category_names[0])

        # سنة وشهر الورود
        self.create_year_month_fields(problem_section, row=1)

        # حالة المشكلة
        status_combo = self.create_combo_field(problem_section, "حالة المشكلة:", "status", row=2)
        status_options = enhanced_db.get_status_options() if hasattr(enhanced_db, 'get_status_options') else []
        if not status_options:
            status_options = [("جديدة", "#3498db"), ("قيد التنفيذ", "#f39c12"), ("تم حلها", "#27ae60"), ("مغلقة", "#95a5a6")]
        status_names = [s[0] for s in status_options]
        status_combo['values'] = status_names
        if status_names:
            status_combo.set(status_names[0])

        # وصف المشكلة
        self.create_text_field(problem_section, "وصف المشكلة:", "problem_description", row=3, height=4)

        # ما تم تنفيذه
        self.create_text_field(problem_section, "ما تم تنفيذه:", "actions_taken", row=4, height=4)

        # بيانات العداد والمديونية
        meter_section = tk.LabelFrame(fields_frame, text="بيانات العداد والمديونية", 
                                     font=self.fonts['subheader'], bg=self.colors['bg_light'], labelanchor='ne')
        meter_section.pack(fill='x', ipady=10, ipadx=10)
        meter_section.pack_propagate(True)

        # آخر قراءة
        self.create_field(meter_section, "آخر قراءة للعداد:", "last_meter_reading", row=0)

        # تاريخ آخر قراءة
        self.create_field(meter_section, "تاريخ آخر قراءة:", "last_reading_date", row=1)

        # المديونية
        self.create_field(meter_section, "المديونية:", "debt_amount", row=2)

        # اختيار الموظف المسؤول عن الإضافة/التعديل
        # عند فتح نافذة إدارة الموظفين، عيّن أرقام أداء وهمية تلقائيًا لمن ليس لديه رقم
        if hasattr(enhanced_db, 'assign_fake_performance_numbers'):
            enhanced_db.assign_fake_performance_numbers()
        employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
        self.employee_var = tk.StringVar()
        employee_names = [emp[1] for emp in employees]
        if employee_names:
            self.employee_var.set(employee_names[0])
        emp_frame = tk.Frame(fields_frame, bg=self.colors['bg_light'])
        emp_frame.pack(fill='x', pady=(15, 0), anchor='e')
        tk.Label(emp_frame, text="الموظف المسؤول:", font=self.fonts['normal'], bg=self.colors['bg_light'], anchor='e', justify='right').pack(side='right', padx=(0, 10))
        emp_combo = ttk.Combobox(emp_frame, textvariable=self.employee_var, values=employee_names, state='readonly', width=30, justify='right')
        emp_combo.pack(side='right', padx=(5, 0))
        self.basic_data_widgets['employee_name'] = emp_combo

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_field(self, parent, label_text, field_name, row, column=0, width=30):
        """إنشاء حقل إدخال عادي بمحاذاة يمين"""
        label = tk.Label(parent, text=label_text, font=self.fonts['normal'], bg=self.colors['bg_light'], anchor='e', justify='right')
        label.grid(row=row, column=column*2, sticky='e', padx=(15, 8), pady=8)
        entry = tk.Entry(parent, font=self.fonts['normal'], width=width, justify='right')
        entry.grid(row=row, column=column*2+1, sticky='e', padx=(0, 15), pady=8)
        self.basic_data_widgets[field_name] = entry
        return entry
    
    def create_text_field(self, parent, label_text, field_name, row, height=3, width=40):
        """إنشاء حقل نص متعدد الأسطر بمحاذاة يمين"""
        label = tk.Label(parent, text=label_text, font=self.fonts['normal'], bg=self.colors['bg_light'], anchor='ne', justify='right')
        label.grid(row=row, column=0, sticky='ne', padx=(15, 8), pady=8)
        text_frame = tk.Frame(parent, bg=self.colors['bg_light'])
        text_frame.grid(row=row, column=1, sticky='e', padx=(0, 15), pady=8)
        text_widget = tk.Text(text_frame, font=self.fonts['normal'], width=width, height=height, wrap='word')
        text_widget.tag_configure('right', justify='right')
        text_widget.insert('1.0', '')
        text_widget.tag_add('right', '1.0', 'end')
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=text_scrollbar.set)
        text_widget.pack(side="left", fill="both", expand=True)
        text_scrollbar.pack(side="right", fill="y")
        self.basic_data_widgets[field_name] = text_widget
        return text_widget
    
    def create_combo_field(self, parent, label_text, field_name, row, width=30):
        """إنشاء حقل قائمة منسدلة بمحاذاة يمين مع متغير خاص"""
        label = tk.Label(parent, text=label_text, font=self.fonts['normal'], bg=self.colors['bg_light'], anchor='e', justify='right')
        label.grid(row=row, column=0, sticky='e', padx=(15, 8), pady=8)
        var = tk.StringVar()
        combo = ttk.Combobox(parent, font=self.fonts['normal'], width=width-3, state='readonly', justify='right', textvariable=var)
        combo.grid(row=row, column=1, sticky='e', padx=(0, 15), pady=8)
        self.basic_data_widgets[field_name] = combo
        self.basic_data_widgets[field_name + '_var'] = var
        return combo

    def create_year_month_fields(self, parent, row):
        """إنشاء حقول اختيار السنة والشهر"""
        label = tk.Label(parent, text="تاريخ الورود:", font=self.fonts['normal'], bg=self.colors['bg_light'], anchor='e', justify='right')
        label.grid(row=row, column=0, sticky='e', padx=(10, 5), pady=5)

        frame = tk.Frame(parent, bg=self.colors['bg_light'])
        frame.grid(row=row, column=1, sticky='e', padx=(0, 10), pady=5)

        # قائمة السنوات
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year, 2001, -1)] # من السنة الحالية حتى 2002
        self.year_received_var = tk.StringVar(value=str(current_year))
        year_combo = ttk.Combobox(frame, textvariable=self.year_received_var, values=years, state='readonly', width=8, justify='right')
        year_combo.pack(side='right', padx=(5, 0))
        self.basic_data_widgets['year_received'] = year_combo
        self.basic_data_widgets['year_received_var'] = self.year_received_var

        # قائمة الشهور
        months = [f"{m:02d}" for m in range(1, 13)]
        self.month_received_var = tk.StringVar(value=f"{datetime.now().month:02d}")
        month_combo = ttk.Combobox(frame, textvariable=self.month_received_var, values=months, state='readonly', width=5, justify='right')
        month_combo.pack(side='right')
        self.basic_data_widgets['month_received'] = month_combo
        self.basic_data_widgets['month_received_var'] = self.month_received_var
    
    def create_attachments_tab(self):
        """إنشاء تبويب المرفقات"""
        attachments_frame = ttk.Frame(self.notebook)
        self.notebook.add(attachments_frame, text="المرفقات")
        
        # أزرار المرفقات - أكثر إحكاما
        buttons_frame = tk.Frame(attachments_frame, bg=self.colors['bg_light'])
        buttons_frame.pack(fill='x', padx=8, pady=6)
        
        add_attachment_btn = tk.Button(buttons_frame, text="📎 إضافة مرفق",
                                      command=self.add_attachment,
                                      font=self.fonts['button'], bg=self.colors['button_action'], fg='white',
                                      relief='flat', padx=15, pady=8)
        add_attachment_btn.pack(side='right')
        
        # إضافة تأثيرات بصرية للزر
        add_attachment_btn.bind('<Enter>', lambda e: add_attachment_btn.config(bg=self.lighten_color(self.colors['button_action'])))
        add_attachment_btn.bind('<Leave>', lambda e: add_attachment_btn.config(bg=self.colors['button_action']))
        # جدول المرفقات (أضف عمود مسار الملف كعمود مخفي)
        columns = ('ID', 'نوع الملف', 'اسم الملف', 'الوصف', 'تاريخ الرفع', 'الموظف', 'مسار الملف')
        self.attachments_tree = ttk.Treeview(attachments_frame, columns=columns, show='headings', height=15)
        for col in columns:
            self.attachments_tree.heading(col, text=col)
            if col == 'ID':
                self.attachments_tree.column(col, width=50)
            elif col == 'نوع الملف':
                self.attachments_tree.column(col, width=80)
            elif col == 'مسار الملف':
                self.attachments_tree.column(col, width=0, stretch=False)  # إخفاء العمود
            else:
                self.attachments_tree.column(col, width=120)
        # سكرول بار للمرفقات
        attachments_scrollbar = ttk.Scrollbar(attachments_frame, orient='vertical', command=self.attachments_tree.yview)
        self.attachments_tree.configure(yscrollcommand=attachments_scrollbar.set)
        self.attachments_tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=(0, 10))
        attachments_scrollbar.pack(side='right', fill='y', pady=(0, 10))
        # ربط النقر المزدوج
        self.attachments_tree.bind('<Double-1>', self.open_attachment)
        self.attachments_tree.bind('<Button-3>', self.show_attachment_context_menu)
    
    def create_correspondences_tab(self):
        """إنشاء تبويب المراسلات"""
        correspondences_frame = ttk.Frame(self.notebook)
        self.notebook.add(correspondences_frame, text="المراسلات")
        
        # أزرار المراسلات - أكثر إحكاما
        buttons_frame = tk.Frame(correspondences_frame, bg=self.colors['bg_light'])
        buttons_frame.pack(fill='x', padx=8, pady=6)
        
        add_correspondence_btn = tk.Button(buttons_frame, text="✉️ إضافة مراسلة",
                                          command=self.add_correspondence,
                                          font=self.fonts['button'], bg=self.colors['button_warning'], fg='white',
                                          relief='flat', padx=15, pady=8)
        add_correspondence_btn.pack(side='right')
        
        # زر حذف مراسلة
        del_correspondence_btn = tk.Button(buttons_frame, text="🗑️ حذف مراسلة",
                                           command=self.delete_correspondence,
                                           font=self.fonts['button'], bg=self.colors['button_delete'], fg='white',
                                           relief='flat', padx=15, pady=8)
        del_correspondence_btn.pack(side='right', padx=(0, 10))
        
        # إضافة تأثيرات بصرية للأزرار
        add_correspondence_btn.bind('<Enter>', lambda e: add_correspondence_btn.config(bg=self.lighten_color(self.colors['button_warning'])))
        add_correspondence_btn.bind('<Leave>', lambda e: add_correspondence_btn.config(bg=self.colors['button_warning']))
        
        del_correspondence_btn.bind('<Enter>', lambda e: del_correspondence_btn.config(bg=self.lighten_color(self.colors['button_delete'])))
        del_correspondence_btn.bind('<Leave>', lambda e: del_correspondence_btn.config(bg=self.colors['button_delete']))
        # جدول المراسلات
        columns = ('ID', 'رقم التسلسل', 'الرقم السنوي', 'المرسل', 'المحتوى', 'التاريخ', 'الموظف')
        self.correspondences_tree = ttk.Treeview(correspondences_frame, columns=columns, show='headings', height=15)
        for col in columns:
            self.correspondences_tree.heading(col, text=col)
            if col == 'ID':
                self.correspondences_tree.column(col, width=50)
            elif col in ['رقم التسلسل', 'الرقم السنوي']:
                self.correspondences_tree.column(col, width=80)
            else:
                self.correspondences_tree.column(col, width=120)
        # سكرول بار للمراسلات
        correspondences_scrollbar = ttk.Scrollbar(correspondences_frame, orient='vertical', command=self.correspondences_tree.yview)
        self.correspondences_tree.configure(yscrollcommand=correspondences_scrollbar.set)
        self.correspondences_tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=(0, 10))
        correspondences_scrollbar.pack(side='right', fill='y', pady=(0, 10))
        # ربط النقر المزدوج
        self.correspondences_tree.bind('<Double-1>', self.edit_correspondence)
    
    def create_audit_log_tab(self):
        """إنشاء تبويب سجل التعديلات"""
        audit_frame = ttk.Frame(self.notebook)
        self.notebook.add(audit_frame, text="سجل التعديلات")
        
        # جدول سجل التعديلات
        columns = ('التاريخ والوقت', 'الموظف', 'نوع الإجراء', 'وصف الإجراء')
        self.audit_tree = ttk.Treeview(audit_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.audit_tree.heading(col, text=col)
            if col == 'التاريخ والوقت':
                self.audit_tree.column(col, width=150)
            elif col == 'الموظف':
                self.audit_tree.column(col, width=120)
            else:
                self.audit_tree.column(col, width=200)
        
        # سكرول بار لسجل التعديلات
        audit_scrollbar = ttk.Scrollbar(audit_frame, orient='vertical', command=self.audit_tree.yview)
        self.audit_tree.configure(yscrollcommand=audit_scrollbar.set)
        
        self.audit_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        audit_scrollbar.pack(side='right', fill='y', pady=10)
    
    # سأكمل باقي الوظائف في الجزء التالي...
    
    def add_new_case(self):
        """تهيئة النموذج لإضافة حالة جديدة"""
        try:
            # مسح جميع الحقول
            for widget in self.basic_data_widgets.values():
                if isinstance(widget, tk.Entry) or isinstance(widget, ttk.Combobox):
                    widget.delete(0, tk.END)
                elif isinstance(widget, tk.Text):
                    widget.delete('1.0', tk.END)
            
            # إعادة تعيين المتغيرات
            self.current_case_id = None
            self.original_received_date = None
            self.current_case_status = None
            
            # تفعيل/تعطيل الأزرار
            self.save_btn.config(state='normal')
            self.print_btn.config(state='disabled')
            
            # تحديث العناوين
            self.customer_name_label.config(text="إدخال حالة جديدة")
            self.solved_by_label.config(text="")
            
            # تعيين تاريخ الورود إلى الحالي
            self.year_received_var.set(str(datetime.now().year))
            self.month_received_var.set(f"{datetime.now().month:02d}")
            
            # مسح التبويبات
            self.clear_tabs()
            
            # تحديث أزرار العمليات
            self.update_action_buttons_style()
            
            # تحديد تبويب البيانات الأساسية
            if hasattr(self, 'notebook'):
                self.notebook.select(4)  # التبويب الأخير (البيانات الأساسية)
            
            self.show_notification("تم تهيئة النموذج لإضافة حالة جديدة", notification_type="info")
            
        except Exception as e:
            self.show_notification(f"خطأ في تهيئة النموذج: {str(e)}", notification_type="error")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تهيئة النموذج:\n{e}")
    
    def clear_tabs(self):
        """مسح محتوى التبويبات"""
        # مسح المرفقات
        for item in self.attachments_tree.get_children():
            self.attachments_tree.delete(item)
        
        # مسح المراسلات
        for item in self.correspondences_tree.get_children():
            self.correspondences_tree.delete(item)
        
        # مسح سجل التعديلات
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

    def update_year_filter_options(self, event=None):
        """تحديث قائمة السنوات بناءً على نوع التاريخ المختار."""
        date_field_display = self.date_field_var.get()
        current_year = datetime.now().year
        # دعم dict وtuple معًا عند حساب سنوات الإدخال
        self.created_years = sorted({
            str(
                case.get('created_date', '') if isinstance(case, dict)
                else (case[7] if len(case) > 7 else '')
            ).split('-')[0]
            for case in self.cases_data
            if (case.get('created_date') if isinstance(case, dict) else (case[7] if len(case) > 7 else ''))
        }, reverse=True)
        if date_field_display == "تاريخ الورود":
            years = [str(y) for y in range(current_year, 2001, -1)]
            self.year_combo['values'] = ["الكل"] + years
        else:
            self.year_combo['values'] = ["الكل"] + self.created_years
        self.year_combo.set("الكل")
        self.perform_search()

    def manage_employees(self):
        employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
        # جلب أرقام الأداء أيضًا
        try:
            conn = sqlite3.connect(enhanced_db.db_name)
            cursor = conn.cursor()
            # استثنِ admin من القائمة
            cursor.execute("SELECT id, name, position, performance_number FROM employees WHERE is_active = 1 AND performance_number != 1 ORDER BY name")
            employees = cursor.fetchall()
            conn.close()
        except Exception:
            pass
        win = tk.Toplevel(self.root)
        win.title("إدارة الموظفين")
        win.geometry("500x550")
        tk.Label(win, text="قائمة الموظفين (اسم - رقم الأداء):", font=self.fonts['header']).pack(pady=10)
        emp_listbox = tk.Listbox(win, font=self.fonts['normal'], height=12)
        emp_listbox.pack(fill='x', padx=20)
        for emp in employees:
            name = emp[1] if len(emp) > 1 else ''
            perf = emp[3] if len(emp) > 3 else ''
            emp_listbox.insert('end', f"{name} - {perf}")
        # إضافة موظف
        add_frame = tk.Frame(win)
        add_frame.pack(pady=10)
        new_emp_var = tk.StringVar()
        new_perf_var = tk.StringVar()
        tk.Label(add_frame, text="اسم الموظف:", font=self.fonts['normal']).pack(side='right', padx=5)
        tk.Entry(add_frame, textvariable=new_emp_var, font=self.fonts['normal'], width=15).pack(side='right', padx=5)
        tk.Label(add_frame, text="رقم الأداء (رقم فريد):", font=self.fonts['normal']).pack(side='right', padx=5)
        perf_entry = tk.Entry(add_frame, textvariable=new_perf_var, font=self.fonts['normal'], width=12)
        perf_entry.pack(side='right', padx=5)
        def add_emp():
            name = new_emp_var.get().strip()
            perf = new_perf_var.get().strip()
            if not name or not perf:
                messagebox.showerror("خطأ", "يجب إدخال اسم الموظف ورقم الأداء.")
                return
            # تحقق أن رقم الأداء عدد صحيح موجب
            try:
                perf_int = int(perf)
                if perf_int <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("خطأ", "رقم الأداء يجب أن يكون عددًا صحيحًا موجبًا.")
                perf_entry.focus_set()
                return
            # تحقق من تفرد رقم الأداء
            try:
                conn = sqlite3.connect(enhanced_db.db_name)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM employees WHERE performance_number = ?", (perf_int,))
                exists = cursor.fetchone()[0]
                conn.close()
                if exists:
                    messagebox.showerror("خطأ", "رقم الأداء مستخدم بالفعل لموظف آخر.")
                    perf_entry.focus_set()
                    return
            except Exception:
                pass
            if hasattr(enhanced_db, 'add_employee'):
                success = enhanced_db.add_employee(name, "موظف", perf_int)
                if success:
                    emp_listbox.insert('end', f"{name} - {perf_int}")
                    new_emp_var.set('')
                    new_perf_var.set('')
                    self.show_notification(f"تم إضافة الموظف: {name}", notification_type="success")
                else:
                    messagebox.showerror("خطأ", "فشل في إضافة الموظف. تأكد من عدم تكرار رقم الأداء.")
        tk.Button(add_frame, text="إضافة", command=add_emp, font=self.fonts['button'], bg='#27ae60', fg='white').pack(side='right', padx=5)
        # حذف موظف
        def del_emp():
            sel = emp_listbox.curselection()
            if sel:
                idx = sel[0]
                entry = emp_listbox.get(idx)
                name = entry.split(' - ')[0].strip()
                # جلب id الموظف من قاعدة البيانات
                employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
                emp_id = None
                for emp in employees:
                    if emp[1] == name:
                        emp_id = emp[0]
                        break
                if emp_id and hasattr(enhanced_db, 'delete_employee'):
                    enhanced_db.delete_employee(emp_id)
                emp_listbox.delete(idx)
                self.show_notification(f"تم حذف الموظف: {name}", notification_type="warning")
        tk.Button(win, text="حذف المحدد", command=del_emp, font=self.fonts['button'], bg='#e74c3c', fg='white').pack(pady=5)
        tk.Button(win, text="إغلاق", command=win.destroy).pack(pady=20)

    

    def on_search_type_change(self, event=None):
        # إزالة أي كومبو بوكس سابق
        if self.search_combo:
            self.search_combo.destroy()
            self.search_combo = None
        search_type = self.search_type_var.get()
        parent = self.search_entry.master
        if search_type == "تصنيف المشكلة":
            categories = enhanced_db.get_categories() if hasattr(enhanced_db, 'get_categories') else []
            category_names = [cat[1] for cat in categories]
            self.search_value_var.set("")
            self.search_combo = ttk.Combobox(parent, values=category_names, textvariable=self.search_value_var, state='readonly')
            self.search_combo.pack(fill='x')
            self.search_combo.bind('<<ComboboxSelected>>', self.perform_search)
            self.search_entry.pack_forget()
        elif search_type == "حالة المشكلة":
            status_options = enhanced_db.get_status_options() if hasattr(enhanced_db, 'get_status_options') else []
            status_names = [s[0] for s in status_options]
            self.search_value_var.set("")
            self.search_combo = ttk.Combobox(parent, values=status_names, textvariable=self.search_value_var, state='readonly')
            self.search_combo.pack(fill='x')
            self.search_combo.bind('<<ComboboxSelected>>', self.perform_search)
            self.search_entry.pack_forget()
        elif search_type == "اسم الموظف":
            # اجلب كل أسماء الموظفين من قاعدة البيانات (وليس فقط من عدلوا الحالات)
            employee_names = [emp[1] for emp in enhanced_db.get_employees()]
            self.search_value_var.set("")
            self.search_combo = ttk.Combobox(parent, values=employee_names, textvariable=self.search_value_var, state='readonly')
            self.search_combo.pack(fill='x')
            self.search_combo.bind('<<ComboboxSelected>>', self.perform_search)
            self.search_entry.pack_forget()
        else:
            if not self.search_entry.winfo_ismapped():
                self.search_entry.pack(fill='x')
            self.search_value_var.set("")
            if self.search_combo:
                self.search_combo.destroy()
                self.search_combo = None
        self.perform_search()

    def add_attachment(self):
        if not self.current_case_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار أو حفظ حالة أولاً.")
            return

        # 1. نافذة اختيار الملف
        file_path = filedialog.askopenfilename(title="اختر الملف المرفق")
        if not file_path:
            return

        # 2. نافذة اختيار الإجراء (ربط أو نسخ)
        choice = self.ask_attachment_action()
        if not choice:
            return

        # 3. نافذة إدخال الوصف والموظف
        details = self.ask_attachment_details()
        if not details:
            return

        description = details['description']
        emp_name = details['emp_name']
        file_info = None

        # 4. تنفيذ الإجراء
        if choice == 'link':
            file_info = self.file_manager.get_attachment_info(file_path, description)
        elif choice == 'copy':
            attachments_path = self.settings.get('attachments_path')
            if not attachments_path or not os.path.isdir(attachments_path):
                messagebox.showerror("خطأ في الإعدادات", "يرجى تحديد مسار صحيح لحفظ المرفقات من قائمة الإعدادات أولاً.")
                return
            file_info = self.file_manager.copy_file_to_dedicated_folder(file_path, self.current_case_id, attachments_path, description)

        # 5. حفظ في قاعدة البيانات
        if file_info:
            self.save_attachment_to_db(file_info, emp_name)

    def ask_attachment_action(self):
        """نافذة منبثقة لسؤال المستخدم عن نوع الإجراء (ربط أو نسخ)."""
        win = tk.Toplevel(self.root)
        win.title("اختر إجراء")
        win.geometry("350x150")
        win.transient(self.root) # تبقى فوق النافذة الرئيسية
        win.grab_set() # تمنع التفاعل مع النافذة الرئيسية

        result = tk.StringVar()

        tk.Label(win, text="كيف تريد إضافة المرفق؟", font=self.fonts['subheader']).pack(pady=15)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        def set_choice(choice):
            result.set(choice)
            win.destroy()

        link_btn = tk.Button(btn_frame, text="🔗 ربط بالملف الأصلي", command=lambda: set_choice('link'), width=20, height=2)
        link_btn.pack(side='right', padx=10)

        copy_btn = tk.Button(btn_frame, text="📋 نسخ للمجلد المخصص", command=lambda: set_choice('copy'), width=20, height=2)
        copy_btn.pack(side='right', padx=10)

        self.root.wait_window(win) # انتظار إغلاق النافذة
        return result.get()

    def ask_attachment_details(self):
        """نافذة لإدخال الوصف واسم الموظف."""
        win = tk.Toplevel(self.root)
        win.title("تفاصيل المرفق")
        win.geometry("400x200")
        win.transient(self.root)
        win.grab_set()

        details = {}

        tk.Label(win, text="الوصف:", font=self.fonts['normal']).pack(pady=(10, 0))
        desc_var = tk.StringVar()
        tk.Entry(win, textvariable=desc_var, font=self.fonts['normal']).pack(fill='x', padx=20)

        tk.Label(win, text="الموظف المسؤول:", font=self.fonts['normal']).pack(pady=(10, 0))
        emp_names = [emp[1] for emp in enhanced_db.get_employees()]
        emp_var = tk.StringVar(value=emp_names[0] if emp_names else "")
        emp_combo = ttk.Combobox(win, values=emp_names, textvariable=emp_var, state='readonly')
        emp_combo.pack(fill='x', padx=20)

        def save_details():
            details['description'] = desc_var.get().strip()
            details['emp_name'] = emp_var.get()
            win.destroy()

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="حفظ", command=save_details, width=12).pack(side='right', padx=10)
        tk.Button(btn_frame, text="إلغاء", command=win.destroy, width=12).pack(side='right')

        self.root.wait_window(win)
        return details if 'description' in details else None

    def save_attachment_to_db(self, file_info, emp_name):
        """حفظ معلومات المرفق في قاعدة البيانات (نسخة مصححة)."""
        # البحث عن هوية الموظف
        emp_id = None
        employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
        for emp in employees:
            if emp[1] == emp_name:
                emp_id = emp[0]
                break
        
        # إنشاء قاموس بيانات نقي ومباشر لقاعدة البيانات
        db_data = {
            'case_id': self.current_case_id,
            'file_name': file_info.get('file_name'),
            'file_path': file_info.get('file_path'),
            'file_type': file_info.get('file_type'),
            'description': file_info.get('description'),
            'upload_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'uploaded_by': emp_id if emp_id else 1 # استخدام ID الموظف
        }

        # التحقق من أن المسار سليم قبل الحفظ
        if not db_data['file_path'] or not isinstance(db_data['file_path'], str):
            messagebox.showerror("خطأ فادح", "حدث خطأ أثناء معالجة مسار الملف. لم يتم حفظ المرفق.")
            return

        if hasattr(enhanced_db, 'add_attachment'):
            enhanced_db.add_attachment(db_data)
        
        if hasattr(enhanced_db, 'log_action'):
            is_linked = True
            try:
                # إذا كان مسار الملف يبدأ بمسار المرفقات المخصص، فهو منسوخ
                attachments_path = self.settings.get('attachments_path')
                if attachments_path and db_data['file_path'].startswith(os.path.abspath(attachments_path)):
                    is_linked = False
            except Exception:
                pass 

            action_type = "ربط مرفق" if is_linked else "نسخ مرفق"
            desc = f"تم {action_type.split(' ')[0]} المرفق: {db_data.get('file_name')} بواسطة {emp_name}"
            enhanced_db.log_action(self.current_case_id, action_type, desc, db_data['uploaded_by'])
        
        self.load_attachments()
        self.show_notification("تمت معالجة المرفق بنجاح", notification_type="success")

    def open_attachment(self, event=None):
        selected = self.attachments_tree.selection()
        if not selected:
            return
        item = self.attachments_tree.item(selected[0])
        # المسار المخزن في قاعدة البيانات هو المسار المطلق الكامل
        full_path = item['values'][-1]
        
        print(f"[DEBUG] محاولة فتح المرفق من المسار المطلق: {full_path}")

        if os.path.exists(full_path):
            try:
                os.startfile(full_path)
            except Exception as e:
                messagebox.showerror("خطأ في الفتح", f"لم يتمكن النظام من فتح الملف.\nالمسار: {full_path}\nالخطأ: {e}")
        else:
            msg = f"الملف غير موجود في المسار التالي:\n{full_path}\n\nقد يكون الملف قد تم حذفه أو نقله. يرجى تحديث المرفق."
            messagebox.showerror("ملف غير موجود", msg)

    def show_attachment_context_menu(self, event=None):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="فتح", command=lambda: self.open_attachment())
        menu.add_command(label="حذف", command=self.delete_attachment)
        if event is not None:
            menu.tk_popup(event.x_root, event.y_root)

    def delete_attachment(self):
        selected = self.attachments_tree.selection()
        if not selected:
            return
        item = self.attachments_tree.item(selected[0])
        attachment_id = item['values'][0]
        file_name = item['values'][2]
        # تأكيد الحذف
        if not messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف المرفق '{file_name}'؟"):
            return
        # حذف من قاعدة البيانات إذا كانت الدالة متوفرة
        if hasattr(enhanced_db, 'delete_attachment'):
            enhanced_db.delete_attachment(attachment_id)
        # سجل التعديلات
        emp_name = self.employee_var.get() if hasattr(self, 'employee_var') else ""
        emp_id = None
        employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
        for emp in employees:
            if emp[1] == emp_name:
                emp_id = emp[0]
                break
        if hasattr(enhanced_db, 'log_action'):
            desc = f"تم حذف المرفق: {file_name} بواسطة {emp_name}"
            enhanced_db.log_action(self.current_case_id, "حذف مرفق", desc, emp_id if emp_id else 1)
        self.load_attachments()
        self.show_notification("تم حذف المرفق", notification_type="warning")

    def add_correspondence(self):
        if not self.current_case_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار أو حفظ حالة أولاً.")
            return
        win = tk.Toplevel(self.root)
        win.title("إضافة مراسلة")
        win.geometry("400x400")
        tk.Label(win, text="المرسل:", font=self.fonts['normal']).pack(pady=(10, 0))
        sender_var = tk.StringVar()
        tk.Entry(win, textvariable=sender_var, font=self.fonts['normal']).pack(fill='x', padx=20)
        # اختيار الموظف
        tk.Label(win, text="الموظف المسؤول:", font=self.fonts['normal']).pack(pady=(10, 0))
        emp_names = [emp[1] for emp in enhanced_db.get_employees()]
        emp_var = tk.StringVar(value=emp_names[0] if emp_names else "")
        emp_combo = ttk.Combobox(win, values=emp_names, textvariable=emp_var, state='readonly')
        emp_combo.pack(fill='x', padx=20)
        # توليد الرقمين تلقائياً
        seq_num, yearly_num = 1, 1
        if hasattr(enhanced_db, 'get_next_correspondence_numbers'):
            seq_num, yearly_num = enhanced_db.get_next_correspondence_numbers(self.current_case_id)
        tk.Label(win, text=f"رقم التسلسل: {seq_num}", font=self.fonts['normal']).pack(pady=(10, 0))
        tk.Label(win, text=f"الرقم السنوي: {yearly_num}", font=self.fonts['normal']).pack(pady=(0, 0))
        tk.Label(win, text="المحتوى:", font=self.fonts['normal']).pack(pady=10)
        content_var = tk.Text(win, height=6)
        content_var.pack(fill='x', padx=20)
        def save_corr():
            sender = sender_var.get().strip()
            content = content_var.get('1.0', tk.END).strip()
            emp_name = emp_var.get()
            emp_id = None
            employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
            for emp in employees:
                if emp[1] == emp_name:
                    emp_id = emp[0]
                    break
            if content and hasattr(enhanced_db, 'add_correspondence'):
                corr_data = {
                    'case_id': self.current_case_id,
                    'case_sequence_number': seq_num,
                    'yearly_sequence_number': yearly_num,
                    'sender': sender,
                    'message_content': content,
                    'created_by': emp_id if emp_id else 1,
                    'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'sent_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                enhanced_db.add_correspondence(corr_data)
                # سجل التعديلات
                if hasattr(enhanced_db, 'log_action'):
                    desc = f"تم إضافة مراسلة رقم {seq_num} بواسطة {emp_name}"
                    enhanced_db.log_action(self.current_case_id, "إضافة مراسلة", desc, emp_id if emp_id else 1)
                self.load_correspondences()
                win.destroy()
                self.show_notification("تمت إضافة المراسلة بنجاح", notification_type="success")
        tk.Button(win, text="حفظ", command=save_corr).pack(pady=10)
        tk.Button(win, text="إلغاء", command=win.destroy).pack()

    def edit_correspondence(self, event=None):
        selected = self.correspondences_tree.selection()
        if not selected:
            return
        item = self.correspondences_tree.item(selected[0])
        corr_id = item['values'][0]
        old_content = item['values'][4]
        win = tk.Toplevel(self.root)
        win.title("تعديل مراسلة")
        win.geometry("400x300")
        tk.Label(win, text="المحتوى:", font=self.fonts['normal']).pack(pady=10)
        content_var = tk.Text(win, height=6)
        content_var.insert('1.0', old_content)
        content_var.pack(fill='x', padx=20)
        def save_corr():
            content = content_var.get('1.0', tk.END).strip()
            if content and hasattr(enhanced_db, 'update_correspondence'):
                enhanced_db.update_correspondence(corr_id, content)
            self.load_correspondences()
            win.destroy()
            self.show_notification("تم تحديث المراسلة", notification_type="success")
        tk.Button(win, text="حفظ", command=save_corr).pack(pady=10)
        tk.Button(win, text="إلغاء", command=win.destroy).pack()

    def delete_correspondence(self):
        selected = self.correspondences_tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "يرجى اختيار مراسلة أولاً.")
            return
        item = self.correspondences_tree.item(selected[0])
        corr_id = item['values'][0]
        seq_num = item['values'][1]
        # تأكيد الحذف
        if not messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد أنك تريد حذف المراسلة رقم {seq_num}؟"):
            return
        try:
            print(f"[DEBUG] محاولة حذف مراسلة corr_id={corr_id}")
            if hasattr(enhanced_db, 'delete_correspondence'):
                enhanced_db.delete_correspondence(int(corr_id))
                print(f"[DEBUG] تم حذف المراسلة corr_id={corr_id}")
            else:
                print("[ERROR] دالة delete_correspondence غير موجودة في قاعدة البيانات!")
                messagebox.showerror("خطأ في الحذف", "دالة حذف المراسلة غير متوفرة في قاعدة البيانات.")
                return
            # سجل التعديلات
            emp_name = self.employee_var.get() if hasattr(self, 'employee_var') else ""
            emp_id = None
            employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
            for emp in employees:
                if emp[1] == emp_name:
                    emp_id = emp[0]
                    break
            if hasattr(enhanced_db, 'log_action'):
                desc = f"تم حذف مراسلة رقم {seq_num} بواسطة {emp_name}"
                enhanced_db.log_action(self.current_case_id, "حذف مراسلة", desc, emp_id if emp_id else 1)
            self.load_correspondences()
            self.show_notification("تم حذف المراسلة", notification_type="warning")
        except Exception as e:
            print(f"[ERROR] Exception أثناء حذف المراسلة: {e}")
            messagebox.showerror("خطأ في الحذف", f"حدث خطأ أثناء حذف المراسلة:\n{e}")

    def load_initial_data(self):
        self.cases_data = enhanced_db.get_all_cases() if hasattr(enhanced_db, 'get_all_cases') else []
        self.filtered_cases = self.cases_data.copy()

        # استخلاص قوائم السنوات
        self.received_years = sorted({str(case.get('received_date', '')).split('-')[0] for case in self.cases_data if case.get('received_date')}, reverse=True)
        self.created_years = sorted({str(case.get('created_date', '')).split('-')[0] for case in self.cases_data if case.get('created_date')}, reverse=True)

        self.update_cases_list()
        self.load_attachments()
        self.load_correspondences()
        self.load_audit_log()
        self.update_year_filter_options() # تحديث قائمة السنوات
        self.year_combo.set("الكل")
        
        # تحديث شريط الحالة - مع فحص وجود العناصر
        try:
            if hasattr(self, 'cases_count_label') and self.cases_count_label and self.cases_count_label.winfo_exists():
                total_cases = len(self.cases_data)
                self.cases_count_label.config(text=f"📋 جميع الحالات: {total_cases}")
        except Exception as e:
            # تجاهل الأخطاء في تحديث شريط الحالة
            pass

    def load_attachments(self):
        """تحميل مرفقات الحالة وعرضها في الجدول (النسخة المصححة)."""
        for i in self.attachments_tree.get_children():
            self.attachments_tree.delete(i)
        
        if not self.current_case_id or not hasattr(enhanced_db, 'get_attachments'):
            return

        # get_attachments تعيد الآن قائمة من القواميس (dict) بالأسماء الصحيحة
        attachments = enhanced_db.get_attachments(self.current_case_id)
        
        for att in attachments:
            # إدخال البيانات بالترتيب الصحيح والمتوقع للجدول
            self.attachments_tree.insert('', 'end', values=(
                att.get('id'),
                att.get('file_type'),
                att.get('file_name'),
                att.get('description'),
                att.get('upload_date'),
                att.get('uploaded_by_name'),
                att.get('file_path')  # المسار الكامل للملف
            ))

    def load_correspondences(self):
        for i in self.correspondences_tree.get_children():
            self.correspondences_tree.delete(i)
        if not self.current_case_id or not hasattr(enhanced_db, 'get_correspondences'):
            return
        correspondences = enhanced_db.get_correspondences(self.current_case_id)
        for corr in correspondences:
            self.correspondences_tree.insert('', 'end', values=(
                corr.get('id'),
                corr.get('case_sequence_number'),
                corr.get('yearly_sequence_number'),
                corr.get('sender'),
                corr.get('message_content'),
                corr.get('sent_date'),
                corr.get('created_by_name')
            ))

    def load_audit_log(self):
        for i in self.audit_tree.get_children():
            self.audit_tree.delete(i)
        if not self.current_case_id or not hasattr(enhanced_db, 'get_case_audit_log'):
            return
        logs = enhanced_db.get_case_audit_log(self.current_case_id)
        for log in logs:
            # log: [id, case_id, action_type, action_description, performed_by, timestamp, old_values, new_values, performed_by_name]
            emp_name = log[8] if log[8] not in [None, ''] else 'غير محدد'
            self.audit_tree.insert('', 'end', values=(
                log[5],  # timestamp
                emp_name,  # performed_by_name (اسم الموظف)
                log[2],  # action_type
                log[3]   # action_description
            ))

    def print_case(self):
        if not self.current_case_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار حالة أولاً.")
            return
        # دعم dict وtuple
        case = None
        for c in self.cases_data:
            try:
                if isinstance(c, dict):
                    cid = c.get('id')
                    if cid is None or not str(cid).isdigit():
                        continue
                    if int(str(cid)) == int(str(self.current_case_id)):
                        case = c
                        break
                elif isinstance(c, tuple):
                    cid = c[0]
                    if cid is None or not str(cid).isdigit():
                        continue
                    if int(str(cid)) == int(str(self.current_case_id)):
                        keys = ['id', 'customer_name', 'subscriber_number', 'status', 'category_name', 'color_code', 'modified_by_name', 'created_date', 'modified_date']
                        case = dict(zip(keys, c))
                        break
            except Exception:
                continue
        if not case:
            messagebox.showerror("خطأ", "تعذر العثور على بيانات الحالة.")
            return
        temp_path = os.path.join(os.getcwd(), f"case_{self.current_case_id}_print.txt")
        # تعريب الحقول
        field_map = {
            'id': 'رقم الحالة',
            'customer_name': 'اسم العميل',
            'subscriber_number': 'رقم المشترك',
            'phone': 'رقم الهاتف',
            'address': 'العنوان',
            'category_name': 'تصنيف المشكلة',
            'status': 'حالة المشكلة',
            'problem_description': 'وصف المشكلة',
            'actions_taken': 'ما تم تنفيذه',
            'last_meter_reading': 'آخر قراءة للعداد',
            'last_reading_date': 'تاريخ آخر قراءة',
            'debt_amount': 'المديونية',
            'created_date': 'تاريخ الإضافة',
            'modified_date': 'تاريخ التعديل',
            'created_by_name': 'أضيف بواسطة',
            'modified_by_name': 'آخر معدل',
            'solved_by_name': 'تم الحل بواسطة',
        }
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write("========== تقرير حالة عميل ==========" + "\n\n")
            f.write("--- بيانات الحالة ---\n")
            for k, v in case.items():
                label = field_map.get(k, k)
                f.write(f"{label}: {v if v is not None else ''}\n")
            f.write("\n--- المرفقات ---\n")
            attachments = enhanced_db.get_attachments(self.current_case_id) if hasattr(enhanced_db, 'get_attachments') else []
            if attachments:
                for att in attachments:
                    f.write(f"ملف: {att.get('file_name', '')} | الوصف: {att.get('description', '')} | التاريخ: {att.get('upload_date', '')}\n")
            else:
                f.write("لا يوجد مرفقات\n")
            f.write("\n--- المراسلات ---\n")
            correspondences = enhanced_db.get_correspondences(self.current_case_id) if hasattr(enhanced_db, 'get_correspondences') else []
            if correspondences:
                for corr in correspondences:
                    f.write(f"مرسل: {corr.get('sender', '')} | التاريخ: {corr.get('created_date', '')}\nالمحتوى: {corr.get('message_content', '')}\n---\n")
            else:
                f.write("لا يوجد مراسلات\n")
            f.write("\n--- سجل التعديلات ---\n")
            audit_log = enhanced_db.get_case_audit_log(self.current_case_id) if hasattr(enhanced_db, 'get_case_audit_log') else []
            if audit_log:
                for log in audit_log:
                    if isinstance(log, dict):
                        f.write(f"{log.get('action_type', '')} | {log.get('action_description', '')} | {log.get('performed_by_name', '')} | {log.get('timestamp', '')}\n")
                    elif isinstance(log, tuple):
                        # ترتيب الأعمدة: [id, case_id, action_type, action_description, performed_by, timestamp, old_values, new_values, performed_by_name]
                        f.write(f"{log[2]} | {log[3]} | {log[8]} | {log[5]}\n")
            else:
                f.write("لا يوجد سجل تعديلات\n")
        try:
            os.startfile(temp_path, 'print')
            self.show_notification("تم إرسال التقرير للطباعة بنجاح", notification_type="success")
        except Exception as e:
            self.show_notification(f"خطأ في الطباعة: {str(e)}", notification_type="error")
            messagebox.showerror("خطأ في الطباعة", f"حدث خطأ أثناء الطباعة:\n{e}")

    def update_cases_list(self):
        """
        تحديث عرض قائمة الحالات
        """
        try:
            if self.scrollable_frame is None or not self.scrollable_frame.winfo_exists():
                return
                
            # تنظيف القائمة الحالية
            for widget in self.scrollable_frame.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass
            self.case_card_widgets = []
            
            # عرض الحالات المفلترة كبطاقات
            for i, case in enumerate(self.filtered_cases):
                try:
                    self.add_case_card(case)
                except Exception as e:
                    # تجاهل الأخطاء في إضافة البطاقات الفردية
                    continue
            
            # تحديث منطقة التمرير
            try:
                if hasattr(self, 'cases_canvas') and self.cases_canvas and self.cases_canvas.winfo_exists():
                    self.scrollable_frame.update_idletasks()
                    self.cases_canvas.configure(scrollregion=self.cases_canvas.bbox("all"))
            except Exception:
                pass
            
            # تمييز البطاقة المحددة
            try:
                self._highlight_selected_case_card()
            except Exception:
                pass
                
        except Exception as e:
            # تجاهل الأخطاء في تحديث قائمة الحالات
            pass

    def save_changes(self):
        """حفظ أو تحديث بيانات الحالة في قاعدة البيانات"""
        if not messagebox.askyesno("تأكيد الحفظ", "هل أنت متأكد أنك تريد حفظ التغييرات؟"):
            return
        data = {}
        for key, widget in self.basic_data_widgets.items():
            if isinstance(widget, tk.Entry) or isinstance(widget, ttk.Combobox):
                var = self.basic_data_widgets.get(key + '_var')
                if var:
                    data[key] = var.get().strip()
                else:
                    data[key] = widget.get().strip()
            elif isinstance(widget, tk.Text):
                data[key] = widget.get('1.0', tk.END).strip()
        # logging.info(f"[DEBUG] القيم المجمعة من الواجهة: {data}")
        # معالجة الحقول المطلوبة
        required_fields = ['customer_name', 'subscriber_number']
        for field in required_fields:
            if not data.get(field):
                messagebox.showerror("خطأ في الإدخال", f"حقل '{field}' مطلوب.")
                return

        # تأكد من وجود جميع الحقول الخاصة بالمشكلة حتى لو كانت فارغة
        for field in ['problem_description', 'actions_taken', 'last_meter_reading', 'last_reading_date', 'debt_amount']:
            if field not in data:
                data[field] = ''

        # سجل محتوى البيانات قبل الحفظ للتشخيص
        # logging.info(f"[DEBUG] بيانات سيتم حفظها: {data}")
        # معالجة تصنيف المشكلة (category) وتحويله إلى category_id
        if 'category' in data:
            category_name = data['category']
            category_id = None
            for cat in enhanced_db.get_categories():
                if cat[1] == category_name:
                    category_id = cat[0]
                    break
            if category_id is None:
                category_id = 1  # قيمة افتراضية إذا لم يوجد التصنيف
            data['category_id'] = category_id
        # معالجة حالة المشكلة (status)
        if 'status' in data:
            data['status'] = data['status'] or 'جديدة'
            # التحقق إذا تم حل المشكلة
            if data['status'] == "تم حلها" and self.current_case_status != "تم حلها":
                # يجب تعريف emp_id و now هنا
                emp_id = 1
                emp_name = data.get('employee_name')
                employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
                for emp in employees:
                    if emp[1] == emp_name:
                        emp_id = emp[0]
                        break
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data['solved_by'] = emp_id
                data['solved_date'] = now
        # إضافة تواريخ الإنشاء والتعديل
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emp_id = 1
        emp_name = data.get('employee_name')
        employees = enhanced_db.get_employees() if hasattr(enhanced_db, 'get_employees') else []
        for emp in employees:
            if emp[1] == emp_name:
                emp_id = emp[0]
                break

        # تجميع تاريخ الورود
        year = self.year_received_var.get()
        month = self.month_received_var.get()
        day = datetime.now().day # استخدم اليوم الحالي كقيمة افتراضية
        received_date_str = f"{year}-{month}-{day:02d}"
        try:
            received_date = datetime.strptime(received_date_str, "%Y-%m-%d")
            data['received_date'] = received_date.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            messagebox.showerror("خطأ في التاريخ", "صيغة تاريخ الورود غير صحيحة.")
            return
        # إزالة الحقول المؤقتة من القاموس قبل الحفظ
        data.pop('category', None)
        data.pop('year_received', None)
        data.pop('month_received', None)

        # التحقق من تعديل تاريخ الورود بعد الحفظ الأول
        if self.current_case_id and self.original_received_date and self.original_received_date != data['received_date']:
            if not messagebox.askyesno("تأكيد تعديل تاريخ الورود", "لقد قمت بتعديل تاريخ ورود الشكوى. هل أنت متأكد من هذا الإجراء؟"):
                return # إلغاء الحفظ إذا رفض المستخدم

        if self.current_case_id is None:
            data['created_date'] = now
            data['modified_date'] = now
            data['created_by'] = emp_id
            data['modified_by'] = emp_id
            new_id = enhanced_db.add_case(data)
            self.current_case_id = new_id
            # سجل التعديلات
            if hasattr(enhanced_db, 'log_action'):
                enhanced_db.log_action(self.current_case_id, "إنشاء", "تم إنشاء الحالة", emp_id)
            self.show_notification("تمت إضافة الحالة بنجاح", notification_type="success")
        else:
            data['modified_date'] = now
            data['modified_by'] = emp_id
            enhanced_db.update_case(self.current_case_id, data)
            # سجل التعديلات
            if hasattr(enhanced_db, 'log_action'):
                enhanced_db.log_action(self.current_case_id, "تحديث", "تم تحديث بيانات الحالة", emp_id)
            self.show_notification("تم تحديث بيانات الحالة بنجاح", notification_type="success")
        self.save_btn.config(state='disabled')
        self.print_btn.config(state='normal')
        
        # إعادة تحميل المرفقات والمراسلات وسجل التعديلات للحالة الحالية
        if hasattr(self, 'functions') and self.functions is not None:
            if hasattr(self.functions, 'load_case_attachments'):
                self.functions.load_case_attachments(self.current_case_id)
            if hasattr(self.functions, 'load_case_correspondences'):
                self.functions.load_case_correspondences(self.current_case_id)
            if hasattr(self.functions, 'load_case_audit_log'):
                self.functions.load_case_audit_log(self.current_case_id)
        
        # تحديث البيانات بطريقة آمنة بدون إعادة إنشاء الواجهة
        try:
            if hasattr(self, 'root') and self.root and self.root.winfo_exists():
                # تحديث البيانات الأساسية فقط
                self.cases_data = enhanced_db.get_all_cases() if hasattr(enhanced_db, 'get_all_cases') else []
                self.filtered_cases = self.cases_data.copy()
                
                # تحديث قائمة الحالات
                self.update_cases_list()
                
                # تحديث شريط الحالة
                try:
                    if hasattr(self, 'cases_count_label') and self.cases_count_label and self.cases_count_label.winfo_exists():
                        total_cases = len(self.cases_data)
                        self.cases_count_label.config(text=f"📋 جميع الحالات: {total_cases}")
                except Exception:
                    pass
                
                # تحديث قوائم السنوات
                self.received_years = sorted({str(case.get('received_date', '')).split('-')[0] for case in self.cases_data if case.get('received_date')}, reverse=True)
                self.created_years = sorted({str(case.get('created_date', '')).split('-')[0] for case in self.cases_data if case.get('created_date')}, reverse=True)
                
                # تحديث خيارات السنة
                self.update_year_filter_options()
                
        except Exception as e:
            # في حالة حدوث خطأ، حاول إعادة تحميل البيانات بعد فترة قصيرة
            self.root.after(100, self.load_initial_data)

    def perform_search(self, event=None):
        """تنفيذ البحث وتحديث قائمة الحالات"""
        search_type = self.search_type_var.get()
        search_value = self.search_value_var.get().strip()
        year = self.year_var.get()
        date_field_display = self.date_field_var.get()
        date_field = self.date_field_map.get(date_field_display, 'received_date')

        try:
            # إذا لم يكن هناك قيمة للبحث ولم يتم تحديد سنة، اعرض كل الحالات
            if not search_value and year == "الكل":
                self.filtered_cases = self.cases_data.copy()
            else:
                # استدعاء دالة البحث المحدثة
                self.filtered_cases = enhanced_db.search_cases(search_type, search_value, year, date_field)
            
            # إعادة تعيين الفهرس المحدد
            self.selected_case_index = 0
            self.update_cases_list()
            
            # عرض عدد النتائج
            result_count = len(self.filtered_cases)
            if search_value or year != "الكل":
                self.show_notification(f"تم العثور على {result_count} حالة", notification_type="info")
            
        except Exception as e:
            self.show_notification(f"خطأ في البحث: {str(e)}", notification_type="error")
            messagebox.showerror("خطأ في البحث", f"حدث خطأ أثناء البحث:\n{e}")
            # في حالة الخطأ، اعرض جميع الحالات
            self.filtered_cases = self.cases_data.copy()
            self.update_cases_list()

    def on_closing(self):
        """معالجة حدث إغلاق النافذة"""
        if messagebox.askokcancel("خروج", "هل تريد الخروج من النظام؟"):
            try:
                self.is_closing = True
                # إنشاء نسخة احتياطية قبل الإغلاق
                if hasattr(self, 'file_manager'):
                    self.file_manager.cleanup_old_backups()
                self.show_notification("جاري إغلاق النظام...", notification_type="info")
                self.root.after(1000, self.root.destroy)
            except Exception as e:
                print(f"خطأ أثناء الإغلاق: {e}")
                self.root.destroy()
    
    def show_dashboard(self):
        """عرض لوحة التحكم الرئيسية (نسخة محسنة تدعم الاستجابة)"""
        self.clear_root()
        self.show_notification("مرحباً بك في لوحة التحكم الرئيسية", notification_type="info")

        dash_frame = tk.Frame(self.root, bg=self.colors['bg_main'])
        dash_frame.pack(fill='both', expand=True, padx=10, pady=10)
        dash_frame.rowconfigure(2, weight=1)
        dash_frame.columnconfigure(0, weight=1)

        # العنوان الرئيسي
        title_label = tk.Label(dash_frame, text="🏠 لوحة عرض الحالات - نظام إدارة مشاكل العملاء",
                              font=self.fonts['header'], fg=self.colors['text_main'],
                              bg=self.colors['bg_main'], anchor='e', justify='right')
        title_label.grid(row=0, column=0, sticky='ew', pady=(10, 15), padx=10)

        # إطار الإحصائيات
        stats_frame = tk.Frame(dash_frame, bg=self.colors['bg_card'], relief='solid', bd=1)
        stats_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))
        stats_frame.columnconfigure(0, weight=1)

        # حساب الإحصائيات
        cases = enhanced_db.get_all_cases() if hasattr(enhanced_db, 'get_all_cases') else []
        total_cases = len(cases)
        active_cases = len([case for case in cases if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) not in ['تم حلها', 'مغلقة']])
        solved_cases = len([case for case in cases if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) == 'تم حلها'])

        # إطار للإحصائيات مع تصميم محسن
        stats_inner_frame = tk.Frame(stats_frame, bg=self.colors['bg_card'])
        stats_inner_frame.pack(expand=True, fill='both', padx=15, pady=15)
        stats_inner_frame.columnconfigure(0, weight=1)
        stats_inner_frame.columnconfigure(1, weight=1)
        stats_inner_frame.columnconfigure(2, weight=1)

        # إحصائيات منفصلة مع أيقونات
        total_label = tk.Label(stats_inner_frame, text=f"📊 إجمالي الحالات: {total_cases}",
                              font=self.fonts['subheader'], fg=self.colors['text_main'],
                              bg=self.colors['bg_card'], anchor='center')
        total_label.grid(row=0, column=0, sticky='ew', padx=5)

        active_label = tk.Label(stats_inner_frame, text=f"🔄 الحالات النشطة: {active_cases}",
                               font=self.fonts['subheader'], fg='#e67e22',
                               bg=self.colors['bg_card'], anchor='center')
        active_label.grid(row=0, column=1, sticky='ew', padx=5)

        solved_label = tk.Label(stats_inner_frame, text=f"✅ الحالات المحلولة: {solved_cases}",
                               font=self.fonts['subheader'], fg='#27ae60',
                               bg=self.colors['bg_card'], anchor='center')
        solved_label.grid(row=0, column=2, sticky='ew', padx=5)

        # جدول الحالات النشطة
        tree_frame = tk.Frame(dash_frame, bg=self.colors['bg_main'])
        tree_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=(0, 10))
        tree_frame.rowconfigure(1, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        tree_title = tk.Label(tree_frame, text="الحالات النشطة",
                             font=self.fonts['subheader'], fg=self.colors['text_main'],
                             bg=self.colors['bg_main'], anchor='e', justify='right')
        tree_title.grid(row=0, column=0, sticky='ew', pady=(0, 5))



        columns = ("اسم العميل", "رقم المشترك", "تصنيف المشكلة", "حالة المشكلة", "تاريخ الإضافة")
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col, anchor='e')
            tree.column(col, anchor='e', stretch=True, width=120, minwidth=80)

        # Scrollbar رأسي
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.grid(row=1, column=0, sticky='nsew')
        scrollbar.grid(row=1, column=1, sticky='ns')

        # تحميل البيانات - عرض فقط الحالات النشطة
        filtered_cases = [case for case in cases if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) not in ['تم حلها', 'مغلقة']]
        for case in filtered_cases:
            item = tree.insert('', 'end', values=(
                case.get('customer_name', '') if isinstance(case, dict) else case[1],
                case.get('subscriber_number', '') if isinstance(case, dict) else case[2],
                case.get('category_name', '') if isinstance(case, dict) else case[4],
                case.get('status', '') if isinstance(case, dict) else case[3],
                case.get('created_date', '') if isinstance(case, dict) else case[7]
            ))
            # ربط النقر على الحالة للانتقال إليها
            tree.tag_bind(item, '<Double-Button-1>', lambda e, c=case: self.load_case_from_dashboard(c))

        # أزرار التحكم
        buttons_frame = tk.Frame(dash_frame, bg=self.colors['bg_main'])
        buttons_frame.grid(row=3, column=0, sticky='ew', pady=10, padx=10)
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)

        # إطار للأزرار مع توزيع أفضل
        buttons_inner_frame = tk.Frame(buttons_frame, bg=self.colors['bg_main'])
        buttons_inner_frame.pack(expand=True)
        buttons_inner_frame.columnconfigure(0, weight=1)
        buttons_inner_frame.columnconfigure(1, weight=1)
        buttons_inner_frame.columnconfigure(2, weight=1)

        enter_btn = tk.Button(buttons_inner_frame, text="🚀 دخول للنظام",
                             command=self.show_main_window,
                             font=self.fonts['button'], bg=self.colors['button_action'], fg='white',
                             relief='flat', padx=30, pady=15)
        enter_btn.grid(row=0, column=2, sticky='ew', padx=5)
        self.create_tooltip(enter_btn, "الانتقال إلى النظام الرئيسي")

        settings_btn = tk.Button(buttons_inner_frame, text="⚙️ الإعدادات",
                                command=self.show_settings_window,
                                font=self.fonts['button'], bg=self.colors['button_secondary'], fg='white',
                                relief='flat', padx=30, pady=15)
        settings_btn.grid(row=0, column=1, sticky='ew', padx=5)
        self.create_tooltip(settings_btn, "إعدادات النظام")

        exit_btn = tk.Button(buttons_inner_frame, text="🚪 خروج",
                            command=self.on_closing,
                            font=self.fonts['button'], bg='#e74c3c', fg='white',
                            relief='flat', padx=30, pady=15)
        exit_btn.grid(row=0, column=0, sticky='ew', padx=5)
        self.create_tooltip(exit_btn, "إغلاق النظام")

        # دعم تغيير الحجم التلقائي للأعمدة عند تغيير حجم النافذة
        def on_resize(event=None):
            total_width = tree_frame.winfo_width() - 20
            col_count = len(columns)
            if total_width > 0:
                for col in columns:
                    tree.column(col, width=max(int(total_width / col_count), 80))

        tree_frame.bind('<Configure>', on_resize)
        self.root.update_idletasks()
        on_resize()

    def load_case_from_dashboard(self, case):
        """الانتقال من الـ dashboard إلى الحالة المحددة"""
        # حفظ الحالة المحددة للتحميل لاحقاً
        self.pending_dashboard_case = case
        
        # الانتقال إلى النافذة الرئيسية
        self.show_main_window()
        
        # إشعار المستخدم
        customer_name = case.get('customer_name', '') if isinstance(case, dict) else case[1] if len(case) > 1 else ''
        self.show_notification(f"جاري تحميل حالة العميل: {customer_name}", notification_type="info")
    


    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_main_window(self):
        self.clear_root()
        # إعادة إنشاء القوائم المنسدلة وشريط الأدوات
        self.create_menu_bar()
        self.create_toolbar()
        self.create_main_layout()
        self.create_status_bar()
        self.after_main_layout()

    def run(self):
        self.show_dashboard()
        self.root.mainloop()

    def load_case(self, case):
        """تحميل بيانات الحالة المختارة في النموذج"""
        try:
            # جلب بيانات الحالة كاملة من قاعدة البيانات
            case_id = None
            if isinstance(case, dict):
                case_id = case.get('id')
            elif isinstance(case, (list, tuple)) and len(case) > 0:
                case_id = case[0]
            else:
                case_id = case
            
            if not case_id:
                self.show_notification("خطأ: معرف الحالة غير صحيح", notification_type="error")
                return
            
            # جلب البيانات الكاملة من قاعدة البيانات
            full_case = None
            if hasattr(enhanced_db, 'get_case_details'):
                full_case = enhanced_db.get_case_details(case_id)
            
            # إذا لم نتمكن من جلب البيانات الكاملة، استخدم البيانات المتوفرة
            if not full_case:
                # البحث في البيانات المحملة
                for c in self.cases_data:
                    current_id = None
                    if isinstance(c, dict):
                        current_id = c.get('id')
                    elif isinstance(c, (list, tuple)) and len(c) > 0:
                        current_id = c[0]
                    
                    if current_id == case_id:
                        full_case = c
                        break
            
            if not full_case:
                self.show_notification("تعذر العثور على بيانات الحالة", notification_type="error")
                return
            
            # تحديث المتغيرات
            self.current_case_id = case_id
            
            # استخراج البيانات بشكل آمن
            if isinstance(full_case, dict):
                self.original_received_date = full_case.get('received_date')
                self.current_case_status = full_case.get('status')
                customer_name = full_case.get('customer_name', '')
                modified_by_name = full_case.get('modified_by_name', '')
            else:
                # إذا كانت البيانات tuple
                self.original_received_date = full_case[7] if len(full_case) > 7 else None
                self.current_case_status = full_case[3] if len(full_case) > 3 else ''
                customer_name = full_case[1] if len(full_case) > 1 else ''
                modified_by_name = full_case[6] if len(full_case) > 6 else ''
            
            # تعبئة الحقول
            for key, widget in self.basic_data_widgets.items():
                if key == 'category':
                    continue  # عالج التصنيف بعد الحلقة فقط
                
                # استخراج القيمة بشكل آمن
                value = ''
                if isinstance(full_case, dict):
                    value = full_case.get(key, '')
                else:
                    # خريطة للحقول في tuple
                    field_map = {
                        'customer_name': 1,
                        'subscriber_number': 2,
                        'phone': None,  # قد لا يكون موجود في tuple
                        'address': None,
                        'status': 3,
                        'problem_description': None,
                        'actions_taken': None,
                        'last_meter_reading': None,
                        'last_reading_date': None,
                        'debt_amount': None
                    }
                    idx = field_map.get(key)
                    if idx is not None and len(full_case) > idx:
                        value = full_case[idx]
                
                # تعبئة الحقل
                if isinstance(widget, tk.Entry):
                    widget.delete(0, tk.END)
                    widget.insert(0, str(value) if value is not None else '')
                elif isinstance(widget, ttk.Combobox):
                    widget.set(str(value) if value is not None else '')
                elif isinstance(widget, tk.Text):
                    widget.delete('1.0', tk.END)
                    widget.insert('1.0', str(value) if value is not None else '')
            
            # تحديث العناوين
            self.customer_name_label.config(text=customer_name)
            self.solved_by_label.config(text=modified_by_name)
            
            # تفعيل الأزرار
            self.save_btn.config(state='normal')
            self.print_btn.config(state='normal')
            
            # تحميل البيانات المرتبطة
            self.load_attachments()
            self.load_correspondences()
            self.load_audit_log()
            
            # تعبئة التصنيف بالاسم فقط
            if 'category' in self.basic_data_widgets:
                category_combo = self.basic_data_widgets['category']
                category_name = ''
                if isinstance(full_case, dict):
                    category_name = full_case.get('category_name', '')
                else:
                    category_name = full_case[4] if len(full_case) > 4 else ''
                
                if category_name:
                    options = list(category_combo['values'])
                    if category_name not in options:
                        category_combo['values'] = options + [category_name]
                    category_combo.set(category_name)
            
            # سنة وشهر الورود
            received_date = self.original_received_date
            if received_date:
                try:
                    if isinstance(received_date, str):
                        received_dt = datetime.strptime(received_date, "%Y-%m-%d %H:%M:%S")
                    else:
                        received_dt = received_date
                    self.year_received_var.set(str(received_dt.year))
                    self.month_received_var.set(f"{received_dt.month:02d}")
                except (ValueError, TypeError):
                    # في حال كان الحقل فارغاً أو بصيغة غير متوقعة
                    self.year_received_var.set(str(datetime.now().year))
                    self.month_received_var.set(f"{datetime.now().month:02d}")
            else:
                # إذا لم يكن هناك تاريخ ورود، استخدم التاريخ الحالي
                self.year_received_var.set(str(datetime.now().year))
                self.month_received_var.set(f"{datetime.now().month:02d}")

            # تحديث أزرار العمليات
            self.update_action_buttons_style()
            
            # تحديث البطاقة المحددة
            self._update_selected_case_index(case_id)
            
            # تحديد تبويب البيانات الأساسية
            if hasattr(self, 'notebook'):
                self.notebook.select(4)  # التبويب الأخير (البيانات الأساسية)
            
            self.show_notification(f"تم تحميل حالة: {customer_name}", notification_type="info")
            
        except Exception as e:
            self.show_notification(f"خطأ في تحميل الحالة: {str(e)}", notification_type="error")
            print(f"خطأ في تحميل الحالة: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_selected_case_index(self, case_id):
        """تحديث فهرس البطاقة المحددة"""
        try:
            for i, case in enumerate(self.filtered_cases):
                current_id = None
                if isinstance(case, dict):
                    current_id = case.get('id')
                elif isinstance(case, (list, tuple)) and len(case) > 0:
                    current_id = case[0]
                
                if current_id == case_id:
                    self.selected_case_index = i
                    self._highlight_selected_case_card()
                    break
        except Exception:
            pass

    def delete_case(self):
        """حذف الحالة الحالية وكل بياناتها"""
        if not self.current_case_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار حالة أولاً.")
            return
        if not messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد أنك تريد حذف هذه الحالة وكل بياناتها؟ لا يمكن التراجع!"):
            return
        try:
            if hasattr(enhanced_db, 'delete_case'):
                enhanced_db.delete_case(self.current_case_id)
            # حذف ملفات المرفقات من النظام
            case_folder = os.path.join('files', f"case_{self.current_case_id}")
            if os.path.exists(case_folder):
                import shutil
                shutil.rmtree(case_folder)
            self.show_notification("تم حذف الحالة وكل بياناتها بنجاح", notification_type="warning")
            self.current_case_id = None
            self.load_initial_data()
            self.save_btn.config(state='disabled')
            self.print_btn.config(state='disabled')
            self.customer_name_label.config(text="اختر حالة من القائمة")
            self.solved_by_label.config(text="")
        except Exception as e:
            messagebox.showerror("خطأ في الحذف", f"حدث خطأ أثناء حذف الحالة:\n{e}")

    def show_all_cases_window(self):
        """عرض جميع الحالات في نافذة منفصلة"""
        win = tk.Toplevel(self.root)
        win.title("جميع الحالات")
        win.geometry("1200x700")
        win.configure(bg=self.colors['bg_main'])
        
        # إطار العنوان
        title_frame = tk.Frame(win, bg=self.colors['header'], height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="جميع الحالات", 
                              font=self.fonts['header'], fg=self.colors['header_text'], 
                              bg=self.colors['header'])
        title_label.pack(expand=True, pady=15)
        
        # إطار الإحصائيات
        stats_frame = tk.Frame(win, bg=self.colors['bg_card'], relief='solid', bd=1)
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        # حساب الإحصائيات
        total_cases = len(self.cases_data)
        active_cases = len([case for case in self.cases_data if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) not in ['تم حلها', 'مغلقة']])
        solved_cases = len([case for case in self.cases_data if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) == 'تم حلها'])
        closed_cases = len([case for case in self.cases_data if (case.get('status') if isinstance(case, dict) else (case[3] if len(case) > 3 else '')) == 'مغلقة'])
        
        stats_text = f"إجمالي الحالات: {total_cases} | الحالات النشطة: {active_cases} | المحلولة: {solved_cases} | المغلقة: {closed_cases}"
        stats_label = tk.Label(stats_frame, text=stats_text, 
                              font=self.fonts['normal'], fg=self.colors['text_main'], 
                              bg=self.colors['bg_card'])
        stats_label.pack(pady=10, padx=20)
        
        # إطار الجدول
        table_frame = tk.Frame(win, bg=self.colors['bg_main'])
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # الجدول
        columns = ("اسم العميل", "رقم المشترك", "تصنيف المشكلة", "حالة المشكلة", "تاريخ الإضافة", "آخر تعديل")
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=25)
        
        for col in columns:
            tree.heading(col, text=col)
            if col in ["اسم العميل", "رقم المشترك"]:
                tree.column(col, width=150)
            elif col in ["تصنيف المشكلة", "حالة المشكلة"]:
                tree.column(col, width=120)
            else:
                tree.column(col, width=130)
        
        # Scrollbar رأسي
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # تعبئة البيانات
        for case in self.cases_data:
            if isinstance(case, dict):
                tree.insert('', 'end', values=(
                    case.get('customer_name', ''),
                    case.get('subscriber_number', ''),
                    case.get('category_name', ''),
                    case.get('status', ''),
                    case.get('created_date', ''),
                    case.get('modified_date', '')
                ))
            elif isinstance(case, tuple):
                # ترتيب الأعمدة حسب get_all_cases
                # ['id', 'customer_name', 'subscriber_number', 'status', 'category_name', 'color_code', 'modified_by_name', 'created_date', 'modified_date']
                tree.insert('', 'end', values=(
                    case[1], case[2], case[4], case[3], case[7], case[8]
                ))
        
        # أزرار التحكم
        buttons_frame = tk.Frame(win, bg=self.colors['bg_main'])
        buttons_frame.pack(fill='x', pady=20, padx=20)
        
        # زر تصدير البيانات
        export_btn = tk.Button(buttons_frame, text="📊 تصدير البيانات", 
                              command=lambda: self.export_cases_data(),
                              font=self.fonts['button'], bg=self.colors['button_action'], fg='white',
                              relief='flat', padx=20, pady=10)
        export_btn.pack(side='right', padx=10)
        
        # زر إغلاق
        close_btn = tk.Button(buttons_frame, text="❌ إغلاق", 
                             command=win.destroy,
                             font=self.fonts['button'], bg=self.colors['button_secondary'], fg='white',
                             relief='flat', padx=20, pady=10)
        close_btn.pack(side='right', padx=10)
    
    def export_cases_data(self):
        """تصدير بيانات الحالات إلى CSV أو Excel فقط"""
        from tkinter import filedialog, simpledialog
        import csv
        from reports_utils import export_cases_to_excel

        # اختيار نوع التقرير (Excel/CSV فقط)
        filetypes = [
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx"),
            ("All files", "*.*")
        ]
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=filetypes,
            title="حفظ تقرير الحالات"
        )
        if not file_path:
            return

        try:
            # تجهيز الأعمدة الرئيسية (تعديل حسب قاعدة البيانات لديك)
            columns = [
                ("اسم العميل", "customer_name"),
                ("عنوان العميل", "customer_address"),
                ("رقم المشترك", "subscriber_number"),
                ("تصنيف المشكلة", "category_name"),
                ("حالة المشكلة", "status"),
                ("تاريخ ورود المشكلة", "received_date"),
                ("تاريخ الإضافة", "created_date"),
                ("آخر تعديل", "modified_date")
            ]
            # تجهيز البيانات كقائمة dicts موحدة
            cases = []
            for case in self.cases_data:
              # معالجة ترتيب الأعمدة بدقة حسب ما ترجعه get_all_cases
                if isinstance(case, dict):
                    cases.append({
                        "customer_name": case.get("customer_name", ""),
                        "customer_address": case.get("customer_address", case.get("address", "")),
                        "subscriber_number": case.get("subscriber_number", ""),
                        "category_name": case.get("category_name", ""),
                        "status": case.get("status", ""),
                        "received_date": case.get("received_date", ""),
                        "created_date": case.get("created_date", ""),
                        "modified_date": case.get("modified_date", "")
                    })
                elif isinstance(case, tuple):
                    # الترتيب الجديد: id, customer_name, customer_address, subscriber_number, status, category_name, color_code, modified_by_name, received_date, created_date, modified_date
                    try:
                        cases.append({
                            "customer_name": case[1] if len(case) > 1 else '',
                            "customer_address": case[2] if len(case) > 2 else '',
                            "subscriber_number": case[3] if len(case) > 3 else '',
                            "category_name": case[5] if len(case) > 5 else '',
                            "status": case[4] if len(case) > 4 else '',
                            "received_date": case[8] if len(case) > 8 else '',
                            "created_date": case[9] if len(case) > 9 else '',
                            "modified_date": case[10] if len(case) > 10 else ''
                        })
                    except Exception:
                        pass
            if file_path.endswith('.xlsx'):
                export_cases_to_excel(cases, file_path, custom_columns=columns)
            else:
                # CSV الافتراضي
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    headers = [col[0] for col in columns]
                    writer.writerow(headers)
                    for case in cases:
                        writer.writerow([
                            case.get('customer_name', ''),
                            case.get('customer_address', ''),
                            case.get('subscriber_number', ''),
                            case.get('category_name', ''),
                            case.get('status', ''),
                            case.get('received_date', ''),
                            case.get('created_date', ''),
                            case.get('modified_date', '')
                        ])
            self.show_notification(f"تم تصدير البيانات إلى: {file_path}", notification_type="success")
        except Exception as e:
            self.show_notification(f"خطأ في تصدير البيانات: {str(e)}", notification_type="error")
            messagebox.showerror("خطأ", f"فشل في تصدير البيانات:\n{e}")

    def apply_sorting(self, event=None):
        """تطبيق الترتيب على قائمة الحالات"""
        def get_val(c, key, idx):
            if isinstance(c, dict):
                return c.get(key, '')
            elif isinstance(c, tuple):
                return c[idx] if len(c) > idx else ''
            return ''
        
        try:
            sort_type = self.sort_var.get()
            if sort_type == "السنة (تنازلي)":
                self.filtered_cases.sort(key=lambda c: get_val(c, 'created_date', 7), reverse=True)
            elif sort_type == "السنة (تصاعدي)":
                self.filtered_cases.sort(key=lambda c: get_val(c, 'created_date', 7))
            elif sort_type == "اسم العميل (أ-ي)":
                self.filtered_cases.sort(key=lambda c: get_val(c, 'customer_name', 1))
            elif sort_type == "اسم العميل (ي-أ)":
                self.filtered_cases.sort(key=lambda c: get_val(c, 'customer_name', 1), reverse=True)
            
            # إعادة تعيين الفهرس المحدد
            self.selected_case_index = 0
            self.update_cases_list()
            
            self.show_notification(f"تم الترتيب حسب: {sort_type}", notification_type="info")
            
        except Exception as e:
            self.show_notification(f"خطأ في الترتيب: {str(e)}", notification_type="error")
            messagebox.showerror("خطأ في الترتيب", f"حدث خطأ أثناء الترتيب:\n{e}")

    def update_status_button_color(self, status_value):
        """تحديث لون زر أو شارة الحالة حسب القيمة (منطق الألوان فقط، بدون ربط مباشر بعناصر الواجهة)"""
        status_colors = {
            'جديدة': '#3498db',
            'قيد التنفيذ': '#f39c12',
            'تم حلها': '#27ae60',
            'مغلقة': '#95a5a6'
        }
        color = status_colors.get(status_value, '#95a5a6')
        # يمكن استخدام color عند رسم أي زر أو شارة حالة في أي مكان
        return color

    def update_action_buttons_style(self):
        """تحديث خصائص أزرار العمليات بعد أي تعديل"""
        for btn in [self.save_btn, self.print_btn]:
            btn.config(font=self.fonts['button'], relief='flat')
            if btn == self.save_btn:
                btn.config(bg='#27ae60', fg='white')
            elif btn == self.print_btn:
                btn.config(bg='#3498db', fg='white')

    def _on_case_list_up(self, event=None):
        if not self.case_card_widgets:
            return
        self.selected_case_index = max(0, self.selected_case_index - 1)
        self._highlight_selected_case_card()
        self._select_case_by_index()
    def _on_case_list_down(self, event=None):
        if not self.case_card_widgets:
            return
        self.selected_case_index = min(len(self.case_card_widgets) - 1, self.selected_case_index + 1)
        self._highlight_selected_case_card()
        self._select_case_by_index()
    def _highlight_selected_case_card(self):
        """تمييز البطاقة المحددة"""
        try:
            if not self.case_card_widgets:
                return
                
            for idx, card in enumerate(self.case_card_widgets):
                try:
                    if not card.winfo_exists():
                        continue
                        
                    if idx == self.selected_case_index:
                        # تمييز البطاقة المحددة بلون مختلف
                        card.config(bg=self.colors['bg_card'], highlightbackground=self.colors['button_action'], highlightthickness=2)
                        # تمييز جميع العناصر داخل البطاقة مع حماية شارة الحالة
                        for child in card.winfo_children():
                            try:
                                if isinstance(child, tk.Label) and child.winfo_exists():
                                    # لا تغير لون شارة الحالة (التي لها خلفية ملونة)
                                    if child.cget('bg') not in [self.colors['status_new'], self.colors['status_inprogress'], 
                                                               self.colors['status_solved'], self.colors['status_closed']]:
                                        child.config(bg=self.colors['bg_card'])
                            except:
                                pass
                    else:
                        # إعادة البطاقات الأخرى للوضع العادي
                        card.config(bg=self.colors['bg_light'], highlightbackground=self.colors['border_light'], highlightthickness=1)
                        # إعادة جميع العناصر داخل البطاقة للوضع العادي مع حماية شارة الحالة
                        for child in card.winfo_children():
                            try:
                                if isinstance(child, tk.Label) and child.winfo_exists():
                                    # لا تغير لون شارة الحالة
                                    if child.cget('bg') not in [self.colors['status_new'], self.colors['status_inprogress'], 
                                                               self.colors['status_solved'], self.colors['status_closed']]:
                                        child.config(bg=self.colors['bg_light'])
                            except:
                                pass
                except Exception:
                    # تجاهل الأخطاء في البطاقات الفردية
                    continue
        except Exception:
            # تجاهل الأخطاء العامة في تمييز البطاقات
            pass
    def _select_case_by_index(self):
        """اختيار الحالة حسب الفهرس"""
        try:
            if 0 <= self.selected_case_index < len(self.filtered_cases):
                case = self.filtered_cases[self.selected_case_index]
                self.load_case(case)
        except Exception:
            # تجاهل الأخطاء في اختيار الحالة
            pass