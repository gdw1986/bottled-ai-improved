# bottled-ai-improved 优化日志

> **最后更新**: 2026-05-04 12:30  
> **已修改文件**: 5 个 (+173/-52 行)
> **AI 接手即读**：本文件包含项目全貌、已完成改动、待办计划，可直接继续工作。

---

## 一、项目概览

| 项 | 值 |
|---|---|
| 仓库 | `gdw1986/bottled-ai-chinese` (fork) |
| 本地路径 | `C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\bottled-ai-improved` |
| 介绍 | Slay the Spire AI Bot，通过 CommunicationMod 获得游戏状态，Python handler 做决策，Rust 做战斗演算 |
| 当前策略 | `requested_strike` — 铁甲战士 Perfected Strike 流派 |
| 核心引擎 | Rust (`rs/`) + Python handlers |
| 数据 | `ironclad_clean.json` — 35,691 局人类玩家 Ironclad 运行记录 |

## 二、项目结构

```
bottled-ai-improved/
├── rs/                          # Rust 核心引擎
│   ├── ai/requested_strike/     # ★ 当前活跃策略
│   │   ├── config.py            # 卡牌评价、删卡优先级、药水列表
│   │   ├── ironclad_comparator.py # 战斗决策比较器
│   │   ├── requested_strike.py  # 策略入口
│   │   └── handlers/            # 各阶段决策处理器
│   │       ├── neow_handler.py        # Neow 起始奖励
│   │       ├── battle_handler.py      # 战斗
│   │       ├── boss_relic_handler.py  # Boss 遗物选择
│   │       ├── shop_purchase_handler.py # 商店购买
│   │       ├── event_handler.py       # 事件选择
│   │       ├── upgrade_handler.py     # 篝火升级
│   │       └── potions_handler.py     # 药水使用
│   ├── calculator/              # 战斗演算 (Monte Carlo tree search)
│   ├── common/                  # 共用 handler 基类
│   ├── game/                    # 游戏实体定义
│   └── machine/                 # 状态机
├── tests/                       # Python 测试
└── logs/                        # 运行日志
```

### 决策流程

```
Neow → [Map/Path] → Battle → Reward(卡牌选择) → Shop → Event → Campfire(升级/休息) → Boss → BossRelic → ...
```

每个阶段对应一个 handler，bot 在每个游戏屏幕状态下调用对应 handler 的 `can_handle()` → `handle()`。

## 三、参考数据 (ironclad_clean.json)

| 指标 | 值 |
|---|---|
| 总 run 数 | 35,691 |
| 总胜场 | 3,853 (10.8%) |
| 进阶模式 runs | 23,494 (胜率 10.1%) |
| A15+ runs | ~6,200 |
| A15+ 胜场 | 335 (用作高难度参考基准) |
| A20 胜率 | 1.5% |

### 数据结构 (每条记录)

每条记录是一个 `{"event": {...}}` 的 JSON 对象，event 内包含标准 Slay the Spire run history 字段：
- `card_choices` — 每层卡牌选择 (picked/not_picked)
- `boss_relics` — Boss 遗物选择
- `relics_obtained` — 获得的遗物
- `event_choices` — 事件选择
- `items_purchased` / `items_purged` — 商店操作
- `master_deck` — 最终卡组
- `campfire_choices` — 篝火选择 (SMITH/REST)
- `damage_taken` — 每场战斗的伤害
- `path_taken` / `path_per_floor` — 路线选择
- `neow_bonus` / `neow_cost` — Neow 奖励
- `victory`, `ascension_level`, `killed_by`

### 分析工具

```bash
python3 -c "
import json
data = json.load(open(r'C:\Users\david\Downloads\ironclad_clean.json'))
a15_wins = [r['event'] for r in data if r['event'].get('ascension_level',0)>=15 and r['event'].get('victory')]
# ... custom analysis ...
"
```

## 四、优化历史

### 早期 (已有 commit)

| Commit | 内容 |
|---|---|
| `4e2772a` | 数据驱动的 CARD_REMOVAL_PRIORITY_LIST |
| `a4123da` | 来自 35k 数据的 map/battle/card 优化 |
| `fae54c1` | Boss 遗物 + 删卡策略中文适配 |
| `61860a9` | deck 匹配区分升级/非升级 |
| `d48af16` | 商店中文环境ом不操作修复 |
| `de91dd1` | ShopPurchaseHandler 中文兼容重写 |
| `ca109d9` | 事件选择用 event_id 而非 event_name |

### P0 (2026-05-04) — Boss 遗物 + 商店

**修改文件**：
- `rs/ai/requested_strike/handlers/boss_relic_handler.py`
- `rs/ai/requested_strike/handlers/shop_purchase_handler.py`

**Boss 遗物优先级 (新排序)**：
```
1. snecko eye          (25.4% wr)
2. pandora's box       (19.3% wr)  ← 新增
3. philosopher's stone (17.9% wr)
4. coffee dripper      (17.6% wr)
5. busted crown        (16.7% wr)
6. mark of pain        (16.3% wr)
7. runic dome          (15.7% wr)
8. velvet choker       (15.4% wr)
9. fusion hammer       (14.9% wr)
10. sozu               (14.3% wr)  ← 之前是 #1
11. cursed key         (13.3% wr)
12. empty cage         (13.1% wr)
13. slaver's collar    (12.7% wr)
14. calling bell       (12.6% wr)
15. runic pyramid      (12.4% wr)
16. black star         (12.1% wr)
17. ectoplasm          (11.8% wr)  ← 之前是 #4
18. tiny house         (10.8% wr)  ← 新增
19. sacred bark        (10.0% wr)
20. astrolabe          ( 9.7% wr)  ← 新增
21. runic cube         ( 8.6% wr)
22. black blood        ( 8.3% wr)
```

Bot 原有 19 个遗物，新增 3 个 (pandora's box, tiny house, astrolabe)，全部按 A15+ win rate 排序。

**商店购买优先级 (新顺序)**：
```
1. Membership Card     ← 之前是 #3，现在提到最前面
2. 诅咒删卡
3. Perfected Strike    ← 之前是 #2 (Membership Card 之前)
4. 常规删卡
5. 遗物 (43 个, 原来 24 个)
6. 卡牌 (19 张, 原来 3 张)
7. 药水
```

### P0.5 (2026-05-04) — 缺失卡牌/遗物补全

基于 A15+ 335 胜场的完整 gap 分析，补充三处空白：

**修改文件**：
- `rs/ai/requested_strike/config.py`
- `rs/ai/requested_strike/handlers/upgrade_handler.py`
- `rs/ai/requested_strike/handlers/shop_purchase_handler.py`

#### DESIRED_CARDS_FOR_DECK 新增 3 张核心卡

| 卡牌 | A15+ 胜场数 | 升级胜率 | 上限 |
|---|---|---|---|
| Armaments | 115 | 20%→32% | 2 |
| Whirlwind | 80 | 12%→30% | 2 |
| Flex | 127 | 13%→28% | 2 |

Armaments 是 Ironclad 最高价值 utility 卡（升级后批量升级手牌），之前完全被忽略。

#### 升级优先级调整

升级列表新增 armaments 排第 2 位（仅次于 apotheosis），HIGH_PRIORITY_UPGRADES 同步加入。

#### 商店遗物列表 +12

Omamori (63), MawBank (59), Ancient Tea Set (55), Potion Belt (55), Question Card (55),
Whetstone (52), Red Mask (51), Juzu Bracelet (50), Nunchaku (50), Art of War (49),
Dead Branch (46), Chemical X (18 buys)

#### 商店卡牌列表 +6

Armaments, Whirlwind, Flex, True Grit, Evolve, Pommel Strike

---

## 五、待办计划

### P1 — Neow Bonus 优先级 + 事件阈值

#### Neow (A15+ 胜场数据)

当前 bot 优先级：
```
upgrade card > common relic > 100 gold > choose card > potions > colorless > max hp > rare card > ...
```

人类 A15+ 胜场 Neow 选择频次：
```
Three Enemy Kill (959) >> Random Common Relic (369) > Boss Relic Swap (337) > Max HP+8 (322) > Random Rare (173) > 100 Gold (149) > ...
```

**改动点**：
- 100 Gold 从 #3 降到 #5-6
- Boss Relic Swap 提到 #3（人类数据 337 次胜场选用）
- Three Enemy Kill 保持 #1（已正确）
- Rare Relic (有代价) 的排位需要评估

#### 事件阈值

当前 requested_strike EventHandler 仅在以下事件做自定义：
- Golden Idol (HP≥50% 选受伤, 否则选 max hp loss)
- World of Goop (HP≥70% 选金币)
- Wing Statue (HP≥60% 选删牌)
- Shining Light (HP≥50% 选升级)

**改动点**：
- Cursed Tome → Obtained Book: bot 当前通过 CommonEventHandler 处理，应确保高 HP 时必拿 Necronomicon
- Mind Bloom: 应为 Fight（人类胜场 #1 事件选择 1134 次），但这是 Act 3 事件，CommonEventHandler 是否已支持需验证
- Falling → Remove Attack: 人类偏好删攻击牌 > 删技能牌，需检查当前行为
- Scrap Ooze → Success: 人类胜场 822 次选这个 vs 拿遗物，需评估
- Ghosts → Ignored: 人类胜场 496 次无视幽灵（拿 3 Apparition 减半 max HP），检查 bot 当前的 Ghosts 行为

### P2 — Upgrade 优先级 + 卡牌评价微调

#### 升级优先级

人类胜场 Top 5 升级目标：
```
1. Armaments (948)   — bot 排到第2页，严重低估
2. Bash (895)
3. Limit Break (823)
4. Inflame (724)
5. Demon Form (717)
```

**改动点**：Armaments 提到 upgrade priority 前 3

#### 卡牌评价微调

DESIRED_CARDS_FOR_DECK (config.py) 已经是数据驱动的，但一些细节：

- **Power Through + Second Wind 组合**：人类 A15+ 大量使用，bot 各给上限但未形成组合逻辑
- **Warcry**：胜率差异 +0.178，应更积极在 Act 1 选
- **Flex**：人类选得很多但 wr 差异小，主要是过渡牌 — 上限可能偏高

### P3 — 路线/路径选择

未分析。35k 数据里有 `path_taken` 和 `path_per_floor`，可以分析：
- 精英狩猎 vs 安全路线 vs 篝火路线的胜率对比
- Act 1 最优路径策略

### P4 — 战斗演算 (ironclad_comparator)

- 当前 comparator 沿用了 peaceful_pummeling 的很多 Defect/Watcher 逻辑
- 可以针对 Ironclad 进一步精简
- 卡牌评分可以按 A15+ win rate 重新校准

---

## 六、如何继续工作

### 查看项目状态
```bash
git -C "C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\bottled-ai-improved" log --oneline -5
git -C "C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\bottled-ai-improved" status --short
git -C "C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\bottled-ai-improved" diff
```

### 运行分析
```bash
python3 -c "
import json
data = json.load(open(r'C:\Users\david\Downloads\ironclad_clean.json'))
# ... 
"
```

### 编辑代码
Handler 文件在：
```
C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\bottled-ai-improved\rs\ai\requested_strike\handlers\
```

### 关键文件一览

| 文件 | 作用 |
|---|---|
| `config.py` | DESIRED_CARDS_FOR_DECK, CARD_REMOVAL_PRIORITY_LIST, 药水列表 |
| `ironclad_comparator.py` | 战斗比较链：生存 > 威胁 > 敌人管理 > 状态 > 伤害 > 资源 |
| `handlers/neow_handler.py` | Neow 初始奖励选择 (可用选项列表 + 优先级) |
| `handlers/boss_relic_handler.py` | Boss 遗物 (优先级列表 + Act/能量遗物条件剔除) |
| `handlers/shop_purchase_handler.py` | 商店 (购买链: MembershipCard → 删卡 → 遗物 → 卡牌 → 药水) |
| `handlers/event_handler.py` | 事件 (自定义 HP 阈值的 4 个事件，其余委托给 CommonEventHandler) |
| `handlers/upgrade_handler.py` | 升级优先级列表 (含 Snecko Eye 特殊处理) |
| `handlers/battle_handler.py` | 战斗入口 (委托给 CommonBattleHandler + IroncladComparator) |
| `handlers/potions_handler.py` | 战斗中/战斗外药水使用 |
