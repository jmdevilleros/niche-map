#!/usr/bin/env python3
"""Convert a Markdown report (tables + images) into a polished PDF with WeasyPrint.

Usage: python md_to_pdf.py input.md output.pdf --footer "Footer text" [--landscape] [--page-break "Ranking,Niche cards,Appendix"]

The first H1 becomes a cover banner; H2 headings that start with any prefix in --page-break begin a new page.
An initial YAML block (--- ... ---), if present, is shown as a metadata box. Image paths are resolved relative to the .md file."""
import argparse, os, re, html, markdown
from weasyprint import HTML

ap = argparse.ArgumentParser(description="Markdown report -> PDF (WeasyPrint).")
ap.add_argument("md", help="input Markdown file"); ap.add_argument("pdf", help="output PDF file")
ap.add_argument("--footer", default="", help="text shown at the bottom-left of every page")
ap.add_argument("--landscape", action="store_true", help="A4 landscape instead of portrait")
ap.add_argument("--page-break", default="", help="comma-separated H2 prefixes that start a new page")
a = ap.parse_args()
with open(a.md, encoding="utf-8") as f: md = f.read()
front = ""
m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
if m:
    front = f"<pre class='front'>{html.escape(m.group(1))}</pre>"; md = md[m.end():]
# normalize lists: nested indentation to 4 spaces and a blank line before a list that follows a paragraph
LI = re.compile(r"^(\s*)([-*+]|\d+\.)\s")
out, prev, infence = [], "", False
for ln in md.split("\n"):
    if ln.startswith("```"): infence = not infence
    m_ = None if infence else LI.match(ln)
    if m_ and 0 < len(m_.group(1)) < 4: ln = "    " + ln.lstrip()
    if m_ and not m_.group(1) and prev.strip() and not LI.match(prev) and not prev.lstrip().startswith("|") and not infence: out.append("")
    out.append(ln); prev = ln
md = "\n".join(out)
body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
body = body.replace("<h1>", "<div class='cover'><h1>", 1).replace("</h1>", "</h1></div>" + front, 1)
for p in [x.strip() for x in a.page_break.split(",") if x.strip()]:
    body = re.sub(rf"<h2>({re.escape(p)})", r"<h2 class='pb'>\1", body)
size = "A4 landscape" if a.landscape else "A4"
footer = a.footer.replace('"', "'")
css = f"""@page{{size:{size};margin:14mm 14mm 15mm;@bottom-right{{content:counter(page) " / " counter(pages);font:8pt sans-serif;color:#999}}@bottom-left{{content:"{footer}";font:8pt sans-serif;color:#aaa}}}}
body{{font-family:Inter,"DejaVu Sans",sans-serif;font-size:9.6pt;line-height:1.45;color:#1d1d28}}
.cover{{background:linear-gradient(110deg,#0b1d3a 0%,#1f5fbf 40%,#19a39a 75%,#c8e65a 100%);color:#fff;border-radius:5mm;padding:10mm 11mm;margin-bottom:4mm}}
.cover h1{{margin:0;font-size:23pt;font-weight:800}}
pre.front{{background:#f2f6fb;color:#1d1d28;border-left:4px solid #1f5fbf;padding:3mm 4mm;font-size:8pt;white-space:pre-wrap}}
h2{{font-size:14.5pt;color:#0b1d3a;border-bottom:2px solid #1f5fbf;padding-bottom:1mm;margin:6mm 0 2.5mm;break-after:avoid}}
h3{{font-size:11.3pt;color:#1f5fbf;margin:4.5mm 0 1.5mm;break-after:avoid}} h4{{font-size:10pt;margin:3mm 0 1mm;break-after:avoid}}
table{{border-collapse:collapse;width:100%;margin:2mm 0 3mm}} tr{{break-inside:avoid}} thead{{display:table-header-group}}
th{{background:#e6eef9;text-align:left;padding:1.5mm;font-size:8pt}}
td{{padding:1.4mm;border-bottom:.4pt solid #ddd;vertical-align:top;font-size:8pt;word-break:break-word}}
blockquote{{background:#f4f8fd;border-left:4px solid #19a39a;margin:2mm 0;padding:2mm 4mm}}
code{{font-size:8pt;background:#eef2f7;padding:0 1mm;border-radius:1mm}}
pre{{background:#0f172a;color:#e2e8f0;padding:3mm;border-radius:2mm;font-size:7.6pt;white-space:pre-wrap;break-inside:avoid}} pre code{{background:none;color:inherit}}
img{{max-width:100%;max-height:150mm;display:block;margin:2mm auto}}
a{{color:#1f5fbf;text-decoration:none}} .pb{{break-before:page}} li{{margin:.5mm 0}}"""
HTML(string=f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>",
     base_url=os.path.dirname(os.path.abspath(a.md))).write_pdf(a.pdf)
print("PDF:", a.pdf)
