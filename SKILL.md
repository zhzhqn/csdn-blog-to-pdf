---
name: csdn-blog-to-pdf
description: "Convert a CSDN blog article or similarly structured web page into a clean, ad-free, image-included PDF for offline reading. Use when a user wants to save a CSDN or web article as a tidy PDF, especially when the page is blocked by CSDN security verification, contains many screenshots, or is cluttered with ads and sidebars. Handles proxy bypass, real-image extraction, and the Windows path pitfall that silently drops images from the PDF."
agent_created: true
---

# CSDN Blog to Clean PDF

## Purpose
Turn a CSDN blog URL into a single self-contained PDF: extract the article body
(id="content_views"), strip ads/sidebars/recommendations, download the real
screenshots (i-blog.csdnimg.cn), and lay it out cleanly. Works around CSDN's
anti-bot security verification page via the environment HTTP proxy, and avoids
the Windows backslash path bug that makes the PDF come out image-less.

## When to use
- User asks to save a CSDN blog as a clean PDF or save a web article as PDF.
- The target is blog.csdn.net and may show a captcha when fetched naively.
- Any page whose real images live on i-blog.csdnimg.cn and whose body is content_views.

## Workflow

### Step 0 — Environment (one-time per session)
Use the managed Python. Create/use a venv and install parsers through the proxy:
```
python -m venv ENV
ENV/Scripts/pip install beautifulsoup4 lxml -i https://pypi.org/simple
```
Confirm proxy vars exist (HTTP_PROXY / HTTPS_PROXY); they are required for both
fetching the page and downloading images. See references/gotchas.md.

### Step 1 — Generate the clean HTML
Run the bundled script from the directory where you want outputs:
```
ENV/python scripts/web_to_pdf.py URL或本地html文件 输出名
```
- If the first arg starts with http(s)://, the script fetches via urllib
  (through the proxy, with a browser UA) — this bypasses the CSDN captcha.
- Otherwise it reads a local .html file (useful when pre-fetching with curl).
- Output: 输出名.html + images_输出名/ (real PNGs).
The script already strips ads, filters ad-placeholder images
(kunyu.csdn.net in data-src), fixes author extraction, and critically writes
clean relative image paths (images_x/img_01.png, never an OS-joined path).

### Step 2 — Render to PDF with Chrome headless
```
"Chrome可执行文件" --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="输出名.pdf" --virtual-time-budget=10000 \
  "file:///绝对路径/输出名.html"
```
Common Chrome: /c/Program Files/Google/Chrome/Application/chrome.exe
or /c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe.
The HTML and its images_* folder must sit in the same directory.

### Step 3 — Verify
- grep -a -c "/Subtype */Image" 输出名.pdf should equal the image count.
- File size should be larger than 1 MB when images are present (image-less PDFs are about 100 to 200 KB).
- head -c 8 should print %PDF-1.4.

## Reusable resources
- scripts/web_to_pdf.py — fetch/parse/extract/build clean HTML. Single command.
- references/gotchas.md — proxy bypass, real-image domain, the Windows
  backslash path bug, author extraction, verification commands.

## Notes and extensions
- To add page numbers or headers, edit the CSS in the script or post-process the PDF.
- For non-CSDN pages, adjust the body selector (content_views to article/main)
  and the image-domain filter in the script.
