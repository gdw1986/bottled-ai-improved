# Bottled AI - 改进版（中文支持）

基于 [bottled-ai-chinese](https://github.com/gdw1986/bottled-ai-chinese) 继续改进，在中文语言支持的基础上，提升 AI 的战斗决策、牌组构建和地图路径规划能力。

上游链路：`xaved88/bottled_ai` → `gdw1986/bottled-ai-chinese` → **本项目**

---

## 改进计划

### ✅ 已完成

#### 来自 bottled-ai-chinese

| 问题 | 修复方案 |
|------|----------|
| `UnicodeDecodeError` | 改用 `sys.stdin.buffer` 读写 UTF-8 |
| 日志乱码 | 所有 `open()` 添加 `encoding='utf-8'` |
| 卡牌匹配失败 | 用 `card.id`（始终英文）翻译中文名 |
| `choose` 命令失败 | 统一改用数字索引 |

#### 本项目新增修复

| 问题 | 修复方案 |
|------|----------|
| 商店不操作（不买/不删卡） | 所有 5 策略的 `shop_purchase_handler.py` 改用数组索引定位，绕过中英文名匹配 |
| `deck.contains_cards` 永远返回 False | 改用 `card.id` 匹配，自动 strip 角色后缀（`Strike_R` → `strike`） |
| 坠落事件中文崩溃 | 支持中文"失去"关键字 + `cn_to_en` 卡名映射，英文游戏直通显示名 |
| Pwnder My Orbs 配置占位符 | 替换 3 张铁甲卡为 26 张真实 Defect 卡（球球流核心牌表） |
| Pwnder 坠落事件硬编码 | 删除 `choose 2` 硬编码，改为 CommonEventHandler 优先级决策 |
| 战斗比较器链非 Nob 退化 | `least_nob_adjusted_scaling_damage` 无 Nob 时返回 None，不再覆盖伤害比较 |
| Disarm+ 力量值错误 | 修复 +3→-3（应为减 3 力量） |
| Headbutt 缺失战斗定义 | 新增 CardId、卡牌定义、战斗效果（1 费攻击 9/14 伤害） |

### 🚧 进行中 / 计划中

| 方向 | 说明 |
|------|------|
| **战斗评估函数（Comparator）** | 加入敌人意图感知、姿态价值、跨回合威胁评估 |
| **动态卡牌拾取** | 根据当前牌组状态动态调整 `DESIRED_CARDS_FOR_DECK`（Ironclad 已有均衡引擎） |
| **地图路径权重动态化** | 根据 HP、牌组实力动态调整精英/休息的吸引力 |
| **药水使用时机优化** | 在高价值时机主动使用普通战斗中的药水 |
| **多角色事件智能决策** | CommonEventHandler 已支持优先级决策，待扩展更多事件 |

---

## 安装

### 环境要求

- Python 3.11.8+
- [PIP](https://pip.pypa.io/en/stable/installation/)
- Steam 版 Slay the Spire
- **游戏语言设为中文**

### Steam 创意工坊 Mod

订阅以下 Mod：

- [BaseMod](https://steamcommunity.com/sharedfiles/filedetails/?id=1605833019)
- [StSLib](https://steamcommunity.com/sharedfiles/filedetails/?id=1609158507)
- [ModTheSpire](https://steamcommunity.com/sharedfiles/filedetails/?id=1605060445)
- [Communication Mod](https://steamcommunity.com/sharedfiles/filedetails/?id=2131373661)

### 安装步骤

1. 将本仓库克隆到游戏安装目录：
   ```
   C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\bottled-ai-improved
   ```
2. 启动游戏并启用上述 Mod。
3. 找到 CommunicationMod 配置目录：
   - Windows: `%LOCALAPPDATA%\ModTheSpire\`
   - macOS: `~/Library/Preferences/ModTheSpire/`
4. 编辑 `CommunicationMod/config.properties`，添加：
   ```
   command=python .\bottled-ai-improved\main.py
   ```

### 启动机器人

在游戏主菜单：**Mods → Communication Mod → Config → Start external process**

可在 `main.py` 中配置运行参数（角色策略、局数、种子等）。

---

## 配置

- **策略选择**：在 `main.py` 中修改 `ALL_STRATEGIES`，可选：
  - `PEACEFUL_PUMMELING`（观者，推荐）
  - `CLAW_IS_LAW`（铁甲战士爪爪流）
  - `PWNDER_MY_ORBS`（故障机器人球球流）
  - `REQUESTED_STRIKE`（铁甲战士打击流）
  - `SHIVS_AND_GIGGLES`（静默猎人飞刀流）
- **暂停机器人**：编辑 `run_controller.txt`
- **调整操作速度**：编辑 `presentation_config.py`

---

## 已知限制

- 英文/中文游戏均可运行，中文事件选项通过卡名映射自动转换
- 四角色的中文支持完整度不一（观者测试最多）

---

## 致谢

- 原项目 [Bottled AI](https://github.com/xaved88/bottled_ai) by xaved88
- 中文适配 [bottled-ai-chinese](https://github.com/gdw1986/bottled-ai-chinese)
- [Communication Mod](https://steamcommunity.com/sharedfiles/filedetails/?id=2131373661)
