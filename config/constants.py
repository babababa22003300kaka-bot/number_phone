"""
Application Constants
ثوابت التطبيق

كل الأرقام السحرية والقيم الثابتة في مكان واحد
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Confidence Thresholds
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_CONFIDENCE_THRESHOLD = 60
HIGH_CONFIDENCE_THRESHOLD = 80
MIN_AUTOMATION_CONFIDENCE = 85
FALLBACK_CONFIDENCE_THRESHOLD = 20
PATH_FUZZING_CONFIDENCE_BOOST = 80

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Performance Settings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_SIZE_BYTES = 3 * 1024 * 1024  # 3MB
DEFAULT_WORKERS = 5
MAX_SERP_RESULTS_PER_DORK = 100
DEFAULT_DORK_COUNT = 20
DEFAULT_DORK_RESULTS_PER_QUERY = 10

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Database Settings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_DB_FILE = "checked_urls.db"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# File Paths
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONFIG_DIR = "config"
SETTINGS_FILE = "settings.json"
DOMAINS_FILE = "domains.txt"
HTML_KEYWORDS_FILE = "html_keywords.txt"
API_KEYWORDS_FILE = "api_keywords.txt"
EXCLUDE_FILE = "exclude.txt"
WORDS_FILE = "words.txt"
NAMES_FILE = "names.txt"
LOCATIONS_FILE = "locations.txt"
DORKS_FILE = "dorks.txt"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Default Values
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_WORDS = ["cloud", "net", "app", "tech", "web", "data", "fast", "pro", "smart", "link"]
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Input Validation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DANGEROUS_URL_CHARS = ['<', '>', ';', '&', '|', '`', '$']
ALLOWED_URL_SCHEMES = ['http', 'https']

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Generation Settings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_URL_GENERATION_COUNT = 500
DORKING_URL_RATIO = 0.5  # نسبة الروابط من Dorking
