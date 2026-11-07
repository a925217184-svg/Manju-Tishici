# -*- coding: utf-8 -*-
"""
打斗场景自动检测器（配合 ai-video-prompt-template 技能使用）

做的事：
  1. 扫一份分镜脚本 / 提示词 / 剧本文本，判定是否含打斗画面（三类触发词）
  2. 逐镜自检：打击感五件套、触点标记词、开局站位、一镜一事件
  3. 输出该加载打斗手册的哪些章节（含 §5.1 需求词对应行）

用法：
  python outputs/_tools/detect_combat.py <文件>            # 人读报告
  python outputs/_tools/detect_combat.py <文件> --json     # 机读

只做检测与定位，不改文件。
"""
import io
import json
import os
import re
import sys

# ---- 触发词 ----
SCENE_WORDS = ["打斗", "战斗", "对决", "交手", "搏杀", "肉搏", "格斗", "厮杀", "追杀", "混战",
               "群战", "BOSS战", "boss战", "妖兽战", "比武", "决斗", "兵器相撞", "挥剑", "斩击",
               "拳脚", "连招", "受击", "终极招式", "反击", "突袭", "攻防", "击杀", "格挡", "招架"]
DEMAND_WORDS = ["炫酷打斗", "不够炸", "场面不够大", "强化打击感", "打的不疼", "打得不够疼", "没手感",
                "丰富特效", "特效单调", "动作不流畅", "卡断", "一块块", "力量感不足", "不出力",
                "一拳就赢", "太轻松", "节奏拖沓", "环境太干净", "看不清谁打了谁", "第一人称", "悬念收尾"]
IMAGE_WORDS = ["撞飞", "击退", "贯穿", "塌陷", "冲击波", "血雾", "碎裂", "倒飞", "砸穿", "崩塌",
               "格挡", "火花", "残影", "命中", "重击", "连击", "闪避", "突进"]

# ---- 打击感五件套（手册 §2.3）----
FIVE = [
    ("接触闪", ["闪白", "爆闪", "黑白闪", "高光爆", "冲击气浪", "冲击波", "闪光"]),
    ("形变", ["凹陷", "形变", "压扁", "扭曲", "撕裂", "陷进", "弯折", "挤压"]),
    ("位移follow-through", ["倒飞", "撞飞", "击退", "飞出", "掀飞", "弹开", "踉跄", "倒地", "后退半步", "滑退"]),
    ("反作用力", ["蹬裂", "反作用", "震退", "被震", "蹬地", "地表裂", "脚下", "卸力"]),
    ("二次破坏", ["贯穿", "砸穿", "塌陷", "崩塌", "碎裂", "崩飞", "倒塌", "炸开", "破碎", "掀翻"]),
]
TOUCH_MARKS = ["黑白闪", "顿帧", "音爆", "震屏", "震镜", "高对比闪"]
STANCE_WORDS = ["站在", "立在", "蹲在", "躺在", "倒在", "悬于", "趴在", "位于", "仍立", "仍倒",
                "中央", "一侧", "上方", "下方", "对峙", "间距"]

SHOT_RE = re.compile(r"^\s*(?:#{0,6}\s*)?(?:【镜\s*)?(?:镜头|镜|镜\s*|Shot\s*)(\d+)", re.I)


def split_shots(lines):
    """返回 [(镜号, 起始行号, 块文本)]"""
    shots = []
    cur = None
    for i, ln in enumerate(lines, 1):
        m = SHOT_RE.match(ln)
        if m:
            if cur:
                shots.append(cur)
            cur = [int(m.group(1)), i, [ln]]
        elif cur is not None:
            cur[2].append(ln)
    if cur:
        shots.append(cur)
    return [(n, s, "\n".join(b)) for n, s, b in shots]


def scan(path):
    text = io.open(path, encoding="utf-8", errors="ignore").read()
    lines = text.split("\n")

    hits = {"场面词": [], "需求词": [], "画面判据": []}
    for i, ln in enumerate(lines, 1):
        for w in SCENE_WORDS:
            if w in ln:
                hits["场面词"].append((w, i, ln.strip()[:60]))
        for w in DEMAND_WORDS:
            if w in ln:
                hits["需求词"].append((w, i, ln.strip()[:60]))
        for w in IMAGE_WORDS:
            if w in ln:
                hits["画面判据"].append((w, i, ln.strip()[:60]))

    combat_mode = any(hits[k] for k in hits)

    shots = []
    if combat_mode:
        for num, start, block in split_shots(lines):
            miss_five = [name for name, kws in FIVE if not any(k in block for k in kws)]
            touch = [t for t in TOUCH_MARKS if t in block]
            head = block[:80]
            stance = any(w in head for w in STANCE_WORDS)
            # 一镜两事件粗判：同一块里同时出现「掷/抛出/挥出」与「命中/砸中/击中」
            launch = any(k in block for k in ["掷出", "抛出", "挥出", "射出", "甩出", "投出"])
            land = any(k in block for k in ["命中", "砸中", "击中", "打中", "贯穿"])
            shots.append({
                "shot": num,
                "line": start,
                "miss_five": miss_five,
                "touch_marks": touch,
                "stance": stance,
                "two_events": launch and land,
            })

    sections = []
    if combat_mode:
        sections = ["§1.3 七字段备料+落位表", "§2.3 打击感五件套", "§2.4 环境破坏四段式",
                    "§3 分类词库", "§5.1 需求词→模块映射", "§5.2 症状→根因→修正",
                    "§5.3 取舍优先级", "§5.4 禁用清单"]
    return {
        "file": path,
        "combat_mode": combat_mode,
        "hits": {k: v for k, v in hits.items()},
        "hit_counts": {k: len(v) for k, v in hits.items()},
        "shots": shots,
        "load_sections": sections,
        "handbook": r"C:\Users\Administrator\.workbuddy\skills\ai-video-prompt-template\references\combat-handbook.md",
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    if not os.path.exists(path):
        print("[ERR] 文件不存在：%s" % path)
        sys.exit(1)
    r = scan(path)
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    print("文件：%s" % r["file"])
    print("判定：%s" % ("✅ 进入打斗模式 —— 必须加载打斗手册" if r["combat_mode"] else "⛔ 未命中打斗触发词，无需加载手册"))
    if not r["combat_mode"]:
        return

    print("\n触发命中：")
    for k, v in r["hits"].items():
        if not v:
            continue
        words = sorted(set(w for w, _, _ in v))
        print("  %s（%d 处）：%s" % (k, len(v), "、".join(words[:18])))

    print("\n逐镜自检（打击感五件套 / 触点标记 / 开局站位 / 一镜一事件）：")
    if not r["shots"]:
        print("  （未识别到「镜头 N」结构，跳过逐镜自检）")
    for s in r["shots"]:
        flags = []
        if s["miss_five"]:
            flags.append("缺五件套：%s" % "、".join(s["miss_five"]))
        if not s["touch_marks"]:
            flags.append("缺触点标记词（黑白闪/顿帧/音爆/震屏）")
        if not s["stance"]:
            flags.append("开头未写开局站位")
        if s["two_events"]:
            flags.append("疑似一镜两事件（掷出+命中同镜）")
        print("  镜%-3s (行%-4s) %s" % (s["shot"], s["line"], "｜".join(flags) if flags else "OK"))

    print("\n应加载的手册章节：")
    for s in r["load_sections"]:
        print("  - %s" % s)
    print("\n手册路径：%s" % r["handbook"])


if __name__ == "__main__":
    main()
