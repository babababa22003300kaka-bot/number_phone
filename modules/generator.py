#!/usr/bin/env python3
"""
وحدة توليد الروابط (Functional Generator)
التزام صارم بمعايير RFC 1035 / RFC 1123
النسخة: 2.3 (Smart Patterns + Names + Locations)
"""

import random
import re
import string
from typing import List

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. دالة التحقق (Validator)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_valid_label(label: str) -> bool:
    """
    التحقق من صحة التسمية (Label) وفقاً لمعايير DNS.
    
    القواعد:
    1. الأحرف المسموحة: a-z, 0-9, -
    2. لا تبدأ ولا تنتهي بشرطة (-).
    3. الطول: 1 - 63 حرف.
    4. لا تحتوي على شرطة سفلية (_) أو مسافات.
    """
    # التحقق من الطول
    if not (1 <= len(label) <= 63):
        return False
    
    # التحقق من النمط العام (Regex)
    pattern = r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$'
    
    if not re.match(pattern, label):
        return False
        
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. دوال مساعدة (Helper Functions)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _generate_random_number(min_length=1, max_length=4) -> str:
    """
    توليد سلسلة أرقام عشوائية بطول متغير
    
    التحديث الجديد: ✅
    - بدل رقم واحد (123)، بنولد سلسلة (1234)
    - الطول من 1 إلى 4 أرقام
    """
    length = random.randint(min_length, max_length)
    return ''.join(random.choice('0123456789') for _ in range(length))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. دوال الأنماط (Pattern Functions)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _pattern_single_word(word_list: List[str]) -> str:
    """نمط: كلمة واحدة عشوائية"""
    if not word_list: return "test"
    return random.choice(word_list).lower()

def _pattern_word_combo(word_list: List[str]) -> str:
    """نمط: كلمتين مدمجين"""
    if not word_list: return "testsite"
    w1 = random.choice(word_list)
    w2 = random.choice(word_list)
    return f"{w1}{w2}".lower()

def _pattern_word_hyphen_word(word_list: List[str]) -> str:
    """نمط: كلمتين بينهما شرطة"""
    if not word_list: return "test-site"
    w1 = random.choice(word_list)
    w2 = random.choice(word_list)
    return f"{w1}-{w2}".lower()

def _pattern_word_number(word_list: List[str]) -> str:
    """نمط: كلمة + أرقام (محدث ✅)"""
    if not word_list: return "site123"
    word = random.choice(word_list)
    num = _generate_random_number()
    return f"{word}{num}".lower()

def _pattern_pure_random(word_list: List[str] = None) -> str:
    """نمط: حروف وأرقام عشوائية تماماً"""
    length = random.randint(4, 10)
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. الأنماط الجديدة (NEW PATTERNS) ✨
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _pattern_name_location(names: List[str], locations: List[str]) -> str:
    """نمط جديد: اسم-مدينة (مثال: ahmed-cairo)"""
    if not names or not locations:
        return "user-city"
    name = random.choice(names).lower()
    location = random.choice(locations).lower()
    return f"{name}-{location}"

def _pattern_word_name(words: List[str], names: List[str]) -> str:
    """نمط جديد: كلمة-اسم (مثال: signup-ahmed)"""
    if not words or not names:
        return "service-user"
    word = random.choice(words).lower()
    name = random.choice(names).lower()
    return f"{word}-{name}"

def _pattern_name_number(names: List[str]) -> str:
    """نمط جديد: اسم + أرقام (مثال: ahmed1234)"""
    if not names:
        return "user123"
    name = random.choice(names).lower()
    num = _generate_random_number()
    return f"{name}{num}"

def _pattern_word_name_number(words: List[str], names: List[str]) -> str:
    """نمط جديد: كلمة-اسم-رقم (مثال: login-ahmed-123)"""
    if not words or not names:
        return "service-user-123"
    word = random.choice(words).lower()
    name = random.choice(names).lower()
    num = _generate_random_number()
    return f"{word}-{name}-{num}"

def _pattern_location_word(locations: List[str], words: List[str]) -> str:
    """نمط جديد: مدينة-كلمة (مثال: cairo-shop)"""
    if not locations or not words:
        return "city-service"
    location = random.choice(locations).lower()
    word = random.choice(words).lower()
    return f"{location}-{word}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. الدالة الرئيسية (Main Generator)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_urls(
    count: int, 
    domains: List[str], 
    word_list: List[str],
    names: List[str] = None,
    locations: List[str] = None
) -> List[str]:
    """
    توليد قائمة من الروابط الصالحة.
    
    Args:
        count: عدد الروابط المطلوب.
        domains: قائمة النطاقات (TLDs).
        word_list: قاموس الكلمات.
        names: قائمة الأسماء (اختياري).
        locations: قائمة المواقع الجغرافية (اختياري).
        
    Returns:
        List[str]: قائمة الروابط الكاملة (https://...).
    """
    results = []
    
    # إذا لم يتم توفير أسماء/مواقع، نستخدم القوائم الافتراضية
    names = names or word_list
    locations = locations or word_list
    
    # قائمة الأنماط المتاحة (القديمة + الجديدة)
    patterns = [
        # الأنماط القديمة (محدثة ✅)
        lambda: _pattern_single_word(word_list),
        lambda: _pattern_word_combo(word_list),
        lambda: _pattern_word_hyphen_word(word_list),
        lambda: _pattern_word_number(word_list),
        lambda: _pattern_pure_random(),
        
        # الأنماط الجديدة ✨
        lambda: _pattern_name_location(names, locations),
        lambda: _pattern_word_name(word_list, names),
        lambda: _pattern_name_number(names),
        lambda: _pattern_word_name_number(word_list, names),
        lambda: _pattern_location_word(locations, word_list),
    ]
    
    while len(results) < count:
        # 1. اختيار نمط عشوائي وتوليد تسمية (Label)
        pattern_func = random.choice(patterns)
        
        try:
            label = pattern_func()
        except Exception:
            label = _pattern_pure_random()
            
        # 2. التحقق من صحة التسمية (Validation)
        if not is_valid_label(label):
            continue
            
        # 3. اختيار نطاق (TLD)
        if not domains:
            domain = "com"
        else:
            domain = random.choice(domains)
            
        # 4. بناء الرابط الكامل
        fqdn = f"{label}.{domain}"
        if len(fqdn) > 253:
            continue
            
        full_url = f"https://{fqdn}"
        results.append(full_url)
        
    return results