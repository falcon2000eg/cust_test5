import os
import shutil
from datetime import datetime

try:
    import tkinter.filedialog as filedialog
    import tkinter.messagebox as messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    filedialog = None
    messagebox = None

# تحديد المسار الجذري للمشروع (المجلد الذي يحتوي على هذا الملف)
# هذا يضمن أن المسارات ستعمل بشكل صحيح بغض النظر عن مكان تشغيل السكربت
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

class FileManager:
    def __init__(self, base_path="files"):
        # استخدام المسار المطلق دائمًا لضمان الموثوقية
        self.base_path = os.path.join(PROJECT_ROOT, base_path)
        self.ensure_base_directory()
    
    def ensure_base_directory(self):
        """التأكد من وجود المجلد الأساسي"""
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            print(f"تم إنشاء مجلد الملفات: {self.base_path}")
    
    def create_case_folder(self, case_id):
        """إنشاء مجلد للحالة"""
        case_folder = os.path.join(self.base_path, f"case_{case_id}")
        if not os.path.exists(case_folder):
            os.makedirs(case_folder)
            print(f"تم إنشاء مجلد الحالة: {case_folder}")
        return case_folder
    
    def copy_file_to_dedicated_folder(self, source_path, case_id, attachments_base_path, description=""):
        """نسخ ملف إلى مجلد مخصص ومنظم حسب رقم الحالة."""
        if not source_path or not os.path.exists(source_path):
            return None

        # إنشاء مجلد الحالة داخل المجلد المخصص
        case_folder = os.path.join(attachments_base_path, f"case_{case_id}")
        if not os.path.exists(case_folder):
            os.makedirs(case_folder)

        file_name = os.path.basename(source_path)
        # لا يتم تغيير اسم الملف للحفاظ عليه كما هو
        new_file_path = os.path.join(case_folder, file_name)

        # التحقق إذا كان الملف موجوداً بالفعل
        if os.path.exists(new_file_path):
            if not messagebox.askyesno("تأكيد", "ملف بنفس الاسم موجود بالفعل. هل تريد استبداله؟"):
                return None # أو يمكن إرجاع معلومات الملف الموجود

        try:
            shutil.copy2(source_path, new_file_path)
            absolute_path = os.path.abspath(new_file_path)
            return {
                'file_name': file_name,
                'file_path': absolute_path, # <-- إرجاع المسار المطلق للملف المنسوخ
                'file_type': self.get_file_type(file_name),
                'description': description,
                'size': self.get_file_size(absolute_path)
            }
        except Exception as e:
            messagebox.showerror("خطأ في النسخ", f"فشل نسخ الملف: {e}")
            return None

    def get_attachment_info(self, file_path, description=""):
        """الحصول على معلومات المرفق دون نسخه، مع استخدام المسار المطلق."""
        if not file_path or not os.path.exists(file_path):
            return None
        
        file_name = os.path.basename(file_path)
        absolute_path = os.path.abspath(file_path)
        
        return {
            'file_name': file_name,
            'file_path': absolute_path,  # <-- تخزين المسار المطلق مباشرة
            'file_type': self.get_file_type(file_name),
            'description': description,
            'size': self.get_file_size(absolute_path)
        }
    
    def select_and_copy_file(self, case_id, description=""):
        """اختيار ونسخ ملف للحالة"""
        if not TKINTER_AVAILABLE:
            print("تحذير: tkinter غير متوفر. استخدم copy_file_to_case_folder مباشرة")
            return None

        # اختيار الملف
        if filedialog is None:
            print("تحذير: filedialog غير متوفر.")
            return None
        file_path = filedialog.askopenfilename(
            title="اختر الملف",
            filetypes=[
                ("ملفات الصور", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("ملفات PDF", "*.pdf"),
                ("ملفات Word", "*.doc *.docx"),
                ("ملفات Excel", "*.xls *.xlsx"),
                ("جميع الملفات", "*.*")
            ]
        )
        
        if not file_path:
            return None
        
        return self.copy_file_to_case_folder(file_path, case_id, description)
    
    def get_file_type(self, file_name):
        """تحديد نوع الملف"""
        extension = os.path.splitext(file_name)[1].lower()
        
        type_mapping = {
            '.jpg': 'صورة', '.jpeg': 'صورة', '.png': 'صورة', 
            '.gif': 'صورة', '.bmp': 'صورة',
            '.pdf': 'PDF',
            '.doc': 'Word', '.docx': 'Word',
            '.xls': 'Excel', '.xlsx': 'Excel',
            '.txt': 'نص',
            '.zip': 'مضغوط', '.rar': 'مضغوط'
        }
        
        return type_mapping.get(extension, 'آخر')
    
    def get_file_size(self, file_path):
        """الحصول على حجم الملف"""
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            
            if size_bytes < 1024:
                return f"{size_bytes} بايت"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} كيلوبايت"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} ميجابايت"
        return "غير معروف"
    
    def open_case_folder(self, case_id):
        """فتح مجلد الحالة"""
        case_folder = os.path.join(self.base_path, f"case_{case_id}")
        
        if os.path.exists(case_folder):
            try:
                # محاولة فتح المجلد حسب نظام التشغيل
                import platform
                system = platform.system()
                
                if system == "Windows":
                    os.startfile(case_folder)
                elif system == "Darwin":  # macOS
                    os.system(f'open "{case_folder}"')
                else:  # Linux وأنظمة أخرى
                    os.system(f'xdg-open "{case_folder}"')
                    
            except Exception as e:
                info_msg = f"مسار مجلد الحالة: {case_folder}"
                if TKINTER_AVAILABLE and messagebox:
                    messagebox.showinfo("معلومات", info_msg)
                else:
                    print(f"معلومات: {info_msg}")
        else:
            warning_msg = "مجلد الحالة غير موجود"
            if TKINTER_AVAILABLE and messagebox:
                messagebox.showwarning("تحذير", warning_msg)
            else:
                print(f"تحذير: {warning_msg}")
    
    def open_file(self, file_path):
        """فتح ملف"""
        if os.path.exists(file_path):
            try:
                import platform
                system = platform.system()
                
                if system == "Windows":
                    os.startfile(file_path)
                elif system == "Darwin":  # macOS
                    os.system(f'open "{file_path}"')
                else:  # Linux وأنظمة أخرى
                    os.system(f'xdg-open "{file_path}"')
                    
            except Exception as e:
                info_msg = f"مسار الملف: {file_path}"
                if TKINTER_AVAILABLE and messagebox:
                    messagebox.showinfo("معلومات", info_msg)
                else:
                    print(f"معلومات: {info_msg}")
        else:
            error_msg = "الملف غير موجود"
            if TKINTER_AVAILABLE and messagebox:
                messagebox.showerror("خطأ", error_msg)
            else:
                print(f"خطأ: {error_msg}")
    
    def delete_file(self, file_path):
        """حذف ملف"""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                error_msg = f"فشل في حذف الملف: {str(e)}"
                if TKINTER_AVAILABLE and messagebox:
                    messagebox.showerror("خطأ", error_msg)
                else:
                    print(f"خطأ: {error_msg}")
                return False
        return False
    
    def move_file_to_case(self, source_path, target_case_id, description=""):
        """نقل ملف موجود إلى حالة أخرى"""
        if not os.path.exists(source_path):
            return False
        
        # إنشاء مجلد الحالة الهدف
        target_folder = self.create_case_folder(target_case_id)
        
        # الحصول على اسم الملف
        file_name = os.path.basename(source_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file_name = f"{timestamp}_{file_name}"
        new_file_path = os.path.join(target_folder, new_file_name)
        
        try:
            shutil.move(source_path, new_file_path)
            return {
                'original_name': file_name,
                'new_name': new_file_name,
                'path': new_file_path,
                'file_name': new_file_name,  # <-- add for UI/db compatibility
                'file_path': new_file_path,  # <-- add for UI/db compatibility
                'file_type': self.get_file_type(file_name),
                'description': description,
                'size': self.get_file_size(new_file_path)
            }
        except Exception as e:
            error_msg = f"فشل في نقل الملف: {str(e)}"
            if TKINTER_AVAILABLE and messagebox:
                messagebox.showerror("خطأ", error_msg)
            else:
                print(f"خطأ: {error_msg}")
            return None
    
    def get_case_files_info(self, case_id):
        """الحصول على معلومات ملفات الحالة"""
        case_folder = os.path.join(self.base_path, f"case_{case_id}")
        files_info = []
        
        if os.path.exists(case_folder):
            for file_name in os.listdir(case_folder):
                file_path = os.path.join(case_folder, file_name)
                if os.path.isfile(file_path):
                    files_info.append({
                        'name': file_name,
                        'path': file_path,
                        'type': self.get_file_type(file_name),
                        'size': self.get_file_size(file_path),
                        'modified_date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        return files_info
    
    def create_backup(self, case_id, backup_path=None):
        """إنشاء نسخة احتياطية من ملفات الحالة"""
        case_folder = os.path.join(self.base_path, f"case_{case_id}")
        
        if not os.path.exists(case_folder):
            return False
        
        if not backup_path:
            backup_path = os.path.join(self.base_path, "backups")
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"case_{case_id}_backup_{timestamp}"
        backup_full_path = os.path.join(backup_path, backup_name)
        
        try:
            shutil.copytree(case_folder, backup_full_path)
            return backup_full_path
        except Exception as e:
            error_msg = f"فشل في إنشاء النسخة الاحتياطية: {str(e)}"
            if TKINTER_AVAILABLE and messagebox:
                messagebox.showerror("خطأ", error_msg)
            else:
                print(f"خطأ: {error_msg}")
            return None
    
    def cleanup_old_backups(self, days_to_keep=30):
        """تنظيف النسخ الاحتياطية القديمة"""
        backup_path = os.path.join(self.base_path, "backups")
        
        if not os.path.exists(backup_path):
            return
        
        current_time = datetime.now()
        cutoff_time = current_time.timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for item in os.listdir(backup_path):
            item_path = os.path.join(backup_path, item)
            if os.path.isdir(item_path):
                if os.path.getmtime(item_path) < cutoff_time:
                    try:
                        shutil.rmtree(item_path)
                        print(f"تم حذف النسخة الاحتياطية القديمة: {item}")
                    except Exception as e:
                        print(f"فشل في حذف النسخة الاحتياطية: {item} - {e}")
    
    def get_storage_info(self):
        """الحصول على معلومات التخزين"""
        total_size = 0
        total_files = 0
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    total_files += 1
                except:
                    pass
        
        return {
            'total_files': total_files,
            'total_size': self.format_size(total_size),
            'base_path': self.base_path
        }
    
    def format_size(self, size_bytes):
        """تنسيق حجم الملف"""
        if size_bytes < 1024:
            return f"{size_bytes} بايت"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} كيلوبايت"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} ميجابايت"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} جيجابايت"