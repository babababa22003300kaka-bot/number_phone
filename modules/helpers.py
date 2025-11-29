"""
Helper Functions - دوال مساعدة
كل شيء دوال بسيطة ومباشرة - بدون classes
"""

from modules.analyzer import WebAnalyzer
from modules.database import HashDB
from modules.telegram_bot import TelegramNotifier
from typing import Dict, List, Optional
from urllib.parse import urlparse


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال إنشاء الخدمات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def create_analyzer(
    html_keywords: List[str],
    api_keywords: List[str],
    exclude_keywords: List[str],
    timeout: int,
    max_size: int,
    user_agent: str,
    browser_url: Optional[str] = None,
    fallback_threshold: int = 20
) -> WebAnalyzer:
    """إنشاء WebAnalyzer - دالة بسيطة"""
    return WebAnalyzer(
        html_keywords=html_keywords,
        api_keywords=api_keywords,
        exclude_keywords=exclude_keywords,
        timeout=timeout,
        max_size=max_size,
        user_agent=user_agent,
        browser_service_url=browser_url,
        fallback_threshold=fallback_threshold
    )


async def create_database(db_file: str, enabled: bool = True) -> Optional[HashDB]:
    """إنشاء قاعدة البيانات - دالة بسيطة"""
    if not enabled:
        return None
    
    db = HashDB(db_file)
    await db.initialize()
    print("💾 Database: Initialized (Async + aiosqlite)")
    
    return db


def create_telegram(token: str, chat_id: str) -> TelegramNotifier:
    """إنشاء Telegram notifier - دالة بسيطة"""
    print("📡 التليجرام: متصل (من ملف .env الآمن)")
    return TelegramNotifier(bot_token=token, chat_id=chat_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال Utility
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sanitize_url(url: str) -> Optional[str]:
    """
    تنظيف وفحص URL قبل الاستخدام
    
    Args:
        url: الرابط
        
    Returns:
        str: الرابط المنظف أو None إذا كان غير آمن
    """
    from config.constants import DANGEROUS_URL_CHARS, ALLOWED_URL_SCHEMES
    
    try:
        parsed = urlparse(url)
        
        # التحقق من البروتوكول
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            return None
        
        # التحقق من وجود hostname
        if not parsed.netloc:
            return None
        
        # تنظيف من أحرف خطيرة
        if any(char in url for char in DANGEROUS_URL_CHARS):
            return None
        
        return url
    except:
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Health Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_health_status(metrics_summary: dict = None) -> dict:
    """
    فحص صحة النظام - دالة بسيطة
    
    Args:
        metrics_summary: ملخص المقاييس (optional)
    
    Returns:
        Dict: حالة النظام
    """
    try:
        import psutil
        
        # Memory check
        memory = psutil.virtual_memory()
        memory_ok = memory.percent < 90
        
        # Disk check
        disk = psutil.disk_usage('/')
        disk_ok = disk.percent < 90
        
        # Process count
        try:
            process_count = len(psutil.Process().children(recursive=True))
        except:
            process_count = 0
        
        health = {
            'status': 'healthy' if (memory_ok and disk_ok) else 'warning',
            'memory_percent': round(memory.percent, 2),
            'disk_percent': round(disk.percent, 2),
            'process_count': process_count
        }
        
        if metrics_summary:
            health['metrics'] = metrics_summary
        
        return health
    
    except ImportError:
        # psutil not installed
        return {
            'status': 'unknown',
            'message': 'psutil not installed'
        }
