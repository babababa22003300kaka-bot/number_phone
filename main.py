#!/usr/bin/env python3
"""
بوت البحث الآلي عن مصادر OTP
الإصدار: 2.6 (Phase 3: Clean Code + Centralized Config)
"""

import asyncio
import sys
import io

from modules.analyzer import WebAnalyzer
from modules.database import HashDB
from modules.telegram_bot import TelegramNotifier
from modules import dork_scanner
from modules import generator
from config.config_manager import get_config
from config.constants import *
from modules.factory import create_analyzer, create_database, create_telegram_notifier
from modules.utils import sanitize_url
from typing import Dict, List, Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 تهيئة طباعة Unicode على Windows
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 الوظائف الأساسية (Async)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def process_url(url: str, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, scan_paths: List[str]) -> Dict:
    """فحص رابط واحد (Async with DB optimization)"""
    if hash_db:
        is_duplicate = await hash_db.is_checked(url)
        if is_duplicate:
            return {"url": url, "status": "duplicate", "confidence": 0}
    
    result = await analyzer.analyze(url, scan_paths=scan_paths)
    
    if hash_db and result:
        await hash_db.mark_checked(
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
🚀 بوت البحث الآلي - v2.6 (Phase 3)
✨ Clean Code + Centralized Config
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # 1. تحميل الإعدادات (نظام مركزي!)
    print("📦 جاري تحميل الإعدادات...")
    config = get_config()
    
    # تحميل البيانات
    domains = config.load_text_file(DOMAINS_FILE)
    words = config.load_text_file(WORDS_FILE, DEFAULT_WORDS)
    names = config.load_text_file(NAMES_FILE)
    locations = config.load_text_file(LOCATIONS_FILE)
    
    if not domains:
        print("❌ لازم تضيف دومينات في domains.txt!")
        sys.exit(1)
    
    print(f"✅ تم تحميل: {len(domains)} دومين")
    print(f"✅ القوائم: {len(words)} كلمات | {len(names)} أسماء | {len(locations)} مواقع")
    print(f"⚡ السرعة: {config.threads} Workers (AsyncIO)")
    
    # 2. إنشاء الخدمات (Factory Pattern!)
    analyzer = await create_analyzer(config)
    hash_db = await create_database(config)
    telegram = create_telegram_notifier(config)
    
    # 3. تشغيل الـ Workers
    queue = asyncio.Queue()
    stats = {'checked': 0, 'found': 0}
    
    workers = [
        asyncio.create_task(worker(queue, analyzer, hash_db, config.confidence_threshold, telegram, stats, config.scan_paths))
        for _ in range(config.threads)
    ]
    
    # 4. إضافة المصادر
    dorking_config = config.get('dorking', {})
    if dorking_config.get('enabled'):
        print(f"🔍 تفعيل Google Dorking (Mode: {dorking_config.get('scanner_mode', 'hybrid')})")
        
        dorks = config.load_text_file(DORKS_FILE)
        api_key = config.get_serpapi_key()
        
        if dorks and api_key:
            print(f"✅ تم تحميل {len(dorks)} Dorks")
            try:
                dork_urls = await dork_scanner.fetch_dork_urls(
                    dorks=dorks,
                    api_key=api_key,
                    count=DEFAULT_DORK_COUNT,
                    num_results_per_dork=DEFAULT_DORK_RESULTS_PER_QUERY
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
    
    ratio = dorking_config.get('ratio', DORKING_URL_RATIO) if dorking_config.get('enabled') else 1.0
    generated_count = int(DEFAULT_URL_GENERATION_COUNT * ratio) if dorking_config.get('enabled') else DEFAULT_URL_GENERATION_COUNT
    
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