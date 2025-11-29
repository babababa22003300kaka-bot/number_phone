"""
Utility Functions
دوال مساعدة عامة
"""

from urllib.parse import urlparse
from typing import Optional
from config.constants import DANGEROUS_URL_CHARS, ALLOWED_URL_SCHEMES


def sanitize_url(url: str) -> Optional[str]:
    """
    تنظيف وفحص URL قبل الاستخدام
    
    Args:
        url: الرابط
        
    Returns:
        str: الرابط المنظف أو None إذا كان غير آمن
    """
    try:
        # Parse URL
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
        
    except Exception:
        return None
