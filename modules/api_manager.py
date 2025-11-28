#!/usr/bin/env python3
"""
API Keys Manager - Functional Style
إدارة مفاتيح API بدوال بسيطة - مفيش كلاسات!

النسخة: 1.0.0
الأسلوب: Functional Programming
"""

import json
from typing import Dict, Optional, List
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# State Management (بسيط جداً!)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_API_KEYS_STATE = {
    'keys': {},           # {service: [key_objects]}
    'current_index': {},  # {service: index}
    'loaded': False
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال التحميل
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_api_keys(filepath: str = "config/api_keys.json") -> Dict:
    """
    تحميل المفاتيح من ملف JSON
    
    Args:
        filepath: مسار ملف المفاتيح
        
    Returns:
        dict: المفاتيح بالشكل {service: [keys]}
        
    مثال:
        >>> keys = load_api_keys()
        >>> 'serpapi' in keys
        True
    """
    global _API_KEYS_STATE
    
    path = Path(filepath)
    
    if not path.exists():
        print(f"⚠️ ملف المفاتيح {filepath} مش موجود!")
        _API_KEYS_STATE['loaded'] = False
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            keys = json.load(f)
        
        # Validation
        if not isinstance(keys, dict):
            print("❌ ملف المفاتيح غير صحيح!")
            return {}
        
        # Store in state
        _API_KEYS_STATE['keys'] = keys
        _API_KEYS_STATE['loaded'] = True
        
        # Initialize indices لكل service
        for service in keys:
            _API_KEYS_STATE['current_index'][service] = 0
        
        # Print summary
        total_keys = sum(len(v) for v in keys.values())
        print(f"✅ تم تحميل {total_keys} مفاتيح من {len(keys)} خدمات")
        
        return keys
        
    except json.JSONDecodeError as e:
        print(f"❌ خطأ في قراءة JSON: {e}")
        _API_KEYS_STATE['loaded'] = False
        return {}
    except Exception as e:
        print(f"💥 خطأ في تحميل المفاتيح: {e}")
        _API_KEYS_STATE['loaded'] = False
        return {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال التدوير (Round-Robin)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_next_key(service: str) -> Optional[Dict]:
    """
    جلب المفتاح التالي من القائمة (بالتدوير)
    
    Args:
        service: اسم الخدمة ('serpapi', 'google_search', etc.)
        
    Returns:
        dict: المفتاح أو None
        
    مثال:
        >>> load_api_keys()
        >>> key = get_next_key('serpapi')
        >>> 'api_key' in key
        True
    """
    global _API_KEYS_STATE
    
    # Check if loaded
    if not _API_KEYS_STATE['loaded']:
        print("⚠️ المفاتيح غير محملة! استخدم load_api_keys() أولاً")
        return None
    
    # Get keys for service
    keys = _API_KEYS_STATE['keys'].get(service, [])
    
    if not keys:
        print(f"⚠️ مافيش مفاتيح لـ {service}!")
        return None
    
    # Get current index
    index = _API_KEYS_STATE['current_index'].get(service, 0)
    
    # Get key
    key = keys[index]
    
    # Rotate index (round-robin)
    next_index = (index + 1) % len(keys)
    _API_KEYS_STATE['current_index'][service] = next_index
    
    return key

def get_serpapi_key() -> Optional[str]:
    """
    جلب مفتاح SerpAPI (wrapper مبسط)
    
    Returns:
        str: API key أو None
        
    مثال:
        >>> api_key = get_serpapi_key()
        >>> isinstance(api_key, str)
        True
    """
    key_info = get_next_key('serpapi')
    
    if not key_info:
        return None
    
    return key_info.get('api_key')

def get_google_search_key() -> Optional[Dict]:
    """
    جلب مفتاح Google Custom Search (wrapper مبسط)
    
    Returns:
        dict: {api_key, cx} أو None
        
    مثال:
        >>> key = get_google_search_key()
        >>> 'api_key' in key and 'cx' in key
        True
    """
    return get_next_key('google_search')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال الاستعلام
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_available_services() -> List[str]:
    """
    قائمة الخدمات المتاحة
    
    Returns:
        list: أسماء الخدمات
        
    مثال:
        >>> services = get_available_services()
        >>> 'serpapi' in services
        True
    """
    global _API_KEYS_STATE
    
    if not _API_KEYS_STATE['loaded']:
        return []
    
    return list(_API_KEYS_STATE['keys'].keys())

def count_keys(service: str) -> int:
    """
    عدد المفاتيح المتاحة لخدمة
    
    Args:
        service: اسم الخدمة
        
    Returns:
        int: عدد المفاتيح
        
    مثال:
        >>> count = count_keys('serpapi')
        >>> count >= 0
        True
    """
    global _API_KEYS_STATE
    
    if not _API_KEYS_STATE['loaded']:
        return 0
    
    return len(_API_KEYS_STATE['keys'].get(service, []))

def is_loaded() -> bool:
    """
    التحقق من تحميل المفاتيح
    
    Returns:
        bool: True لو محملة
    """
    global _API_KEYS_STATE
    return _API_KEYS_STATE['loaded']

def reset_indices() -> None:
    """
    إعادة تعيين indices التدوير لكل الخدمات
    
    مفيد لو عايز تبدأ من أول مفتاح تاني
    """
    global _API_KEYS_STATE
    
    for service in _API_KEYS_STATE['current_index']:
        _API_KEYS_STATE['current_index'][service] = 0
    
    print("🔄 تم إعادة تعيين indices")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال مساعدة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_key_info(service: str) -> Dict:
    """
    معلومات عن مفاتيح خدمة معينة
    
    Args:
        service: اسم الخدمة
        
    Returns:
        dict: {count, current_index}
    """
    global _API_KEYS_STATE
    
    return {
        'service': service,
        'count': count_keys(service),
        'current_index': _API_KEYS_STATE['current_index'].get(service, 0),
        'available': count_keys(service) > 0
    }

def print_summary() -> None:
    """
    طباعة ملخص للمفاتيح المتاحة
    """
    global _API_KEYS_STATE
    
    if not _API_KEYS_STATE['loaded']:
        print("⚠️ المفاتيح غير محملة")
        return
    
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 ملخص مفاتيح API")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    for service in _API_KEYS_STATE['keys']:
        info = get_key_info(service)
        status = "✅" if info['available'] else "❌"
        print(f"{status} {service}: {info['count']} مفاتيح (Index: {info['current_index']})")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال التتبع (Usage Tracking)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def track_key_usage(service: str, email: str, db_path: str = "checked_urls.db"):
    """
    تسجيل استخدام مفتاح (دالة بسيطة)
    
    Args:
        service: اسم الخدمة
        email: البريد الإلكتروني
        db_path: مسار قاعدة البيانات
    """
    try:
        from modules.database import record_api_usage
        record_api_usage(db_path, service, email)
    except Exception as e:
        print(f"⚠️ Error tracking usage: {e}")

def check_usage_limit(service: str, email: str, limit: int, db_path: str = "checked_urls.db") -> Dict:
    """
    فحص الميزانية (دالة بسيطة)
    
    Args:
        service: اسم الخدمة
        email: البريد الإلكتروني
        limit: الحد الأقصى
        db_path: مسار قاعدة البيانات
        
    Returns:
        dict: حالة الميزانية
    """
    try:
        from modules.analytics import check_api_budget
        return check_api_budget(db_path, service, email, limit)
    except Exception as e:
        print(f"⚠️ Error checking budget: {e}")
        return {"used": 0, "limit": limit, "remaining": limit, "percentage": 0, "status": "ok"}

def get_serpapi_key_with_tracking(db_path: str = "checked_urls.db", limit: int = 100) -> Optional[str]:
    """
    جلب مفتاح SerpAPI مع تتبع وفحص ميزانية
    
    Args:
        db_path: مسار قاعدة البيانات
        limit: الحد الأقصى
        
    Returns:
        str: API key أو None
    """
    key_info = get_next_key('serpapi')
    
    if not key_info:
        return None
    
    email = key_info.get('email', 'unknown')
    
    # فحص الميزانية
    budget = check_usage_limit('serpapi', email, limit, db_path)
    
    if budget['status'] == 'critical':
        print(f"🔴 [API] {email} exceeded 90% quota ({budget['used']}/{limit})")
        # محاولة المفتاح التالي
        return get_serpapi_key_with_tracking(db_path, limit)
    
    elif budget['status'] == 'warning':
        print(f"🟡 [API] {email} at {budget['percentage']:.0f}% quota")
    
    # تسجيل الاستخدام
    track_key_usage('serpapi', email, db_path)
    
    return key_info['api_key']

