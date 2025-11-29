"""
Centralized Configuration Manager
مدير الإعدادات المركزي

يجمع كل مصادر الإعدادات في مكان واحد
Priority: Environment Variables → settings.json → Defaults
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv


class ConfigManager:
    """مدير الإعدادات المركزي - يجمع كل مصادر الإعدادات"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._settings = {}
        self._loaded = False
        
        # تحميل .env أولاً
        load_dotenv()
    
    def load(self):
        """تحميل كل الإعدادات"""
        if self._loaded:
            return
        
        # تحميل settings.json
        settings_file = self.config_dir / "settings.json"
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                self._settings = json.load(f)
        
        self._loaded = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        جلب إعداد
        الأولوية: Environment Variable → settings.json → default
        """
        # Try environment variable first
        env_value = os.getenv(key.upper())
        if env_value is not None:
            return env_value
        
        # Try settings.json
        if key in self._settings:
            return self._settings[key]
        
        # Return default
        return default
    
    def get_telegram_config(self) -> Optional[Dict]:
        """جلب إعدادات التليجرام"""
        if not self.get('telegram', {}).get('enabled'):
            return None
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if token and chat_id:
            return {
                'bot_token': token,
                'chat_id': chat_id,
                'logo_url': self.get('telegram', {}).get('logo_url')
            }
        return None
    
    def get_serpapi_key(self) -> Optional[str]:
        """جلب SerpAPI key"""
        # Try first key
        key1 = os.getenv("SERP_API_KEY_1")
        if key1 and 'YOUR_' not in key1.upper():
            return key1
        
        # Try second key
        key2 = os.getenv("SERP_API_KEY_2")
        if key2 and 'YOUR_' not in key2.upper():
            return key2
        
        return None
    
    def load_text_file(self, filename: str, default: List[str] = None) -> List[str]:
        """تحميل ملف نصي"""
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            return default or []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    
    @property
    def threads(self) -> int:
        """عدد الـ Workers"""
        return self.get('threads', 5)
    
    @property
    def timeout(self) -> int:
        """Timeout بالثواني"""
        return self.get('timeout', 10)
    
    @property
    def confidence_threshold(self) -> int:
        """حد الثقة الأدنى"""
        return self.get('confidence_threshold', 60)
    
    @property
    def max_response_size(self) -> int:
        """أقصى حجم للـ response"""
        return self.get('max_response_size', 3145728)
    
    @property
    def user_agent(self) -> str:
        """User Agent"""
        return self.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    @property
    def use_hash_db(self) -> bool:
        """استخدام قاعدة البيانات"""
        return self.get('use_hash_db', True)
    
    @property
    def hash_db_file(self) -> str:
        """ملف قاعدة البيانات"""
        return self.get('hash_db_file', 'checked_urls.db')
    
    @property
    def scan_paths(self) -> List[str]:
        """مسارات الفحص"""
        return self.get('scan_paths', [])


# Global singleton instance
_config = None


def get_config() -> ConfigManager:
    """
    جلب الـ config manager (Singleton Pattern)
    
    Returns:
        ConfigManager: المدير المركزي للإعدادات
    """
    global _config
    if _config is None:
        _config = ConfigManager()
        _config.load()
    return _config
