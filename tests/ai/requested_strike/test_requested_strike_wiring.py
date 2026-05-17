from rs.ai.requested_strike.handlers.boss_relic_handler import BossRelicHandler
from rs.ai.requested_strike.handlers.event_handler import EventHandler
from rs.ai.requested_strike.handlers.potions_handler import (
    PotionsBossHandler,
    PotionsEliteHandler,
    PotionsEventFightHandler,
)
from rs.ai.requested_strike.handlers.shop_purchase_handler import ShopPurchaseHandler
from rs.ai.requested_strike.handlers.upgrade_handler import UpgradeHandler
from rs.ai.requested_strike.requested_strike import REQUESTED_STRIKE
from rs.common.handlers.card_reward.common_card_reward_handler import CommonCardRewardHandler
from rs.common.handlers.common_battle_handler import CommonBattleHandler
from rs.common.handlers.common_campfire_handler import CommonCampfireHandler
from rs.common.handlers.common_grid_select_handler import CommonGridSelectHandler
from rs.common.handlers.common_map_handler import CommonMapHandler
from rs.common.handlers.common_purge_handler import CommonPurgeHandler


def test_requested_strike_uses_release_03_baseline_handlers():
    handler_types = [type(handler) for handler in REQUESTED_STRIKE.handlers]

    assert handler_types[:3] == [
        PotionsBossHandler,
        PotionsEventFightHandler,
        PotionsEliteHandler,
    ]
    assert CommonBattleHandler in handler_types
    assert BossRelicHandler in handler_types
    assert UpgradeHandler in handler_types
    assert CommonGridSelectHandler in handler_types
    assert CommonPurgeHandler in handler_types
    assert CommonCardRewardHandler in handler_types
    assert EventHandler in handler_types
    assert CommonMapHandler in handler_types
    assert CommonCampfireHandler in handler_types
    assert ShopPurchaseHandler in handler_types


def test_requested_strike_does_not_use_experimental_handlers():
    handler_module_names = {type(handler).__module__ for handler in REQUESTED_STRIKE.handlers}

    assert "rs.ai.requested_strike.handlers.battle_handler" not in handler_module_names
    assert "rs.ai.requested_strike.handlers.card_reward_handler" not in handler_module_names
    assert "rs.ai.requested_strike.handlers.map_handler" not in handler_module_names
    assert "rs.ai.requested_strike.handlers.campfire_handler" not in handler_module_names
    assert "rs.ai.requested_strike.handlers.purge_handler" not in handler_module_names
