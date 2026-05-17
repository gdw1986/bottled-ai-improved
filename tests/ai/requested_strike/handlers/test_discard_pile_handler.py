import unittest

from ai.requested_strike.rs_test_handler_fixture import RsTestHandlerFixture
from rs.ai.requested_strike.handlers.discard_pile_handler import DiscardPileToTopDeckHandler
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook


class DiscardPileToTopDeckHandlerTestCase(RsTestHandlerFixture):
    def test_headbutt_grid_picks_lethal(self):
        cards = [
            self._card("Defend_R", "SKILL"),
            self._card("Strike_R", "ATTACK", upgrades=1),
        ]
        state = self._state(
            cards=cards,
            monsters=[self._monster(current_hp=9)],
        )
        handler = DiscardPileToTopDeckHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "choose 1", "wait 30"], handler.handle(state).commands)

    def test_headbutt_grid_picks_requested_strike_core_card(self):
        cards = [
            self._card("Shrug It Off", "SKILL"),
            self._card("Perfected Strike", "ATTACK"),
            self._card("Strike_R", "ATTACK"),
        ]
        state = self._state(cards=cards)
        handler = DiscardPileToTopDeckHandler()

        self.assertTrue(handler.can_handle(state))
        self.assertEqual(["wait 30", "choose 1", "wait 30"], handler.handle(state).commands)

    def test_does_not_handle_liquid_memories_grid(self):
        cards = [self._card("Strike_R", "ATTACK")]
        state = self._state(cards=cards, current_action="BetterDiscardPileToHandAction")

        self.assertFalse(DiscardPileToTopDeckHandler().can_handle(state))

    @staticmethod
    def _state(cards: list[dict], monsters: list[dict] = None, current_action: str = "DiscardPileToTopOfDeckAction"):
        if monsters is None:
            monsters = [DiscardPileToTopDeckHandlerTestCase._monster()]

        game_state = {
            "screen_type": "GRID",
            "screen_state": {"cards": cards, "num_cards": 1},
            "choice_list": [card["name"] for card in cards],
            "seed": 1,
            "combat_state": {
                "draw_pile": [],
                "discard_pile": [],
                "exhaust_pile": [],
                "cards_discarded_this_turn": 0,
                "times_damaged": 0,
                "monsters": monsters,
                "turn": 1,
                "limbo": [],
                "hand": [],
                "player": {
                    "orbs": [],
                    "current_hp": 70,
                    "block": 0,
                    "max_hp": 80,
                    "powers": [],
                    "energy": 3,
                },
            },
            "deck": cards,
            "relics": [{"name": "Burning Blood", "id": "Burning Blood", "counter": -1}],
            "max_hp": 80,
            "act_boss": "The Guardian",
            "gold": 0,
            "action_phase": "WAITING_ON_USER",
            "act": 1,
            "screen_name": "GRID",
            "room_phase": "COMBAT",
            "is_screen_up": True,
            "current_action": current_action,
            "potions": [],
            "current_hp": 70,
            "floor": 1,
            "ascension_level": 0,
            "class": "IRONCLAD",
            "map": [],
            "room_type": "MonsterRoom",
        }
        return GameState(
            {
                "available_commands": ["choose", "wait", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": game_state,
            },
            TheBotsMemoryBook.new_default(),
        )

    @staticmethod
    def _monster(current_hp: int = 50) -> dict:
        return {
            "is_gone": False,
            "move_hits": 1,
            "move_base_damage": 6,
            "move_adjusted_damage": 6,
            "max_hp": max(50, current_hp),
            "name": "Cultist",
            "current_hp": current_hp,
            "block": 0,
            "id": "Cultist",
            "powers": [],
        }

    @staticmethod
    def _card(card_id: str, card_type: str, upgrades: int = 0) -> dict:
        return {
            "exhausts": False,
            "is_playable": True,
            "cost": 1,
            "name": card_id + ("+" if upgrades else ""),
            "id": card_id,
            "type": card_type,
            "ethereal": False,
            "uuid": card_id + str(upgrades),
            "upgrades": upgrades,
            "rarity": "BASIC",
            "has_target": card_type == "ATTACK",
        }


if __name__ == '__main__':
    unittest.main()
