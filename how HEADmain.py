[1mdiff --git a/main.py b/main.py[m
[1mindex 7f15826..13cf910 100644[m
[1m--- a/main.py[m
[1m+++ b/main.py[m
[36m@@ -1,30 +1,17 @@[m
 #!/usr/bin/env python3[m
 """[m
 بوت البحث الآلي عن مصادر OTP[m
[31m-الإصدار: 2.2 (Functional Generator + Strict DNS)[m
[32m+[m[32mالإصدار: 2.4 (Phase 3: Hybrid System)[m
 """[m
 [m
 import asyncio[m
 import json[m
[32m+[m[32mimport os[m
 import sys[m
 import time[m
 import io[m
 from pathlib import Path[m
[31m-from typing import List, Dict[m
[31m-[m
[31m-# Force UTF-8 for Windows Console[m
[31m-sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')[m
[31m-sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')[m
[31m-[m
[31m-from modules.analyzer import WebAnalyzer[m
[31m-from modules.generator import generate_urls[m
[31m-from modules.telegram_bot import TelegramNotifier[m
[31m-from modules.database import HashDB[m
[31m-[m
[31m-# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[m
[31m-# 📁 تحميل الإعدادات[m
[31m-# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[m
[31m-[m
[32m+[m[32mfrom dotenv import load_dotenv[m
 def load_config() -> Dict:[m
     """تحميل الإعدادات"""[m
     config_path = Path("config/settings.json")[m
[36m@@ -39,7 +26,6 @@[m [mdef load_file_lines(filepath: str) -> List[str]:[m
     """تحميل ملف نصي"""[m
     path = Path(filepath)[m
     if not path.exists():[m
[31m-        # لو ملف الكلمات مش موجود، نرجع قائمة افتراضية[m
         if "words" in filepath:[m
             return ["cloud", "net", "app", "tech", "web", "data", "fast", "pro", "smart", "link"][m
         print(f"⚠️ الملف {filepath} مش موجود!")[m
[36m@@ -54,63 +40,45 @@[m [mdef load_file_lines(filepath: str) -> List[str]:[m
 [m
 async def process_url(url: str, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, scan_paths: List[str]) -> Dict:[m
     """فحص رابط واحد (Async)"""[m
[31m-    # تحقق من الـ Hash[m
     if hash_db and hash_db.is_checked(url):[m
         return {"url": url, "status": "duplicate", "confidence": 0}[m
     [m
[31m-    # التحليل مع الـ Path Fuzzing[m
     result = await analyzer.analyze(url, scan_paths=scan_paths)[m
     [m
[31m-    # تسجيل في الـ Hash[m
     if hash_db and result:[m
         hash_db.mark_checked(url, result.get("status", "unknown"))[m
     [m
[31m-    # تحقق من الثقة[m
     if result and result.get("confidence", 0) >= threshold:[m
         return result[m
     [m
[31m-    return result # Return result anyway for logging[m
[32m+[m[32m    return result[m
 [m
 async def worker(queue: asyncio.Queue, analyzer: WebAnalyzer, hash_db: HashDB, threshold: int, telegram: TelegramNotifier, stats: Dict, scan_paths: List[str]):[m
     """عامل (Worker) بيسحب روابط من الطابور ويفحصها"""[m
     while True:[m
         url = await queue.get()[m
         try:[m
[31m-            # طباعة قبل الفحص (Verbose)[m
             print(f"🔍 [CHECK] {url} ...", end="\r")[m
             [m
             result = await process_url(url, analyzer, hash_db, threshold, scan_paths)[m
             [m
             stats['checked'] += 1[m
             [m
[31m-            # طباعة النتيجة[m
             if result:[m
                 confidence = result.get("confidence", 0)[m
                 status = result.get("status", "unknown")[m
                 [m
                 if confidence >= threshold:[m
                     stats['found'] += 1[m
[31m-                    print(f"✅ [FOUND] {url} (Conf: {confidence}%) - Phone: {result.get('phone_score')}% | Verify: {result.get('verify_score')}%")[m
[32m+[m[32m                    sigs = result.get("evidence", {}).get("signatures", [])[m
[32m+[m[32m                    sig_text = f" [Sigs: {','.join(sigs)}]" if sigs else ""[m
[32m+[m[32m                    print(f"✅ [FOUND] {url} (Conf: {confidence}%){sig_text} - Phone: {result.get('phone_score')}% | Verify: {result.get('verify_score')}%")[m
                     [m
[31m-                    # إرسال للتليجرام[m
                     if telegram:[m
                         await telegram.send_result(result)[m
                 [m
[31m-                elif status == "protected":[m
[31m-                    print(f"🛡️ [PROT] {url} ({result.get('protection')})")[m
[31m-                [m
[31m-                elif status == "timeout":[m
[31m-                    print(f"⏱️ [TIME] {url} (Timeout)")[m
[31m-                [m
[31m-                elif status == "connection_error":[m
[31m-                    print(f"🔌 [CONN] {url} (Connection Error)")[m
[31m-                [m
[31m-                elif status == "duplicate":[m
[31m-                    print(f"🔄 [DUPL] {url} (Already Checked)")[m
[31m-                [m
[31m-                else:[m
[31m-                    # فشل عادي (Low Confidence)[m
[31m-                    print(f"❌ [FAIL] {url} (Conf: {confidence}%)")[m
[32m+[m[32m                elif status == "excluded":[m
[32m+[m[32m                    print(f"🚫 [EXCL] {url} ({result.get('reason')})")[m
             else:[m
                 print(f"⚠️ [ERR ] {url} (No Result)")[m
 [m
[36m@@ -127,33 +95,46 @@[m [masync def worker(queue: asyncio.Queue, analyzer: WebAnalyzer, hash_db: HashDB, t[m
 async def main_async():[m
     print("""[m
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[m
[31m-🚀 بوت البحث الآلي - v2.2 (Functional)[m
[32m+[m[32m🚀 بوت البحث الآلي - v2.4 (Phase 3)[m
[32m+[m[32m✨ Hybrid System: HTTPX + Playwright[m
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[m
     """)[m
     [m
     # 1. التحميل[m
     print("📦 جاري تحميل الإعدادات...")[m
[32m+[m[41m    [m
[32m+[m[32m    # تحميل متغيرات البيئة من ملف .env[m
[32m+[m[32m    load_dotenv()[m
[32m+[m[41m    [m
     config = load_config()[m
     domains = load_file_lines("config/domains.txt")[m
     html_keywords = load_file_lines("config/html_keywords.txt")[m
     api_keywords = load_file_lines("config/api_keywords.txt")[m
[31m-    words = load_file_lines("config/words.txt") # تحميل الكلمات[m
[32m+[m[32m    exclude_keywords = load_file_lines("config/exclude.txt")[m
[32m+[m[32m    words = load_file_lines("config/words.txt")[m
[32m+[m[32m    names = load_file_lines("config/names.txt")[m
[32m+[m[32m    locations = load_file_lines("config/locations.txt")[m
     [m
     if not domains:[m
         print("❌ لازم تضيف دومينات في domains.txt!")[m
         sys.exit(1)[m
     [m
[31m-    print(f"✅ تم تحميل: {len(domains)} دومين | {len(html_keywords)} HTML KW | {len(api_keywords)} API KW | {len(words)} Words")[m
[32m+[m[32m    print(f"✅ تم تحميل: {len(domains)} دومين | {len(html_keywords)} HTML KW | {len(api_keywords)} API KW")[m
[32m+[m[32m    print(f"✅ القوائم: {len(words)} كلمات | {len(names)} أسماء | {len(locations)} مواقع | {len(exclude_keywords)} استبعاد")[m
     print(f"⚡ السرعة: {config['threads']} Workers (AsyncIO)")[m
     [m
     # 2. الإعداد[m
[32m+[m[32m    hybrid_config = config.get('hybrid_system', {})[m
     [m
     analyzer = WebAnalyzer([m
         html_keywords=html_keywords,[m
         api_keywords=api_keywords,[m
[32m+[m[32m        exclude_keywords=exclude_keywords,[m
         timeout=config['timeout'],[m
         max_size=config['max_response_size'],[m
[31m-        user_agent=config['user_agent'][m
[32m+[m[32m        user_agent=config['user_agent'],[m
[32m+[m[32m        browser_service_url=hybrid_con