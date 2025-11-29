#!/usr/bin/env python3
"""
Enhanced Database - Functional Style  
نظام قاعدة البيانات المحسّن - دوال بسيطة!

النسخة: 2.0.0 (Phase 5)
"""

import hashlib
import sqlite3
import aiosqlite
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Global database pool
_db_pool = None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال الإنشاء (Database Initialization)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def init_database(db_path: str = "checked_urls.db"):
    """
    إنشاء قاعدة البيانات مع كل الجداول (Async)
    
    Args:
        db_path: مسار قاعدة البيانات
    """
    global _db_pool
    _db_pool = {'path': db_path}
    
    async with aiosqlite.connect(db_path) as conn:
        # الجدول الرئيسي (محسّن)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS checked_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                url_hash TEXT,
                status TEXT NOT NULL,
                confidence INTEGER DEFAULT 0,
                method TEXT DEFAULT 'httpx',
                phone_score INTEGER DEFAULT 0,
                verify_score INTEGER DEFAULT 0,
                signatures TEXT,
                source TEXT DEFAULT 'generator',
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول أداء الـ Dorks
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dork_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dork TEXT NOT NULL UNIQUE,
                used_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                total_confidence INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول نتائج الفحص التفصيلية
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                method TEXT NOT NULL,
                source TEXT NOT NULL,
                dork_used TEXT,
                phone_score INTEGER,
                verify_score INTEGER,
                signatures TEXT,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول استخدام API
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                api_key_email TEXT NOT NULL,
                used_count INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reset_date DATE,
                UNIQUE(service, api_key_email)
            )
        """)
        
        # Indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_url_hash ON checked_urls(url_hash)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_checked_at ON checked_urls(checked_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON checked_urls(source)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dork ON dork_performance(dork)")
        
        await conn.commit()
    print("✅ Database initialized successfully (Async)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال الـ Hash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_url_hash(url: str) -> str:
    """توليد hash للرابط"""
    return hashlib.md5(url.encode()).hexdigest()

async def is_url_checked(url: str) -> bool:
    """تحقق لو الرابط اتفحص قبل كده (Async)"""
    global _db_pool
    db_path = _db_pool['path']
    url_hash = get_url_hash(url)
    
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(
            "SELECT 1 FROM checked_urls WHERE url_hash = ?",
            (url_hash,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال التسجيل
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def mark_url_checked(
    url: str,
    status: str = "checked",
    confidence: int = 0,
    method: str = "httpx",
    source: str = "generator",
    **kwargs
):
    """
    تسجيل الرابط كـ مفحوص (Async)
    
    Args:
        url: الرابط
        status: الحالة
        confidence: درجة الثقة
        method: httpx/playwright
        source: generator/dorking
        **kwargs: phone_score, verify_score, signatures
    """
    global _db_pool
    db_path = _db_pool['path']
    url_hash = get_url_hash(url)
    
    signatures = kwargs.get('signatures', [])
    if isinstance(signatures, list):
        signatures = json.dumps(signatures)
    
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            INSERT OR REPLACE INTO checked_urls 
            (url, url_hash, status, confidence, method, phone_score, verify_score, signatures, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            url,
            url_hash,
            status,
            confidence,
            method,
            kwargs.get('phone_score', 0),
            kwargs.get('verify_score', 0),
            signatures,
            source
        ))
        
        await conn.commit()

def record_dork_usage(
    db_path: str,
    dork: str,
    success: bool = False,
    confidence: int = 0
):
    """
    تسجيل استخدام dork (د الة بسيطة)
    
    Args:
        db_path: مسار قاعدة البيانات
        dork: نص الـ dork
        success: هل نجح؟
        confidence: درجة الثقة
    """
    conn = sqlite3.connect(db_path)
    
    # تحقق من وجود الـ dork
    existing = conn.execute(
        "SELECT used_count, success_count, total_confidence FROM dork_performance WHERE dork = ?",
        (dork,)
    ).fetchone()
    
    if existing:
        new_used = existing[0] + 1
        new_success = existing[1] + (1 if success else 0)
        new_total_conf = existing[2] + (confidence if success else 0)
        
        conn.execute("""
            UPDATE dork_performance
            SET used_count = ?, success_count = ?, total_confidence = ?, last_used = CURRENT_TIMESTAMP
            WHERE dork = ?
        """, (new_used, new_success, new_total_conf, dork))
    else:
        conn.execute("""
            INSERT INTO dork_performance (dork, used_count, success_count, total_confidence)
            VALUES (?, 1, ?, ?)
        """, (dork, 1 if success else 0, confidence if success else 0))
    
    conn.commit()
    conn.close()

def record_scan_result(
    db_path: str,
    url: str,
    confidence: int,
    method: str,
    source: str,
    **kwargs
):
    """
    تسجيل نتيجة فحص مفصلة (دالة بسيطة)
    
    Args:
        db_path: مسار قاعدة البيانات
        url: الرابط
        confidence: درجة الثقة
        method: httpx/playwright
        source: generator/dorking
        **kwargs: dork_used, phone_score, verify_score, signatures, evidence
    """
    conn = sqlite3.connect(db_path)
    
    signatures = kwargs.get('signatures', [])
    if isinstance(signatures, list):
        signatures = json.dumps(signatures)
    
    evidence = kwargs.get('evidence', {})
    if isinstance(evidence, dict):
        evidence = json.dumps(evidence)
    
    conn.execute("""
        INSERT INTO scan_results
        (url, confidence, method, source, dork_used, phone_score, verify_score, signatures, evidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url,
        confidence,
        method,
        source,
        kwargs.get('dork_used'),
        kwargs.get('phone_score', 0),
        kwargs.get('verify_score', 0),
        signatures,
        evidence
    ))
    
    conn.commit()
    conn.close()

def record_api_usage(
    db_path: str,
    service: str,
    email: str
):
    """
    تسجيل استخدام API key (دالة بسيطة)
    
    Args:
        db_path: مسار قاعدة البيانات
        service: اسم الخدمة
        email: البريد الإلكتروني
    """
    conn = sqlite3.connect(db_path)
    
    # تحقق من وجود السجل
    existing = conn.execute(
        "SELECT used_count FROM api_usage WHERE service = ? AND api_key_email = ?",
        (service, email)
    ).fetchone()
    
    if existing:
        conn.execute("""
            UPDATE api_usage
            SET used_count = used_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE service = ? AND api_key_email = ?
        """, (service, email))
    else:
        conn.execute("""
            INSERT INTO api_usage (service, api_key_email, used_count)
            VALUES (?, ?, 1)
        """, (service, email))
    
    conn.commit()
    conn.close()

def get_api_usage_count(
    db_path: str,
    service: str,
    email: str
) -> int:
    """
    جلب عدد استخدامات API key
    
    Args:
        db_path: مسار قاعدة البيانات
        service: اسم الخدمة
        email: البريد الإلكتروني
        
    Returns:
        int: عدد الاستخدامات
    """
    conn = sqlite3.connect(db_path)
    
    result = conn.execute(
        "SELECT used_count FROM api_usage WHERE service = ? AND api_key_email = ?",
        (service, email)
    ).fetchone()
    
    conn.close()
    return result[0] if result else 0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دالة الإحصائيات (للتوافق مع الكود القديم)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_stats(db_path: str) -> dict:
    """إحصائيات قاعدة البيانات"""
    conn = sqlite3.connect(db_path)
    
    total = conn.execute("SELECT COUNT(*) FROM checked_urls").fetchone()[0]
    success = conn.execute("SELECT COUNT(*) FROM checked_urls WHERE confidence >= 60").fetchone()[0]
    
    conn.close()
    
    return {
        "total_checked": total,
        "successful": success,
        "success_rate": (success / total * 100) if total > 0 else 0
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HashDB Class (للتوافق مع الكود القديم)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HashDB:
    """Async wrapper للتوافق مع الكود القديم"""
    
    def __init__(self, db_file: str = "checked_urls.db"):
        self.db_path = db_file
        self._initialized = False
    
    async def initialize(self):
        """تهيئة async pool"""
        if not self._initialized:
            await init_database(self.db_path)
            self._initialized = True
    
    def get_hash(self, url: str) -> str:
        return get_url_hash(url)
    
    async def is_checked(self, url: str) -> bool:
        return await is_url_checked(url)
    
    async def mark_checked(self, url: str, status: str = "checked", **kwargs):
        await mark_url_checked(url, status, **kwargs)
    
    async def get_stats(self) -> dict:
        return await get_stats()