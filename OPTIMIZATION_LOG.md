# bottled-ai-improved 优化日志

> **最后更新**: 2026-05-17
> **状态**: 已归档。`codex/baseline-recovery` 已撤回 RequestedStrike 的数据驱动/实验性策略模块，当前活跃策略恢复到 `release-03` 基线，并只保留中文界面、choice 索引、确认流程等机械兼容修复。
> **AI 接手即读**：下方 P0-P5 章节是历史实验记录，不代表当前运行架构。

---

## 一、项目概览

| 项 | 值 |
|---|---|
| 仓库 | `gdw1986/bottled-ai-chinese` (fork) |
| 本地路径 | `C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\bottled-ai-improved` |
| 介绍 | Slay the Spire AI Bot，通过 CommunicationMod 获得游戏状态，Python handler 做决策，Rust 做战斗演算 |
| 当前策略 | `requested_strike` — 铁甲战士 Perfected Strike 流派 |
| 核心引擎 | Python（Rust 命名风格模块） |
| 数据 | `ironclad_clean.json` — 35,691 局人类玩家 Ironclad 运行记录；当前 RequestedStrike 基线不再读取该数据 |

## 二、项目结构

```
bottled-ai-improved/
├── rs/                          # Rust 核心引擎
│   ├── ai/requested_strike/     # ★ 当前活跃策略
│   │   ├── config.py            # release-03 卡牌/删卡/药水基线列表
│   │   ├── requested_strike.py  # 策略入口
│   │   └── handlers/            # 各阶段决策处理器
│   │       ├── neow_handler.py        # Neow 起始奖励
│   │       ├── boss_relic_handler.py  # Boss 遗物选择
│   │       ├── shop_purchase_handler.py # 商店购买
│   │       ├── event_handler.py       # 事件选择
│   │       ├── upgrade_handler.py     # 篝火升级
│   │       └── potions_handler.py     # 药水使用
│   ├── calculator/              # 战斗演算 (Monte Carlo tree search)
│   ├── common/                  # 共用 handler；RequestedStrike 当前使用通用战斗/选牌/路线/篝火/删牌
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

### P0.8 (2026-05-09) — Boss 宝箱房死循环修复
**问题**: AI 在 Boss 宝箱房过渡状态（`screen_type=MAP, room_type=TreasureRoomBoss, next_nodes=[]`）匹配到 `DefaultWaitHandler`，发出 `wait 30` 后游戏状态不变，形成死循环。

**根因**: `CommonChestHandler.can_handle()` 只检查 `room_type == "TreasureRoom"`，漏掉了 `TreasureRoomBoss`。该状态下 `available_commands` 不含 `choose`/`confirm`/`proceed`，只有 `["potion", "return", "key", "click", "wait", "state"]`，导致没有任何 handler 匹配，落到 `DefaultWaitHandler`。

**修改文件**: `rs/common/handlers/common_chest_handler.py`
```python
chest_room_types = ("TreasureRoom", "TreasureRoomBoss")  # 新增 TreasureRoomBoss
...
and state.game_state()['room_type'] in chest_room_types
```

**影响范围**: 所有 AI 策略均使用 `CommonChestHandler`（REQUESTED_STRIKE, CLAW_IS_LAW, PEACEFUL_PUMMELING, PWNDER_MY_ORBS, SHIVS_AND_GIGGLES, example）。

**验证**: ✅ 导入测试通过，策略加载正常

### P0.9 (2026-05-07) — Limit Break 有剩余能量时不打出修复
**问题**: AI 在战斗中即使有剩余能量也不打 Limit Break（力量翻倍卡），而是直接结束回合。

**根因**: `prefers_block_under_threat` 位于比较器链第 7 位，`prefers_strength_gain` 位于第 12 位。当两条路径的 threat 都 >10 且 block 不同时，`prefers_block_under_threat` 总是选 block 更多的路径，即使另一条路径力量翻倍。这导致 AI 选 Defend 而非 Limit Break。

**修复**: 在 `prefers_block_under_threat` 中增加力量增长豁免——当 challenger 路径力量增长更多且两条路径都能存活时，返回 `None` 让位给 `prefers_strength_gain`。

```python
if chal_str_gain > best_str_gain:
    best_survives = best.state.player.current_hp > best_threat
    chal_survives = challenger.state.player.current_hp > chal_threat
    if best_survives and chal_survives:
        return None  # Defer to prefers_strength_gain
```

**安全兜底**: 如果力量路径会死（chal_survives=False），格挡偏好仍然生效。

### P1.2 (2026-05-07) — PurgeHandler 重复索引死循环修复
**问题**: Empty Cage 等多选 purge（purge 2 张卡）时，3x 同名 Strike_R 全部映射到 choice_list 中第一个索引 0，导致 `choose 0` 选中再取消，无限循环。

**根因**: `_find_in_choice_list()` 总是返回第一个匹配项，不追踪已分配的索引。

**修复**: `_find_in_choice_list` 增加 `exclude: set[int]` 参数，已分配的索引被跳过，确保每张同名卡牌映射到不同的 choice 索引。

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

### P1 (2026-05-06) — 战斗比较器修复 + Pwnder 策略补全 + 坠落事件智能决策

**背景**：AI 不使用 Disarm、Headbutt、Perfected Strike 三张卡，根因是比较器链 bug 和卡牌定义缺失。

**修改文件**：
- `rs/common/comparators/core/comparisons.py`
- `rs/calculator/card_effects.py`
- `rs/calculator/cards.py`
- `rs/calculator/enums/card_id.py`
- `rs/machine/state.py`
- `rs/ai/pwnder_my_orbs/config.py`
- `rs/ai/pwnder_my_orbs/handlers/event_handler.py`
- `rs/ai/pwnder_my_orbs/pwnder_my_orbs.py`
- `tests/ai/pwnder_my_orbs/handlers/test_event_handler.py`

#### 1. 战斗比较器链修复

`least_nob_adjusted_scaling_damage` 在非 Gremlin Nob 战斗中退化：
- **Bug**：无 Nob 时，`nob_adjusted_scaling_damage()` 返回 0，等价于"最低 HP 损失"比较
- **影响**：覆盖后续伤害比较器，导致 AI 不愿做有利伤害交换（宁可少受 5 点伤也不打 18 点伤害）
- **修复**：无 Nob 时 `return None`，让决策权交给 `lowest_health_monster` 等比较器

#### 2. 卡牌战斗定义补全

| 卡牌 | 修复内容 |
|------|----------|
| Disarm+ | 力量值 `+3` → `-3`（原本写成正值，等于给敌人加力量） |
| Headbutt | 新增 `CardId.HEADBUTT`、卡牌定义（1 费攻击）、战斗效果（9/14 伤害，单体） |

#### 3. 坠落事件卡名映射（state.py）

Falling 事件选项文本包含卡牌名，需匹配配置列表做决策：
- **中文游戏**：选项含"失去"+中文名（如"失去宁静+"），需翻译为英文配置键名
- **英文游戏**：选项含"Lose"+英文名（如"Lose Tranquility+"），直接小写化即可
- **关键修复**：卡牌 ID 含角色后缀（`Strike_R`/`Strike_P`），需剥离后缀才能匹配通用键名 `strike`
- **`is_chinese()` 检测**：区分中英文游戏，避免英文显示名被错误映射为 ID 名（如 `Tranquility` → `clear the mind`）

映射流程：
```
Falling 选项文本 → 提取卡名 → is_chinese()? 
  → Yes: cn_to_en 映射 (中文→英文配置键名)
  → No: 直接小写化 (英文显示名已是配置键名)
→ 去除 "+" 后缀 → 与 removal_priority_list / DESIRED_CARDS_FOR_DECK 匹配
```

#### 4. Pwnder My Orbs 策略补全

| 问题 | 修复 |
|------|------|
| `DESIRED_CARDS_FOR_DECK` 只有 3 张铁甲卡（占位符） | 替换为 26 张真实 Defect 卡，按优先级分 5 组 |
| EventHandler 收到空 `cards_desired_for_deck=[]` | 改为传入 `DESIRED_CARDS_FOR_DECK` |
| Falling 事件硬编码 `choose 2`（永远删攻击牌） | 删除硬编码，走 CommonEventHandler 优先级决策 |

Defect 26 张核心卡牌分组：
```
Group 1 (Core): electrodynamics, echo form, defragment, biased cognition, capacitor,
                loop, core surge, fission, buffer, skim
Group 2 (Orb):  ball lightning, cold snap, doom and gloom
Group 3 (Atk):  sunder, streamline, ftl, sweeping beam, bullseye, compile driver
Group 4 (Frost): glacier, coolheaded, chill
Group 5 (Def):  charge battery, autoshields, equilibrium, reinforced body
```

#### 5. Disarm 不出牌 — 比较器链缺失敌人力量削减评估（2026-05-06 补丁）

**现象**：AI 即使有剩余能量也不出 Disarm 而是直接结束回合。

**根因**：比较器链中 `lowest_health_monster`（第14位）在 `least_incoming_damage`（第20位）之前。
Disarm 不造成伤害 → 怪物血量更高 → 在"最低血量怪物"比较中输给出攻击牌的路径 → 永远走不到评估受伤减少的比较器。

**示例**：
```
路径A (Strike+Defend): 怪物 24HP STR=0, 玩家受7伤
路径B (Disarm+Defend): 怪物 30HP STR=-2, 玩家受5伤
→ 第14步 lowest_health_monster: 24 < 30 → 选A，Disarm被淘汰
→ 第20步 least_incoming_damage 永远执行不到（5 < 7 应选B）
```

**修复**：新增 `most_enemy_strength_reduction` 比较器（comparisons.py），插入在
`lowest_total_monster_health` 之后、`most_enemy_vulnerable` 之前（约第16位）。

- 计算所有存活怪物的力量变化量（`current_str - original_str`）
- 乘以估算剩余回合数（基于怪物 HP 比例），体现跨回合减伤价值
- 负值越大（削减越多）→ 路径越优
- 不影响已有行为：如果两个路径敌人力量没变化，返回 None，交给后续比较器

**影响范围**：Ironclad（Disarm、Piercing Wail）、Silent（Piercing Wail）等力量削减卡牌。
Defect/Watcher 当前无此类卡牌，不受影响。

---

## 五、待办计划

### ~~P1 — Neow Bonus 优先级 + 事件阈值~~ → 已完成 (2026-05-06)

> 已完成部分：坠落事件智能决策（CommonEventHandler 优先级逻辑替代硬编码）、
> 卡名映射（中英文通用）、Pwnder 策略补全、战斗比较器链修复。
> Neow Bonus 重排和更多事件阈值优化移至 P2。

#### ~~Neow (A15+ 胜场数据)~~ → 移至 P2

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

### P2 — Neow Bonus 重排 + 事件阈值扩展

#### Neow (A15+ 胜场数据)

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

### P3 — Upgrade 优先级 + 卡牌评价微调

#### 升级优先级

未分析。35k 数据里有 `path_taken` 和 `path_per_floor`，可以分析：
- 精英狩猎 vs 安全路线 vs 篝火路线的胜率对比
- Act 1 最优路径策略

### P4 — 路线/路径选择

### P5 — 战斗演算 (ironclad_comparator)

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
