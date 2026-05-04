from dataclasses import dataclass

from rs.ai.requested_strike.ironclad_comparator import IroncladComparator
from rs.common.handlers.common_battle_handler import CommonBattleHandler, BattleHandlerConfig
from rs.machine.handlers.handler import Handler


@dataclass
class IroncladBattleHandlerConfig(BattleHandlerConfig):
    """Ironclad-specific battle handler config using IroncladComparator."""
    general_comparator = IroncladComparator


def get_ironclad_battle_handler(max_path_count: int = 11_000) -> Handler:
    """Factory for Ironclad-optimized battle handler.

    Uses IroncladComparator which adds:
    - Ironclad-specific power ratings (Rage)
    - Survival-priority logic (block under threat, power setup when safe)
    - Priority target selection (kill dangerous enemies first)
    """
    config = IroncladBattleHandlerConfig()
    config.general_comparator = IroncladComparator
    return CommonBattleHandler(config=config, max_path_count=max_path_count)
