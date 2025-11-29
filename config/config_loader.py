"""
Config Loader - دوال تحميل الإعدادات
كل شيء دوال بسيطة - بدون classes!
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# تحميل .env مرة واحدة عند الاستيراد
load_dotenv()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال تحميل الملفات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_json(filepath: str) -> Dict:
    """تحميل ملف JSON"""
    path = Path(filepath)
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_text_lines(filepath: str, default: List[str] = None) -> List[str]:
    """تحميل ملف نصي كقائمة"""
    path = Path(filepath)
    
    if not path.exists():
        return default or []
    
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال جلب الإعدادات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_setting(settings: Dict, key: str, default=None):
    """
    جلب إعداد - يفضل Environment Variable أولاً
    
    Priority: ENV → settings.json → default
    """
    # Try environment variable first
    env_value = os.getenv(key.upper())
    if env_value is not None:
        return env_value
    
    # Try settings dict
    if key in settings:
        return settings[key]
    
    # Return default
    return default


def get_serpapi_key() -> Optional[str]:
    """جلب SerpAPI key من البيئة"""
    # Try first key
    key1 = os.getenv("SERP_API_KEY_1")
    if key1 and 'YOUR_' not in key1.upper():
        return key1
    
    # Try second key
    key2 = os.getenv("SERP_API_KEY_2")
    if key2 and 'YOUR_' not in key2.upper():
        return key2
    
    return None


def get_telegram_config(settings: Dict) -> Optional[Dict]:
    """جلب إعدادات التليجرام"""
    telegram_settings = settings.get('telegram', {})
    
    if not telegram_settings.get('enabled'):
        return None
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        return {
            'bot_token': token,
            'chat_id': chat_id
        }
    
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال مساعدة للوصول السريع
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_threads(settings: Dict) -> int:
    """عدد الـ Workers"""
    return get_setting(settings, 'threads', 5)


def get_timeout(settings: Dict) -> int:
    """Timeout بالثواني"""
    return get_setting(settings, 'timeout', 10)


def get_confidence_threshold(settings: Dict) -> int:
    """حد الثقة"""
    return get_setting(settings, 'confidence_threshold', 60)


def get_max_response_size(settings: Dict) -> int:
    """أقصى حجم للـ response"""
    return get_setting(settings, 'max_response_size', 3145728)


def get_user_agent(settings: Dict) -> str:
    """User Agent"""
    return get_setting(settings, 'user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')


def get_hash_db_file(settings: Dict) -> str:
    """ملف قاعدة البيانات"""
    return get_setting(settings, 'hash_db_file', 'checked_urls.db')


def use_hash_db(settings: Dict) -> bool:
    """استخدام قاعدة البيانات"""
    return get_setting(settings, 'use_hash_db', True)


def get_scan_paths(settings: Dict) -> List[str]:
    """مسارات الفحص"""
    return get_setting(settings, 'scan_paths', [])
