#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 v1.6 的 .md 直接转成【单个自包含 .html】：
- 顶栏：标题 + 「复制全部」按钮（复制复制区，即第一个 fenced 块）
- 复制区：原样可读，按窗口自适应换行
- 核对区：轻量 markdown 渲染（##/### 标题、- 列表、段落、带图资产表），原样可读
- 核对区里的 ![资产名](相对路径) 参考图会被缩到最大宽 360px 后 base64 内联，
  使整个 HTML 自包含、不依赖外部图片文件。
目的：用户只要一个文件，既能逐行核错、又能一键复制，不必 md+html 分开。
用法：
  python make_full_html.py <输入.md> -o <输出.html> --title 标题
"""
import sys, re, html, argparse, os, base64, io

FENCE_RE = re.compile(r"```(?:[^\n]*)\n(.*?)```", re.S)
IMG_RE = re.compile(r"^!\[(.*?)\]\((.*?)\)\s*$")

def extract_copy_area(md: str) -> str:
    m = FENCE_RE.search(md)
    if not m:
        raise SystemExit("错误：未在 md 中找到任何 fenced 代码块（复制区应为第一个 ``` 块）。")
    return m.group(1).strip("\n")

def split_review(md: str) -> str:
    # 取第一个 fenced 块之后的所有内容作为核对区
    m = FENCE_RE.search(md)
    if not m:
        return ""
    return md[m.end():].strip("\n")

def light_md_to_html(text: str) -> str:
    # 轻量转换：标题 / 列表 / 图片 / 段落；其余按纯文本转义
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue
        # 图片（独立行）
        im = IMG_RE.match(line.strip())
        if im:
            alt, path = im.group(1), im.group(2).strip()
            out.append(f'<img class="asset" alt="{html.escape(alt, quote=True)}" src="{html.escape(path, quote=True)}">')
            i += 1
            continue
        # 标题
        h = re.match(r"^(#{1,4})\s+(.*)$", line)
        if h:
            lvl = len(h.group(1))
            out.append(f"<h{lvl}>{inline(h.group(2))}</h{lvl}>")
            i += 1
            continue
        # 列表
        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\s*[-*]\s+", "", lines[i])) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        # 段落（连续非空行）
        para = [line]
        i += 1
        while i < n and lines[i].strip() != "" and not re.match(r"^#{1,4}\s+", lines[i]) and not re.match(r"^\s*[-*]\s+", lines[i]) and not IMG_RE.match(lines[i].strip()):
            para.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(para)) + "</p>")
    return "\n".join(out)

def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s

def resize_b64(abspath: str, max_w: int = 360) -> str:
    """读图、等比缩到 max_w 以内、返回 base64 data URI；失败返回原路径。"""
    try:
        from PIL import Image
        with Image.open(abspath) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w > max_w:
                im = im.resize((max_w, max(1, int(h * max_w / w))), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            data = base64.b64encode(buf.getvalue()).decode("ascii")
        return "data:image/png;base64," + data
    except Exception:
        return None

def embed_images(review_html: str, base_dir: str) -> str:
    """把 <img class="asset" src="相对路径"> 改为 base64 内联（找不到或失败则保留相对路径）。"""
    def repl(m):
        tag, alt, src = m.group(0), m.group(1), m.group(2)
        if src.startswith("data:"):
            return tag
        ap = src
        if not os.path.isabs(ap):
            ap = os.path.normpath(os.path.join(base_dir, src))
        if os.path.isfile(ap):
            uri = resize_b64(ap)
            if uri:
                return f'<img class="asset" alt="{alt}" src="{uri}">'
        return tag
    return re.sub(r'<img class="asset" alt="([^"]*)" src="([^"]*)">', repl, review_html)

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif; color:#1f2328; background:#f5f6f8; }}
  .topbar {{ position: sticky; top:0; z-index:10; display:flex; align-items:center; gap:12px;
            padding:10px 16px; background:#fff; border-bottom:1px solid #e3e6ea; box-shadow:0 1px 4px rgba(0,0,0,.05); }}
  .topbar h1 {{ font-size:15px; margin:0; flex:1; color:#24292f; font-weight:600; }}
  .copybtn {{ border:none; background:#2f6feb; color:#fff; font-size:14px; padding:8px 16px;
             border-radius:8px; cursor:pointer; white-space:nowrap; }}
  .copybtn:hover {{ background:#2257c4; }}
  .copybtn.done {{ background:#1a9a52; }}
  .wrap {{ max-width: 920px; margin:16px auto; padding:0 16px 60px; }}
  .card {{ background:#fff; border:1px solid #e3e6ea; border-radius:12px; padding:16px; margin-bottom:18px; }}
  .card h2.label {{ font-size:13px; color:#57606a; margin:0 0 10px; letter-spacing:.04em; }}
  pre.area {{ white-space: pre-wrap; word-break: break-word; font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
             font-size:13px; line-height:1.7; background:#fafbfc; border:1px solid #eaecef; border-radius:8px;
             padding:14px; margin:0; overflow-x:auto; }}
  .review h2 {{ font-size:17px; margin:18px 0 8px; }}
  .review h3 {{ font-size:15px; margin:14px 0 6px; color:#24292f; }}
  .review h4 {{ font-size:14px; margin:12px 0 4px; }}
  .review p {{ margin:6px 0; line-height:1.7; font-size:14px; }}
  .review ul {{ margin:6px 0; padding-left:22px; }}
  .review li {{ margin:4px 0; line-height:1.7; font-size:14px; }}
  .review code {{ background:#f0f1f3; padding:1px 5px; border-radius:4px; font-size:13px; }}
  .review img.asset {{ display:block; max-width:300px; width:auto; height:auto; border:1px solid #e3e6ea;
                       border-radius:8px; margin:8px 0 4px; background:#fafbfc; }}
  .asset-cap {{ font-size:12px; color:#8a949e; margin:0 0 14px; }}
  .note {{ font-size:12px; color:#8a949e; margin-top:8px; }}
</style>
</head>
<body>
  <div class="topbar">
    <h1>{title}</h1>
    <button id="cp" class="copybtn" onclick="copyArea()">复制全部</button>
  </div>
  <div class="wrap">
    <div class="card">
      <h2 class="label">复制区（直接粘贴到即梦 / 可灵等生视频工具）</h2>
      <pre class="area" id="src">{copy_area}</pre>
      <p class="note">点右上角「复制全部」即可一键复制上面整段。</p>
    </div>
    <div class="card review">
      <h2 class="label">核对区（不进提示词，仅供逐行检查）</h2>
{review_html}
    </div>
  </div>
<script>
function copyArea() {{
  var t = document.getElementById('src').innerText;
  function ok() {{ var b=document.getElementById('cp'); b.innerText='已复制 ✓'; b.classList.add('done'); setTimeout(function(){{b.innerText='复制全部';b.classList.remove('done');}},1800); }}
  function fail() {{ var b=document.getElementById('cp'); b.innerText='复制失败，请手动选'; }}
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(t).then(ok, function(){{ legacyCopy(t, ok, fail); }});
  }} else {{ legacyCopy(t, ok, fail); }}
}}
function legacyCopy(t, ok, fail) {{
  try {{
    var ta = document.createElement('textarea'); ta.value=t; ta.style.position='fixed'; ta.style.top='-9999px';
    document.body.appendChild(ta); ta.select(); var r=document.execCommand('copy'); document.body.removeChild(ta);
    r?ok():fail();
  }} catch(e) {{ fail(); }}
}}
</script>
</body>
</html>
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--title", default="分镜提示词")
    args = ap.parse_args()

    with open(args.md, encoding="utf-8") as f:
        md = f.read()

    try:
        copy_area = extract_copy_area(md)
    except SystemExit as e:
        print(e, file=sys.stderr); return 1

    review = split_review(md)
    review_html = light_md_to_html(review)
    # 把核对区参考图 base64 内联（相对路径基于 md 所在目录）
    review_html = embed_images(review_html, os.path.dirname(os.path.abspath(args.md)))

    out = TEMPLATE.format(
        title=args.title,
        copy_area=html.escape(copy_area, quote=False),
        review_html=review_html,
    )
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)
    print("已生成：" + args.out)

if __name__ == "__main__":
    sys.exit(main())
