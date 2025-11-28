#!/usr/bin/env python3
"""
Analytics Engine - Functional Style
تحليل الأداء بدوال بسيطة - مفيش كلاسات!

النسخة: 1.0.0
الأسلوب: Functional Programming
"""

import sqlite3
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال الإحصائيات العامة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_total_scans(db_path: str, days: int = 7) -> int:
    """
    إجمالي عدد الفحوصات في آخر X أيام
    
    Args:
        db_path: مسار قاعدة البيانات
        days: عدد الأيام
        
    Returns:
        int: عدد الفحوصات
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = cursor.execute("""
            SELECT COUNT(*) FROM checked_urls
            WHERE checked_at >= ?
        """, (cutoff_date,)).fetchone()
        
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"❌ Error in get_total_scans: {e}")
        return 0

def get_success_rate(db_path: str, days: int = 7, threshold: int = 60) -> float:
    """
    نسبة النجاح العامة
    
    Args:
        db_path: مسار قاعدة البيانات
        days: عدد الأيام
        threshold: حد الثقة للنجاح
        
    Returns:
        float: نسبة النجاح (0-100)
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        total = cursor.execute("""
            SELECT COUNT(*) FROM checked_urls
            WHERE checked_at >= ?
        """, (cutoff_date,)).fetchone()[0]
        
        if total == 0:
            conn.close()
            return 0.0
        
        success = cursor.execute("""
            SELECT COUNT(*) FROM checked_urls
            WHERE checked_at >= ? AND confidence >= ?
        """, (cutoff_date, threshold)).fetchone()[0]
        
        conn.close()
        return (success / total) * 100
    except Exception as e:
        print(f"❌ Error in get_success_rate: {e}")
        return 0.0

def get_average_confidence(db_path: str, days: int = 7) -> float:
    """
    متوسط الثقة
    
    Args:
        db_path: مسار قاعدة البيانات
        days: عدد الأيام
        
    Returns:
        float: متوسط الثقة (0-100)
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = cursor.execute("""
            SELECT AVG(confidence) FROM checked_urls
            WHERE checked_at >= ? AND confidence > 0
        """, (cutoff_date,)).fetchone()
        
        conn.close()
        return result[0] if result and result[0] else 0.0
    except Exception as e:
        print(f"❌ Error in get_average_confidence: {e}")
        return 0.0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال تحليل الأوضاع (Modes)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mode_comparison(db_path: str, days: int = 7) -> Dict:
    """
    مقارنة بين generator vs dorking
    
    Args:
        db_path: مسار قاعدة البيانات
        days: عدد الأيام
        
    Returns:
        dict: إحصائيات المقارنة
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Generator stats
        gen_total = cursor.execute("""
            SELECT COUNT(*) FROM checked_urls
            WHERE checked_at >= ? AND (source = 'generator' OR source IS NULL)
        """, (cutoff_date,)).fetchone()[0]
        
        gen_success = cursor.execute("""
            SELECT COUNT(*) FROM checked_urls
            WHERE checked_at >= ? AND (source = 'generator' OR source IS NULL) AND confidence >= 60
        """, (cutoff_date,)).fetchone()[0]
        
        # Dorking stats
        dork_total = cursor.execute("""
            SELECT COUNT(*) FROM checked_urls
            WHERE checked_at >= ? AND source = 'dorking'
        """, (cutoff_date,)).fetchone()[0]
        
        dork_success = cursor.execute("""
            SELECT COUNT(*) FROM checked_urls
            WHERE checked_at >= ? AND source = 'dorking' AND confidence >= 60
        """, (cutoff_date,)).fetchone()[0]
        
        conn.close()
        
        return {
            "generator": {
                "count": gen_total,
                "success": gen_success,
                "success_rate": (gen_success / gen_total * 100) if gen_total > 0 else 0
            },
            "dorking": {
                "count": dork_total,
                "success": dork_success,
                "success_rate": (dork_success / dork_total * 100) if dork_total > 0 else 0
            }
        }
    except Exception as e:
        print(f"❌ Error in get_mode_comparison: {e}")
        return {"generator": {"count": 0, "success": 0, "success_rate": 0}, "dorking": {"count": 0, "success": 0, "success_rate": 0}}

def get_method_comparison(db_path: str, days: int = 7) -> Dict:
    """
    مقارنة بين httpx vs playwright
    
    Args:
        db_path: مسار قاعدة البيانات
        days: عدد الأيام
        
    Returns:
        dict: إحصائيات المقارنة
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        methods = {}
        for method in ['httpx', 'playwright']:
            total = cursor.execute("""
                SELECT COUNT(*) FROM checked_urls
                WHERE checked_at >= ? AND (method = ? OR (method IS NULL AND ? = 'httpx'))
            """, (cutoff_date, method, method)).fetchone()[0]
            
            avg_conf = cursor.execute("""
                SELECT AVG(confidence) FROM checked_urls
                WHERE checked_at >= ? AND (method = ? OR (method IS NULL AND ? = 'httpx')) AND confidence > 0
            """, (cutoff_date, method, method)).fetchone()[0]
            
            methods[method] = {
                "count": total,
                "avg_confidence": avg_conf if avg_conf else 0
            }
        
        conn.close()
        return methods
    except Exception as e:
        print(f"❌ Error in get_method_comparison: {e}")
        return {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال تحليل الـ Dorks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_top_dorks(db_path: str, limit: int = 10) -> List[Dict]:
    """
    أفضل Dorks (حسب نسبة النجاح)
    
    Args:
        db_path: مسار قاعدة البيانات
        limit: عدد النتائج
        
    Returns:
        list: قائمة أفضل dorks
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        results = cursor.execute("""
            SELECT 
                dork,
                used_count,
                success_count,
                ROUND(success_count * 100.0 / used_count, 2) as success_rate,
                ROUND(total_confidence * 1.0 / success_count, 0) as avg_confidence
            FROM dork_performance
            WHERE used_count >= 3
            ORDER BY success_rate DESC, success_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        conn.close()
        
        return [
            {
                "dork": r[0],
                "used": r[1],
                "success": r[2],
                "success_rate": r[3],
                "avg_confidence": r[4] if r[4] else 0
            }
            for r in results
        ]
    except Exception as e:
        print(f"❌ Error in get_top_dorks: {e}")
        return []

def get_worst_dorks(db_path: str, limit: int = 5) -> List[Dict]:
    """
    أسوأ Dorks (أقل نجاح)
    
    Args:
        db_path: مسار قاعدة البيانات
        limit: عدد النتائج
        
    Returns:
        list: قائمة أسوأ dorks
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        results = cursor.execute("""
            SELECT 
                dork,
                used_count,
                success_count,
                ROUND(success_count * 100.0 / used_count, 2) as success_rate
            FROM dork_performance
            WHERE used_count >= 3
            ORDER BY success_rate ASC
            LIMIT ?
        """, (limit,)).fetchall()
        
        conn.close()
        
        return [
            {
                "dork": r[0],
                "used": r[1],
                "success": r[2],
                "success_rate": r[3]
            }
            for r in results
        ]
    except Exception as e:
        print(f"❌ Error in get_worst_dorks: {e}")
        return []

def get_dork_stats(db_path: str, dork: str) -> Dict:
    """
    إحصائيات dork محدد
    
    Args:
        db_path: مسار قاعدة البيانات
        dork: الـ dork المطلوب
        
    Returns:
        dict: إحصائيات مفصلة
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        result = cursor.execute("""
            SELECT used_count, success_count, total_confidence, last_used
            FROM dork_performance
            WHERE dork = ?
        """, (dork,)).fetchone()
        
        conn.close()
        
        if not result:
            return {}
        
        return {
            "dork": dork,
            "used": result[0],
            "success": result[1],
            "total_confidence": result[2],
            "last_used": result[3],
            "success_rate": (result[1] / result[0] * 100) if result[0] > 0 else 0,
            "avg_confidence": (result[2] / result[1]) if result[1] > 0 else 0
        }
    except Exception as e:
        print(f"❌ Error in get_dork_stats: {e}")
        return {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال تحليل البصمات (Signatures)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_top_signatures(db_path: str, limit: int = 10, days: int = 30) -> List[Dict]:
    """
    أكثر البصمات اكتشافاً
    
    Args:
        db_path: مسار قاعدة البيانات
        limit: عدد النتائج
        days: عدد الأيام
        
    Returns:
        list: قائمة البصمات
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # جلب كل البصمات
        results = cursor.execute("""
            SELECT signatures FROM checked_urls
            WHERE checked_at >= ? AND signatures IS NOT NULL AND signatures != ''
        """, (cutoff_date,)).fetchall()
        
        conn.close()
        
        # عد البصمات
        signature_counts = {}
        for row in results:
            try:
                sigs = json.loads(row[0]) if row[0].startswith('[') else row[0].split(',')
                for sig in sigs:
                    sig = sig.strip()
                    signature_counts[sig] = signature_counts.get(sig, 0) + 1
            except:
                continue
        
        # ترتيب
        sorted_sigs = sorted(signature_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [{"signature": sig, "count": count} for sig, count in sorted_sigs]
    except Exception as e:
        print(f"❌ Error in get_top_signatures: {e}")
        return []

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال تحليل الوقت
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_daily_trend(db_path: str, days: int = 30) -> List[Dict]:
    """
    الاتجاه اليومي
    
    Args:
        db_path: مسار قاعدة البيانات
        days: عدد الأيام
        
    Returns:
        list: إحصائيات يومية
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        results = cursor.execute("""
            SELECT 
                DATE(checked_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN confidence >= 60 THEN 1 ELSE 0 END) as success
            FROM checked_urls
            WHERE checked_at >= ?
            GROUP BY DATE(checked_at)
            ORDER BY date DESC
        """, (cutoff_date,)).fetchall()
        
        conn.close()
        
        return [
            {
                "date": r[0],
                "total": r[1],
                "success": r[2],
                "success_rate": (r[2] / r[1] * 100) if r[1] > 0 else 0
            }
            for r in results
        ]
    except Exception as e:
        print(f"❌ Error in get_daily_trend: {e}")
        return []

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال إدارة API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_api_usage_summary(db_path: str) -> List[Dict]:
    """
    ملخص استخدام API keys
    
    Args:
        db_path: مسار قاعدة البيانات
        
    Returns:
        list: ملخص الاستخدام
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        results = cursor.execute("""
            SELECT service, api_key_email, used_count, last_used
            FROM api_usage
            ORDER BY service, used_count DESC
        """).fetchall()
        
        conn.close()
        
        return [
            {
                "service": r[0],
                "email": r[1],
                "used": r[2],
                "last_used": r[3]
            }
            for r in results
        ]
    except Exception as e:
        print(f"❌ Error in get_api_usage_summary: {e}")
        return []

def check_api_budget(db_path: str, service: str, email: str, limit: int) -> Dict:
    """
    فحص حالة الميزانية
    
    Args:
        db_path: مسار قاعدة البيانات
        service: اسم الخدمة
        email: البريد الإلكتروني
        limit: الحد الأقصى
        
    Returns:
        dict: حالة الميزانية
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        result = cursor.execute("""
            SELECT used_count FROM api_usage
            WHERE service = ? AND api_key_email = ?
        """, (service, email)).fetchone()
        
        conn.close()
        
        used = result[0] if result else 0
        remaining = max(0, limit - used)
        percentage = (used / limit * 100) if limit > 0 else 0
        
        # تحديد الحالة
        if percentage >= 90:
            status = "critical"
        elif percentage >= 70:
            status = "warning"
        else:
            status = "ok"
        
        return {
            "used": used,
            "limit": limit,
            "remaining": remaining,
            "percentage": round(percentage, 1),
            "status": status
        }
    except Exception as e:
        print(f"❌ Error in check_api_budget: {e}")
        return {"used": 0, "limit": limit, "remaining": limit, "percentage": 0, "status": "ok"}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال التقارير
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_summary_report(db_path: str, days: int = 7) -> Dict:
    """
    تقرير شامل عن آخر X أيام
    
    Args:
        db_path: مسار قاعدة البيانات
        days: عدد الأيام
        
    Returns:
        dict: تقرير شامل
    """
    return {
        "period": f"Last {days} days",
        "total_scans": get_total_scans(db_path, days),
        "success_rate": round(get_success_rate(db_path, days), 2),
        "avg_confidence": round(get_average_confidence(db_path, days), 2),
        "mode_comparison": get_mode_comparison(db_path, days),
        "method_comparison": get_method_comparison(db_path, days),
        "top_dorks": get_top_dorks(db_path, 5),
        "top_signatures": get_top_signatures(db_path, 5, days)
    }

def generate_performance_insights(db_path: str) -> List[str]:
    """
    توصيات تلقائية لتحسين الأداء
    
    Args:
        db_path: مسار قاعدة البيانات
        
    Returns:
        list: قائمة التوصيات
    """
    insights = []
    
    try:
        # تحليل الأوضاع
        modes = get_mode_comparison(db_path, 30)
        if modes['dorking']['success_rate'] > modes['generator']['success_rate'] + 20:
            insights.append(f"🎯 Dorking mode has {modes['dorking']['success_rate']:.1f}% success vs {modes['generator']['success_rate']:.1f}% for generator - use more dorking!")
        
        # أفضل dorks
        top_dorks = get_top_dorks(db_path, 3)
        if top_dorks and top_dorks[0]['success_rate'] > 70:
            insights.append(f"⭐ Top dork '{top_dorks[0]['dork'][:40]}...' has {top_dorks[0]['success_rate']}% success - prioritize it!")
        
        # أسوأ dorks
        worst = get_worst_dorks(db_path, 3)
        if worst and worst[0]['success_rate'] < 20:
            insights.append(f"⚠️ Dork '{worst[0]['dork'][:40]}...' has only {worst[0]['success_rate']}% success - consider removing it")
        
        # Playwright
        methods = get_method_comparison(db_path, 30)
        if 'playwright' in methods and methods['playwright']['avg_confidence'] > methods['httpx']['avg_confidence'] + 10:
            insights.append(f"🚀 Playwright improves confidence by {methods['playwright']['avg_confidence'] - methods['httpx']['avg_confidence']:.0f}% - it's working!")
        
    except Exception as e:
        insights.append(f"❌ Error generating insights: {e}")
    
    return insights if insights else ["✅ Everything looks good! Keep scanning."]
