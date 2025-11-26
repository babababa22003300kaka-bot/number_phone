#!/usr/bin/env python3
"""
بوت البحث الآلي عن مصادر OTP
الإصدار: 2.0 النهائي
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from modules.analyzer import WebAnalyzer
from modules.generator import URLGenerator
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
        print(f"⚠️ الملف {filepath} مش موجود!")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 الوظائف الأساسية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def process_url(url: str, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int) -> Dict:
    """فحص رابط واحد"""
    # تحقق من الـ Hash
    if hash_db.is_checked(url):
        return {"url": url, "status": "duplicate", "confidence": 0}
    
    # التحليل
    result = analyzer.analyze(url)
    
    # تسجيل في الـ Hash
    hash_db.mark_checked(url, result.get("status", "unknown"))
    
    # تحقق من الثقة
    if result and result.get("confidence", 0) >= threshold:
        return result
    
    return None

async def send_to_telegram(notifier: TelegramNotifier, result: Dict):
    """إرسال للتليجرام"""
    await notifier.send_result(result)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 البرنامج الرئيسي
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 بوت البحث الآلي - v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. التحميل
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("📦 جاري تحميل الإعدادات...")
    
    config = load_config()
    domains = load_file_lines("config/domains.txt")
    html_keywords = load_file_lines("config/html_keywords.txt")
    api_keywords = load_file_lines("config/api_keywords.txt")
    
    if not domains:
        print("❌ لازم تضيف دومينات في domains.txt!")
        sys.exit(1)
    
    print(f"✅ تم تحميل:")
    print(f"   • {len(domains)} دومين")
    print(f"   • {len(html_keywords)} كلمة HTML")
    print(f"   • {len(api_keywords)} كلمة API")
    print(f"   • عدد السريدات: {config['threads']}")
    print(f"   • حد الثقة: {config['confidence_threshold']}%")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. الإعداد
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🔧 جاري الإعداد...")
    
    # المولد
    generator = URLGenerator(domains)
    
    # المحلل
    analyzer = WebAnalyzer(
        html_keywords=html_keywords,
        api_keywords=api_keywords,
        timeout=config['timeout'],
        max_size=config['max_response_size'],
        user_agent=config['user_agent']
    )
    
    # الـ Hash DB
    hash_db = None
    if config.get('use_hash_db', True):
        hash_db = HashDB(config.get('hash_db_file', 'checked_urls.db'))
        stats = hash_db.get_stats()
        print(f"   • قاعدة البيانات: {stats['total_checked']} رابط مُسجّل")
    
    # التليجرام
    telegram = None
    if config['telegram']['bot_token'] != "YOUR_BOT_TOKEN_HERE":
        telegram = TelegramNotifier(
            bot_token=config['telegram']['bot_token'],
            chat_id=config['telegram']['chat_id']
        )
        print("   • التليجرام: متصل ✅")
    else:
        print("   • التليجرام: غير مُفعّل ⚠️")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. البحث
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🚀 بدء البحث...\n")
    
    batch_size = config['threads']
    found_count = 0
    checked_count = 0
    
    try:
        while True:
            # توليد دُفعة
            urls = generator.generate(batch_size)
            
            # الفحص بالتوازي
            with ThreadPoolExecutor(max_workers=config['threads']) as executor:
                futures = {
                    executor.submit(
                        process_url, 
                        url, 
                        analyzer, 
                        hash_db, 
                        config['confidence_threshold']
                    ): url 
                    for url in urls
                }
                
                for future in as_completed(futures):
                    checked_count += 1
                    result = future.result()
                    
                    if result and result.get("confidence", 0) >= config['confidence_threshold']:
                        found_count += 1
                        
                        # طباعة
                        print(f"✅ [{found_count}] {result['url']} - {result['confidence']}%")
                        
                        # إرسال للتليجرام
                        if telegram:
                            asyncio.run(send_to_telegram(telegram, result))
                    
                    # إحصائيات كل 100 رابط
                    if checked_count % 100 == 0:
                        print(f"\n📊 الإحصائيات: {checked_count} مُفحوص | {found_count} محتمل\n")
            
            # تأخير بسيط
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⏸️ توقف البحث...")
    
    finally:
        # الإحصائيات النهائية
        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 الإحصائيات النهائية
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• تم فحص: {checked_count} موقع
• مواقع محتملة: {found_count} ({(found_count/checked_count*100) if checked_count else 0:.1f}%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
        
        analyzer.close()

if __name__ == "__main__":
    main()