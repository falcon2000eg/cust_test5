import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import json
from customer_issues_database import enhanced_db

class EnhancedFunctions:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        # تحميل سنوات البيانات
        self.load_years()
        
        # تحميل تصنيفات المشاكل
        self.load_categories()
        
        # تحميل خيارات الحالة
        self.load_status_options()
        
        # تحميل الحالات
        self.load_cases()
    
    def load_years(self):
        """تحميل سنوات البيانات"""
        try:
            # الحصول على السنوات المتاحة
            query = "SELECT DISTINCT strftime('%Y', created_date) as year FROM cases ORDER BY year DESC"
            years_data = enhanced_db.execute_query(query)
            
            years = ["الكل"]
            for year_row in years_data:
                if year_row[0]:
                    years.append(year_row[0])
            
            # إضافة السنة الحالية إذا لم تكن موجودة
            current_year = str(datetime.now().year)
            if current_year not in years:
                years.append(current_year)
            
            self.main_window.year_combo['values'] = years
            
        except Exception as e:
            print(f"خطأ في تحميل السنوات: {e}")
    
    def load_categories(self):
        """تحميل تصنيفات المشاكل"""
        try:
            categories_data = enhanced_db.get_categories()
            categories = [cat[1] for cat in categories_data]  # اسم التصنيف
            
            if hasattr(self.main_window, 'basic_data_widgets'):
                category_combo = self.main_window.basic_data_widgets.get('category')
                if category_combo:
                    category_combo['values'] = categories
            
            # حفظ بيانات التصنيفات للاستخدام في البحث
            self.categories_data = categories
            
        except Exception as e:
            print(f"خطأ في تحميل التصنيفات: {e}")
    
    def load_status_options(self):
        """تحميل خيارات الحالة"""
        try:
            status_options = enhanced_db.get_status_options()
            statuses = [status[0] for status in status_options]  # اسم الحالة
            
            if hasattr(self.main_window, 'basic_data_widgets'):
                status_combo = self.main_window.basic_data_widgets.get('status')
                if status_combo:
                    status_combo['values'] = statuses
            
            # حفظ بيانات الحالات للاستخدام في البحث
            self.status_data = statuses
            
        except Exception as e:
            print(f"خطأ في تحميل خيارات الحالة: {e}")
    
    def load_cases(self, year=None):
        """تحميل الحالات"""
        try:
            if year and year != "الكل":
                cases_data = enhanced_db.get_cases_by_year(int(year))
            else:
                cases_data = enhanced_db.get_cases_by_year()
            
            self.main_window.cases_data = cases_data
            self.main_window.filtered_cases = cases_data.copy()
            self.refresh_cases_display()
            
        except Exception as e:
            print(f"خطأ في تحميل الحالات: {e}")
            messagebox.showerror("خطأ", f"فشل في تحميل الحالات: {e}")
    
    def refresh_cases_display(self):
        """تحديث عرض الحالات"""
        # مسح العرض الحالي
        for widget in self.main_window.scrollable_frame.winfo_children():
            widget.destroy()
        
        # عرض الحالات
        for i, case_data in enumerate(self.main_window.filtered_cases):
            self.create_case_card(case_data, i)
        
        # تحديث منطقة السكرول
        self.main_window.scrollable_frame.update_idletasks()
        self.main_window.cases_canvas.configure(scrollregion=self.main_window.cases_canvas.bbox("all"))
    
    def create_case_card(self, case_data, index, return_widget=False):
        """إنشاء بطاقة الحالة مع تصميم محسن"""
        # دعم dict أو tuple
        if isinstance(case_data, dict):
            case_id = case_data.get('id')
            customer_name = case_data.get('customer_name', '')
            subscriber_number = case_data.get('subscriber_number', '')
            status = case_data.get('status', '')
            category_name = case_data.get('category_name', '')
            color_code = case_data.get('color_code', '')
            modified_by_name = case_data.get('modified_by_name', '')
            created_date = case_data.get('created_date', '')
            modified_date = case_data.get('modified_date', '')
        else:
            case_id, customer_name, subscriber_number, status, category_name, color_code, modified_by_name, created_date, modified_date = case_data
        
        # إطار البطاقة مع تصميم محسن
        card_frame = tk.Frame(self.main_window.scrollable_frame, bg='#ffffff', relief='solid', bd=1, padx=15, pady=12)
        card_frame.pack(fill='x', padx=10, pady=5)
        
        # لون الحدود حسب الحالة
        status_colors = {
            'جديدة': '#3498db',
            'قيد التنفيذ': '#f39c12',
            'تم حلها': '#27ae60',
            'مغلقة': '#95a5a6'
        }
        border_color = status_colors.get(status, '#95a5a6')
        card_frame.configure(highlightbackground=border_color, highlightthickness=2)
        
        # اسم العميل
        name_label = tk.Label(card_frame, text=customer_name, 
                             font=self.main_window.fonts['subheader'], fg='#2c3e50', bg='#ffffff')
        name_label.pack(anchor='e', pady=(0, 5))
        
        # رقم المشترك
        if subscriber_number:
            subscriber_label = tk.Label(card_frame, text=f"رقم المشترك: {subscriber_number}", 
                                       font=self.main_window.fonts['normal'], fg='#7f8c8d', bg='#ffffff')
            subscriber_label.pack(anchor='e', pady=2)
        
        # تصنيف المشكلة
        if category_name:
            category_label = tk.Label(card_frame, text=f"التصنيف: {category_name}", 
                                     font=self.main_window.fonts['normal'], fg='#7f8c8d', bg='#ffffff')
            category_label.pack(anchor='e', pady=2)
        
        # شارة الحالة
        status_frame = tk.Frame(card_frame, bg='#ffffff')
        status_frame.pack(anchor='e', pady=5)
        
        status_badge = tk.Label(status_frame, text=status,
                               font=self.main_window.fonts['small'], fg='white',
                               bg=border_color, padx=10, pady=3, relief='flat')
        status_badge.pack(side='right')
        
        # تاريخ الإنشاء
        if created_date:
            try:
                date_obj = datetime.strptime(created_date, "%Y-%m-%d %H:%M:%S")
                formatted_date = date_obj.strftime("%Y/%m/%d")
                date_label = tk.Label(card_frame, text=f"تاريخ الإنشاء: {formatted_date}", 
                                     font=self.main_window.fonts['small'], fg='#95a5a6', bg='#ffffff')
                date_label.pack(anchor='e', pady=2)
            except:
                pass
        
        # آخر مُعدِّل
        if modified_by_name:
            modifier_label = tk.Label(card_frame, text=f"آخر تعديل: {modified_by_name}", 
                                     font=self.main_window.fonts['small'], fg='#95a5a6', bg='#ffffff')
            modifier_label.pack(anchor='e', pady=(2, 0))
        
        # ربط النقر لاختيار الحالة
        def on_card_click(event, cid=case_id):
            self.select_case(cid)
        
        # ربط النقر لجميع عناصر البطاقة
        for widget in [card_frame, name_label, status_badge]:
            widget.bind("<Button-1>", on_card_click)
            widget.bind("<Enter>", lambda e, w=widget: w.configure(bg='#f8f9fa'))
            widget.bind("<Leave>", lambda e, w=widget: w.configure(bg='#ffffff'))
        
        if return_widget:
            return card_frame
    
    def select_case(self, case_id):
        """اختيار حالة"""
        self.main_window.current_case_id = case_id
        self.load_case_details(case_id)
        
        # تفعيل الأزرار
        self.main_window.save_btn.configure(state='normal')
        self.main_window.print_btn.configure(state='normal')
    
    def load_case_details(self, case_id):
        """تحميل تفاصيل الحالة"""
        try:
            # تحميل البيانات الأساسية
            case_details = enhanced_db.get_case_details(case_id)
            
            if case_details:
                # تحديث رأس العرض
                self.main_window.customer_name_label.configure(text=case_details.get('customer_name', ''))
                if case_details.get('solved_by_name'):
                    self.main_window.solved_by_label.configure(text=f"تم الحل بواسطة: {case_details.get('solved_by_name')}")
                else:
                    self.main_window.solved_by_label.configure(text="")
                
                # ملء البيانات الأساسية
                self.fill_basic_data(case_details)
                
                # تحميل المرفقات
                self.load_case_attachments(case_id)
                
                # تحميل المراسلات
                self.load_case_correspondences(case_id)
                
                # تحميل سجل التعديلات
                self.load_case_audit_log(case_id)
        
        except Exception as e:
            print(f"خطأ في تحميل تفاصيل الحالة: {e}")
            messagebox.showerror("خطأ", f"فشل في تحميل تفاصيل الحالة: {e}")
    
    def fill_basic_data(self, case_details):
        """ملء البيانات الأساسية"""
        if not hasattr(self.main_window, 'basic_data_widgets'):
            return
        
        widgets = self.main_window.basic_data_widgets
        
        # ملء الحقول النصية
        text_fields = {
            'customer_name': case_details.get('customer_name', ''),
            'subscriber_number': case_details.get('subscriber_number', ''),
            'phone': case_details.get('phone', ''),
            'last_meter_reading': str(case_details.get('last_meter_reading', '')),
            'last_reading_date': case_details.get('last_reading_date', ''),
            'debt_amount': str(case_details.get('debt_amount', ''))
        }
        
        for field_name, value in text_fields.items():
            widget = widgets.get(field_name)
            if widget and hasattr(widget, 'delete'):
                widget.delete(0, tk.END)
                widget.insert(0, value)
        
        # ملء الحقول النصية متعددة الأسطر
        text_areas = {
            'address': case_details.get('address', ''),
            'problem_description': case_details.get('problem_description', ''),
            'actions_taken': case_details.get('actions_taken', '')
        }
        
        for field_name, value in text_areas.items():
            widget = widgets.get(field_name)
            if widget and hasattr(widget, 'delete'):
                widget.delete('1.0', tk.END)
                widget.insert('1.0', value)
        
        # ملء القوائم المنسدلة
        category_widget = widgets.get('category')
        if category_widget:
            category_name = case_details.get('category_name', '')
            options = list(category_widget['values'])
            if category_name and category_name not in options:
                category_widget['values'] = options + [category_name]
            category_widget.set(category_name or '')
        
        status_widget = widgets.get('status')
        if status_widget:
            status_widget.set(case_details.get('status', ''))
        
        # تحديث الموظف المسؤول
        employee_widget = widgets.get('employee_name')
        if employee_widget:
            emp_name = case_details.get('modified_by_name') or case_details.get('created_by_name') or ''
            options = list(employee_widget['values'])
            if emp_name and emp_name not in options:
                employee_widget['values'] = options + [emp_name]
            employee_widget.set(emp_name)
        # تحديث تاريخ الورود (السنة والشهر)
        received_date = case_details.get('received_date')
        if received_date:
            try:
                dt = datetime.strptime(received_date, "%Y-%m-%d %H:%M:%S")
                self.main_window.year_received_var.set(str(dt.year))
                self.main_window.month_received_var.set(f"{dt.month:02d}")
            except Exception:
                pass
    
    def load_case_attachments(self, case_id):
        """تحميل مرفقات الحالة (النسخة المصححة)."""
        try:
            # مسح الجدول الحالي
            for item in self.main_window.attachments_tree.get_children():
                self.main_window.attachments_tree.delete(item)
            
            # get_attachments تعيد الآن قائمة من القواميس (dict) بالأسماء الصحيحة
            attachments = enhanced_db.get_attachments(case_id)
            
            for att in attachments:
                # إدخال البيانات بالترتيب الصحيح والمتوقع للجدول
                self.main_window.attachments_tree.insert('', 'end', values=(
                    att.get('id'),
                    att.get('file_type'),
                    att.get('file_name'),
                    att.get('description'),
                    att.get('upload_date'),
                    att.get('uploaded_by_name'),
                    att.get('file_path')  # المسار الكامل للملف
                ))
        
        except Exception as e:
            print(f"خطأ في تحميل المرفقات: {e}")
    
    def load_case_correspondences(self, case_id):
        """تحميل مراسلات الحالة"""
        try:
            # مسح الجدول الحالي
            for item in self.main_window.correspondences_tree.get_children():
                self.main_window.correspondences_tree.delete(item)
            
            # تحميل المراسلات
            correspondences = enhanced_db.get_case_correspondences(case_id)
            
            for correspondence in correspondences:
                self.main_window.correspondences_tree.insert('', 'end', values=(
                    correspondence[0],  # ID
                    correspondence[2],  # case_sequence_number
                    correspondence[3],  # yearly_sequence_number
                    correspondence[4],  # sender
                    correspondence[5][:50] + '...' if len(correspondence[5]) > 50 else correspondence[5],  # message_content (مقطوع)
                    correspondence[6],  # sent_date
                    correspondence[9] or ''  # created_by_name
                ))
        
        except Exception as e:
            print(f"خطأ في تحميل المراسلات: {e}")
    
    def load_case_audit_log(self, case_id):
        """تحميل سجل تعديلات الحالة"""
        try:
            # مسح الجدول الحالي
            for item in self.main_window.audit_tree.get_children():
                self.main_window.audit_tree.delete(item)
            
            # تحميل سجل التعديلات
            audit_logs = enhanced_db.get_case_audit_log(case_id)
            
            for log in audit_logs:
                self.main_window.audit_tree.insert('', 'end', values=(
                    log[5],  # timestamp
                    log[7] or '',  # performed_by_name
                    log[2],  # action_type
                    log[3]   # action_description
                ))
        
        except Exception as e:
            print(f"خطأ في تحميل سجل التعديلات: {e}")
    
    def filter_by_year(self, event=None):
        """فلترة حسب السنة"""
        selected_year = self.main_window.year_var.get()
        self.load_cases(selected_year if selected_year != "الكل" else None)
    
    def on_search_type_change(self, event=None):
        """تغيير نوع البحث"""
        search_type = self.main_window.search_type_var.get()
        
        # إزالة الحقل الحالي
        if self.main_window.search_combo:
            self.main_window.search_combo.destroy()
            self.main_window.search_combo = None
        
        # إظهار أو إخفاء حقل النص
        if search_type in ["تصنيف المشكلة", "حالة المشكلة", "اسم الموظف"]:
            # إخفاء حقل النص
            self.main_window.search_entry.pack_forget()
            
            # إنشاء قائمة منسدلة
            self.main_window.search_combo = ttk.Combobox(
                self.main_window.search_entry.master,
                font=self.main_window.fonts['normal'],
                state='readonly'
            )
            
            # ملء القائمة حسب النوع
            if search_type == "تصنيف المشكلة":
                self.main_window.search_combo['values'] = getattr(self, 'categories_data', [])
            elif search_type == "حالة المشكلة":
                self.main_window.search_combo['values'] = getattr(self, 'status_data', [])
            elif search_type == "اسم الموظف":
                employees = enhanced_db.get_employees()
                self.main_window.search_combo['values'] = [emp[1] for emp in employees]
            
            self.main_window.search_combo.pack(fill='x')
            self.main_window.search_combo.bind('<<ComboboxSelected>>', self.perform_search)
        else:
            # إظهار حقل النص
            if self.main_window.search_combo:
                self.main_window.search_combo.pack_forget()
            self.main_window.search_entry.pack(fill='x')
        
        # مسح البحث الحالي
        self.main_window.search_value_var.set('')
        self.main_window.filtered_cases = self.main_window.cases_data.copy()
        self.refresh_cases_display()
    
    def perform_search(self, event=None):
        """تنفيذ البحث"""
        search_type = self.main_window.search_type_var.get()
        # الحصول على قيمة البحث
        if self.main_window.search_combo and self.main_window.search_combo.winfo_viewable():
            search_value = self.main_window.search_combo.get()
        else:
            search_value = self.main_window.search_value_var.get()
        if not search_value.strip():
            # إذا كان البحث فارغ، عرض جميع الحالات
            self.main_window.filtered_cases = self.main_window.cases_data.copy()
        else:
            # تنفيذ البحث
            try:
                # تأكد أن البحث على category_name وليس category_id
                stype = search_type
                if search_type == "تصنيف المشكلة":
                    stype = "تصنيف المشكلة"
                search_results = enhanced_db.search_cases(stype, search_value.strip())
                self.main_window.filtered_cases = search_results
            except Exception as e:
                print(f"خطأ في البحث: {e}")
                messagebox.showerror("خطأ", f"فشل في البحث: {e}")
                return
        self.refresh_cases_display()
    
    def add_new_case(self):
        """إضافة حالة جديدة"""
        try:
            # إنشاء حالة جديدة فارغة
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # الحصول على المستخدم
            employees = enhanced_db.get_employees()
            if not employees:
                messagebox.showerror("خطأ", "لا توجد موظفين في النظام")
                return
            
            employee_dialog = EmployeeSelectionDialog(self.main_window.root, employees, "اختر الموظف المسؤول عن إنشاء الحالة")
            if not employee_dialog.result:
                return
            
            creator_id = employee_dialog.result['id']
            
            # إدخال الحالة الجديدة
            query = """
                INSERT INTO cases (customer_name, subscriber_number, created_date, created_by, modified_date, modified_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            enhanced_db.execute_query(query, ("عميل جديد", "00000000000000", current_time, creator_id, current_time, creator_id))
            
            # الحصول على ID الحالة الجديدة
            new_case_id = enhanced_db.execute_query("SELECT last_insert_rowid()")[0][0]
            
            # تسجيل العملية
            enhanced_db.log_action(new_case_id, "إنشاء", "تم إنشاء حالة جديدة", creator_id)
            
            # إعادة تحميل الحالات
            self.load_cases()
            
            # اختيار الحالة الجديدة
            self.select_case(new_case_id)
            
            messagebox.showinfo("نجح", "تم إنشاء حالة جديدة بنجاح")
            
        except Exception as e:
            print(f"خطأ في إنشاء حالة جديدة: {e}")
            messagebox.showerror("خطأ", f"فشل في إنشاء حالة جديدة: {e}")


class EmployeeSelectionDialog:
    def __init__(self, parent, employees, title="اختر موظف"):
        self.result = None
        
        # إنشاء النافذة
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()
        
        # توسيط النافذة
        self.dialog.transient(parent)
        
        # المحتوى
        main_frame = tk.Frame(self.dialog, bg='#ffffff')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # العنوان
        title_label = tk.Label(main_frame, text=title, font=('Arial', 12, 'bold'), bg='#ffffff')
        title_label.pack(pady=(0, 20))
        
        # قائمة الموظفين
        self.employees_var = tk.StringVar()
        employees_frame = tk.Frame(main_frame, bg='#ffffff')
        employees_frame.pack(fill='both', expand=True)
        
        for emp in employees:
            rb = tk.Radiobutton(employees_frame, text=f"{emp[1]} - {emp[2] if len(emp) > 2 else 'موظف'}", 
                               variable=self.employees_var, value=str(emp[0]),
                               font=('Arial', 10), bg='#ffffff')
            rb.pack(anchor='w', pady=2)
        
        # أزرار
        buttons_frame = tk.Frame(main_frame, bg='#ffffff')
        buttons_frame.pack(fill='x', pady=(20, 0))
        
        cancel_btn = tk.Button(buttons_frame, text="إلغاء", command=self.cancel,
                              font=('Arial', 10), bg='#95a5a6', fg='white', relief='flat', padx=20)
        cancel_btn.pack(side='left')
        
        ok_btn = tk.Button(buttons_frame, text="موافق", command=self.ok,
                          font=('Arial', 10), bg='#27ae60', fg='white', relief='flat', padx=20)
        ok_btn.pack(side='right')
        
        # ربط Enter و Escape
        self.dialog.bind('<Return>', lambda e: self.ok())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        
        # انتظار النتيجة
        self.dialog.wait_window()
    
    def ok(self):
        selected_id = self.employees_var.get()
        if selected_id:
            self.result = {'id': int(selected_id)}
        self.dialog.destroy()
    
    def cancel(self):
        self.result = None
        self.dialog.destroy()