# CSDN 转 PDF 关键坑点（gotchas）

## 1. CSDN 安全验证（验证码）
直接无代理请求 CSDN 文章会被拦截到「请进行安全验证(Security Verification)」页面，
拿不到正文。绕过方法：通过环境的 HTTP 代理访问。
- 本机通常已设置 `HTTP_PROXY` / `HTTPS_PROXY`（如 `http://127.0.0.1:59759`）。
- `curl` 与 `urllib` 都会自动读取这些环境变量；用浏览器 UA 即可正常拿到 200 + 完整 HTML。
- 校验是否成功：`grep -c "安全验证" xxx.html` 应为 0，且页面里要能找到 `id="content_views"`。

## 2. 真实图片域名 vs 广告占位
CSDN 正文配图真实地址在 `i-blog.csdnimg.cn`（或 `img-blog.csdnimg.cn`）。
`img` 标签的 `data-src` 往往是 `kunyu.csdn.net/...` 的广告占位图，**必须过滤**，
否则会下载到无意义的广告图或失败。筛选规则：只保留含 `i-blog.csdnimg.cn` / `img-blog.csdnimg.cn` 的 src。

## 3. 图片相对路径的 Windows 反斜杠坑（最容易导致“PDF 没图”）
- 正文容器：`#content_views`。
- 错误写法：`os.path.join(WORK, "images_x")` 在 Windows 会得到 `D:/a/b\images_x`，
  再 `.split("/")[-1]` 会截断成 `b\images_x`，拼到 `src` 后变成
  `b\images_x/img_01.png` —— 路径错误，Chrome 加载不到图，PDF 里就没图。
- 正确写法：直接用「文件夹名/文件名」的纯相对路径，例如 `"images_x/img_01.png"`，
  不要从绝对路径里 split 出来。HTML 与 images 目录放在同一目录即可。
- 验证：生成 HTML 后 `grep 'src=' xxx.html` 应看到 `images_x/img_01.png` 这类干净相对路径。

## 4. 作者提取不稳定
CSDN 页面里 class 含 `author`/`nick-name` 的元素常常命中标语（如「成就一亿技术人!」），
不可靠。最稳的是从主页链接 `https://blog.csdn.net/<用户名>` 正则提取用户名作为作者。

## 5. 依赖与渲染
- 解析用 BeautifulSoup + lxml：`pip install beautifulsoup4 lxml`（走代理源）。
- 最终 PDF 用本机 Chrome 无头打印：`chrome --headless=new --no-sandbox
  --no-pdf-header-footer --print-to-pdf=out.pdf file:///.../xxx.html`。
- Chrome 常见路径：`/c/Program Files/Google/Chrome/Application/chrome.exe`、
  `/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`。
- 校验 PDF 是否含图：`grep -a -c "/Subtype */Image" out.pdf` 应等于图片数量；
  或看文件体积（带图通常 >1MB，缺图只有一两百 KB）。

## 6. 图片下载也要走代理
下载 `i-blog.csdnimg.cn` 的图同样需要代理（环境变量已就绪），并带上
`Referer: https://blog.csdn.net/` 与浏览器 UA，否则可能 403。
