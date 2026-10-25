#!/usr/bin/env python3
"""Rebuild ../index.html from template.html, planner-data.json and fonts.css.

Usage: python3 build/build.py

index.html is what GitHub Pages serves. It is generated: edit the files in this
folder (usually planner-data.json for agenda fixes, template.html for the page),
then run this script and commit both the source and the regenerated index.html.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
LINKEDIN = "https://www.linkedin.com/in/pedrofortuna/"

template = (HERE / "template.html").read_text(encoding="utf-8")
fonts = (HERE / "fonts.css").read_text(encoding="utf-8")
data = json.loads((HERE / "planner-data.json").read_text(encoding="utf-8"))

# Compact JSON, with "</" escaped so the data cannot close its <script> tag
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

html = (template.replace("/*__FONTS__*/", fonts)
                .replace("/*__DATA__*/", payload)
                .replace("/*__LINKEDIN__*/", LINKEDIN))
for marker in ("__FONTS__", "__DATA__", "__LINKEDIN__"):
    assert marker not in html, f"placeholder {marker} left in output"

talks = sum(1 for d in data["days"] for it in d["items"] if it.get("kind") == "talk")
missing = [it["id"] for d in data["days"] for it in d["items"] if it.get("kind") == "talk" and not it.get("topics")]
assert not missing, f"talks without topics: {missing}"

(ROOT / "index.html").write_text(html, encoding="utf-8")
print(f"index.html written: {len(html.encode('utf-8')):,} bytes, {talks} talks, {len(data['workshops'])} workshops")
