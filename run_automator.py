#!/usr/bin/env python3
"""
Automation Runner
تشغيل سيناريوهات الأتمتة على المواقع الناجحة

النسخة: 1.0.0
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# إضافة modules للـ path
sys.path.append(str(Path(__file__).parent))

from modules import automator

DB_PATH = "checked_urls.db"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال مساعدة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_top_sites(
    db_path: str = DB_PATH,
    threshold: int = 85,
    limit: int = 10
) -> List[Dict]:
    """
    جلب أفضل المواقع من قاعدة البيانات
    
    Args:
        db_path: مسار قاعدة البيانات
        threshold: حد الثقة الأدنى
        limit: عدد المواقع
        
    Returns:
        list: قائمة المواقع
    """
    import sqlite3
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        results = cursor.execute("""
            SELECT DISTINCT url, confidence, phone_score, verify_score
            FROM checked_urls
            WHERE confidence >= ? AND status != 'duplicate'
            ORDER BY confidence DESC, checked_at DESC
            LIMIT ?
        """, (threshold, limit)).fetchall()
        
        conn.close()
        
        return [
            {
                "url": r[0],
                "confidence": r[1],
                "phone_score": r[2],
                "verify_score": r[3]
            }
            for r in results
        ]
        
    except Exception as e:
        print(f"❌ Error loading sites from database: {e}")
        return []

def save_report(results: List[Dict], output_file: str = "automation_results.json"):
    """
    حفظ تقرير النتائج
    
    Args:
        results: نتائج الأتمتة
        output_file: ملف الإخراج
    """
    # إحصائيات
    total = len(results)
    successful = sum(1 for r in results if 'success' in r.get('status', ''))
    with_verification = sum(1 for r in results if r.get('status') == 'success_with_verification')
    otp_detected = sum(1 for r in results if r.get('otp_detected'))
    
    report = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_sites": total,
            "successful": successful,
            "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
            "with_verification": with_verification,
            "otp_detected": otp_detected
        },
        "results": results
    }
    
    # حفظ
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Report saved to: {output_file}")

def print_summary(results: List[Dict]):
    """
    طباعة ملخص النتائج
    
    Args:
        results: نتائج الأتمتة
    """
    total = len(results)
    successful = sum(1 for r in results if 'success' in r.get('status', ''))
    failed = total - successful
    with_verification = sum(1 for r in results if r.get('status') == 'success_with_verification')
    otp_detected = sum(1 for r in results if r.get('otp_detected'))
    
    print("\n" + "="*60)
    print("📊 AUTOMATION SUMMARY")
    print("="*60)
    print(f"Total Sites Tested:        {total}")
    print(f"Successful Automations:    {successful} ({successful/total*100:.1f}%)" if total > 0 else "Successful: 0")
    print(f"Failed Automations:        {failed}")
    print(f"With Verification Page:    {with_verification}")
    print(f"OTP Codes Detected:        {otp_detected}")
    print("="*60)
    
    # أفضل النتائج
    if with_verification > 0:
        print("\n🎯 Best Results (with verification):")
        for r in results:
            if r.get('status') == 'success_with_verification':
                otp_status = f" [OTP: {r['otp_detected']}]" if r.get('otp_detected') else ""
                print(f"  ✅ {r['url']}{otp_status}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# الدالة الرئيسية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    """الدالة الرئيسية لتشغيل الأتمتة"""
    
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Automation Runner - v1.0 (Phase 7)
   Full Registration Testing & OTP Detection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. جلب المواقع المستهدفة
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("📦 Loading top sites from database...")
    print(f"   Threshold: Confidence >= 85%")
    print(f"   Limit: 10 sites")
    
    sites = get_top_sites(
        db_path=DB_PATH,
        threshold=85,
        limit=10
    )
    
    if not sites:
        print("\n❌ No sites found with confidence >= 85%")
        print("   Run the main scanner first to collect sites.")
        return
    
    print(f"\n✅ Found {len(sites)} sites to test:")
    for i, site in enumerate(sites, 1):
        print(f"   {i}. {site['url']} (Conf: {site['confidence']}%)")
    
    # تأكيد
    print(f"\n⚠️ Browser windows will open for each site (headless=False for debugging)")
    print("   Press Ctrl+C to cancel, or wait 5 seconds to start...\n")
    
    try:
        await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\n⏸️ Cancelled by user")
        return
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. تشغيل السيناريوهات
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    results = []
    
    for i, site in enumerate(sites, 1):
        print(f"\n\n{'#'*60}")
        print(f"# Testing {i}/{len(sites)}")
        print(f"# URL: {site['url']}")
        print(f"# Confidence: {site['confidence']}%")
        print(f"{'#'*60}")
        
        try:
            result = await automator.run_registration_scenario(
                url=site['url'],
                phone_number=None,  # توليد تلقائي
                headless=False,  # False = شوف المتصفح
                timeout=30000,
                screenshot_dir="screenshots"
            )
            
            # إضافة معلومات إضافية
            result['original_confidence'] = site['confidence']
            results.append(result)
            
            # طباعة النتيجة
            print(f"\n{'─'*60}")
            print(f"📊 Result: {result['status']}")
            print(f"   Steps completed: {sum(1 for v in result['steps'].values() if v == 'success')}/{len(result['steps'])}")
            
            if result.get('otp_detected'):
                print(f"   🎯 OTP Detected: {result['otp_detected']}")
            
            if result.get('errors'):
                print(f"   ⚠️ Errors: {len(result['errors'])}")
            
            print(f"{'─'*60}")
            
        except Exception as e:
            print(f"\n💥 Error testing {site['url']}: {e}")
            results.append({
                "url": site['url'],
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "errors": [str(e)],
                "steps": {},
                "screenshots": []
            })
        
        # استراحة بين المواقع
        if i < len(sites):
            print("\n⏸️ Waiting 3 seconds before next site...")
            await asyncio.sleep(3)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. حفظ التقرير
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    save_report(results, "automation_results.json")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. طباعة الملخص
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print_summary(results)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# نقطة الدخول
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    # إنشاء مجلد Screenshots
    Path("screenshots").mkdir(exist_ok=True)
    
    try:
        # تشغيل الأتمتة
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n\n⏸️ Automation stopped by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
