"""
Report Generator - إنشاء تقارير
Simple script to generate reports
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.analytics import *


def generate_report():
    """إنشاء تقرير شامل"""
    print("📊 Generating report...")
    
    # Get data
    stats = get_summary_stats()
    results = get_all_results(min_confidence=60)
    
    print(f"✅ Found {len(results)} results")
    
    # Generate HTML
    html_file = generate_html_report(stats, results, "report.html")
    print(f"✅ HTML: {html_file}")
    
    # Export JSON
    json_file = export_to_json(results, "results.json")
    print(f"✅ JSON: {json_file}")
    
    # Export CSV
    csv_file = export_to_csv(results, "results.csv")
    print(f"✅ CSV: {csv_file}")
    
    print("\n🎉 Report generation complete!")


if __name__ == '__main__':
    generate_report()
