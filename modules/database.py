#!/usr/bin/env python3
"""نظام الـ Hash Database لتجنب التكرار"""

import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

class HashDB:
    """قاعدة بيانات خفيفة لتخزين hash المواقع المفحوصة"""
    
    def __init__(self, db_file: str = "checked_urls.db"):
        self.db_path = Path(db_file)
        self._init_db()
    
    def _init_db(self):
        """إنشاء الجدول لو مش موجود"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checked_urls (
                    url_hash TEXT PRIMARY KEY,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON checked_urls(url_hash)")
    
    def get_hash(self, url: str) -> str:
        """توليد hash للرابط"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def is_checked(self, url: str) -> bool:
        """تحقق لو الرابط اتفحص قبل كده"""
        url_hash = self.get_hash(url)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM checked_urls WHERE url_hash = ?", 
                (url_hash,)
            )
            return cursor.fetchone() is not None
    
    def mark_checked(self, url: str, status: str = "checked"):
        """تسجيل الرابط كـ مفحوص"""
        url_hash = self.get_hash(url)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO checked_urls (url_hash, status) VALUES (?, ?)",
                (url_hash, status)
            )
    
    def get_stats(self) -> dict:
        """إحصائيات قاعدة البيانات"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM checked_urls")
            total = cursor.fetchone()[0]
            return {"total_checked": total}