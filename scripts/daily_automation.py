#!/usr/bin/env python3
import os
import sys
from datetime import datetime
import subprocess

def run_daily_automation():
    """Run all automated tasks"""
    
    print(f"🤖 LLM Safety Mechanisms - Daily Automation")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*50)
    
    # 1. Check for new sources
    print("\n1️⃣ Checking for new sources...")
    subprocess.run([sys.executable, "scripts/source_monitor.py"])
    
    # 2. Extract evidence from new sources
    if os.environ.get('OPENAI_API_KEY'):
        print("\n2️⃣ Extracting evidence with LLM...")
        subprocess.run([sys.executable, "scripts/evidence_extractor_llm.py"])
    else:
        print("\n⚠️  Skipping LLM extraction (no API key)")
    
    # 3. Verify existing sources
    print("\n3️⃣ Verifying source URLs...")
    subprocess.run([sys.executable, "scripts/verify_sources.py", "--check-new-only"])
    
    # 4. Update dashboard
    print("\n4️⃣ Regenerating dashboard...")
    subprocess.run([sys.executable, "scripts/generate_dashboard.py"])
    subprocess.run([sys.executable, "scripts/generate_report.py"])
    
    # 5. Git status
    print("\n5️⃣ Git status:")
    subprocess.run(["git", "status", "--short"])
    
    print("\n✅ Daily automation complete!")

if __name__ == "__main__":
    run_daily_automation()