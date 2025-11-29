"""
Logging Module - نظام السجلات
Functions only - بدون classes

يوفر نظام تسجيل منظم وقابل للبحث
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOG_DIR = "logs"
LOG_FILE = "bot.log"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Setup Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def setup_logger(
    log_dir: str = LOG_DIR,
    log_file: str = LOG_FILE,
    level: str = "INFO",
    console: bool = True
) -> logging.Logger:
    """
    إعداد نظام السجلات - دالة بسيطة
    
    Args:
        log_dir: مجلد السجلات
        log_file: اسم الملف
        level: مستوى التسجيل (DEBUG, INFO, WARNING, ERROR)
        console: عرض في الكونسول
    
    Returns:
        Logger: مسجل الأحداث
    """
    # Create logs directory
    Path(log_dir).mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("bot_logger")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        f"{log_dir}/{log_file}",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(console_handler)
    
    return logger


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Logging Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def log_info(logger: logging.Logger, message: str, **context):
    """
    تسجيل معلومة - دالة بسيطة
    
    Args:
        logger: المسجل
        message: الرسالة
        **context: معلومات إضافية
    """
    if context:
        message = f"{message} | {context}"
    logger.info(message)


def log_success(logger: logging.Logger, message: str, **context):
    """
    تسجيل نجاح - دالة بسيطة
    
    Args:
        logger: المسجل
        message: الرسالة
        **context: معلومات إضافية
    """
    if context:
        message = f"✅ {message} | {context}"
    else:
        message = f"✅ {message}"
    logger.info(message)


def log_warning(logger: logging.Logger, message: str, **context):
    """
    تسجيل تحذير - دالة بسيطة
    
    Args:
        logger: المسجل
        message: الرسالة
        **context: معلومات إضافية
    """
    if context:
        message = f"⚠️ {message} | {context}"
    else:
        message = f"⚠️ {message}"
    logger.warning(message)


def log_error(logger: logging.Logger, message: str, error: Optional[Exception] = None, **context):
    """
    تسجيل خطأ - دالة بسيطة
    
    Args:
        logger: المسجل
        message: الرسالة
        error: الخطأ (Exception)
        **context: معلومات إضافية
    """
    error_msg = f"❌ {message}"
    if error:
        error_msg += f" | Error: {str(error)}"
    if context:
        error_msg += f" | {context}"
    logger.error(error_msg, exc_info=error is not None)


def log_debug(logger: logging.Logger, message: str, **context):
    """
    تسجيل debug - دالة بسيطة
    
    Args:
        logger: المسجل
        message: الرسالة
        **context: معلومات إضافية
    """
    if context:
        message = f"{message} | {context}"
    logger.debug(message)
