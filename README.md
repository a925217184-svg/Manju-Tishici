# AI 视频 / 生图提示词技能集（WorkBuddy Skills）

一套面向 **AI 视频生成** 与 **AI 生图** 的 WorkBuddy 技能（Skill），用于把脚本 / 视觉想法稳定地转化为可执行的生成提示词。本仓库把 4 个相互补充的技能收在一个独立仓库里，方便单独安装、二次开发与版本管理。

> 适用客户端：WorkBuddy（或任何兼容 `SKILL.md` 技能协议的 Agent）。

---

## 一、包含的 4 个技能

| 技能 | 定位 | 管「单张」还是「整片」 | 主要目标工具 |
|---|---|---|---|
| [`ai-video-prompt-template`](./ai-video-prompt-template) | 通用 AI 视频分镜骨架（纯结构，不预设风格），含**自动打斗检测 + 打斗参考手册** | 整片（多镜视频） | 即梦 / 可灵 / Runway / Sora / Veo 全兼容 |
| [`manju-composition`](./manju-composition) | 把任意视觉想法设计成「一个电影镜头」的生图提示词 | 单张（关键帧 / 概念图） | 即梦 / Midjourney 等文生图 |
| [`manju-storyboard`](./manju-storyboard) | 把完整剧本转成可拍摄分镜脚本 + 逐镜 Seedance 视频提示词 | 整片（场次 → 逐镜） | 主要 Seedance |
| [`manju-color-palette`](./manju-color-palette) | 从参考图提炼扁平化色卡参考图提示词 | 单张（色彩规范页） | 文生图 |

**核心区别**：`composition` / `color-palette` 是「单张图」上游工具（关键帧 + 色彩规范）；`storyboard` / `ai-video-prompt-template` 是「视频整片」工具。`storyboard` 偏 Seedance 场次管理，`ai-video-prompt-template` 偏通用骨架 + 最强防崩坏 / 打斗约束。

---

## 二、仓库结构

```
ai-video-prompt-skills/
├── README.md                         ← 本文件（总览 + 安装 + 流水线）
├── ai-video-prompt-template/         ← 技能 1
│   ├── SKILL.md                      角色定义 / 工作流 / 全部硬规矩（v1.6 定稿）
│   ├── README.md                     用法文档 / 输出格式 / 配套文件清单
│   ├── references/
│   │   ├── template.md               三层骨架模板 + 运镜类型库（镜头参考）
│   │   ├── combat-handbook.md        【动作参考库】打斗提示词参考手册（45KB）
│   │   ├── 表情参考库.md             【表情参考库】角色情绪/神态/微表情写法词表
│   │   ├── 镜头参考库.md             【镜头参考库】景别/画幅/运镜/机位全词表 + 实测机位参数
│   │   └── 巨物灾难模版.md           【巨物原理与词库】尺寸锚/运动信条/受力动词/解剖锁/genre 负词
│   └── scripts/
│       ├── detect_combat.py          自动判定是否进打斗模式（命令行）
│       └── sync_combat_handbook.py   从真源同步刷新 combat-handbook.md
├── manju-composition/                ← 技能 2
│   ├── SKILL.md / README.md
│   └── references/构图大师.json      电影构图规则库（场景/画幅/镜头/光影/材质/色彩）
├── manju-storyboard/                 ← 技能 3
│   ├── SKILL.md / README.md
│   └── references/分镜大师.json      分镜导演规则库（Story Bible/景别/运镜/Seedance 结构）
└── manju-color-palette/              ← 技能 4
    ├── SKILL.md / README.md
    └── references/色卡参考图生成器.md 色卡页生成规范
```

---

## 三、文件清单（确保「相关联的东西」一个不漏）

| 文件 | 体积 | 角色 | 属于哪类「参考库」 |
|---|---|---|---|
| `ai-video-prompt-template/references/combat-handbook.md` | 45KB | 打斗 / 动作反馈 / 环境破坏规范 | **动作参考库（核心）** |
| `ai-video-prompt-template/references/template.md` | 10KB | 三层骨架模板 + 运镜类型库 + 节奏公式 | 镜头 / 运镜参考（内嵌） |
| `ai-video-prompt-template/scripts/detect_combat.py` | 7KB | 命令行打斗检测（命中词 / 缺件自检） | 动作参考库配套工具 |
| `ai-video-prompt-template/scripts/sync_combat_handbook.py` | 12KB | 从真源重新生成 combat-handbook.md | 动作参考库配套工具 |
| `manju-composition/references/构图大师.json` | 6KB | 电影构图全规则（场景/画幅/镜头/光影/材质/色彩/禁止项） | 构图 / 镜头参考 |
| `manju-storyboard/references/分镜大师.json` | 6KB | 分镜导演全规则（景别/运镜/Seedance 结构/参考图优先级） | 分镜 / 镜头参考 |
| `manju-color-palette/references/色卡参考图生成器.md` | 3KB | 色卡页生成规范（结构/视觉要求/禁止项） | 色彩参考 |
| `ai-video-prompt-template/references/表情参考库.md` | 新增 | 七情词表 / 复杂矛盾情绪拆分 / 常态表情基线 / 微表情肌肉写法 / 与台词语序融合 / 多角色表情差 / 防崩坏 NEG | **表情参考库（新增）** |
| `ai-video-prompt-template/references/镜头参考库.md` | 新增 | 景别7种 / 画幅 / 运镜全词表 / 镜头类型与视场角 / 构图 / 机位角度 / 实测机位参数(10m·35°·45°等) / 运镜写作铁律 | **镜头参考库（新增，原内嵌词库统一抽取）** |
| `ai-video-prompt-template/references/巨物灾难模版.md` | 新增 | 体积感＝尺寸对比锚 / 重量感＝运动信条＋受力结果动词＋动量连续 / 解剖锁 / genre 专属负词 / 原脚本字段→v1.5 板块对照表 | **巨物原理与词库（新增，v1.6 定稿已焊死进主结构）** |

> 仓库当前共 **19 个文件**（4 个 SKILL.md + 8 个 references + 2 个 scripts + 4 个用法 README + 1 个顶层 README）。

### 关于「动作参考库 / 镜头参考库 / 表情参考库 / 巨物词库」的透明说明

你提到「不要遗漏动作参考库、镜头参考库、表情参考库」。经逐文件核对，本技能集的真实情况如下，便于你心里有数：

- **动作参考库 ✅ 已包含**：就是 `ai-video-prompt-template/references/combat-handbook.md`（打斗提示词参考手册）。它规定了打击感五件套、环境破坏四段式、需求词→模块映射等，是 `ai-video-prompt-template` 在检测到打斗场面时自动加载的真源。配套还有 `detect_combat.py` 与 `sync_combat_handbook.py` 两个脚本。
  - ⚠️ 该手册还有一个**外部真源**：`F:\AI视频制作\outputs\打斗提示词参考手册_v1.md`。仓库内 `combat-handbook.md` 是它的自动生成副本。若要修改打斗规范，**改真源后用 `sync_combat_handbook.py` 重新生成**，不要手改仓库里的副本。
- **镜头 / 运镜参考库 ✅ 已包含（现已抽成独立文件）**：原先运镜类型库、常用机位词库、叙事节奏公式内嵌在 `template.md` 与 SKILL.md，`manju-storyboard` 的景别/运镜/构图词库在 `分镜大师.json`。现已**统一抽取并扩充**为独立的 [`镜头参考库.md`](./ai-video-prompt-template/references/镜头参考库.md)，并补入用户实测的真实机位参数（第三人称射击 10m/35°/45°、2.5D 斜俯视、割草 60° 俯视、视场角补救顺序等）与运镜写作铁律（四要素 vs 两要素、落幅、来袭方向锁、客观机位）。
- **表情参考库 ✅ 已包含（本次新增）**：原 4 个技能没有独立的表情词表，现新建 [`表情参考库.md`](./ai-video-prompt-template/references/表情参考库.md)，提供基础七情可粘贴短语、复杂矛盾情绪拆分写法、常态表情基线（写进文字锁表）、微表情肌肉写法、与台词语序融合规则、多角色表情差、防崩坏 NEG 清单、表情强度分级。
- **巨物原理与词库 ✅ 已包含（后续追加）**：[`巨物灾难模版.md`](./ai-video-prompt-template/references/巨物灾难模版.md) 提炼自用户实测极好的「深海章鱼毁城」提示词（体积感 / 重量感 / 氛围都对）。**v1.5 起（v1.6 定稿沿用）它的机制已全部焊死进主结构**——【资产锁】角色设计里的 `动态表现：` 承载尺寸锚／运动信条／解剖锁、【分镜】逐镜光线/特效/音效必写、【负面提示词】题材组固定追加；本文件命中巨物题材时用来查词表。

---

## 四、安装到 WorkBuddy

每个子目录就是一个独立技能，直接整目录复制到 WorkBuddy 的技能目录即可：

```bash
# Windows（Git Bash）
cp -r ai-video-prompt-template  "$USERPROFILE/.workbuddy/skills/"
cp -r manju-composition         "$USERPROFILE/.workbuddy/skills/"
cp -r manju-storyboard          "$USERPROFILE/.workbuddy/skills/"
cp -r manju-color-palette       "$USERPROFILE/.workbuddy/skills/"
```

- 只装你需要的：例如只做视频就装 `ai-video-prompt-template` + `manju-storyboard`。
- 技能之间的依赖：`ai-video-prompt-template` 依赖其自带的 `references/` 与 `scripts/`，请**整目录复制**，不要只拿 `SKILL.md`。
- `SKILL.md` 含 WorkBuddy 读取用的 frontmatter（`name` / `description` / `agent_created` 等），请勿删除。

---

## 五、如何串成一条流水线（推荐用法）

对「漫剧 / 短剧 / 买量片」这种完整项目，四个技能互补，典型顺序：

1. **`manju-color-palette`** → 先锁全片色彩系统（一张色卡规范页，所有人 / 场景生图都对齐这套 HEX）。
2. **`manju-composition`** → 把关键场景 / 角色设计成电影感关键帧（概念图、定妆照、场景气氛图）。
3. **`ai-video-prompt-template`** 或 **`manju-storyboard`** → 把剧本落成视频分镜提示词：
   - 用多工具（即梦故事模式 / 可灵 / Runway / Sora）或含打斗动作 → 选 `ai-video-prompt-template`（它那套台词融入 / 惯用手锁 / 防玩具感 / 编号重映射是你长期踩坑沉淀的，最懂这类项目）。
   - 目标纯 Seedance、且要按场次管理剧本数据库 + 逐镜 Seedance Prompt → 选 `manju-storyboard`。
4. 若含打斗：`ai-video-prompt-template` 会自动联动 `combat-handbook.md` 强化打击感。

---

## 六、License

本仓库用于个人 / 团队内部 WorkBuddy 技能分发。如需对外开源，请自行添加 LICENSE 文件。
