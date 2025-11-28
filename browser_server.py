#!/usr/bin/env python3
"""
BaaS Server - Browser-as-a-Service
يستقبل URLs ويعيد HTML بعد تصيير JavaScript

الإصدار: 1.0.0
التقنية: FastAPI + Playwright
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from playwright.async_api import async_playwright
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OTP Scanner - BaaS Server",
    description="Browser-as-a-Service for rendering JavaScript-heavy sites",
    version="1.0.0"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Request/Response Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RenderRequest(BaseModel):
    url: HttpUrl
    wait_until: str = "networkidle"  # or "load", "domcontentloaded"
    timeout: int = 30000  # milliseconds

class RenderResponse(BaseModel):
    url: str
    html: str
    status_code: int
    error: str = None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Global State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

browser = None
context = None
playwright_instance = None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Lifecycle Events
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.on_event("startup")
async def startup_event():
    """تشغيل المتصفح عند بدء السيرفر"""
    global browser, context, playwright_instance
    logger.info("🚀 Starting BaaS Server...")
    logger.info("📦 Initializing Playwright...")
    
    try:
        playwright_instance = await async_playwright().start()
        browser = await playwright_instance.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu'
            ]
        )
        
        # Create persistent context (faster for multiple pages)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        logger.info("✅ Browser ready (Chromium headless)")
        logger.info("🌐 Swagger UI: http://127.0.0.1:5000/docs")
        
    except Exception as e:
        logger.error(f"💥 Failed to start browser: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """إغلاق المتصفح عند إيقاف السيرفر"""
    global browser, context, playwright_instance
    logger.info("🛑 Shutting down BaaS Server...")
    
    if context:
        await context.close()
    if browser:
        await browser.close()
    if playwright_instance:
        await playwright_instance.stop()
    
    logger.info("✅ Cleanup complete")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/render", response_model=RenderResponse)
async def render_page(request: RenderRequest):
    """
    تصيير صفحة بـ Playwright
    
    Args:
        request: {url, wait_until, timeout}
        
    Returns:
        {url, html, status_code, error}
    """
    if not browser or not context:
        raise HTTPException(
            status_code=503,
            detail="Browser not initialized. Please restart the server."
        )
    
    url = str(request.url)
    logger.info(f"📄 Received render request: {url}")
    
    page = None
    try:
        # Create new page in existing context
        page = await context.new_page()
        
        # Navigate and wait for specified event
        logger.info(f"⏳ Loading page (wait_until={request.wait_until})...")
        response = await page.goto(
            url,
            wait_until=request.wait_until,
            timeout=request.timeout
        )
        
        # Get full HTML after JS execution
        html = await page.content()
        status_code = response.status if response else 0
        
        logger.info(f"✅ Rendered successfully: {url}")
        logger.info(f"   Status: {status_code} | HTML size: {len(html):,} chars")
        
        return RenderResponse(
            url=url,
            html=html,
            status_code=status_code
        )
    
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Timeout after {request.timeout}ms: {url}")
        raise HTTPException(
            status_code=504,
            detail=f"Page load timeout after {request.timeout}ms"
        )
    
    except Exception as e:
        logger.error(f"💥 Error rendering {url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to render page: {str(e)}"
        )
    
    finally:
        # Always close page to free resources
        if page:
            await page.close()
            logger.info(f"🗑️ Page closed: {url}")

@app.get("/health")
async def health_check():
    """فحص صحة السيرفر"""
    return {
        "status": "healthy",
        "browser_running": browser is not None,
        "context_ready": context is not None
    }

@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "service": "OTP Scanner - BaaS Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "render": "POST /render",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Entry Point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import uvicorn
    
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 BaaS Server - Browser-as-a-Service
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Port: 5000
Swagger UI: http://127.0.0.1:5000/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5000,
        log_level="info",
        access_log=True
    )
