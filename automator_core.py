import subprocess
import sys

def run_test():
    print("🚀 Starting Alternative Automation Engine...")
    try:
        # استخدام subprocess لتنفيذ الأمر مباشرة مع النظام
        result = subprocess.run(
            ["echo", "✅ Alternative Tool Success: Subprocess is working!"], 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout.strip())
            print("🎉 Engine is Ready.")
        else:
            print(f"❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"💥 Critical Failure: {e}")

if __name__ == "__main__":
    run_test()
