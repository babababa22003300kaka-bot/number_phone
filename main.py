#!/usr/bin/env python3
"""
بوت البحث الآلي عن مصادر OTP
الإصدار: 2.2 (Functional Generator + Strict DNS)
"""

import asyncio
import json
import sys
import time
import io
from pathlib import Path
from typing import List, Dict

# Force UTF-8 for Windows Console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from modules.analyzer import WebAnalyzer
from modules.generator import generate_urls
from modules.telegram_bot import TelegramNotifier
from modules.database import HashDB

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📁 تحميل الإعدادات
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
        # لو ملف الكلمات مش موجود، نرجع قائمة افتراضية
        if "words" in filepath:
            return ["cloud", "net", "app", "tech", "web", "data", "fast", "pro", "smart", "link"]
        print(f"⚠️ الملف {filepath} مش موجود!")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 الوظائف الأساسية (Async)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def process_url(url: str, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, scan_paths: List[str]) -> Dict:
    """فحص رابط واحد (Async)"""
    # تحقق من الـ Hash
    if hash_db and hash_db.is_checked(url):
        return {"url": url, "status": "duplicate", "confidence": 0}
    
    # التحليل مع الـ Path Fuzzing
    result = await analyzer.analyze(url, scan_paths=scan_paths)
    
    # تسجيل في الـ Hash
    if hash_db and result:
        hash_db.mark_checked(url, result.get("status", "unknown"))
    
    # تحقق من الثقة
    if result and result.get("confidence", 0) >= threshold:
        return result
    
    return result # Return result anyway for logging

async def worker(queue: asyncio.Queue, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, telegram: TelegramNotifier, stats: Dict, scan_paths: List[str]):
    """عامل (Worker) بيسحب روابط من الطابور ويفحصها"""
    while True:
        url = await queue.get()
        try:
            # طباعة قبل الفحص (Verbose)
            print(f"🔍 [CHECK] {url} ...", end="\r")
            
            result = await process_url(url, analyzer, hash_db, threshold, scan_paths)
            
            stats['checked'] += 1
            
            # طباعة النتيجة
            if result:
                confidence = result.get("confidence", 0)
                status = result.get("status", "unknown")
                
                if confidence >= threshold:
                    stats['found'] += 1
                    print(f"✅ [FOUND] {url} (Conf: {confidence}%) - Phone: {result.get('phone_score')}% | Verify: {result.get('verify_score')}%")
                    
                    # إرسال للتليجرام
                    if telegram:
                        await telegram.send_result(result)
                
                elif status == "protected":
                    print(f"🛡️ [PROT] {url} ({result.get('protection')})")
                
                elif status == "timeout":
                    print(f"⏱️ [TIME] {url} (Timeout)")
                
                elif status == "connection_error":
                    print(f"🔌 [CONN] {url} (Connection Error)")
                
                elif status == "duplicate":
                    print(f"🔄 [DUPL] {url} (Already Checked)")
                
                else:
                    # فشل عادي (Low Confidence)
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
🚀 بوت البحث الآلي - v2.2 (Functional)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # 1. التحميل
    print("📦 جاري تحميل الإعدادات...")
    config = load_config()
    domains = load_file_lines("config/domains.txt")
    html_keywords = load_file_lines("config/html_keywords.txt")
    api_keywords = load_file_lines("config/api_keywords.txt")
    words = load_file_lines("config/words.txt") # تحميل الكلمات
    
    if not domains:
        print("❌ لازم تضيف دومينات في domains.txt!")
        sys.exit(1)
    
    print(f"✅ تم تحميل: {len(domains)} دومين | {len(html_keywords)} HTML KW | {len(api_keywords)} API KW | {len(words)} Words")
    print(f"⚡ السرعة: {config['threads']} Workers (AsyncIO)")
    
    # 2. الإعداد
    
    analyzer = WebAnalyzer(
        html_keywords=html_keywords,
        api_keywords=api_keywords,
        timeout=config['timeout'],
        max_size=config['max_response_size'],
        user_agent=config['user_agent']
    )
    
    hash_db = None
    if config.get('use_hash_db', True):
        hash_db = HashDB(config.get('hash_db_file', 'checked_urls.db'))
    
    telegram = None
    if config['telegram']['bot_token'] != "YOUR_BOT_TOKEN_HERE":
        telegram = TelegramNotifier(
            bot_token=config['telegram']['bot_token'],
            chat_id=config['telegram']['chat_id']
        )
        print("📡 التليجرام: متصل")
    
    # 3. تشغيل الـ Workers
    queue = asyncio.Queue()
    stats = {'checked': 0, 'found': 0}
    scan_paths = config.get('scan_paths', [])
    
    workers = []
    for _ in range(config['threads']):
        task = asyncio.create_task(worker(queue, analyzer, hash_db, config['confidence_threshold'], telegram, stats, scan_paths))
        workers.append(task)
    
    print("\n🚀 انطلاق! (اضغط Ctrl+C للإيقاف)\n")
    
    try:
        batch_size = config['threads'] * 2
        while True:
            # لو الطابور فاضي شوية، نملاه
            if queue.qsize() < batch_size:
                # استخدام الدالة الجديدة generate_urls
                urls = generate_urls(batch_size, domains, words)
                for url in urls:
                    await queue.put(url)
            
            # استراحة قصيرة عشان الـ CPU م يولعش
            await asyncio.sleep(0.1)
            
            # تحديث العنوان كل فترة (اختياري)
            # print(f"📊 Checked: {stats['checked']} | Found: {stats['found']}", end="\r")

    except KeyboardInterrupt:
        print("\n\n⏸️ جاري الإيقاف...")
    
    finally:
        # تنظيف
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