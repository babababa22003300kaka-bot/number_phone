"""
Execution Engine - محرك التشغيل المرن
Pure functions only - Config-driven - Zero hardcoded values

يوفر دوال نقية للتحكم في أوضاع التشغيل الثلاثة:
- HTTP-Only: سريع وخفيف (httpx فقط)
- Browser-Only: قوي وشامل (Playwright فقط)  
- Auto-Hybrid: ذكي ومتكيف (HTTP → Browser عند الحاجة)
"""

from typing import Dict, Tuple, Optional
import re


def get_execution_mode(config: Dict) -> str:
    """
    استخراج وضع التشغيل من الـ config
    
    Args:
        config: إعدادات البوت الكاملة
        
    Returns:
        "http" | "browser" | "auto" (default: "auto")
        
    Example:
        >>> config = {"execution": {"mode": "http"}}
        >>> get_execution_mode(config)
        "http"
    """
    execution_config = config.get('execution', {})
    mode = execution_config.get('mode', 'auto')
    
    valid_modes = ['http', 'browser', 'auto']
    if mode not in valid_modes:
        print(f"⚠️ Invalid execution mode '{mode}', falling back to 'auto'")
        print(f"   Valid modes: {', '.join(valid_modes)}")
        return 'auto'
    
    return mode


def should_run_automator(config: Dict) -> bool:
    """
    هل نشغل automator.py عند العثور على موقع؟
    
    Args:
        config: إعدادات البوت
        
    Returns:
        True = شغل automator تلقائياً
        False = اجمع المواقع فقط
        
    Config:
        settings.json -> execution.run_automator_on_found
    """
    execution_config = config.get('execution', {})
    return execution_config.get('run_automator_on_found', True)


def should_use_browser(
    url: str, 
    http_result: Optional[Dict], 
    config: Dict
) -> Tuple[bool, str]:
    """
    هل نحتاج نتحول للمتصفح؟ (في Auto mode فقط)
    
    Args:
        url: الرابط المفحوص
        http_result: نتيجة HTTP (None = فشل كامل)
        config: إعدادات البوت
        
    Returns:
        (should_use: bool, reason: str)
        
    Reasons:
        - "http_failed": فشل HTTP تماماً
        - "protection_cloudflare": حماية Cloudflare
        - "protection_captcha": reCAPTCHA
        - "js_required": محتاج JavaScript
        - "low_confidence_X": ثقة منخفضة (X = confidence%)
        - "http_sufficient": HTTP كافي
        
    Config:
        settings.json -> execution.fallback.*
    """
    fallback_config = config.get('execution', {}).get('fallback', {})
    
    # 1. لو HTTP فشل تماماً → Browser ضروري
    if not http_result:
        return True, "http_failed"
    
    # 2. فحص حماية (Cloudflare, Captcha)
    if fallback_config.get('on_cloudflare', True):
        protection = http_result.get('protection')
        if protection in ['cloudflare', 'captcha', 'recaptcha']:
            return True, f"protection_{protection}"
    
    # 3. فحص متطلبات JavaScript
    if fallback_config.get('on_js_detected', True):
        if http_result.get('js_required', False):
            return True, "js_required"
    
    # 4. فحص الثقة المنخفضة (optional)
    if fallback_config.get('on_low_confidence', False):
        threshold = fallback_config.get('confidence_threshold', 30)
        confidence = http_result.get('confidence', 0)
        if 0 < confidence < threshold:
            return True, f"low_confidence_{confidence}"
    
    return False, "http_sufficient"


def detect_js_requirement(html: str) -> bool:
    """
    كشف إذا الصفحة محتاجة JavaScript للعرض
    
    Args:
        html: HTML الصفحة
        
    Returns:
        True = الصفحة محتاجة JS بشكل أساسي
        False = الصفحة تعمل بدون JS
        
    Detection Methods:
        - Framework keywords (React, Vue, Angular, Next.js)
        - High script tag count
        - Empty body with many scripts
    """
    if not html or len(html) < 100:
        return False
    
    html_lower = html.lower()
    
    # مؤشرات قوية على احتياج JS
    js_frameworks = [
        'react',
        'vue.js',
        'angular',
        '__next',          # Next.js
        'nuxt',            # Nuxt.js
        'gatsby',          # Gatsby
        'webpack',
        'app-root',        # Angular root
        'data-reactroot',  # React root
        'id="__nuxt"',     # Nuxt root
        'data-vuejs',      # Vue.js
    ]
    
    for framework in js_frameworks:
        if framework in html_lower:
            return True
    
    # فحص نسبة الـ <script> tags
    script_count = html_lower.count('<script')
    if script_count > 10:  # عدد كبير من السكريبتات
        return True
    
    # فحص إذا الـ body فاضية تقريباً (SPA indicator)
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_lower, re.DOTALL)
    if body_match:
        body_content = body_match.group(1)
        # إزالة كل السكريبتات
        body_text = re.sub(r'<script.*?</script>', '', body_content, flags=re.DOTALL)
        # لو الباقي قليل جداً → SPA
        if len(body_text.strip()) < 200 and script_count > 3:
            return True
    
    return False


def detect_protection(html: str, headers: Dict) -> Tuple[bool, Optional[str]]:
    """
    كشف أنواع الحماية (Cloudflare, reCAPTCHA, etc.)
    
    Args:
        html: HTML الصفحة
        headers: Response headers
        
    Returns:
        (is_protected: bool, protection_type: str | None)
        
    Protection Types:
        - "cloudflare"
        - "captcha" / "recaptcha"
        - None (no protection)
    """
    if not html:
        return False, None
    
    html_lower = html.lower()
    
    # Cloudflare indicators
    cloudflare_indicators = [
        'cloudflare',
        'cf-ray',
        '__cf_chl',
        'challenge-platform',
        'just a moment',  # Cloudflare waiting page
    ]
    
    for indicator in cloudflare_indicators:
        if indicator in html_lower:
            return True, "cloudflare"
    
    # Check headers for Cloudflare
    if headers:
        for key, value in headers.items():
            if 'cloudflare' in key.lower() or 'cf-ray' in key.lower():
                return True, "cloudflare"
    
    # reCAPTCHA indicators
    captcha_indicators = [
        'recaptcha',
        'g-recaptcha',
        'grecaptcha',
        'captcha-challenge',
    ]
    
    for indicator in captcha_indicators:
        if indicator in html_lower:
            return True, "captcha"
    
    return False, None


def print_execution_mode_banner(mode: str, config: Dict):
    """
    طباعة رسالة وضع التشغيل في بداية البوت
    
    Args:
        mode: وضع التشغيل ("http" | "browser" | "auto")
        config: إعدادات البوت
    """
    execution_config = config.get('execution', {})
    automator_enabled = execution_config.get('run_automator_on_found', True)
    
    mode_names = {
        'http': 'HTTP-Only (Fast & Light)',
        'browser': 'Browser-Only (Full Power)',
        'auto': 'Auto-Hybrid (Smart)'
    }
    
    mode_name = mode_names.get(mode, mode)
    automator_status = "Enabled ✅" if automator_enabled else "Disabled ⛔"
    
    print(f"⚙️  Execution Mode: {mode_name}")
    print(f"🤖 Automator: {automator_status}")
    
    # توضيح إضافي للـ Auto mode
    if mode == 'auto':
        http_first = execution_config.get('http_first', True)
        strategy = 'HTTP-first with Browser fallback' if http_first else 'Browser-first'
        print(f"📋 Strategy: {strategy}")
        
        fallback_config = execution_config.get('fallback', {})
        triggers = []
        if fallback_config.get('on_js_detected', True):
            triggers.append('JS')
        if fallback_config.get('on_cloudflare', True):
            triggers.append('Cloudflare')
        if fallback_config.get('on_low_confidence', False):
            triggers.append(f"LowConf<{fallback_config.get('confidence_threshold', 30)}%")
        
        if triggers:
            print(f"🔄 Browser Triggers: {', '.join(triggers)}")


def get_execution_metrics_summary(mode: str, stats: Dict) -> str:
    """
    ملخص الـ metrics حسب وضع التشغيل
    
    Args:
        mode: وضع التشغيل
        stats: إحصائيات التشغيل
        
    Returns:
        Formatted summary string
    """
    if mode == 'http':
        return f"HTTP-Only Mode: {stats.get('checked', 0)} URLs checked"
    elif mode == 'browser':
        return f"Browser-Only Mode: {stats.get('checked', 0)} URLs checked"
    else:  # auto
        http_count = stats.get('http_count', 0)
        browser_count = stats.get('browser_count', 0)
        return f"Auto-Hybrid: {http_count} via HTTP, {browser_count} via Browser"
