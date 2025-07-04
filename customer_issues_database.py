import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def update_correspondence(self, correspondence_id, new_content):
        """تحديث محتوى مراسلة محددة"""
        query = "UPDATE correspondences SET message_content = ?, modified_date = ? WHERE id = ?"
        params = (new_content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), correspondence_id)
        self.execute_query(query, params)
    def delete_case(self, case_id):
        """حذف حالة وجميع بياناتها المرتبطة (المرفقات، المراسلات، سجل التعديلات)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            # حذف سجل التعديلات
            cursor.execute("DELETE FROM audit_log WHERE case_id = ?", (case_id,))
            # حذف المرفقات
            cursor.execute("DELETE FROM attachments WHERE case_id = ?", (case_id,))
            # حذف المراسلات
            cursor.execute("DELETE FROM correspondences WHERE case_id = ?", (case_id,))
            # حذف الحالة نفسها
            cursor.execute("DELETE FROM cases WHERE id = ?", (case_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting case {case_id}: {e}")
            return False
        finally:
            conn.close()
    def __init__(self, db_name="customer_issues_enhanced.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """إنشاء قاعدة البيانات والجداول المحسنة"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # جدول الموظفين
        # إضافة عمود رقم الأداء إذا لم يكن موجودًا
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                position TEXT,
                performance_number TEXT UNIQUE,
                created_date TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        # التأكد من وجود العمود في الجداول القديمة (ترقية قاعدة البيانات)
        try:
            cursor.execute("ALTER TABLE employees ADD COLUMN performance_number TEXT UNIQUE")
        except Exception:
            pass  # العمود موجود بالفعل
        
        # جدول تصنيفات المشاكل المحسن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issue_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                description TEXT,
                color_code TEXT DEFAULT '#3498db'
            )
        ''')
        
        # جدول الحالات المحسن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                subscriber_number TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                category_id INTEGER,
                status TEXT DEFAULT 'جديدة',
                problem_description TEXT,
                actions_taken TEXT,
                last_meter_reading REAL,
                last_reading_date TEXT,
                debt_amount REAL DEFAULT 0,
                received_date TEXT,
                created_date TEXT,
                created_by INTEGER,
                modified_date TEXT,
                modified_by INTEGER,
                solved_by INTEGER,
                solved_date TEXT,
                FOREIGN KEY (category_id) REFERENCES issue_categories (id),
                FOREIGN KEY (created_by) REFERENCES employees (id),
                FOREIGN KEY (modified_by) REFERENCES employees (id),
                FOREIGN KEY (solved_by) REFERENCES employees (id)
            )
        ''')
        
        # جدول المراسلات المحسن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS correspondences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                case_sequence_number INTEGER,
                yearly_sequence_number TEXT,
                sender TEXT,
                message_content TEXT,
                sent_date TEXT,
                created_by INTEGER,
                created_date TEXT,
                FOREIGN KEY (case_id) REFERENCES cases (id),
                FOREIGN KEY (created_by) REFERENCES employees (id)
            )
        ''')
        
        # جدول المرفقات المحسن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                description TEXT,
                upload_date TEXT,
                uploaded_by INTEGER,
                FOREIGN KEY (case_id) REFERENCES cases (id),
                FOREIGN KEY (uploaded_by) REFERENCES employees (id)
            )
        ''')
        
        # جدول سجل التعديلات المحسن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                action_type TEXT,
                action_description TEXT,
                performed_by INTEGER,
                timestamp TEXT,
                old_values TEXT,
                new_values TEXT,
                FOREIGN KEY (case_id) REFERENCES cases (id),
                FOREIGN KEY (performed_by) REFERENCES employees (id)
            )
        ''')
        
        # إدخال الموظفين الافتراضيين
        default_employees = [
            ('مدير النظام', 'مدير'),
            ('أحمد محمد', 'موظف خدمة عملاء'),
            ('فاطمة علي', 'مهندس صيانة'),
            ('محمد حسن', 'فني أول')
        ]
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for emp_name, position in default_employees:
            cursor.execute('''
                INSERT OR IGNORE INTO employees (name, position, created_date)
                VALUES (?, ?, ?)''', (emp_name, position, current_time))
        # بعد إدخال الموظفين الافتراضيين، عيّن أرقام أداء وهمية لمن ليس لديهم رقم
        try:
            cursor.execute("SELECT id FROM employees WHERE performance_number IS NULL OR performance_number = ''")
            rows = cursor.fetchall()
            for idx, (emp_id,) in enumerate(rows, 1):
                fake_number = f"PERF{emp_id:04d}"
                cursor.execute("UPDATE employees SET performance_number = ? WHERE id = ?", (fake_number, emp_id))
            conn.commit()
        except Exception as e:
            print(f"خطأ في تعيين أرقام الأداء الوهمية: {e}")
        
        # إدخال تصنيفات المشاكل المحسنة
        enhanced_categories = [
            ('عبث بالعداد', 'التلاعب في قراءات العداد أو كسره', '#e74c3c'),
            ('توصيلات غير شرعية', 'توصيلات غاز غير مرخصة', '#e67e22'),
            ('خطأ قراءة', 'خطأ في قراءة العداد', '#f39c12'),
            ('مشكلة فواتير', 'مشاكل في الفواتير والمدفوعات', '#9b59b6'),
            ('تغيير نشاط', 'طلب تغيير نوع النشاط', '#3498db'),
            ('تصحيح رقم عداد', 'تصحيح أرقام العدادات', '#1abc9c'),
            ('نقل رقم مشترك', 'نقل الاشتراك لموقع آخر', '#2ecc71'),
            ('كسر بالشاشة', 'كسر أو تلف شاشة العداد', '#e74c3c'),
            ('عطل عداد', 'أعطال فنية في العداد', '#c0392b'),
            ('هدم وازالة', 'طلبات هدم أو إزالة التوصيلات', '#7f8c8d'),
            ('أخرى', 'مشاكل أخرى غير مصنفة', '#95a5a6')
        ]
        
        for cat_name, description, color in enhanced_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO issue_categories (category_name, description, color_code)
                VALUES (?, ?, ?)
            ''', (cat_name, description, color))
        
        conn.commit()
        conn.close()
        # إضافة الأعمدة الناقصة بعد إنشاء الجداول (للتوافق مع قواعد بيانات قديمة)
        self.add_missing_columns()
    
    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        return sqlite3.connect(self.db_name)
    
    def execute_query(self, query, params=None):
        """تنفيذ استعلام قاعدة بيانات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            conn.commit()
            return result
        except Exception as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return []
        finally:
            conn.close()
    
    def get_employees(self, active_only=True):
        """الحصول على قائمة الموظفين"""
        query = "SELECT id, name, position FROM employees"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        return self.execute_query(query)
    
    def add_employee(self, name, position="موظف", performance_number=None):
        """إضافة موظف جديد مع رقم أداء"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = "INSERT INTO employees (name, position, performance_number, created_date) VALUES (?, ?, ?, ?)"
        try:
            self.execute_query(query, (name, position, performance_number, current_time))
            return True
        except Exception as e:
            print(f"خطأ في إضافة الموظف: {e}")
            return False

    def assign_fake_performance_numbers(self):
        """تعيين أرقام أداء وهمية للموظفين الذين ليس لديهم رقم أداء"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM employees WHERE performance_number IS NULL OR performance_number = ''")
            rows = cursor.fetchall()
            for idx, (emp_id,) in enumerate(rows, 1):
                fake_number = f"PERF{emp_id:04d}"
                cursor.execute("UPDATE employees SET performance_number = ? WHERE id = ?", (fake_number, emp_id))
            conn.commit()
        except Exception as e:
            print(f"خطأ في تعيين أرقام الأداء الوهمية: {e}")
        finally:
            conn.close()
    
    def delete_employee(self, employee_id):
        """حذف موظف (تعطيل)"""
        query = "UPDATE employees SET is_active = 0 WHERE id = ?"
        try:
            self.execute_query(query, (employee_id,))
            return True
        except:
            return False
    
    def get_cases_by_year(self, year=None):
        """الحصول على الحالات حسب السنة"""
        if year:
            query = """
                SELECT c.id, c.customer_name, c.subscriber_number, c.status, 
                       ic.category_name, ic.color_code, e.name as modified_by_name,
                       c.created_date, c.modified_date
                FROM cases c
                LEFT JOIN issue_categories ic ON c.category_id = ic.id
                LEFT JOIN employees e ON c.modified_by = e.id
                WHERE strftime('%Y', c.created_date) = ?
                ORDER BY c.modified_date DESC, c.created_date DESC
            """
            return self.execute_query(query, (str(year),))
        else:
            query = """
                SELECT c.id, c.customer_name, c.subscriber_number, c.status, 
                       ic.category_name, ic.color_code, e.name as modified_by_name,
                       c.created_date, c.modified_date
                FROM cases c
                LEFT JOIN issue_categories ic ON c.category_id = ic.id
                LEFT JOIN employees e ON c.modified_by = e.id
                ORDER BY c.modified_date DESC, c.created_date DESC
            """
            return self.execute_query(query)
    
    def search_cases(self, search_field, search_value, year=None, date_field='created_date'):
        """البحث في الحالات مع دعم الفلترة بالسنة ونوع التاريخ (دائماً يرجع قائمة dicts)"""
        columns = ['id', 'customer_name', 'subscriber_number', 'status', 'category_name', 'color_code', 'modified_by_name', 'created_date', 'modified_date']
        
        params = []
        where_clauses = []

        # Base query
        base_query = """
            SELECT DISTINCT c.id, c.customer_name, c.subscriber_number, c.status, 
                   ic.category_name, ic.color_code, e.name as modified_by_name,
                   c.created_date, c.modified_date
            FROM cases c
            LEFT JOIN issue_categories ic ON c.category_id = ic.id
            LEFT JOIN employees e ON c.modified_by = e.id
        """

        # Add joins for comprehensive search
        if search_field == "شامل" and search_value:
            base_query += """
                LEFT JOIN correspondences co ON c.id = co.case_id
                LEFT JOIN attachments a ON c.id = a.case_id
            """

        # Add search clauses based on search_field and search_value
        if search_value:
            if search_field == "شامل":
                search_pattern = f"%{search_value}%"
                where_clauses.append("""(c.customer_name LIKE ? OR c.subscriber_number LIKE ? 
                   OR c.address LIKE ? OR c.problem_description LIKE ?
                   OR c.actions_taken LIKE ? OR co.message_content LIKE ?
                   OR a.description LIKE ?)""")
                params.extend([search_pattern] * 7)
            elif search_field in ["اسم العميل", "رقم المشترك", "العنوان"]:
                field_map = {"اسم العميل": "c.customer_name", "رقم المشترك": "c.subscriber_number", "العنوان": "c.address"}
                where_clauses.append(f"{field_map[search_field]} LIKE ?")
                params.append(f"%{search_value}%")
            elif search_field in ["تصنيف المشكلة", "حالة المشكلة", "اسم الموظف"]:
                field_map = {"تصنيف المشكلة": "ic.category_name", "حالة المشكلة": "c.status", "اسم الموظف": "e.name"}
                where_clauses.append(f"{field_map[search_field]} = ?")
                params.append(search_value)

        # Add year filter
        if year and year != "الكل":
            # تحديد حقل التاريخ بناءً على المدخل
            valid_date_fields = {'created_date': 'c.created_date', 'received_date': 'c.received_date'}
            date_column = valid_date_fields.get(date_field, 'c.created_date')
            where_clauses.append(f"strftime('%Y', {date_column}) = ?")
            params.append(str(year))

        # Construct final query
        query = base_query
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY c.modified_date DESC, c.created_date DESC"

        rows = self.execute_query(query, tuple(params))
        return [dict(zip(columns, row)) for row in rows]
    
    def get_case_details(self, case_id):
        """الحصول على تفاصيل حالة محددة"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # هذا يجعل كل صف عبارة عن dict تلقائيًا
        cursor = conn.cursor()
        query = """
            SELECT c.*, ic.category_name, ic.color_code,
                   creator.name as created_by_name,
                   modifier.name as modified_by_name,
                   solver.name as solved_by_name
            FROM cases c
            LEFT JOIN issue_categories ic ON c.category_id = ic.id
            LEFT JOIN employees creator ON c.created_by = creator.id
            LEFT JOIN employees modifier ON c.modified_by = modifier.id
            LEFT JOIN employees solver ON c.solved_by = solver.id
            WHERE c.id = ?
        """
        cursor.execute(query, (case_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)  # ترجع dict مباشرة بالأسماء الصحيحة
        return None
    
    def get_case_correspondences(self, case_id):
        """الحصول على مراسلات الحالة"""
        query = """
            SELECT co.*, e.name as created_by_name
            FROM correspondences co
            LEFT JOIN employees e ON co.created_by = e.id
            WHERE co.case_id = ?
            ORDER BY co.sent_date DESC
        """
        return self.execute_query(query, (case_id,))
    
    def get_case_attachments(self, case_id):
        """الحصول على مرفقات الحالة مع تحديد الأعمدة بشكل صريح لتجنب الأخطاء."""
        query = """
            SELECT 
                a.id, a.case_id, a.file_name, a.file_path, a.file_type, 
                a.description, a.upload_date, a.uploaded_by, e.name as uploaded_by_name
            FROM attachments a
            LEFT JOIN employees e ON a.uploaded_by = e.id
            WHERE a.case_id = ?
            ORDER BY a.upload_date DESC
        """
        return self.execute_query(query, (case_id,))
    
    def get_case_audit_log(self, case_id):
        """الحصول على سجل تعديلات الحالة"""
        query = """
            SELECT al.*, e.name as performed_by_name
            FROM audit_log al
            LEFT JOIN employees e ON al.performed_by = e.id
            WHERE al.case_id = ?
            ORDER BY al.timestamp DESC
        """
        return self.execute_query(query, (case_id,))
    
    def get_categories(self):
        """الحصول على تصنيفات المشاكل"""
        query = "SELECT id, category_name, color_code FROM issue_categories ORDER BY category_name"
        return self.execute_query(query)
    
    def get_status_options(self):
        """الحصول على خيارات الحالة"""
        return [
            ('جديدة', '#3498db'),
            ('قيد التنفيذ', '#f39c12'), 
            ('تم حلها', '#27ae60'),
            ('مغلقة', '#95a5a6')
        ]
    
    def get_next_correspondence_numbers(self, case_id):
        """الحصول على أرقام المراسلة التالية"""
        # رقم تسلسلي خاص بالحالة
        case_seq_query = "SELECT COALESCE(MAX(case_sequence_number), 0) + 1 FROM correspondences WHERE case_id = ?"
        case_seq_result = self.execute_query(case_seq_query, (case_id,))
        case_sequence = case_seq_result[0][0] if case_seq_result else 1
        
        # رقم تسلسلي عام على مستوى السنة
        current_year = datetime.now().year
        yearly_seq_query = """
            SELECT COALESCE(MAX(CAST(SUBSTR(yearly_sequence_number, 1, INSTR(yearly_sequence_number, '-') - 1) AS INTEGER)), 0) + 1
            FROM correspondences 
            WHERE yearly_sequence_number LIKE ?
        """
        yearly_seq_result = self.execute_query(yearly_seq_query, (f"%-{current_year}",))
        yearly_sequence = yearly_seq_result[0][0] if yearly_seq_result and yearly_seq_result[0][0] else 1
        yearly_sequence_number = f"{yearly_sequence}-{current_year}"
        
        return case_sequence, yearly_sequence_number
    
    def log_action(self, case_id, action_type, action_description, performed_by, old_values=None, new_values=None):
        """تسجيل إجراء في سجل التعديلات مع حفظ اسم الموظف بشكل دائم"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # جلب اسم الموظف الحالي
        emp_name = None
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM employees WHERE id = ?", (performed_by,))
            row = cursor.fetchone()
            if row:
                emp_name = row[0]
        except Exception:
            pass
        finally:
            conn.close()
        query = """
            INSERT INTO audit_log (case_id, action_type, action_description, performed_by, timestamp, old_values, new_values, performed_by_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_query(query, (case_id, action_type, action_description, performed_by, timestamp, str(old_values) if old_values else None, str(new_values) if new_values else None, emp_name))
    
    def add_case(self, case_data):
        """إضافة حالة جديدة"""
        query = '''
            INSERT INTO cases (
                customer_name, subscriber_number, phone, address, category_id, status, 
                problem_description, actions_taken, last_meter_reading, last_reading_date, 
                debt_amount, received_date, created_date, created_by, modified_date, modified_by, solved_by, solved_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            case_data.get('customer_name'),
            case_data.get('subscriber_number'),
            case_data.get('phone'),
            case_data.get('address'),
            case_data.get('category_id'),
            case_data.get('status', 'جديدة'),
            case_data.get('problem_description'),
            case_data.get('actions_taken'),
            case_data.get('last_meter_reading'),
            case_data.get('last_reading_date'),
            case_data.get('debt_amount', 0),
            case_data.get('received_date'),
            case_data.get('created_date'),
            case_data.get('created_by'),
            case_data.get('modified_date'),
            case_data.get('modified_by'),
            case_data.get('solved_by'),
            case_data.get('solved_date')
        )
        print("PARAMS TO SAVE:", params)
        self.execute_query(query, params)

    def update_case(self, case_id, case_data):
        """تحديث بيانات حالة"""
        query = '''
            UPDATE cases SET
                customer_name=?, subscriber_number=?, phone=?, address=?, category_id=?, status=?,
                problem_description=?, actions_taken=?, last_meter_reading=?, last_reading_date=?,
                debt_amount=?, received_date=?, modified_date=?, modified_by=?, solved_by=?, solved_date=?
            WHERE id=?
        '''
        params = (
            case_data.get('customer_name'),
            case_data.get('subscriber_number'),
            case_data.get('phone'),
            case_data.get('address'),
            case_data.get('category_id'),
            case_data.get('status'),
            case_data.get('problem_description'),
            case_data.get('actions_taken'),
            case_data.get('last_meter_reading'),
            case_data.get('last_reading_date'),
            case_data.get('debt_amount'),
            case_data.get('received_date'),
            case_data.get('modified_date'),
            case_data.get('modified_by'),
            case_data.get('solved_by'),
            case_data.get('solved_date'),
            case_id
        )
        self.execute_query(query, params)

    def add_attachment(self, attachment_data):
        """إضافة مرفق جديد"""
        query = '''
            INSERT INTO attachments (
                case_id, file_name, file_path, file_type, description, upload_date, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            attachment_data.get('case_id'),
            attachment_data.get('file_name'),
            attachment_data.get('file_path'),
            attachment_data.get('file_type'),
            attachment_data.get('description'),
            attachment_data.get('upload_date'),
            attachment_data.get('uploaded_by')
        )
        self.execute_query(query, params)

    def add_correspondence(self, correspondence_data):
        """إضافة مراسلة جديدة"""
        query = '''
            INSERT INTO correspondences (
                case_id, case_sequence_number, yearly_sequence_number, sender, message_content, sent_date, created_by, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            correspondence_data.get('case_id'),
            correspondence_data.get('case_sequence_number'),
            correspondence_data.get('yearly_sequence_number'),
            correspondence_data.get('sender'),
            correspondence_data.get('message_content'),
            correspondence_data.get('sent_date'),
            correspondence_data.get('created_by'),
            correspondence_data.get('created_date')
        )
        self.execute_query(query, params)

    def get_all_cases(self):
        """الحصول على جميع الحالات كقوائم dict مع العنوان وتاريخ الورود"""
        query = '''
            SELECT c.id, c.customer_name, c.address, c.subscriber_number, c.status, 
                   ic.category_name, ic.color_code, e.name as modified_by_name,
                   c.received_date, c.created_date, c.modified_date
            FROM cases c
            LEFT JOIN issue_categories ic ON c.category_id = ic.id
            LEFT JOIN employees e ON c.modified_by = e.id
            ORDER BY c.modified_date DESC, c.created_date DESC
        '''
        rows = self.execute_query(query)
        columns = ['id', 'customer_name', 'customer_address', 'subscriber_number', 'status', 'category_name', 'color_code', 'modified_by_name', 'received_date', 'created_date', 'modified_date']
        return [dict(zip(columns, row)) for row in rows]

    def get_attachments(self, case_id):
        """الحصول على مرفقات الحالة (واجهة مختصرة)"""
        # يعيد قائمة dicts متوافقة مع الواجهة
        rows = self.get_case_attachments(case_id)
        columns = ['id', 'case_id', 'file_name', 'file_path', 'file_type', 'description', 'upload_date', 'uploaded_by', 'uploaded_by_name']
        return [dict(zip(columns, row)) for row in rows]

    def get_correspondences(self, case_id):
        """الحصول على مراسلات الحالة (واجهة مختصرة)"""
        rows = self.get_case_correspondences(case_id)
        columns = ['id', 'case_id', 'case_sequence_number', 'yearly_sequence_number', 'sender', 'message_content', 'sent_date', 'created_by', 'created_date', 'created_by_name']
        return [dict(zip(columns, row)) for row in rows]

    def delete_attachment(self, attachment_id):
        """حذف مرفق حسب رقم المرفق"""
        query = "DELETE FROM attachments WHERE id = ?"
        self.execute_query(query, (attachment_id,))

    def delete_correspondence(self, correspondence_id):
        """حذف مراسلة حسب رقم المراسلة"""
        query = "DELETE FROM correspondences WHERE id = ?"
        self.execute_query(query, (correspondence_id,))

    def add_missing_columns(self):
        """إضافة الأعمدة الناقصة (مثل received_date) إذا لم تكن موجودًا، وأجعلها تُنفذ تلقائيًا عند تهيئة قاعدة البيانات."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # تحقق من وجود العمود
        cursor.execute("PRAGMA table_info(cases)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'received_date' not in columns:
            try:
                cursor.execute("ALTER TABLE cases ADD COLUMN received_date TEXT")
                conn.commit()
                print("تم إضافة العمود received_date بنجاح.")
            except Exception as e:
                print(f"[ERROR] فشل في إضافة العمود received_date: {e}")
        # أضف عمود performed_by_name إذا لم يكن موجودًا
        cursor.execute("PRAGMA table_info(audit_log)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'performed_by_name' not in columns:
            try:
                cursor.execute("ALTER TABLE audit_log ADD COLUMN performed_by_name TEXT")
                conn.commit()
                print("تم إضافة العمود performed_by_name بنجاح.")
            except Exception as e:
                print(f"[ERROR] فشل في إضافة العمود performed_by_name: {e}")
        conn.close()

# إنشاء مثيل قاعدة البيانات المحسنة
enhanced_db = DatabaseManager()