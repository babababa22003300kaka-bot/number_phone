#!/usr/bin/env python3
"""
Automation Engine - Functional Style
أتمتة التسجيل والاختبار - دوال بسيطة

النسخة: 1.0.0
الأسلوب: Functional Programming (مفيش كلاسات!)
"""

from playwright.async_api import async_playwright, Page, Browser
from typing import Dict, List, Optional, Tuple
import random
import re
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال توليد البيانات الوهمية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_fake_name() -> str:
    """
    توليد اسم وهمي
    
    Returns:
        str: اسم وهمي
    """
    first_names = ['ahmed', 'mohamed', 'sara', 'fatima', 'ali', 'omar', 'layla', 'youssef']
    last_names = ['hassan', 'ibrahim', 'mahmoud', 'salem', 'rashid', 'khalil']
    return f"{random.choice(first_names)}_{random.choice(last_names)}{random.randint(10,99)}"

def generate_fake_email() -> str:
    """
    توليد إيميل وهمي
    
    Returns:
        str: إيميل وهمي
    """
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
    username = generate_fake_name().replace('_', '.')
    return f"{username}@{random.choice(domains)}"

def generate_fake_password() -> str:
    """
    توليد باسورد وهمي قوي
    
    Returns:
        str: باسورد وهمي
    """
    return f"Test{random.randint(1000,9999)}!@#"

def generate_fake_phone(country_code: str = "+20") -> str:
    """
    توليد رقم هاتف وهمي
    
    Args:
        country_code: كود الدولة
        
    Returns:
        str: رقم هاتف
    """
    return f"{country_code}1{random.randint(100000000, 999999999)}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال Selectors (محددات الحقول)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_name_selectors() -> List[str]:
    """
    قائمة selectors لحقل الاسم
    
    Returns:
        list: قائمة المحددات
    """
    return [
        'input[name="username"]',
        'input[name="name"]',
        'input[name="fullname"]',
        'input[name="full_name"]',
        'input[id="username"]',
        'input[id="name"]',
        'input[placeholder*="name" i]',
        'input[placeholder*="username" i]',
        'input[type="text"]:first-of-type',
        '#username',
        '#name'
    ]

def get_email_selectors() -> List[str]:
    """قائمة selectors لحقل الإيميل"""
    return [
        'input[name="email"]',
        'input[type="email"]',
        'input[id="email"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="e-mail" i]',
        '#email'
    ]

def get_phone_selectors() -> List[str]:
    """قائمة selectors لحقل الهاتف"""
    return [
        'input[name="phone"]',
        'input[name="mobile"]',
        'input[name="telephone"]',
        'input[type="tel"]',
        'input[id="phone"]',
        'input[id="mobile"]',
        'input[placeholder*="phone" i]',
        'input[placeholder*="mobile" i]',
        'input[placeholder*="number" i]',
        '#phone',
        '#mobile'
    ]

def get_password_selectors() -> List[str]:
    """قائمة selectors لحقل الباسورد"""
    return [
        'input[name="password"]',
        'input[type="password"]',
        'input[id="password"]',
        'input[placeholder*="password" i]',
        '#password'
    ]

def get_submit_button_selectors() -> List[str]:
    """قائمة selectors لزر التسجيل"""
    return [
        'button:has-text("sign up")',
        'button:has-text("register")',
        'button:has-text("create account")',
        'button:has-text("submit")',
        'button:has-text("next")',
        'button:has-text("continue")',
        'button[type="submit"]',
        'input[type="submit"]',
        'a:has-text("sign up")',
        '[class*="submit"]',
        '[class*="signup"]'
    ]

def get_send_code_selectors() -> List[str]:
    """قائمة selectors لزر إرسال الكود"""
    return [
        'button:has-text("send code")',
        'button:has-text("send otp")',
        'button:has-text("verify")',
        'button:has-text("get code")',
        'button:has-text("send")',
        'button[type="submit"]',
        'input[type="submit"]'
    ]

def get_otp_input_selectors() -> List[str]:
    """قائمة selectors لحقل OTP"""
    return [
        'input[name="otp"]',
        'input[name="code"]',
        'input[name="verification_code"]',
        'input[id="otp"]',
        'input[id="code"]',
        'input[placeholder*="code" i]',
        'input[placeholder*="otp" i]',
        'input[type="text"][maxlength="4"]',
        'input[type="text"][maxlength="6"]'
    ]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دوال التفاعل مع الصفحة
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def try_fill_field(
    page: Page,
    selectors: List[str],
    value: str,
    field_name: str,
    timeout: int = 2000
) -> bool:
    """
    محاولة ملء حقل باستخدام قائمة selectors
    
    Args:
        page: صفحة Playwright
        selectors: قائمة المحددات
        value: القيمة المراد إدخالها
        field_name: اسم الحقل (للطباعة)
        timeout: المهلة بالمللي ثانية
        
    Returns:
        bool: True لو نجح
    """
    for selector in selectors:
        try:
            element = page.locator(selector).first
            
            # تحقق من الظهور
            is_visible = await element.is_visible(timeout=timeout)
            
            if is_visible:
                # محاولة الملء
                await element.fill(value)
                print(f"  ✅ Filled {field_name}: {selector}")
                return True
                
        except Exception as e:
            continue
    
    print(f"  ⚠️ Could not find {field_name} field")
    return False

async def try_click_button(
    page: Page,
    selectors: List[str],
    button_name: str,
    timeout: int = 2000,
    wait_after: int = 1000
) -> bool:
    """
    محاولة الضغط على زر باستخدام قائمة selectors
    
    Args:
        page: صفحة Playwright
        selectors: قائمة المحددات
        button_name: اسم الزر (للطباعة)
        timeout: المهلة بالمللي ثانية
        wait_after: انتظار بعد الضغط
        
    Returns:
        bool: True لو نجح
    """
    for selector in selectors:
        try:
            element = page.locator(selector).first
            
            # تحقق من الظهور والقدرة على الضغط
            is_visible = await element.is_visible(timeout=timeout)
            
            if is_visible:
                # محاولة الضغط
                await element.click()
                print(f"  ✅ Clicked {button_name}: {selector}")
                
                # انتظار قصير
                await page.wait_for_timeout(wait_after)
                return True
                
        except Exception as e:
            continue
    
    print(f"  ⚠️ Could not find {button_name} button")
    return False

async def detect_otp_in_page(page: Page) -> Optional[str]:
    """
    محاولة اكتشاف OTP في محتوى الصفحة
    
    Args:
        page: صفحة Playwright
        
    Returns:
        str: OTP إذا وُجد، None غير ذلك
    """
    try:
        # الحصول على نص الصفحة
        page_text = await page.text_content('body')
        
        if not page_text:
            return None
        
        # البحث عن أرقام 4-6 خانات
        otp_patterns = [
            r'code[:\s]+(\d{4,6})',  # "Code: 1234"
            r'otp[:\s]+(\d{4,6})',   # "OTP: 5678"
            r'verification[:\s]+(\d{4,6})',  # "Verification: 9012"
            r'\b(\d{4})\b',           # رقم 4 خانات منفصل
            r'\b(\d{6})\b'            # رقم 6 خانات منفصل
        ]
        
        for pattern in otp_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                # إرجاع أول match
                return matches[0]
        
        return None
        
    except Exception as e:
        print(f"  ⚠️ Error detecting OTP: {e}")
        return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# السيناريو الكامل (الدالة الرئيسية)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def run_registration_scenario(
    url: str,
    phone_number: Optional[str] = None,
    headless: bool = False,
    timeout: int = 30000,
    screenshot_dir: str = "screenshots"
) -> Dict:
    """
    تنفيذ سيناريو تسجيل كامل (الدالة الرئيسية)
    
    Args:
        url: رابط الموقع
        phone_number: رقم الهاتف (None = توليد تلقائي)
        headless: تشغيل بدون واجهة
        timeout: timeout عام بالمللي ثانية
        screenshot_dir: مجلد Screenshots
        
    Returns:
        dict: تقرير مفصل عن النتائج
    """
    # توليد بيانات
    fake_name = generate_fake_name()
    fake_email = generate_fake_email()
    fake_password = generate_fake_password()
    fake_phone = phone_number or generate_fake_phone()
    
    # تقرير النتائج
    report = {
        "url": url,
        "status": "unknown",
        "timestamp": datetime.now().isoformat(),
        "test_data": {
            "name": fake_name,
            "email": fake_email,
            "phone": fake_phone
        },
        "steps": {},
        "errors": [],
        "screenshots": [],
        "otp_detected": None
    }
    
    browser = None
    
    try:
        async with async_playwright() as p:
            # فتح المتصفح
            print(f"\n{'='*60}")
            print(f"🤖 Starting automation for: {url}")
            print(f"{'='*60}")
            
            browser = await p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            page.set_default_timeout(timeout)
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # الخطوة 1: فتح الموقع
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            print("\n📍 Step 1: Opening website...")
            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)
                report['steps']['open_site'] = 'success'
                print("  ✅ Website loaded successfully")
                
                # Screenshot
                screenshot_path = f"{screenshot_dir}/{url.split('//')[-1].replace('/', '_')}_1_opened.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                report['screenshots'].append(screenshot_path)
                
            except Exception as e:
                report['steps']['open_site'] = f'failed: {str(e)}'
                report['errors'].append(f"Failed to open site: {e}")
                report['status'] = 'failed_open'
                await browser.close()
                return report
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # الخطوة 2: ملء النموذج
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            print("\n📍 Step 2: Filling registration form...")
            
            # الاسم
            name_filled = await try_fill_field(
                page, get_name_selectors(), fake_name, "name"
            )
            report['steps']['fill_name'] = 'success' if name_filled else 'failed'
            
            # الإيميل
            email_filled = await try_fill_field(
                page, get_email_selectors(), fake_email, "email"
            )
            report['steps']['fill_email'] = 'success' if email_filled else 'failed'
            
            # الباسورد
            password_filled = await try_fill_field(
                page, get_password_selectors(), fake_password, "password"
            )
            report['steps']['fill_password'] = 'success' if password_filled else 'failed'
            
            # الهاتف (اختياري في هذه المرحلة)
            phone_filled = await try_fill_field(
                page, get_phone_selectors(), fake_phone, "phone"
            )
            report['steps']['fill_phone'] = 'success' if phone_filled else 'skipped'
            
            # Screenshot
            screenshot_path = f"{screenshot_dir}/{url.split('//')[-1].replace('/', '_')}_2_filled.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            report['screenshots'].append(screenshot_path)
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # الخطوة 3: إرسال النموذج
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            print("\n📍 Step 3: Submitting form...")
            
            submit_clicked = await try_click_button(
                page, get_submit_button_selectors(), "submit", wait_after=3000
            )
            report['steps']['click_submit'] = 'success' if submit_clicked else 'failed'
            
            if not submit_clicked:
                report['status'] = 'failed_submit'
                await browser.close()
                return report
            
            # انتظار للتحميل
            await page.wait_for_timeout(2000)
            
            # Screenshot
            screenshot_path = f"{screenshot_dir}/{url.split('//')[-1].replace('/', '_')}_3_submitted.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            report['screenshots'].append(screenshot_path)
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # الخطوة 4: التحقق من صفحة التحقق
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            print("\n📍 Step 4: Checking for verification page...")
            
            current_url = page.url
            verification_keywords = ['verify', 'otp', 'verification', 'confirm', 'code']
            
            is_verification_page = any(kw in current_url.lower() for kw in verification_keywords)
            
            if is_verification_page:
                report['steps']['reached_verification'] = 'success'
                print("  ✅ Reached verification page!")
                
                # ملء الهاتف لو مش ممتلئ
                if not phone_filled:
                    print("\n📍 Step 4.1: Filling phone number...")
                    phone_filled_now = await try_fill_field(
                        page, get_phone_selectors(), fake_phone, "phone (verification)"
                    )
                    report['steps']['fill_phone_verification'] = 'success' if phone_filled_now else 'failed'
                    
                    if phone_filled_now:
                        # محاولة إرسال الكود
                        print("\n📍 Step 4.2: Requesting OTP code...")
                        send_clicked = await try_click_button(
                            page, get_send_code_selectors(), "send code", wait_after=3000
                        )
                        report['steps']['send_code'] = 'success' if send_clicked else 'failed'
                
                # Screenshot
                screenshot_path = f"{screenshot_dir}/{url.split('//')[-1].replace('/', '_')}_4_verification.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                report['screenshots'].append(screenshot_path)
                
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # الخطوة 5: محاولة قراءة OTP
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                print("\n📍 Step 5: Looking for OTP code...")
                
                otp_code = await detect_otp_in_page(page)
                
                if otp_code:
                    print(f"  🎯 OTP Detected: {otp_code}")
                    report['otp_detected'] = otp_code
                    report['steps']['otp_detection'] = 'success'
                    
                    # محاولة إدخال OTP
                    otp_filled = await try_fill_field(
                        page, get_otp_input_selectors(), otp_code, "OTP"
                    )
                    report['steps']['fill_otp'] = 'success' if otp_filled else 'failed'
                    
                else:
                    print("  ⚠️ OTP not found in page")
                    report['steps']['otp_detection'] = 'not_found'
                
                report['status'] = 'success_with_verification'
                
            else:
                report['steps']['reached_verification'] = 'not_detected'
                report['status'] = 'success_no_verification'
                print("  ℹ️ No verification page detected")
            
            await browser.close()
            
    except Exception as e:
        report['status'] = 'error'
        report['errors'].append(f"Unexpected error: {str(e)}")
        print(f"\n❌ Error: {e}")
        
        if browser:
            await browser.close()
    
    return report
