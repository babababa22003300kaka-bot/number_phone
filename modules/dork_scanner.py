#!/usr/bin/env python3
"""
Google Dorking Scanner - Functional Style
البحث الموجه باستخدام Google Dorking - دوال بسيطة

النسخة: 1.0.0
الأسلوب: Functional Programming (دوال فقط - مفيش كلاسات!)
"""

import random
import requests
from typing import List, Dict, Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال تحميل الإعدادات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_dorks(filepath: str) -> List[str]:
    """
    تحميل استعلامات الـ Dorks من ملف
    
    Args:
        filepath: مسار ملف dorks.txt
        
    Returns:
        list: قائمة استعلامات البحث
        
    مثال:
        >>> dorks = load_dorks("config/dorks.txt")
        >>> len(dorks)
        15
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            dorks = [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
        
        print(f"✅ تم تحميل {len(dorks)} Dorks")
        return dorks
        
    except FileNotFoundError:
        print(f"⚠️ الملف {filepath} مش موجود!")
        return []
    except Exception as e:
        print(f"💥 خطأ في تحميل Dorks: {e}")
        return []

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال البحث (SerpAPI)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def search_with_serpapi(
    dork: str, 
    api_key: str, 
    num_results: int = 10,
    timeout: int = 10
) -> List[Dict]:
    """
    بحث باستخدام SerpAPI
    
    Args:
        dork: استعلام البحث (Google Dork)
        api_key: مفتاح SerpAPI
        num_results: عدد النتائج المطلوبة (1-100)
        timeout: timeout بالثواني
        
    Returns:
        list: قائمة النتائج، كل عنصر dict
        
    مثال:
        >>> results = search_with_serpapi('site:.io "phone verification"', 'API_KEY')
        >>> len(results)
        10
    """
    url = "https://serpapi.com/search"
    params = {
        'q': dork,
        'api_key': api_key,
        'num': min(num_results, 100),  # Max 100
        'hl': 'en',
        'gl': 'us'
    }
    
    try:
        response = requests.get(url, params=params, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('organic_results', [])
            return results
        
        elif response.status_code == 401:
            print("❌ SerpAPI: Invalid API Key")
            return []
        
        elif response.status_code == 429:
            print("⚠️ SerpAPI: Rate limit exceeded")
            return []
        
        else:
            print(f"❌ SerpAPI Error: {response.status_code}")
            return []
            
    except requests.Timeout:
        print(f"⏱️ SerpAPI Timeout after {timeout}s")
        return []
    except Exception as e:
        print(f"💥 SerpAPI Exception: {e}")
        return []

def extract_urls_from_results(results: List[Dict]) -> List[str]:
    """
    استخراج الروابط من نتائج البحث
    
    Args:
        results: نتائج SerpAPI (list of dicts)
        
    Returns:
        list: قائمة الروابط النظيفة
        
    مثال:
        >>> results = [{'link': 'https://example.com/signup?ref=x'}]
        >>> extract_urls_from_results(results)
        ['https://example.com/signup']
    """
    urls = []
    
    for result in results:
        link = result.get('link')
        
        if not link:
            continue
        
        # تأكد إنه HTTP/HTTPS
        if not link.startswith(('http://', 'https://')):
            continue
        
        # تنظيف الرابط
        # إزالة query parameters (اختياري)
        clean_link = link.split('?')[0] if '?' in link else link
        
        # إزالة trailing slash
        clean_link = clean_link.rstrip('/')
        
        urls.append(clean_link)
    
    return urls

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الدالة الرئيسية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_dork_urls(
    dorks: List[str],
    api_key: str,
    count: int = 20,
    num_results_per_dork: int = 10
) -> List[str]:
    """
    جلب روابط باستخدام Google Dorking
    
    Args:
        dorks: قائمة استعلامات البحث
        api_key: مفتاح SerpAPI
        count: عدد الروابط المطلوبة إجمالاً
        num_results_per_dork: عدد النتائج لكل dork
        
    Returns:
        list: قائمة الروابط المستخرجة
        
    مثال:
        >>> dorks = ["site:.io phone", "inurl:signup mobile"]
        >>> urls = fetch_dork_urls(dorks, "API_KEY", count=20)
        >>> len(urls) <= 20
        True
    """
    # Validation
    if not dorks:
        print("⚠️ [DORK] مافيش Dorks للبحث!")
        return []
    
    if not api_key or 'YOUR_' in api_key.upper():
        print("⚠️ [DORK] API Key مش صحيح!")
        return []
    
    all_urls = []
    
    # اختر Dork عشوائي
    dork = random.choice(dorks)
    print(f"🔎 [DORK] Searching: {dork[:60]}...")
    
    # ابحث
    results = search_with_serpapi(
        dork, 
        api_key, 
        num_results=num_results_per_dork
    )
    
    if not results:
        print("⚠️ [DORK] No results found")
        return []
    
    # استخرج الروابط
    urls = extract_urls_from_results(results)
    all_urls.extend(urls)
    
    print(f"✅ [DORK] Found {len(urls)} URLs")
    
    # لو عايزين أكثر، نعمل dork تاني
    if len(all_urls) < count and len(dorks) > 1:
        # اختر dork مختلف
        remaining_dorks = [d for d in dorks if d != dork]
        if remaining_dorks:
            dork2 = random.choice(remaining_dorks)
            print(f"🔎 [DORK] Additional search: {dork2[:60]}...")
            
            results2 = search_with_serpapi(
                dork2,
                api_key,
                num_results=count - len(all_urls)
            )
            
            urls2 = extract_urls_from_results(results2)
            all_urls.extend(urls2)
            print(f"✅ [DORK] Found {len(urls2)} more URLs")
    
    # إرجاع العدد المطلوب فقط
    return all_urls[:count]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال مساعدة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def validate_dork(dork: str) -> bool:
    """
    التحقق من صحة استعلام Dork
    
    Args:
        dork: استعلام البحث
        
    Returns:
        bool: True لو صحيح
    """
    if not dork or len(dork) < 3:
        return False
    
    # لو فيه أحرف غريبة أو رموز خطيرة
    dangerous_chars = ['<', '>', ';', '&', '|']
    if any(char in dork for char in dangerous_chars):
        return False
    
    return True

def get_random_dork(dorks: List[str]) -> Optional[str]:
    """
    اختيار dork عشوائي من القائمة
    
    Args:
        dorks: قائمة الـ dorks
        
    Returns:
        str: dork عشوائي أو None
    """
    valid_dorks = [d for d in dorks if validate_dork(d)]
    
    if not valid_dorks:
        return None
    
    return random.choice(valid_dorks)
