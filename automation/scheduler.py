"""
Scheduler - جدولة تشغيل تلقائية
Functions only - بدون classes
"""

import schedule
import time
import subprocess
import sys
from datetime import datetime


def run_bot():
    """
    تشغيل البوت - دالة بسيطة
    """
    print(f"\n{'='*50}")
    print(f"🚀 Starting bot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=".",
            capture_output=False
        )
        
        if result.returncode == 0:
            print(f"\n✅ Bot completed successfully")
        else:
            print(f"\n⚠️ Bot exited with code {result.returncode}")
    
    except Exception as e:
        print(f"\n❌ Error running bot: {e}")


def schedule_bot(interval_hours=24):
    """
    جدولة تشغيل البوت - دالة بسيطة
    
    Args:
        interval_hours: كل كام ساعة يشتغل
    """
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ Bot Scheduler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interval: Every {interval_hours} hours
First run: Immediate
Next run: {interval_hours} hours from now
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Press Ctrl+C to stop
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # Schedule
    schedule.every(interval_hours).hours.do(run_bot)
    
    # Run immediately on start
    run_bot()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n⏸️ Scheduler stopped by user")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Schedule bot execution")
    parser.add_argument(
        '--interval',
        type=int,
        default=24,
        help='Hours between runs (default: 24)'
    )
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run once and exit'
    )
    
    args = parser.parse_args()
    
    if args.run_once:
        run_bot()
    else:
        schedule_bot(args.interval)
