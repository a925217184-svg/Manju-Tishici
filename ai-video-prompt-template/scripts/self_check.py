#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用自检（全片四查）· 第一遍自动粗筛
配合 ai-video-prompt-template 技能使用，不是最终判定——语义结论由人/AI 收尾。

用法：
    python self_check.py <分镜md文件> [--quiet]

输出：
    ① 片级角色表 + 镜×角色矩阵（漏写站位/乱入角色预警）
    ② 俯视/背对机位下「不可见细节」关键词预警（查二）
    ③ 朝向—描述冲突预警（查三，镜头权重>提示词权重）
    ④ 运镜种类计数 + 一镜到底豁免判定（查四）
"""
import re
import sys
import os

AT_RE = re.compile(r'@([\u4e00-\u9fffA-Za-z0-9_]+)')
SHOT_RE = re.compile(r'^(?:\*\*)?镜头\s*\d+')  # 仅匹配行首的镜头标题，不匹配「运镜：同镜头1」这类
CAM_FIXED = re.compile(r'一镜到底|固定机位|不切镜|锁定跟随|不环绕|不甩镜')
# 俯视/背对机位下，画面里写了这些词 => 大概率不可见 => 预警
LOW_ANGLE_BAD = ['胸口', '胸前', '正脸', '面部', '表情', '纹身', '正面纹', '胸甲纹', '徽记', '五官']
BACK_BAD = ['胸前', '正面伤口', '胸甲', ' facial', '正脸', '面部', '正面纹']
HIGH_KEY = re.compile(r'俯视|俯角|斜俯|高位')
BACK_KEY = re.compile(r'背对|背影|后背|后脑')


def extract_shots(text):
    """返回 [(shot_title, yunjing_line, huamian_lines)]"""
    lines = text.splitlines()
    shots = []
    cur = None
    yun, hua = [], []
    in_area = True  # 默认解析全篇；若检测到 fenced 复制区则只取区内
    fence_on = False
    area_lines = []
    for ln in lines:
        if ln.strip().startswith('```'):
            fence_on = not fence_on
            if fence_on:
                area_lines = []
            else:
                # 复制区结束
                pass
            continue
        if fence_on:
            area_lines.append(ln)
    # 若存在复制区，优先只用复制区
    parse_src = '\n'.join(area_lines) if area_lines else text

    lines = parse_src.splitlines()
    cur_title = None
    yunjing, huamian = [], []
    for ln in lines:
        if SHOT_RE.match(ln):
            if cur_title is not None:
                shots.append((cur_title, '\n'.join(yunjing), '\n'.join(huamian)))
            cur_title = ln.strip()
            yunjing, huamian = [], []
            continue
        s = ln.strip()
        if s.startswith('运镜：') or s.startswith('运镜:'):
            yunjing.append(s)
        elif s.startswith('画面：') or s.startswith('画面:'):
            huamian.append(s)
    if cur_title is not None:
        shots.append((cur_title, '\n'.join(yunjing), '\n'.join(huamian)))
    return shots


def main():
    if len(sys.argv) < 2:
        print("用法: python self_check.py <分镜md>")
        sys.exit(1)
    path = sys.argv[1]
    if not os.path.exists(path):
        print("文件不存在:", path)
        sys.exit(1)
    text = open(path, encoding='utf-8').read()
    shots = extract_shots(text)

    # 片级角色表
    roster = {}
    for title, yun, hua in shots:
        for m in AT_RE.findall(yun + '\n' + hua):
            roster[m] = roster.get(m, 0) + 1

    print("=" * 60)
    print("① 片级角色表（@引用去重）")
    print("=" * 60)
    if not roster:
        print("  （未检测到 @角色，可能用了纯文字设计版，跳过①）")
    else:
        for k, v in sorted(roster.items(), key=lambda x: -x[1]):
            print(f"  @{k}  ×{v}")

    # 镜×角色矩阵 + 站位关键词
    print("\n" + "=" * 60)
    print("① 镜 × 角色矩阵（[站]=写了站位关键词  [缺]=疑似漏写）")
    print("=" * 60)
    POS_KW = re.compile(r'正中|中心|左前|右前|左缘|右缘|左侧|右侧|背景|画外|边缘|几何正|占画面|占高|前方|后方|身前|身后|居中|四角|顶端|底端')
    for title, yun, hua in shots:
        chars = AT_RE.findall(hua)
        if not chars:
            print(f"  {title[:30]:32}  （无 @角色）")
            continue
        tags = []
        for c in dict.fromkeys(chars):
            # 固定机位/「同镜头N」即站位沿用，不判缺站位
            inherited = bool(re.search(r'同镜头|固定机位|锁定跟随|不换高度|不环绕|不甩镜', yun))
            has_pos = inherited or bool(POS_KW.search(yun + '\n' + hua))
            tags.append(f"@{c}{'' if has_pos else '[缺站位]'}")
        print(f"  {title[:26]:28} " + "  ".join(tags))

    # 查二/查三 关键词预警
    print("\n" + "=" * 60)
    print("②/③ 机位—可见性 预警（镜头权重 > 提示词权重）")
    print("=" * 60)
    warned = False
    for title, yun, hua in shots:
        joint = yun + '\n' + hua
        if HIGH_KEY.search(joint):
            bad = [w for w in LOW_ANGLE_BAD if w in hua]
            if bad:
                warned = True
                print(f"  [查二·俯视] {title[:24]:26} 画面含不可见细节: {bad}")
        if BACK_KEY.search(joint):
            bad = [w for w in BACK_BAD if w in hua]
            if bad:
                warned = True
                print(f"  [查三·背对] {title[:24]:26} 画面含不可见细节: {bad}")
    if not warned:
        print("  未触发自动预警（语义冲突仍需人/AI 复核）")

    # 查四 运镜种类 + 豁免
    print("\n" + "=" * 60)
    print("④ 镜头丰富度")
    print("=" * 60)
    yun_lines = [y for _, y, _ in shots if y]
    kinds = set()
    for y in yun_lines:
        for kw in ['俯视', '仰视', '平视', '过肩', '特写', '近景', '中景', '全景', '远景', '跟随', '环绕', '固定', '推', '拉', '摇', '移', '航拍', '俯拍', '背拍', '侧拍', '正拍']:
            if kw in y:
                kinds.add(kw)
    fixed = any(CAM_FIXED.search(y) for y in yun_lines)
    print(f"  运镜关键词种类数: {len(kinds)}  （{sorted(kinds)}）")
    if fixed:
        print("  判定: 检测到「一镜到底/固定机位/锁定跟随」→ 查四 = N/A（豁免），反查是否误切镜")
    else:
        if len(kinds) <= 2:
            print("  判定: ⚠️ 运镜种类偏少，建议增加景别/机位交替（除非项目本就要求单调）")
        else:
            print("  判定: ✅ 运镜种类充足")

    print("\n[说明] 本报告为第一遍粗筛，②/③ 的语义冲突与①的乱入角色仍需人工/AI 最终判定。")


if __name__ == '__main__':
    main()
