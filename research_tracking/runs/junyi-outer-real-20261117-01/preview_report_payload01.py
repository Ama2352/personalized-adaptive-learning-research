"""Trích nguyên CSS/phần outer để kiểm offline trong tab MCP riêng."""
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[3]
html=(root/'research_tracking/supervisor_reports/2026-11-16/01_tien_do/BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
section=re.search(r'<section id="outer-progress">.*?</section>',html,re.S).group(0)
css=re.search(r'<style>.*?</style>',html,re.S).group(0)
print(json.dumps(dict(html='<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'+css+'</head><body><main>'+section+'</main></body></html>')))
