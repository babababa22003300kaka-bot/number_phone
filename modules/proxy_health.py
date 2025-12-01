"""
Proxy Health Checks & Metrics
Pure functions - Config-driven - Zero state

يوفر دوال لفحص صحة البروكسيات وقياس أدائها:
- فحص صحة البروكسيات
- قياس الـ latency
- تصفية البروكسيات الصحية
- اختيار الأسرع
"""

import httpx
import time
from typing import Dict, List, Optional


# Test URL الافتراضي - يمكن تغييره من config
DEFAULT_TEST_URL = "http://httpbin.org/ip"


def check_proxy_health(
    proxy_url: str, 
    test_url: str = DEFAULT_TEST_URL,
    timeout: int = 5
) -> Dict:
    """
    فحص صحة بروكسي واحد
    
    Args:
        proxy_url: عنوان البروكسي (format: http://ip:port or http://user:pass@ip:port)
        test_url: URL للاختبار (default: httpbin.org/ip)
        timeout: Timeout بالثواني
        
    Returns:
        {
            'proxy': str,         # عنوان البروكسي
            'healthy': bool,      # هل صحي؟
            'latency': float,     # الوقت بالـ ms (None = فشل)
            'error': str | None   # رسالة الخطأ
        }
        
    Example:
        >>> result = check_proxy_health("http://proxy.example.com:8080")
        >>> if result['healthy']:
        >>>     print(f"Proxy OK! Latency: {result['latency']}ms")
        
    Config:
        settings.json -> proxy.health_check_url (override DEFAULT_TEST_URL)
    """
    start_time = time.time()
    
    try:
        # استخدام httpx للفحص
        with httpx.Client(
            proxies=proxy_url, 
            timeout=timeout, 
            verify=False  # تجاهل SSL errors للاختبار
        ) as client:
            response = client.get(test_url)
            latency = (time.time() - start_time) * 1000  # تحويل لـ ms
            
            return {
                'proxy': proxy_url,
                'healthy': response.status_code == 200,
                'latency': round(latency, 2),
                'error': None,
                'status_code': response.status_code
            }
            
    except httpx.ProxyError as e:
        return {
            'proxy': proxy_url,
            'healthy': False,
            'latency': None,
            'error': f"Proxy Error: {str(e)[:80]}"
        }
    except httpx.ConnectTimeout:
        return {
            'proxy': proxy_url,
            'healthy': False,
            'latency': None,
            'error': "Connection Timeout"
        }
    except httpx.ConnectError as e:
        return {
            'proxy': proxy_url,
            'healthy': False,
            'latency': None,
            'error': f"Connection Error: {str(e)[:80]}"
        }
    except Exception as e:
        return {
            'proxy': proxy_url,
            'healthy': False,
            'latency': None,
            'error': f"Unknown Error: {str(e)[:80]}"
        }


def check_all_proxies(
    proxy_list: List[str],
    test_url: str = DEFAULT_TEST_URL,
    timeout: int = 5,
    verbose: bool = True
) -> List[Dict]:
    """
    فحص جميع البروكسيات في القائمة
    
    Args:
        proxy_list: قائمة البروكسيات
        test_url: URL للاختبار
        timeout: Timeout لكل بروكسي
        verbose: طباعة التقدم؟
        
    Returns:
        List of health check results
        
    Example:
        >>> proxies = ["http://p1.com:8080", "http://p2.com:8080"]
        >>> results = check_all_proxies(proxies)
        >>> healthy = filter_healthy_proxies(results)
    """
    results = []
    
    if verbose:
        print(f"\n🔍 Checking {len(proxy_list)} proxies...")
    
    for i, proxy_url in enumerate(proxy_list, 1):
        if verbose:
            # عرض التقدم
            print(f"  [{i}/{len(proxy_list)}] Testing {proxy_url[:50]}...", end='\r')
        
        result = check_proxy_health(proxy_url, test_url, timeout)
        results.append(result)
    
    if verbose:
        # ملخص النتائج
        healthy_count = sum(1 for r in results if r['healthy'])
        print(f"\n✅ Health Check Complete: {healthy_count}/{len(proxy_list)} healthy\n")
        
        # عرض البروكسيات الفاشلة
        failed = [r for r in results if not r['healthy']]
        if failed and len(failed) <= 5:  # عرض أول 5 فقط
            print("⚠️  Failed proxies:")
            for r in failed[:5]:
                error = r['error'][:60] if r['error'] else 'Unknown'
                print(f"   • {r['proxy'][:50]} - {error}")
            if len(failed) > 5:
                print(f"   ... and {len(failed) - 5} more")
            print()
    
    return results


def filter_healthy_proxies(health_results: List[Dict]) -> List[str]:
    """
    استخراج البروكسيات الصحية فقط
    
    Args:
        health_results: نتائج check_all_proxies
        
    Returns:
        List of healthy proxy URLs
        
    Example:
        >>> results = check_all_proxies(proxies)
        >>> healthy = filter_healthy_proxies(results)
        >>> print(f"Got {len(healthy)} working proxies")
    """
    return [
        result['proxy'] 
        for result in health_results 
        if result['healthy']
    ]


def get_fastest_proxy(health_results: List[Dict], top_n: int = 1) -> Optional[str]:
    """
    احصل على أسرع بروكسي (أو الـ N الأسرع)
    
    Args:
        health_results: نتائج check_all_proxies
        top_n: عدد البروكسيات المطلوبة (default: 1)
        
    Returns:
        أسرع proxy URL (أو None إذا لا يوجد)
        أو List of top N proxies إذا top_n > 1
        
    Example:
        >>> results = check_all_proxies(proxies)
        >>> fastest = get_fastest_proxy(results)
        >>> print(f"Fastest: {fastest}")
    """
    # تصفية الصحية فقط
    healthy = [
        r for r in health_results 
        if r['healthy'] and r['latency'] is not None
    ]
    
    if not healthy:
        return None if top_n == 1 else []
    
    # ترتيب حسب السرعة
    sorted_proxies = sorted(healthy, key=lambda x: x['latency'])
    
    if top_n == 1:
        return sorted_proxies[0]['proxy']
    else:
        return [p['proxy'] for p in sorted_proxies[:top_n]]


def print_proxy_health_report(health_results: List[Dict]):
    """
    طباعة تقرير مفصل عن صحة البروكسيات
    
    Args:
        health_results: نتائج check_all_proxies
    """
    total = len(health_results)
    healthy = [r for r in health_results if r['healthy']]
    healthy_count = len(healthy)
    
    print("=" * 50)
    print("📊 PROXY HEALTH REPORT")
    print("=" * 50)
    print(f"Total Proxies: {total}")
    print(f"Healthy: {healthy_count} ({healthy_count/total*100:.1f}%)")
    print(f"Failed: {total - healthy_count} ({(total-healthy_count)/total*100:.1f}%)")
    
    if healthy:
        latencies = [r['latency'] for r in healthy]
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"\nLatency Stats:")
        print(f"  • Average: {avg_latency:.2f}ms")
        print(f"  • Min: {min_latency:.2f}ms")
        print(f"  • Max: {max_latency:.2f}ms")
        
        # أسرع 3
        fastest = get_fastest_proxy(health_results, top_n=3)
        if fastest:
            print(f"\n⚡ Fastest 3 Proxies:")
            for i, proxy in enumerate(fastest, 1):
                result = next(r for r in healthy if r['proxy'] == proxy)
                print(f"  {i}. {proxy[:50]} - {result['latency']:.2f}ms")
    
    print("=" * 50)
    print()


def get_proxy_health_config(config: Dict) -> Dict:
    """
    استخراج إعدادات proxy health check من config
    
    Args:
        config: إعدادات البوت الكاملة
        
    Returns:
        {
            'enabled': bool,
            'test_url': str,
            'timeout': int,
            'check_on_startup': bool
        }
        
    Config Keys:
        settings.json -> proxy.health_check.enabled
        settings.json -> proxy.health_check.test_url
        settings.json -> proxy.health_check.timeout
        settings.json -> proxy.health_check.check_on_startup
    """
    proxy_config = config.get('proxy', {})
    health_config = proxy_config.get('health_check', {})
    
    return {
        'enabled': health_config.get('enabled', False),
        'test_url': health_config.get('test_url', DEFAULT_TEST_URL),
        'timeout': health_config.get('timeout', 5),
        'check_on_startup': health_config.get('check_on_startup', True)
    }
