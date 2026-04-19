# Bottled AI 中文版

基于 [Bottled AI](https://github.com/xaved88/bottled_ai) 修改，添加了**中文游戏语言**支持。

Slay the Spire（杀戮尖塔）自动打牌机器人，支持在中文游戏界面下正常运行。

## 与原版的区别

原版 Bottled AI 仅支持英文游戏语言。在中文环境下会出现以下问题：

| 问题 | 现象 | 修复方案 |
|------|------|----------|
| 编码错误 | stdin 读取中文 JSON 时 `UnicodeDecodeError` | 改用 `sys.stdin.buffer` 读写 UTF-8 |
| 日志乱码 | 含中文的日志写入时 `UnicodeEncodeError` | 所有 `open()` 添加 `encoding='utf-8'` |
| 卡牌匹配失败 | `choice_list` 返回中文名（如"打击"），bot 无法匹配英文名 | 自动利用 `card.id`（始终英文）翻译回英文 |
| choose 命令失败 | CommunicationMod 不认识中文名（如 `choose 攻击`） | 统一改用数字索引（如 `choose 0`） |

### 修改的文件

- `main.py` — 添加 stdin/stdout UTF-8 编码
- `rs/api/client.py` — 用 buffer 读写绕过 `input()` 的编码问题
- `rs/helper/logger.py` — 日志写入 UTF-8
- `rs/machine/state.py` — 核心翻译层：`_build_choice_name_map()` 自动翻译
- `rs/common/handlers/common_upgrade_handler.py` — 升级选择改用索引
- `rs/common/handlers/common_neow_handler.py` — Neow 事件改用索引
- `rs/common/handlers/common_campfire_handler.py` — 篝火改用索引
- `rs/common/handlers/common_mass_discard_handler.py` — 批量弃牌改用索引
- `rs/common/handlers/common_shop_entrance_handler.py` — 商店入口改用索引
- `rs/common/handlers/common_event_handler.py` — 5 个事件处理改用索引

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

1. 将本仓库克隆到游戏安装目录下的 `bottled_ai` 文件夹：
   ```
   E:\Steam\steamapps\common\SlayTheSpire\bottled_ai
   ```
2. 启动游戏并启用上述 Mod（会生成 Mod 配置文件）。
3. 找到 CommunicationMod 配置目录：
   - Windows: `%LOCALAPPDATA%\ModTheSpire\`
   - macOS: `~/Library/Preferences/ModTheSpire/`
4. 编辑 `CommunicationMod/config.properties`，添加：
   ```
   command=python .\\bottled_ai\\main.py
   ```

### 启动机器人

在游戏主菜单中：

1. **Mods** → **Communication Mod** → **Config** → **Start external process**

可在 `main.py` 中配置运行参数（角色策略、次数、种子等）。

> 超时时间为 10 秒，如果启动后无反应，请查看 ModTheSpire 控制台或 `communication_mod_errors.log`。

## 配置

- **策略选择**：在 `main.py` 中修改 `strategy` 变量，可选策略：
  - `PEACEFUL_PUMMELING`（静观其变，观者角色，推荐）
  - `CLAW_IS_LAW`
  - `PWNDER_MY_ORBS`
  - `REQUESTED_STRIKE`
  - `SHIVS_AND_GIGGLES`
- **暂停机器人**：编辑 `run_controller.txt`
- **调整操作速度**：编辑 `presentation_config.py`

## 已知限制

- 部分事件（EVENT）的中文选项标签无法自动翻译，会 fallback 到默认行为（选第一项）
- 四角色（Defect/Silent/Ironclad）的中文支持未经完整测试
- `has_relic()` 等基于 name 匹配的方法理论上不受影响（遗物 name 在 JSON 中保持英文）

## 致谢

- 原项目 [Bottled AI](https://github.com/xaved88/bottled_ai) by xaved88
- [Communication Mod](https://steamcommunity.com/sharedfiles/filedetails/?id=2131373661) — 提供 bot 与游戏之间的通信接口
