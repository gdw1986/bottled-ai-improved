from typing import List

from rs.ai.requested_strike.config import CARD_REMOVAL_PRIORITY_LIST, DESIRED_CARDS_FOR_DECK, HIGH_PRIORITY_UPGRADES, \
    DESIRED_POTIONS
from rs.ai.requested_strike.handlers.boss_relic_handler import BossRelicHandler
from rs.ai.requested_strike.handlers.discard_pile_handler import DiscardPileToTopDeckHandler
from rs.ai.requested_strike.handlers.event_handler import EventHandler
from rs.ai.requested_strike.handlers.neow_handler import NeowHandler
from rs.ai.requested_strike.handlers.potions_handler import PotionsScalingHandler, PotionsHealHandler, \
    PotionsEmergencyHandler, SmokeBombEscapeHandler, LiquidMemoriesHandler, LiquidMemoriesGridHandler, \
    SneckoOilEmergencyHandler
from rs.ai.requested_strike.handlers.shop_purchase_handler import ShopPurchaseHandler
from rs.ai.requested_strike.handlers.upgrade_handler import UpgradeHandler
from rs.common.handlers.common_astrolabe_handler import CommonAstrolabeHandler
from rs.ai.requested_strike.handlers.battle_handler import get_ironclad_battle_handler
from rs.ai.requested_strike.handlers.campfire_handler import IroncladCampfireHandler
from rs.ai.requested_strike.handlers.card_reward_handler import DynamicCardRewardHandler
from rs.common.handlers.common_chest_handler import CommonChestHandler
from rs.common.handlers.common_combat_reward_handler import CommonCombatRewardHandler
from rs.common.handlers.common_grid_select_handler import CommonGridSelectHandler
from rs.common.handlers.common_mass_discard_handler import CommonMassDiscardHandler
from rs.ai.requested_strike.handlers.map_handler import IroncladMapHandler
from rs.ai.requested_strike.handlers.purge_handler import PurgeHandler
from rs.common.handlers.common_scry_handler import CommonScryHandler
from rs.common.handlers.common_shop_entrance_handler import CommonShopEntranceHandler
from rs.common.handlers.common_transform_handler import CommonTransformHandler
from rs.machine.ai_strategy import AiStrategy
from rs.machine.character import Character
from rs.machine.handlers.handler import Handler

requested_strike_custom_battle_handlers: List[Handler] = [
    # Potion Handlers: special-case tactical potions before generic proactive/reactive use.
    LiquidMemoriesHandler(),
    SmokeBombEscapeHandler(),
    SneckoOilEmergencyHandler(),
    LiquidMemoriesGridHandler(),
    PotionsScalingHandler(),
    PotionsHealHandler(),
    PotionsEmergencyHandler(),
]

REQUESTED_STRIKE: AiStrategy = AiStrategy(
    name='REQUESTED_STRIKE',
    character=Character.IRONCLAD,
    handlers=requested_strike_custom_battle_handlers + [
        CommonAstrolabeHandler(CARD_REMOVAL_PRIORITY_LIST),
        get_ironclad_battle_handler(),

        # General Stuff
        BossRelicHandler(),
        UpgradeHandler(),
        CommonTransformHandler(CARD_REMOVAL_PRIORITY_LIST),
        DiscardPileToTopDeckHandler(),
        CommonGridSelectHandler(CARD_REMOVAL_PRIORITY_LIST),
        PurgeHandler(),
        CommonCombatRewardHandler(desired_potions=DESIRED_POTIONS),
        DynamicCardRewardHandler(DESIRED_CARDS_FOR_DECK),
        NeowHandler(),
        EventHandler(removal_priority_list=CARD_REMOVAL_PRIORITY_LIST, cards_desired_for_deck=DESIRED_CARDS_FOR_DECK),
        CommonChestHandler(),
        IroncladMapHandler(),
        IroncladCampfireHandler(HIGH_PRIORITY_UPGRADES, CARD_REMOVAL_PRIORITY_LIST),
        CommonShopEntranceHandler(),
        ShopPurchaseHandler(),
        CommonMassDiscardHandler(),
        CommonScryHandler(),
    ]
)
