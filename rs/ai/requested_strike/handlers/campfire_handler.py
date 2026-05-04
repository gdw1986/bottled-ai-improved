"""
Ironclad-specific campfire handler with Act 1 HP bias.

In Act 1, rest threshold raised from 60% to 75% because:
- 80 max HP pool is small; 60% = 48 HP leaves little buffer for Act 1 elites
- Survivors in 35,691 runs average 0.43 more campfires/act than losers
- Early survival trumps early upgrades

In Act 2/3, baseline 60% threshold applies (restored by Burning Blood + larger pool).
"""
from presentation_config import presentation_mode, p_delay
from rs.common.handlers.common_campfire_handler import CommonCampfireHandler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class IroncladCampfireHandler(CommonCampfireHandler):

    def handle(self, state: GameState) -> HandlerAction:
        choice_list = state.get_choice_list()
        act = state.game_state().get('act', 1)

        pantograph_trigger_floors = [15, 32, 49]
        pantograph_will_cover = state.has_relic("Pantograph") and state.floor() in pantograph_trigger_floors \
            and state.get_player_health_percentage() >= 0.4
        pantograph_floor_49 = state.has_relic("Pantograph") and state.get_player_health_percentage() >= 0.60

        # Act 1: rest threshold = 75% (up from 60%)
        # Act 2/3: rest threshold = 60% (Burning Blood + larger HP pool)
        rest_threshold = 0.75 if act == 1 else 0.60

        worth_healing = state.get_player_health_percentage() <= rest_threshold and not pantograph_will_cover
        worth_healing_floor_49 = state.floor() == 49 and state.get_player_health_percentage() <= 0.85 \
            and not pantograph_floor_49
        important_upgrade_available = state.deck.contains_cards(self.high_priority_upgrades) and 'smith' in choice_list

        desired_choice = "rest"

        if 'rest' in choice_list and (worth_healing or worth_healing_floor_49):
            desired_choice = "rest"
        elif 'toke' in choice_list and state.deck.contains_curses_we_can_remove():
            desired_choice = "toke"
        elif 'smith' in choice_list and important_upgrade_available:
            desired_choice = "smith"
        elif 'lift' in choice_list and state.get_relic_counter("Girya") < 2:
            desired_choice = "lift"
        elif 'dig' in choice_list:
            desired_choice = "dig"
        elif 'smith' in choice_list:
            desired_choice = 'smith'
        elif 'toke' in choice_list and state.deck.contains_cards(self.card_removal_priorities):
            desired_choice = "toke"

        idx = choice_list.index(desired_choice) if desired_choice in choice_list else 0
        if presentation_mode:
            return HandlerAction(commands=[p_delay, "choose " + str(idx), p_delay])
        return HandlerAction(commands=["choose " + str(idx)])
