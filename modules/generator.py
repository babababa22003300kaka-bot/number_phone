#!/usr/bin/env python3
"""توليد المواقع العشوائية"""

from typing import List
from faker import Faker
import random

class URLGenerator:
    """مولد الروابط العشوائية"""
    
    def __init__(self, domains: List[str]):
        self.domains = domains
        self.faker = Faker()
        
        # أنماط توليد مختلفة
        self.patterns = [
            self._pattern_full_name,
            self._pattern_company,
            self._pattern_word_combo,
            self._pattern_brand
        ]
    
    def _pattern_full_name(self) -> str:
        """نمط: الاسم الكامل بدون مسافات"""
        name = self.faker.name().lower().replace(" ", "")
        return name
    
    def _pattern_company(self) -> str:
        """نمط: اسم شركة"""
        company = self.faker.company().lower()
        company = company.replace(" ", "").replace(",", "").replace(".", "")
        return company[:20]  # حد أقصى 20 حرف
    
    def _pattern_word_combo(self) -> str:
        """نمط: كلمتين مدمجين"""
        word1 = self.faker.word()
        word2 = self.faker.word()
        return f"{word1}{word2}".lower()
    
    def _pattern_brand(self) -> str:
        """نمط: براند عشوائي"""
        colors = ['blue', 'red', 'green', 'smart', 'fast', 'pro', 'tech', 'cloud']
        nouns = ['box', 'hub', 'net', 'link', 'connect', 'wave', 'sync', 'plus']
        return random.choice(colors) + random.choice(nouns)
    
    def generate(self, count: int = 1) -> List[str]:
        """توليد عدد من الروابط"""
        urls = []
        for _ in range(count):
            # اختيار نمط عشوائي
            pattern_func = random.choice(self.patterns)
            name = pattern_func()
            
            # اختيار دومين عشوائي
            domain = random.choice(self.domains)
            
            # بناء الرابط
            url = f"https://{name}.{domain}"
            urls.append(url)
        
        return urls