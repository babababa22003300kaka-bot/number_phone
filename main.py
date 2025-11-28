#!/usr/bin/env python3
"""
بوت البحث الآلي عن مصادر OTP
الإصدار: 2.4 (Phase 3: Hybrid System)
"""

import asyncio
import json
import sys
import time
import io
from pathlib import Path
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 الوظائف الأساسية (Async)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def process_url(url: str, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, scan_paths: List[str]) -> Dict:
    """فحص رابط واحد (Async)"""
    if hash_db and hash_db.is_checked(url):
        return {"url": url, "status": "duplicate", "confidence": 0}
    
    result = await analyzer.analyze(url, scan_paths=scan_paths)
    
    if hash_db and result:
        hash_db.mark_checked(url, result.get("status", "unknown"))
    
    if result and result.get("confidence", 0) >= threshold:
        return result
    
    return result

async def worker(queue: asyncio.Queue, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, telegram: TelegramNotifier, stats: Dict, scan_paths: List[str]):
    """عامل (Worker) بيسحب روابط من الطابور ويفحصها"""
    while True:
        url = await queue.get()
        try:
            print(f"🔍 [CHECK] {url} ...", end="\r")
            
            result = await process_url(url, analyzer, hash_db, threshold, scan_paths)
            
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
🚀 بوت البحث الآلي - v2.4 (Phase 3)
✨ Hybrid System: HTTPX + Playwright
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # 1. التحميل
    print("📦 جاري تحميل الإعدادات...")
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