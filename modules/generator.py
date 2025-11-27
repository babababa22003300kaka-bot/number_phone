#!/usr/bin/env python3
"""
وحدة توليد الروابط (Functional Generator)
التزام صارم بمعايير RFC 1035 / RFC 1123
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
    # ^[a-z0-9]      : يبدأ بحرف أو رقم
    # ([a-z0-9-]*    : يمكن أن يحتوي على أحرف، أرقام، أو شرطات في المنتصف
    # [a-z0-9])?$    : ينتهي بحرف أو رقم (اختياري للحروف الواحدة)
    pattern = r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$'
    
    if not re.match(pattern, label):
        return False
        
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. دوال الأنماط (Pattern Functions)
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
    """نمط: كلمة ورقم عشوائي"""
    if not word_list: return "site123"
    word = random.choice(word_list)
    num = random.randint(1, 999)
    return f"{word}{num}".lower()

def _pattern_pure_random(word_list: List[str] = None) -> str:
    """نمط: حروف وأرقام عشوائية تماماً"""
    length = random.randint(4, 10)
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. الدالة الرئيسية (Main Generator)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_urls(count: int, domains: List[str], word_list: List[str]) -> List[str]:
    """
    توليد قائمة من الروابط الصالحة.
    
    Args:
        count: عدد الروابط المطلوب.
        domains: قائمة النطاقات (TLDs).
        word_list: قاموس الكلمات.
        
    Returns:
        List[str]: قائمة الروابط الكاملة (https://...).
    """
    results = []
    
    # قائمة الأنماط المتاحة
    patterns = [
        _pattern_single_word,
        _pattern_word_combo,
        _pattern_word_hyphen_word,
        _pattern_word_number,
        _pattern_pure_random
    ]
    
    while len(results) < count:
        # 1. اختيار نمط عشوائي وتوليد تسمية (Label)
        pattern_func = random.choice(patterns)
        
        # بعض الأنماط قد لا تحتاج word_list، لكن نمررها للتوحيد
        try:
            label = pattern_func(word_list)
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
        # التحقق من طول FQDN (Label + . + Domain) <= 253
        fqdn = f"{label}.{domain}"
        if len(fqdn) > 253:
            continue
            
        full_url = f"https://{fqdn}"
        results.append(full_url)
        
    return results