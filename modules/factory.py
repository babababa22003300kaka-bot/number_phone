"""
Factory Functions
دوال إنشاء الكائنات

تبسيط إنشاء الكائنات المعقدة
"""

from modules.analyzer import WebAnalyzer
from modules.database import HashDB
from modules.telegram_bot import TelegramNotifier
from config.config_manager import ConfigManager
from config.constants import *
from typing import Optional


async def create_analyzer(config: ConfigManager) -> WebAnalyzer:
    """
    إنشاء WebAnalyzer بكل الإعدادات
    
    Args:
        config: مدير الإعدادات
        
    Returns:
        WebAnalyzer: محلل مهيأ بالكامل
    """
    hybrid_config = config.get('hybrid_system', {})
    
    return WebAnalyzer(
        html_keywords=config.load_text_file(HTML_KEYWORDS_FILE),
        api_keywords=config.load_text_file(API_KEYWORDS_FILE),
        exclude_keywords=config.load_text_file(EXCLUDE_FILE),
        timeout=config.timeout,
        max_size=config.max_response_size,
        user_agent=config.user_agent,
        browser_service_url=hybrid_config.get('browser_service_url') if hybrid_config.get('enabled') else None,
        fallback_threshold=hybrid_config.get('fallback_confidence_threshold', FALLBACK_CONFIDENCE_THRESHOLD)
    )


async def create_database(config: ConfigManager) -> Optional[HashDB]:
    """
    إنشاء وتهيئة قاعدة البيانات
    
    Args:
        config: مدير الإعدادات
        
    Returns:
        HashDB: قاعدة بيانات مهيأة أو None
    """
    if not config.use_hash_db:
        return None
    
    hash_db = HashDB(config.hash_db_file)
    await hash_db.initialize()
    print("💾 Database: Initialized (Async + aiosqlite)")
    
    return hash_db


def create_telegram_notifier(config: ConfigManager) -> Optional[TelegramNotifier]:
    """
    إنشاء Telegram notifier
    
    Args:
        config: مدير الإعدادات
        
    Returns:
        TelegramNotifier: مُرسل التليجرام أو None
    """
    telegram_config = config.get_telegram_config()
    
    if not telegram_config:
        if config.get('telegram', {}).get('enabled'):
            print("⚠️ التليجرام: معطل (تأكد من إعداد ملف .env)")
        return None
    
    print("📡 التليجرام: متصل (من ملف .env الآمن)")
    
    return TelegramNotifier(
        bot_token=telegram_config['bot_token'],
        chat_id=telegram_config['chat_id']
    )
