#!/usr/bin/env python3
"""بوت التليجرام للإرسال"""

import asyncio
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError

class TelegramNotifier:
    """مُرسل النتائج للتليجرام"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
    
    async def send_result(self, result: dict):
        """إرسال نتيجة واحدة"""
        try:
            # تنسيق الرسالة
            message = self._format_message(result)
            
            # إرسال نص فقط
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            return True
        
        except TelegramError as e:
            print(f"❌ خطأ في إرسال التليجرام: {e}")
            return False
    
    def _format_message(self, result: dict) -> str:
        """تنسيق الرسالة"""
        url = result.get("url", "Unknown")
        confidence = result.get("confidence", 0)
        phone = result.get("phone_score", 0)
        verify = result.get("verify_score", 0)
        
        # الإيموجي حسب الثقة
        if confidence >= 80:
            emoji = "🔥"
        elif confidence >= 60:
            emoji = "✅"
        else:
            emoji = "⚠️"
        
        message = f"""
{emoji} **موقع محتمل**

🔗 **الرابط:**
`{url}`

📊 **التقييم:**
• الثقة: {confidence}%
• Phone: {phone}%
• Verify: {verify}%

🕒 اتفحص دلوقتي
        """.strip()
        
        return message