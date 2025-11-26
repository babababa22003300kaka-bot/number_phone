#!/usr/bin/env python3
"""محرك التحليل المُحسّن"""

import re
import httpx
from bs4 import BeautifulSoup
from html import unescape
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

class WebAnalyzer:
    """محلل الصفحات الذكي"""
    
    def __init__(
        self, 
        html_keywords: List[str],
        api_keywords: List[str],
        timeout: int = 10,
        max_size: int = 3145728,
        user_agent: str = None
    ):
        self.html_keywords = [k.lower() for k in html_keywords]
        self.api_keywords = [k.lower() for k in api_keywords]
        self.timeout = timeout
        self.max_size = max_size
        
        # إعداد الـ client
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,  # مهم جداً!
            limits=httpx.Limits(max_connections=100),
            headers={
                "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
            }
        )
    
    def detect_protection(self, response: httpx.Response, html: str) -> Tuple[bool, str]:
        """كشف Cloudflare/Captcha"""
        # Cloudflare
        if 'cf-ray' in response.headers or 'cloudflare' in html.lower():
            return True, "cloudflare"
        
        # Captcha
        captcha_indicators = ['recaptcha', 'hcaptcha', 'captcha', 'g-recaptcha']
        if any(ind in html.lower() for ind in captcha_indicators):
            return True, "captcha"
        
        return False, "clean"
    
    def analyze_inputs(self, soup: BeautifulSoup) -> Dict:
        """تحليل حقول الإدخال"""
        phone_score = 0
        verify_score = 0
        evidence = []
        
        for inp in soup.find_all(["input", "textarea", "select"]):
            # جمع الـ attributes
            attrs_text = " ".join([
                str(inp.get(a, "")) 
                for a in ["id", "name", "class", "placeholder", "type", 
                         "inputmode", "autocomplete", "aria-label"]
            ]).lower()
            
            # Type=tel أو inputmode=tel
            if inp.get("type") == "tel" or inp.get("inputmode") == "tel":
                phone_score += 30
                evidence.append({
                    "type": "input_type_tel",
                    "confidence": "high",
                    "element": str(inp)[:200]
                })
            
            # Autocomplete
            if "tel" in inp.get("autocomplete", "").lower():
                phone_score += 20
            
            # HTML Keywords
            for kw in self.html_keywords:
                if kw in attrs_text:
                    if kw in ["phone", "mobile", "tel"]:
                        phone_score += 15
                    elif kw in ["verify", "otp", "code"]:
                        verify_score += 15
                    evidence.append({
                        "type": "input_keyword",
                        "keyword": kw,
                        "element": str(inp)[:200]
                    })
            
            # Pattern للـ phone
            pattern = inp.get("pattern", "")
            if pattern and re.search(r'[\d\+\-\(\)]{6,}', pattern):
                phone_score += 10
        
        return {
            "phone_score": min(phone_score, 100),
            "verify_score": min(verify_score, 100),
            "evidence": evidence[:10]  # أول 10 فقط
        }
    
    def analyze_text(self, soup: BeautifulSoup) -> Dict:
        """تحليل النصوص والـ labels"""
        phone_score = 0
        verify_score = 0
        evidence = []
        
        for tag in soup.find_all(["label", "button", "a", "h1", "h2", "h3", "span"]):
            text = unescape(" ".join(tag.stripped_strings)).lower()
            if not text or len(text) > 200:
                continue
            
            for kw in self.html_keywords:
                if kw in text:
                    if kw in ["phone", "mobile", "signup", "register"]:
                        phone_score += 5
                    elif kw in ["verify", "otp", "send"]:
                        verify_score += 10
                    evidence.append({
                        "type": "text_keyword",
                        "keyword": kw,
                        "snippet": text[:100]
                    })
        
        return {
            "phone_score": min(phone_score, 50),
            "verify_score": min(verify_score, 50),
            "evidence": evidence[:10]
        }
    
    def analyze_api(self, soup: BeautifulSoup, html: str) -> Dict:
        """تحليل الـ API endpoints"""
        verify_score = 0
        endpoints = []
        
        # استخراج الـ scripts
        scripts = soup.find_all("script")
        script_text = " ".join([s.get_text() for s in scripts if s.string])
        
        # البحث عن URLs
        url_pattern = r'(?:https?://[^\s"\'\)<>]+|/api/[^\s"\'\)<>]+|/v\d+/[^\s"\'\)<>]+)'
        found_urls = re.findall(url_pattern, html + script_text)
        
        for url in found_urls:
            url_lower = url.lower()
            for kw in self.api_keywords:
                if kw in url_lower:
                    verify_score += 20
                    endpoints.append({
                        "url": url,
                        "keyword": kw,
                        "confidence": "high"
                    })
                    break
        
        # البحث عن function names
        api_patterns = [
            r'(send(?:Otp|OTP|Sms|SMS|Code|Verification))',
            r'(verify(?:Otp|OTP|Code|Phone|SMS))',
            r'(check(?:Otp|OTP|Phone))'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, script_text, re.IGNORECASE)
            for match in matches[:5]:
                verify_score += 15
                endpoints.append({
                    "function": match,
                    "confidence": "medium"
                })
        
        return {
            "verify_score": min(verify_score, 100),
            "endpoints": endpoints[:10]
        }
    
    def calculate_confidence(self, results: Dict) -> int:
        """حساب الثقة النهائية"""
        phone_score = results["phone_score"]
        verify_score = results["verify_score"]
        
        # لو في phone قوي + verify قوي
        if phone_score >= 40 and verify_score >= 40:
            return min(phone_score + verify_score, 100)
        
        # لو في phone قوي بس
        elif phone_score >= 50:
            return phone_score + (verify_score // 2)
        
        # لو في verify قوي بس
        elif verify_score >= 50:
            return verify_score + (phone_score // 2)
        
        # ضعيف
        else:
            return (phone_score + verify_score) // 2
    
    def analyze(self, url: str) -> Optional[Dict]:
        """التحليل الشامل"""
        try:
            # الطلب
            response = self.client.get(url)
            
            # التحقق من الحجم
            if len(response.content) > self.max_size:
                return None
            
            html = response.text
            
            # كشف الحماية
            is_protected, protection_type = self.detect_protection(response, html)
            if is_protected:
                return {
                    "url": url,
                    "status": "protected",
                    "protection": protection_type,
                    "confidence": 0
                }
            
            # التحليل
            soup = BeautifulSoup(html, "lxml")
            
            inputs = self.analyze_inputs(soup)
            text = self.analyze_text(soup)
            api = self.analyze_api(soup, html)
            
            # الدرجات
            phone_score = inputs["phone_score"] + text["phone_score"]
            verify_score = inputs["verify_score"] + text["verify_score"] + api["verify_score"]
            
            results = {
                "phone_score": min(phone_score, 100),
                "verify_score": min(verify_score, 100)
            }
            
            confidence = self.calculate_confidence(results)
            
            return {
                "url": url,
                "status": "analyzed",
                "http_status": response.status_code,
                "confidence": confidence,
                "phone_score": results["phone_score"],
                "verify_score": results["verify_score"],
                "evidence": {
                    "inputs": inputs["evidence"][:5],
                    "text": text["evidence"][:5],
                    "api": api["endpoints"][:5]
                }
            }
        
        except httpx.TimeoutException:
            return {"url": url, "status": "timeout", "confidence": 0}
        except httpx.ConnectError:
            return {"url": url, "status": "connection_error", "confidence": 0}
        except Exception as e:
            return {"url": url, "status": "error", "error": str(e), "confidence": 0}
    
    def close(self):
        """إغلاق الـ client"""
        self.client.close()