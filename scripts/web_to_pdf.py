#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csdn-blog-to-pdf —— 把 CSDN 博客（或类似结构网页）转成干净、带图、去广告的 HTML。
用法:
  python web_to_pdf.py <URL 或 本地html文件> [输出名]
  - 若第一个参数是 http(s):// 开头，则用 urllib 抓取页面（走环境代理，可绕过 CSDN 安全验证）
  - 否则当作本地 HTML 文件读取
输出: <输出名>.html  +  images_<输出名>/  目录（真实配图）
随后用 Chrome --print-to-pdf 把 html 打印成 PDF（见 SKILL.md）。
"""
import os, re, sys, urllib.request
from bs4 import BeautifulSoup

WORK = os.getcwd()  # 在调用目录工作，便于复用

src = sys.argv[1] if len(sys.argv) > 1 else "csdn_raw.html"
out_base = sys.argv[2] if len(sys.argv) > 2 else "article"

IMG_FOLDER = "images_" + out_base
IMG_DIR = os.path.join(WORK, IMG_FOLDER)
os.makedirs(IMG_DIR, exist_ok=True)

# ---- 1. 获取 HTML ----
if src.startswith("http://") or src.startswith("https://"):
    req = urllib.request.Request(
        src,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://blog.csdn.net/",
        },
    )
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    # 同时落盘一份原始 HTML，方便排查
    open(os.path.join(WORK, out_base + "_raw.html"), "w", encoding="utf-8").write(html)
else:
    html = open(src, encoding="utf-8").read()

soup = BeautifulSoup(html, "lxml")

# ---- 2. 标题 ----
title_tag = soup.find("h1", class_="title-article") or soup.find("h1")
title = title_tag.get_text(strip=True) if title_tag else "文章"

# ---- 3. 作者 / 时间 ----
author = "未知"
date = ""
m_blog = re.search(r"https://blog\.csdn\.net/([A-Za-z0-9_-]+)", html)
if m_blog:
    author = m_blog.group(1)  # CSDN 主页链接里的用户名即作者（class 提取不稳定，优先用此）
info = soup.find(class_=re.compile("article-info|bar-content"))
if info:
    m = re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", info.get_text(" ", strip=True))
    if m:
        date = m.group(0)

# ---- 4. 正文 + 去广告/侧栏 ----
body = soup.find(id="content_views")
if body is None:
    body = soup.find("article") or soup.find("main") or soup.body
for bad in body.select("script, style, .recommend, .blog-tail, .operating, .comment-box, .toc-box, #blogComment, .csdn-side, .htmledit_views, .ad"):
    bad.decompose()

# ---- 5. 下载真实配图（过滤广告占位）----
seen = {}
for im in body.find_all("img"):
    src_url = im.get("src") or im.get("data-src") or ""
    # CSDN 真实图域名是 i-blog.csdnimg.cn；data-src 里的 kunyu.csdn.net 是广告占位，丢弃
    if "i-blog.csdnimg.cn" not in src_url and "img-blog.csdnimg.cn" not in src_url:
        im.decompose()
        continue
    if src_url in seen:
        im["src"] = seen[src_url]
        continue
    fn = f"img_{len(seen)+1:02d}.png"
    try:
        req = urllib.request.Request(
            src_url,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://blog.csdn.net/"},
        )
        data = urllib.request.urlopen(req, timeout=30).read()
        open(os.path.join(IMG_DIR, fn), "wb").write(data)
        rel = IMG_FOLDER + "/" + fn  # 关键：用干净的“文件夹名/文件名”相对路径，不要拼绝对路径
        seen[src_url] = rel
        im["src"] = rel
    except Exception as e:
        print("img fail", src_url, e)
        im.decompose()
    im.attrs.pop("width", None)
    im.attrs.pop("height", None)
    im["style"] = "max-width:100%;height:auto;display:block;margin:10px auto;"

for a in body.find_all("a"):
    a.attrs.pop("target", None)

clean = str(body)

CSS = """
*{box-sizing:border-box;}
body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;color:#222;line-height:1.85;font-size:16px;max-width:820px;margin:0 auto;padding:40px 28px;}
h1{font-size:27px;color:#1a1a1a;border-bottom:3px solid #c0392b;padding-bottom:12px;margin-bottom:6px;}
.meta{color:#888;font-size:13px;margin:8px 0 28px;border-bottom:1px solid #eee;padding-bottom:14px;}
.meta b{color:#555;}
h2{font-size:21px;margin:32px 0 12px;color:#c0392b;border-left:5px solid #c0392b;padding-left:10px;}
p{margin:12px 0;}
img{max-width:100%;height:auto;display:block;margin:14px auto;border:1px solid #eee;border-radius:4px;}
a{color:#2980b9;text-decoration:none;}
ul,ol{padding-left:24px;}
li{margin:6px 0;}
code{background:#f4f4f4;padding:2px 6px;border-radius:3px;font-family:Consolas,monospace;font-size:14px;}
blockquote{background:#f8f9fa;border-left:4px solid #ddd;margin:14px 0;padding:8px 16px;color:#555;}
.art-foot{margin-top:40px;color:#aaa;font-size:12px;border-top:1px solid #eee;padding-top:14px;}
"""

doc = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title><style>{CSS}</style></head><body>
<h1>{title}</h1>
<div class="meta">作者：<b>{author}</b> ｜ 发布时间：{date or '未知'} ｜ 来源：CSDN 博客（已整理去广告）</div>
{clean}
<div class="art-foot">本文整理自 CSDN 博客《{title}》，仅作离线阅读用途。</div>
</body></html>"""

html_path = os.path.join(WORK, out_base + ".html")
open(html_path, "w", encoding="utf-8").write(doc)
print("title:", title)
print("author:", author, "date:", date)
print("images:", len(seen))
print("html:", html_path)
print("images_dir:", os.path.join(WORK, IMG_FOLDER))
