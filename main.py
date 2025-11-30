#!/usr/bin/env python3
"""
بوت البحث الآلي عن مصادر OTP
الإصدار: 2.7 (With Logging + Metrics)
"""

import asyncio
import sys
import io

# Functional imports - دوال فقط!
from config.config_loader import *
from config.constants import *
from modules.helpers import *
from modules import dork_scanner, generator
from typing import Dict

# Phase 4: Monitoring - Step 1 & 2
from modules.logger import setup_logger, log_info, log_success, log_error
from modules.metrics import start_metrics, track_url_checked, track_url_found, print_metrics_report

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 تهيئة طباعة Unicode على Windows
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 الوظائف الأساسية (Async)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def process_url(url, analyzer, hash_db, threshold, scan_paths):
    """فحص رابط واحد - دالة بسيطة"""
    if hash_db:
        if await hash_db.is_checked(url):
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
    
    return result


async def worker(queue, analyzer, hash_db, threshold, telegram, stats, scan_paths):
    """Worker - دالة بسيطة"""
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
            
            # Step 2: Track metrics
            track_url_checked()
            
            if result:
                confidence = result.get("confidence", 0)
                status = result.get("status", "unknown")
                
                if confidence >= threshold:
                    stats['found'] += 1
                    
                    # Step 2: Track found
                    track_url_found()
                    
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
🚀 بوت البحث الآلي - v2.7
✨ With Logging + Metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # Step 1: Basic Logging
    logger = setup_logger(level="INFO", console=False)
    log_info(logger, "Bot started - v2.7 with logging and metrics")
    
    # Step 2: Start Metrics
    start_metrics()
    
    # 1. تحميل الإعدادات - دوال بسيطة!
    print("📦 جاري تحميل الإعدادات...")
    settings = load_json("config/settings.json")
    
    # تحميل الملفات
    domains = load_text_lines(f"{CONFIG_DIR}/{DOMAINS_FILE}")
    html_kw = load_text_lines(f"{CONFIG_DIR}/{HTML_KEYWORDS_FILE}")
    api_kw = load_text_lines(f"{CONFIG_DIR}/{API_KEYWORDS_FILE}")
    exclude = load_text_lines(f"{CONFIG_DIR}/{EXCLUDE_FILE}")
    words = load_text_lines(f"{CONFIG_DIR}/{WORDS_FILE}", DEFAULT_WORDS)
    names = load_text_lines(f"{CONFIG_DIR}/{NAMES_FILE}")
    locations = load_text_lines(f"{CONFIG_DIR}/{LOCATIONS_FILE}")
    
    if not domains:
        print("❌ لازم تضيف دومينات في domains.txt!")
        sys.exit(1)
    
    print(f"✅ تم تحميل: {len(domains)} دومين")
    print(f"✅ القوائم: {len(words)} كلمات | {len(names)} أسماء | {len(locations)} مواقع")
    print(f"⚡ السرعة: {get_threads(settings)} Workers (AsyncIO)")
    
    # 2. إنشاء الخدمات - دوال بسيطة!
    hybrid_config = get_setting(settings, 'hybrid_system', {})
    
    analyzer = await create_analyzer(
        html_kw, api_kw, exclude,
        get_timeout(settings),
        get_max_response_size(settings),
        get_user_agent(settings),
        hybrid_config.get('browser_service_url') if hybrid_config.get('enabled') else None,
        hybrid_config.get('fallback_confidence_threshold', FALLBACK_CONFIDENCE_THRESHOLD)
    )
    
    hash_db = await create_database(
        get_hash_db_file(settings),
        use_hash_db(settings)
    )
    
    # Telegram
    telegram = None
    telegram_config = get_telegram_config(settings)
    if telegram_config:
        telegram = create_telegram(
            telegram_config['bot_token'],
            telegram_config['chat_id']
        )
    else:
        if get_setting(settings, 'telegram', {}).get('enabled'):
            print("⚠️ التليجرام: معطل (تأكد من إعداد ملف .env)")
    
    # 3. تشغيل الـ Workers
    queue = asyncio.Queue()
    stats = {'checked': 0, 'found': 0}
    scan_paths = get_scan_paths(settings)
    
    workers = [
        asyncio.create_task(
            worker(queue, analyzer, hash_db, 
                   get_confidence_threshold(settings), 
                   telegram, stats, scan_paths)
        )
        for _ in range(get_threads(settings))
    ]
    
    # 4. إضافة المصادر
    dorking_config = get_setting(settings, 'dorking', {})
    if dorking_config.get('enabled'):
        print(f"🔍 تفعيل Google Dorking (Mode: {dorking_config.get('scanner_mode', 'hybrid')})")
        
        dorks = load_text_lines(f"{CONFIG_DIR}/{DORKS_FILE}")
        api_key = get_serpapi_key()
        
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
        
        # Logging & Metrics
        log_success(logger, f"Scan completed: {stats['checked']} checked, {stats['found']} found")
        print_metrics_report(logger)
        
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