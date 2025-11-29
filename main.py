#!/usr/bin/env python3
"""
بوت البحث الآلي عن مصادر OTP
الإصدار: 2.5 (Phase 2: Performance Optimized + Async Database)
"""

import asyncio
import json
import os
import sys
import time
import io
from pathlib import Path
from dotenv import load_dotenv

from modules.analyzer import WebAnalyzer
from modules.database import HashDB
from modules.telegram_bot import TelegramNotifier
from modules import dork_scanner
from modules import generator
from typing import Dict, List, Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 تهيئة طباعة Unicode على Windows
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 وظائف المساعدة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_config() -> Dict:
    """تحميل الإعدادات"""
    config_path = Path("config/settings.json")
    if not config_path.exists():
        print("❌ ملف settings.json مش موجود!")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_file_lines(filepath: str) -> List[str]:
    """تحميل ملف نصي"""
    path = Path(filepath)
    if not path.exists():
        if "words" in filepath:
            return ["cloud", "net", "app", "tech", "web", "data", "fast", "pro", "smart", "link"]
        print(f"⚠️ الملف {filepath} مش موجود!")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_serpapi_key() -> Optional[str]:
    """
    تحميل SerpAPI key من متغيرات البيئة
    يجرب SERP_API_KEY_1 أولاً، ثم SERP_API_KEY_2
    """
    # Try first key
    key1 = os.getenv("SERP_API_KEY_1")
    if key1 and 'YOUR_' not in key1.upper():
        return key1
    
    # Try second key
    key2 = os.getenv("SERP_API_KEY_2")
    if key2 and 'YOUR_' not in key2.upper():
        return key2
    
    return None

def sanitize_url(url: str) -> Optional[str]:
    """
    تنظيف وفحص URL قبل الاستخدام
    
    Args:
        url: الرابط
        
    Returns:
        str: الرابط المنظف أو None إذا كان غير آمن
    """
    from urllib.parse import urlparse
    
    try:
        # Parse URL
        parsed = urlparse(url)
        
        # التحقق من البروتوكول
        if parsed.scheme not in ['http', 'https']:
            return None
        
        # التحقق من وجود hostname
        if not parsed.netloc:
            return None
        
        # تنظيف من أحرف خطيرة
        dangerous_chars = ['<', '>', ';', '&', '|', '`', '$']
        if any(char in url for char in dangerous_chars):
            return None
        
        return url
        
    except Exception:
        return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 الوظائف الأساسية (Async)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def process_url(url: str, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, scan_paths: List[str]) -> Dict:
    """فحص رابط واحد (Async with DB optimization)"""
    if hash_db:
        is_duplicate = await hash_db.is_checked(url)  # ← Async!
        if is_duplicate:
            return {"url": url, "status": "duplicate", "confidence": 0}
    
    result = await analyzer.analyze(url, scan_paths=scan_paths)
    
    if hash_db and result:
        await hash_db.mark_checked(  # ← Async!
            url,
            result.get("status", "unknown"),
            confidence=result.get("confidence", 0),
            method=result.get("method", "httpx"),
            phone_score=result.get("phone_score", 0),
            verify_score=result.get("verify_score", 0),
            signatures=result.get("evidence", {}).get("signatures", [])
        )
    
    if result and result.get("confidence", 0) >= threshold:
        return result
    
    return result

async def worker(queue: asyncio.Queue, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, telegram: TelegramNotifier, stats: Dict, scan_paths: List[str]):
    """عامل (Worker) بيسحب روابط من الطابور ويفحصها"""
    while True:
        url = await queue.get()
        try:
            # تنظيف URL أولاً
            clean_url = sanitize_url(url)
            if not clean_url:
                print(f"⚠️ [SKIP] {url} (Invalid URL)")
                continue
            
            print(f"🔍 [CHECK] {clean_url} ...", end="\r")
            
            result = await process_url(clean_url, analyzer, hash_db, threshold, scan_paths)
            
            stats['checked'] += 1
            
            if result:
                confidence = result.get("confidence", 0)
                status = result.get("status", "unknown")
                
                if confidence >= threshold:
                    stats['found'] += 1
                    sigs = result.get("evidence", {}).get("signatures", [])
                    sig_text = f" [Sigs: {','.join(sigs)}]" if sigs else ""
                    print(f"✅ [FOUND] {url} (Conf: {confidence}%){sig_text} - Phone: {result.get('phone_score')}% | Verify: {result.get('verify_score')}%")
                    
                    if telegram:
                        await telegram.send_result(result)
                
                elif status == "excluded":
                    print(f"🚫 [EXCL] {url} ({result.get('reason')})")
                
                elif status == "protected":
                    print(f"🛡️ [PROT] {url} ({result.get('protection')})")
                
                elif status == "timeout":
                    print(f"⏱️ [TIME] {url} (Timeout)")
                
                elif status == "connection_error":
                    print(f"🔌 [CONN] {url} (Connection Error)")
                
                elif status == "duplicate":
                    print(f"🔄 [DUPL] {url} (Already Checked)")
                
                else:
                    print(f"❌ [FAIL] {url} (Conf: {confidence}%)")
            else:
                print(f"⚠️ [ERR ] {url} (No Result)")

        except Exception as e:
            print(f"💥 [ERR ] {url}: {str(e)}")
        
        finally:
            queue.task_done()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 البرنامج الرئيسي
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main_async():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 بوت البحث الآلي - v2.5 (Phase 2)
✨ Performance Optimized + Async DB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # 1. التحميل
    print("📦 جاري تحميل الإعدادات...")
    
    # تحميل متغيرات البيئة من ملف .env
    load_dotenv()
    
    config = load_config()
    domains = load_file_lines("config/domains.txt")
    html_keywords = load_file_lines("config/html_keywords.txt")
    api_keywords = load_file_lines("config/api_keywords.txt")
    exclude_keywords = load_file_lines("config/exclude.txt")
    words = load_file_lines("config/words.txt")
    names = load_file_lines("config/names.txt")
    locations = load_file_lines("config/locations.txt")
    
    if not domains:
        print("❌ لازم تضيف دومينات في domains.txt!")
        sys.exit(1)
    
    print(f"✅ تم تحميل: {len(domains)} دومين | {len(html_keywords)} HTML KW | {len(api_keywords)} API KW")
    print(f"✅ القوائم: {len(words)} كلمات | {len(names)} أسماء | {len(locations)} مواقع | {len(exclude_keywords)} استبعاد")
    print(f"⚡ السرعة: {config['threads']} Workers (AsyncIO)")
    
    # 2. الإعداد
    hybrid_config = config.get('hybrid_system', {})
    
    analyzer = WebAnalyzer(
        html_keywords=html_keywords,
        api_keywords=api_keywords,
        exclude_keywords=exclude_keywords,
        timeout=config['timeout'],
        max_size=config['max_response_size'],
        user_agent=config['user_agent'],
        browser_service_url=hybrid_config.get('browser_service_url') if hybrid_config.get('enabled') else None,
        fallback_threshold=hybrid_config.get('fallback_confidence_threshold', 20)
    )
    
    hash_db = None
    if config.get('use_hash_db', True):
        hash_db = HashDB(config.get('hash_db_file', 'checked_urls.db'))
        await hash_db.initialize()  # ← Async initialization!
        print("💾 Database: Initialized (Async + aiosqlite)")
    
    telegram = None
    # قراءة بيانات التليجرام من متغيرات البيئة
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if config.get('telegram', {}).get('enabled', False) and bot_token and chat_id:
        telegram = TelegramNotifier(
            bot_token=bot_token,
            chat_id=chat_id
        )
        print("📡 التليجرام: متصل (من ملف .env الآمن)")
    else:
        if config.get('telegram', {}).get('enabled', False):
            print("⚠️ التليجرام: معطل (تأكد من إعداد ملف .env)")
    
    # 3. تشغيل الـ Workers
    queue = asyncio.Queue()
    stats = {'checked': 0, 'found': 0}
    scan_paths = config.get('scan_paths', [])
    
    workers = [
        asyncio.create_task(worker(queue, analyzer, hash_db, config['confidence_threshold'], telegram, stats, scan_paths))
        for _ in range(config['threads'])
    ]
    
    # 4. إضافة المصادر
    dorking_config = config.get('dorking', {})
    if dorking_config.get('enabled'):
        print(f"🔍 تفعيل Google Dorking (Mode: {dorking_config.get('scanner_mode', 'hybrid')})")
        
        # تحميل الـ dorks من الملف
        dorks_file = dorking_config.get('dorks_file', 'config/dorks.txt')
        dorks = dork_scanner.load_dorks(dorks_file)
        
        # قراءة API key من متغيرات البيئة (أكثر أماناً)
        api_key = load_serpapi_key()
        
        if dorks and api_key:
            print(f"✅ تم تحميل {len(dorks)} Dorks")
            try:
                dork_urls = await dork_scanner.fetch_dork_urls(  # ← Async!
                    dorks=dorks,
                    api_key=api_key,
                    count=20,
                    num_results_per_dork=10
                )
                
                print(f"✅ نتائج Dorking: {len(dork_urls)} رابط")
                
                for url in dork_urls:
                    await queue.put(url)
            except Exception as e:
                print(f"⚠️ خطأ في Dorking: {e}")
        else:
            print("⚠️ Dorking: غير مفعل (تحقق من .env)")
    
    # إضافة الروابط المولدة
    total_urls = 0
    
    ratio = dorking_config.get('ratio', 0.5) if dorking_config.get('enabled') else 1.0
    generated_count = int(500 * ratio) if dorking_config.get('enabled') else 500
    
    # استخدام الدالة مباشرة
    generated_urls = generator.generate_urls(
        count=generated_count,
        domains=domains,
        word_list=words,
        names=names,
        locations=locations
    )
    
    for url in generated_urls:
        await queue.put(url)
        total_urls += 1
    
    print(f"🌐 إجمالي الروابط: {total_urls + queue.qsize()}")
    
    # 5. انتظار انتهاء كل المهام
    try:
        await queue.join()
    except KeyboardInterrupt:
        print("\n⏸️ توقف يدوي...")
    finally:
        await analyzer.close()
        
        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 الإحصائيات النهائية
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• تم فحص: {stats['checked']} موقع
• مواقع محتملة: {stats['found']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

def main():
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()