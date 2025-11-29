"""
Metrics Module - قياس الأداء
Functions only - بدون classes

يتتبع مقاييس الأداء والإحصائيات
"""

import time
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Global Metrics Storage
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_metrics = {
    'start_time': None,
    'urls_checked': 0,
    'urls_found': 0,
    'errors': defaultdict(int),
    'status_counts': defaultdict(int),
    'processing_times': [],
    'memory_snapshots': []
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Metrics Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def start_metrics():
    """بدء تتبع المقاييس - دالة بسيطة"""
    _metrics['start_time'] = time.time()


def track_url_checked():
    """تتبع URL تم فحصه - دالة بسيطة"""
    _metrics['urls_checked'] += 1


def track_url_found():
    """تتبع URL تم العثور عليه - دالة بسيطة"""
    _metrics['urls_found'] += 1


def track_error(error_type: str):
    """
    تتبع خطأ - دالة بسيطة
    
    Args:
        error_type: نوع الخطأ
    """
    _metrics['errors'][error_type] += 1


def track_status(status: str):
    """
    تتبع حالة - دالة بسيطة
    
    Args:
        status: الحالة (success, duplicate, timeout, etc.)
    """
    _metrics['status_counts'][status] += 1


def track_processing_time(duration: float):
    """
    تتبع وقت المعالجة - دالة بسيطة
    
    Args:
        duration: المدة بالثواني
    """
    _metrics['processing_times'].append(duration)


def track_memory():
    """تتبع استخدام الذاكرة - دالة بسيطة"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        _metrics['memory_snapshots'].append(memory_mb)
    except ImportError:
        # psutil not installed
        pass


def get_metrics_summary() -> Dict:
    """
    جلب ملخص المقاييس - دالة بسيطة
    
    Returns:
        Dict: ملخص شامل للمقاييس
    """
    elapsed = time.time() - _metrics['start_time'] if _metrics['start_time'] else 0
    
    avg_time = (
        sum(_metrics['processing_times']) / len(_metrics['processing_times'])
        if _metrics['processing_times'] else 0
    )
    
    avg_memory = (
        sum(_metrics['memory_snapshots']) / len(_metrics['memory_snapshots'])
        if _metrics['memory_snapshots'] else 0
    )
    
    return {
        'elapsed_seconds': round(elapsed, 2),
        'urls_checked': _metrics['urls_checked'],
        'urls_found': _metrics['urls_found'],
        'success_rate': round(_metrics['urls_found'] / _metrics['urls_checked'] * 100, 2) if _metrics['urls_checked'] > 0 else 0,
        'avg_processing_time_ms': round(avg_time * 1000, 2),
        'avg_memory_mb': round(avg_memory, 2),
        'errors': dict(_metrics['errors']),
        'status_counts': dict(_metrics['status_counts'])
    }


def print_metrics_report(logger=None):
    """
    طباعة تقرير المقاييس - دالة بسيطة
    
    Args:
        logger: المسجل (optional)
    """
    metrics = get_metrics_summary()
    
    separator = "=" * 50
    lines = [
        separator,
        "📊 PERFORMANCE METRICS",
        separator,
        f"⏱️  Elapsed Time: {metrics['elapsed_seconds']}s",
        f"🔍 URLs Checked: {metrics['urls_checked']}",
        f"✅ URLs Found: {metrics['urls_found']}",
        f"📈 Success Rate: {metrics['success_rate']}%",
        f"⚡ Avg Processing: {metrics['avg_processing_time_ms']}ms"
    ]
    
    if metrics['avg_memory_mb'] > 0:
        lines.append(f"💾 Avg Memory: {metrics['avg_memory_mb']}MB")
    
    if metrics['errors']:
        lines.append(f"❌ Errors: {dict(metrics['errors'])}")
    
    if metrics['status_counts']:
        lines.append(f"📊 Status Counts: {dict(metrics['status_counts'])}")
    
    lines.append(separator)
    
    # Print to console and logger
    for line in lines:
        print(line)
        if logger:
            from modules.logger import log_info
            log_info(logger, line)


def reset_metrics():
    """إعادة تعيين المقاييس - دالة بسيطة"""
    _metrics['start_time'] = None
    _metrics['urls_checked'] = 0
    _metrics['urls_found'] = 0
    _metrics['errors'].clear()
    _metrics['status_counts'].clear()
    _metrics['processing_times'].clear()
    _metrics['memory_snapshots'].clear()
