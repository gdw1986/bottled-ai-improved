from dataclasses import dataclass

from rs.common.handlers.common_battle_handler import CommonBattleHandler, BattleHandlerConfig
from rs.ai.peaceful_pummeling.comparators.watcher_improved_comparator import WatcherImprovedComparator


@dataclass
class WatcherBattleHandlerConfig(BattleHandlerConfig):
    """Watcher 专用的战斗处理器配置，使用改进版 Comparator。"""
    general_comparator = WatcherImprovedComparator


class PeacefulBattleHandler(CommonBattleHandler):
    """
    Watcher（Peaceful Pummeling）专用的战斗处理器。

    与 CommonBattleHandler 的区别：
    - 默认使用 WatcherImprovedComparator，支持敌人意图感知和姿态价值评估
    - 保留了特殊战斗（Big Fight、Gremlin Nob、三重哨兵等）的专用 Comparator
    """

    def __init__(self, max_path_count: int = 11_000):
        super().__init__(config=WatcherBattleHandlerConfig(), max_path_count=max_path_count)
