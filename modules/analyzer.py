#!/usr/bin/env python3
"""محرك التحليل المُحسّن (AsyncIO) - النسخة 2.4 (Phase 3)"""

import re
import httpx
from bs4 import BeautifulSoup
from html import unescape
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

class WebAnalyzer:
    """محلل الصفحات الذكي (نسخة AsyncIO + Browser Fallback)"""
    
    def __init__(
        self, 
        html_keywords: List[str],
        api_keywords: List[str],
        exclude_keywords: List[str] = None,
        timeout: int = 10,
        max_size: int = 3145728,
        user_agent: str = None,
        browser_service_url: str = None,
        fallback_threshold: int = 20
    ):
        self.html_keywords = [k.lower() for k in html_keywords]
        self.api_keywords = [k.lower() for k in api_keywords]
        self.exclude_keywords = [k.lower() for k in (exclude_keywords or [])]
        self.timeout = timeout
        self.max_size = max_size
        self.browser_service_url = browser_service_url
        self.fallback_threshold = fallback_threshold
        
        # إعداد الـ AsyncClient
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
            headers={
                "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
            },
            verify=False  # تجاهل أخطاء SSL للسرعة
        )
    
    def _check_exclusion(self, html: str) -> Tuple[bool, str]:
        """فحص كلمات الاستبعاد في محتوى الصفحة"""
        html_lower = html.lower()
        for keyword in self.exclude_keywords:
            if keyword in html_lower:
                return True, keyword
        return False, ""
    
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
            attrs_text = " ".join([
                str(inp.get(a, "")) 
                for a in ["id", "name", "class", "placeholder", "type", 
                         "inputmode", "autocomplete", "aria-label"]
            ]).lower()
            
            if inp.get("type") == "tel" or inp.get("inputmode") == "tel":
                phone_score += 30
                evidence.append({
                    "type": "input_type_tel",
                    "confidence": "high",
                    "element": str(inp)[:200]
                })
            
            if "tel" in inp.get("autocomplete", "").lower():
                phone_score += 20
            
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
            
            pattern = inp.get("pattern", "")
            if pattern and re.search(r'[\d\+\-\(\)]{6,}', pattern):
                phone_score += 10
        
        return {
            "phone_score": min(phone_score, 100),
            "verify_score": min(verify_score, 100),
            "evidence": evidence[:10]
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
        
        scripts = soup.find_all("script")
        script_text = " ".join([s.get_text() for s in scripts if s.string])
        
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
            "endpoints": endpoints[:10],
            "script_text": script_text
        }
    
    def _check_signatures(self, html: str, script_text: str) -> Dict:
        """كشف بصمات مزودي خدمات OTP/SMS"""
        signatures = {
            "firebase": [
                r'firebase\.initializeApp',
                r'firebase\.auth\(\)',
                r'signInWithPhoneNumber',
                r'recaptcha-container'
            ],
            "twilio": [
                r'Twilio\.Device',
                r'Twilio\.Chat',
                r'api\.twilio\.com'
            ],
            "msg91": [
                r'msg91\.com',
                r'msg91'
            ],
            "infobip": [
                r'infobip',
                r'api\.infobip'
            ],
            "nexmo": [
                r'nexmo',
                r'vonage',
                r'api\.nexmo'
            ],
            "aws_sns": [
                r'aws-sdk',
                r'AWS\.SNS',
                r'sns\.amazonaws'
            ],
            "plivo": [
                r'plivo',
                r'api\.plivo'
            ],
            "messagebird": [
                r'messagebird',
                r'rest\.messagebird'
            ]
        }
        
        found_signatures = []
        score = 0
        combined_text = html + " " + script_text
        
        for provider, patterns in signatures.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    found_signatures.append(provider)
                    score += 25
                    break
        
        return {
            "score": min(score, 50),
            "signatures": found_signatures
        }
    
    def calculate_confidence(self, results: Dict) -> int:
        """حساب الثقة النهائية"""
        phone_score = results["phone_score"]
        verify_score = results["verify_score"]
        
        if phone_score >= 40 and verify_score >= 40:
            return min(phone_score + verify_score, 100)
        elif phone_score >= 50:
            return phone_score + (verify_score // 2)
        elif verify_score >= 50:
            return verify_score + (phone_score // 2)
        else:
            return (phone_score + verify_score) // 2

    async def check_paths(self, base_url: str, paths: List[str]) -> List[Dict]:
        """فحص المسارات الفرعية (Path Fuzzing)"""
        found_paths = []
        
        for path in paths:
            full_url = urljoin(base_url, path)
            try:
                print(f"🔍 [PATH] Checking {full_url} ...", end="\r")
                response = await self.client.get(full_url)
                
                if response.status_code == 200:
                    html = response.text
                    soup = BeautifulSoup(html, "lxml")
                    inputs = self.analyze_inputs(soup)
                    text = self.analyze_text(soup)
                    
                    sub_score = inputs["phone_score"] + text["phone_score"] + inputs["verify_score"]
                    
                    if sub_score > 20:
                        found_paths.append({
                            "url": full_url,
                            "score": sub_score,
                            "title": soup.title.string.strip() if soup.title else "No Title"
                        })
            except:
                continue
                
        return found_paths
    
    async def _fallback_browser_check(self, url: str) -> Optional[str]:
        """محاولة الفحص العميق باستخدام BaaS Server"""
        if not self.browser_service_url:
            return None
        
        try:
            response = await self.client.post(
                self.browser_service_url,
                json={"url": url, "timeout": 30000},
                timeout=35.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("html")
        except Exception as e:
            print(f"⚠️ [BaaS] Failed to render {url}: {str(e)}")
        
        return None

    async def analyze(self, url: str, scan_paths: List[str] = None) -> Optional[Dict]:
        """التحليل الشامل (Async) مع Browser Fallback"""
        try:
            # الطلب الرئيسي (HTTPX Fast)
            response = await self.client.get(url)
            
            if len(response.content) > self.max_size:
                return {"url": url, "status": "oversize", "confidence": 0}
            
            html = response.text
            
            # فحص الاستبعاد
            is_excluded, excluded_keyword = self._check_exclusion(html)
            if is_excluded:
                return {
                    "url": url,
                    "status": "excluded",
                    "reason": excluded_keyword,
                    "confidence": 0
                }
            
            # كشف الحماية
            is_protected, protection_type = self.detect_protection(response, html)
            if is_protected:
                return {
                    "url": url,
                    "status": "protected",
                    "protection": protection_type,
                    "confidence": 0
                }
            
            # التحليل الرئيسي
            soup = BeautifulSoup(html, "lxml")
            inputs = self.analyze_inputs(soup)
            text = self.analyze_text(soup)
            api = self.analyze_api(soup, html)
            signatures = self._check_signatures(html, api.get("script_text", ""))
            
            phone_score = inputs["phone_score"] + text["phone_score"]
            verify_score = inputs["verify_score"] + text["verify_score"] + api["verify_score"] + signatures["score"]
            
            results = {
                "phone_score": min(phone_score, 100),
                "verify_score": min(verify_score, 100)
            }
            
            confidence = self.calculate_confidence(results)
            method = "httpx"
            
            # 🔄 Browser Fallback (Phase 3)
            if self.browser_service_url and confidence < self.fallback_threshold:
                print(f"🔄 [RETRY] {url} with Browser (Conf: {confidence}% < {self.fallback_threshold}%)...")
                full_html = await self._fallback_browser_check(url)
                
                if full_html:
                    # إعادة التحليل بالـ HTML الجديد
                    soup = BeautifulSoup(full_html, "lxml")
                    inputs = self.analyze_inputs(soup)
                    text = self.analyze_text(soup)
                    api = self.analyze_api(soup, full_html)
                    signatures = self._check_signatures(full_html, api.get("script_text", ""))
                    
                    phone_score = inputs["phone_score"] + text["phone_score"]
                    verify_score = inputs["verify_score"] + text["verify_score"] + api["verify_score"] + signatures["score"]
                    
                    results = {
                        "phone_score": min(phone_score, 100),
                        "verify_score": min(verify_score, 100)
                    }
                    
                    confidence = self.calculate_confidence(results)
                    method = "playwright"
                    print(f"✅ [BROWSER] New confidence: {confidence}%")
            
            # Path Fuzzing
            valid_paths = []
            if scan_paths and (confidence > 10 or response.status_code == 200):
                valid_paths = await self.check_paths(url, scan_paths)
                
                if valid_paths:
                    confidence = max(confidence, 80)
                    results["phone_score"] = max(results["phone_score"], 80)
            
            return {
                "url": url,
                "status": "analyzed",
                "http_status": response.status_code,
                "confidence": confidence,
                "phone_score": results["phone_score"],
                "verify_score": results["verify_score"],
                "method": method,
                "evidence": {
                    "inputs": inputs["evidence"][:5],
                    "text": text["evidence"][:5],
                    "api": api["endpoints"][:5],
                    "signatures": signatures["signatures"],
                    "paths": valid_paths
                }
            }
        
        except httpx.TimeoutException:
            return {"url": url, "status": "timeout", "confidence": 0}
        except httpx.ConnectError:
            return {"url": url, "status": "connection_error", "confidence": 0}
        except Exception as e:
            return {"url": url, "status": "error", "error": str(e), "confidence": 0}
    
    async def close(self):
        """إغلاق الـ client"""
        await self.client.aclose()