#!/usr/bin/env python3
"""
Proxy Manager - Pure Functions Only
نظام إدارة البروكسي - دوال نقية فقط

All proxy logic in simple, pure functions.
Following UNIVERSAL_PROMPT principles:
- Zero hard-coded values
- Maximum flexibility
- Absolute simplicity (pure functions only)
"""

from typing import Dict, List, Optional
from pathlib import Path
import random


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Core Proxy Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_proxy_list(config: Dict) -> Optional[List[str]]:
    """
    تحميل قائمة البروكسيات من ملف - دالة نقية
    
    Args:
        config: dict with:
            - proxy.enabled: bool
            - proxy.list_file: str (path)
    
    Returns:
        list: قائمة البروكسيات أو None
    """
    proxy_config = config.get('proxy', {})
    
    # Check if enabled
    if not proxy_config.get('enabled', False):
        return None
    
    # Get file path
    file_path = proxy_config.get('list_file', 'config/proxies.txt')
    
    # Check if file exists
    proxy_file = Path(file_path)
    if not proxy_file.exists():
        print(f"⚠️ Proxy file not found: {file_path}, continuing without proxies.")
        return None
    
    # Load proxies
    try:
        with open(proxy_file, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not proxies:
            print(f"⚠️ Proxy file is empty: {file_path}, continuing without proxies.")
            return None
        
        print(f"✅ Loaded {len(proxies)} proxies from {file_path}")
        return proxies
    
    except Exception as e:
        print(f"⚠️ Error loading proxies: {e}, continuing without proxies.")
        return None


def choose_proxy(proxy_list: Optional[List[str]], rotate: bool = True) -> Optional[str]:
    """
    اختيار بروكسي من القائمة - دالة نقية
    
    Args:
        proxy_list: قائمة البروكسيات
        rotate: True = اختيار عشوائي, False = الأول دائماً
    
    Returns:
        str: البروكسي المختار أو None
    """
    if not proxy_list:
        return None
    
    if rotate:
        return random.choice(proxy_list)
    else:
        return proxy_list[0]


def build_httpx_proxy_dict(proxy_url: Optional[str]) -> Optional[Dict]:
    """
    بناء dict للبروكسي لـ httpx - دالة نقية
    
    Args:
        proxy_url: عنوان البروكسي
    
    Returns:
        dict: {"http://": "...", "https://": "..."} أو None
    """
    if not proxy_url:
        return None
    
    # httpx format: both http and https use same proxy
    return {
        "http://": proxy_url,
        "https://": proxy_url
    }


def build_playwright_proxy_dict(proxy_url: Optional[str]) -> Optional[Dict]:
    """
    بناء dict للبروكسي لـ Playwright - دالة نقية
    
    Args:
        proxy_url: عنوان البروكسي
    
    Returns:
        dict: {"server": "...", "username": "...", "password": "..."} أو None
    """
    if not proxy_url:
        return None
    
    # Parse proxy URL
    # Format: protocol://[user:pass@]host:port
    try:
        from urllib.parse import urlparse
        
        parsed = urlparse(proxy_url)
        
        proxy_dict = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        
        if parsed.username:
            proxy_dict["username"] = parsed.username
        if parsed.password:
            proxy_dict["password"] = parsed.password
        
        return proxy_dict
    
    except Exception as e:
        print(f"⚠️ Error parsing proxy URL: {e}")
        return None


def should_use_proxy(config: Dict) -> bool:
    """
    التحقق من تفعيل البروكسي - دالة نقية
    
    Args:
        config: الإعدادات
    
    Returns:
        bool: True إذا كان البروكسي مفعل
    """
    return config.get('proxy', {}).get('enabled', False)


def mask_proxy_url(proxy_url: str) -> str:
    """
    إخفاء بيانات الاعتماد في رابط البروكسي - دالة نقية
    
    Args:
        proxy_url: الرابط الكامل
    
    Returns:
        str: الرابط بدون كلمة المرور
    """
    if not proxy_url:
        return ""
    
    # Hide credentials for logging
    if '@' in proxy_url:
        # Format: protocol://user:pass@host:port -> protocol://***@host:port
        parts = proxy_url.split('@')
        return f"***@{parts[-1]}"
    else:
        return proxy_url
