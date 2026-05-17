"""
Ironclad-specific map handler: conservative Act 1 pathing.

Changes from default CommonMapHandler:
- Act 1 elite HP loss raised from 15 → 22 (accounts for variance/burst)
- Act 1 hallway HP loss raised from 2 → 5 (strikes + defends are weak)
- Higher survivability penalty multiplier (20 vs 15)
- More aggressive rest at campfires in Act 1 (75% threshold in simulation)

Empirical basis: 37% of runs die in Act 1 (13,195/35,691).
Survivors average 0.7 higher max HP entering Act 2 than deaths.
"""
from rs.common.handlers.common_map_handler import CommonMapHandler
from rs.game.path import PathHandlerConfig

# Gross damage estimates. Path simulation applies Burning Blood after fights,
# so these need to include the pre-heal damage rather than the net HP loss.
CONSERVATIVE_HALLWAY_HP_LOSS = {1: 11, 2: 14, 3: 11}
CONSERVATIVE_ELITE_HP_LOSS = {1: 30, 2: 32, 3: 24}

ironclad_map_config = PathHandlerConfig(
    hallway_fight_base_reward=1,
    hallway_fight_prayer_wheel=0.3,
    hallway_question_card_reward=0.15,
    hallway_fight_gold=15,
    hallway_fight_health_loss=lambda state: CONSERVATIVE_HALLWAY_HP_LOSS.get(state.game_state()['act'], 5),
    elite_base_reward=1,
    elite_question_card_reward=0.15,
    elite_fight_gold=30,
    elite_fight_health_loss=lambda state: CONSERVATIVE_ELITE_HP_LOSS.get(state.game_state()['act'], 15),
    relic_reward=1.5,
    curse_reward_loss=1.5,
    upgrade_reward=1.5,
    event_value_reward=lambda state: 1 if state.game_state()['act'] == 1 else 1.2,
    gold_at_shop_reward=lambda state, gold_to_spend: gold_to_spend / 100,
    gold_after_boss_reward=lambda state: state.game_state()['gold'] / 200,
    survivability_reward_calculation=lambda reward, survivability: reward + (survivability - 1) * 20,
)


class IroncladMapHandler(CommonMapHandler):

    def __init__(self):
        super().__init__(ironclad_map_config)
