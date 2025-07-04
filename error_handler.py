import logging
from tkinter import messagebox

def handle_error(message, exception=None, show_messagebox=True, level='error'):
    """
    دالة مركزية لتسجيل وعرض الأخطاء
    message: نص الخطأ
    exception: الاستثناء الأصلي (اختياري)
    show_messagebox: هل يظهر رسالة للمستخدم
    level: مستوى التسجيل ('error', 'warning', 'info')
    """
    full_message = message
    if exception:
        full_message += f"\nالتفاصيل: {exception}"
    if level == 'error':
        logging.error(full_message)
    elif level == 'warning':
        logging.warning(full_message)
    else:
        logging.info(full_message)
    if show_messagebox:
        messagebox.showerror("خطأ في النظام", full_message)
