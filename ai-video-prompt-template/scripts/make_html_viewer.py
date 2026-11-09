#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 ai-video-prompt-template 交付的 .md 中抽取「复制区」（第一个 fenced 代码块），
生成一份带「一键复制」按钮 + 自适应换行的 HTML 观看版。

用法:
    python make_html_viewer.py <input.md> [-o output.html] [--title 标题]

说明:
    - 复制区 = md 中第一个 ```...``` 代码块（交付规范里它就是独立的复制区）。
    - 生成的 HTML 用 <pre style="white-space:pre-wrap"> 自适应换行（不污染 md 纯净度），
      顶部「复制全部」按钮调用 navigator.clipboard 一键复制，失败回退 execCommand。
    - MD 本身保持纯净可复制，HTML 只是观看/复制便利版。
"""
import argparse
import html
import os
import re
import sys

FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def extract_copy_area(text: str, path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        # 纯可复制版 txt：整份文件就是复制区
        return text.strip("\n")
    m = FENCE_RE.search(text)
    if not m:
        raise SystemExit(
            "错误：未在 md 中找到任何 fenced 代码块（复制区应为第一个 ``` 块）。\n"
            "若是纯 txt 可复制版，请直接用 .txt 作为入参；若是旧版「核对版」md，请改用对应的 02_提示词_可复制版_*.txt。"
        )
    return m.group(1).strip("\n")


def build_html(copy_area: str, title: str) -> str:
    safe = html.escape(copy_area)
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
         margin: 24px; background: #ffffff; color: #1f2933; }}
  .bar {{ display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }}
  h1 {{ font-size: 15px; font-weight: 600; margin: 0; }}
  button {{ font-size: 13px; padding: 7px 16px; border: 1px solid #185FA5; background: #185FA5;
           color: #fff; border-radius: 8px; cursor: pointer; }}
  button:hover {{ background: #0C447C; }}
  #msg {{ font-size: 12px; color: #16a34a; }}
  pre {{ white-space: pre-wrap; word-break: break-word; background: #f7f8fa;
         border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px;
         font-size: 13px; line-height: 1.7; margin: 0; }}
</style>
</head>
<body>
  <div class="bar">
    <h1>{html.escape(title)}</h1>
    <button id="copyBtn" type="button">复制全部</button>
    <span id="msg"></span>
  </div>
  <pre id="content">{safe}</pre>
  <script>
    (function () {{
      var btn = document.getElementById('copyBtn');
      var content = document.getElementById('content');
      var msg = document.getElementById('msg');
      function flash(t) {{ msg.textContent = t; setTimeout(function () {{ msg.textContent = ''; }}, 1600); }}
      btn.addEventListener('click', function () {{
        var text = content.textContent;
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(text).then(function () {{ flash('已复制到剪贴板'); }}, fallback);
        }} else {{ fallback(); }}
        function fallback() {{
          var r = document.createRange(); r.selectNodeContents(content);
          var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
          try {{ document.execCommand('copy'); flash('已复制到剪贴板'); }}
          catch (e) {{ flash('复制失败，请手动选择'); }}
          s.removeAllRanges();
        }}
      }});
    }})();
  </script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="生成带一键复制按钮的复制区 HTML 观看版")
    ap.add_argument("input", help="源 .md 文件路径")
    ap.add_argument("-o", "--output", help="输出 HTML 路径（默认与输入同目录，名加 _viewer）")
    ap.add_argument("--title", help="页面标题（默认取文件名）")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        return 1

    with open(args.input, "r", encoding="utf-8") as f:
        md_text = f.read()

    try:
        copy_area = extract_copy_area(md_text, args.input)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1

    title = args.title or os.path.splitext(os.path.basename(args.input))[0]
    out = args.output or (os.path.splitext(args.input)[0] + "_viewer.html")

    with open(out, "w", encoding="utf-8") as f:
        f.write(build_html(copy_area, title))

    print(f"已生成：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
