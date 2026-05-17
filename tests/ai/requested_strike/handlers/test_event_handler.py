import unittest

from rs.ai.requested_strike.config import CARD_REMOVAL_PRIORITY_LIST, DESIRED_CARDS_FOR_DECK
from rs.ai.requested_strike.handlers.event_handler import EventHandler
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook


class RequestedStrikeEventHandlerTestCase(unittest.TestCase):
    def test_big_fish_heals_when_low_in_act_one(self):
        state = self._big_fish_state(current_hp=33, max_hp=85, act=1)
        handler = EventHandler(CARD_REMOVAL_PRIORITY_LIST, DESIRED_CARDS_FOR_DECK)

        self.assertEqual("choose 0", handler.find_event_choice(state))

    def test_big_fish_takes_max_hp_when_safe(self):
        state = self._big_fish_state(current_hp=70, max_hp=80, act=1)
        handler = EventHandler(CARD_REMOVAL_PRIORITY_LIST, DESIRED_CARDS_FOR_DECK)

        self.assertEqual("choose 1", handler.find_event_choice(state))

    def test_wheel_of_change_single_choice_does_not_queue_wait(self):
        state = self._wheel_of_change_state()
        handler = EventHandler(CARD_REMOVAL_PRIORITY_LIST, DESIRED_CARDS_FOR_DECK)

        self.assertEqual(["choose 0"], handler.handle(state).commands)

    @staticmethod
    def _big_fish_state(current_hp: int, max_hp: int, act: int) -> GameState:
        game_state = {
            "choice_list": ["banana", "donut", "box"],
            "screen_type": "EVENT",
            "screen_state": {
                "event_id": "Big Fish",
                "body_text": "",
                "options": [
                    {"choice_index": 0, "disabled": False, "text": "[Banana] Heal 1/3 HP.", "label": "Banana"},
                    {"choice_index": 1, "disabled": False, "text": "[Donut] Max HP +5.", "label": "Donut"},
                    {"choice_index": 2, "disabled": False, "text": "[Box] Relic. Cursed.", "label": "Box"},
                ],
                "event_name": "Big Fish",
            },
            "seed": 1,
            "deck": [],
            "relics": [{"name": "Burning Blood", "id": "Burning Blood", "counter": -1}],
            "max_hp": max_hp,
            "act_boss": "Hexaghost",
            "gold": 100,
            "action_phase": "WAITING_ON_USER",
            "act": act,
            "screen_name": "NONE",
            "room_phase": "EVENT",
            "is_screen_up": True,
            "potions": [],
            "current_hp": current_hp,
            "floor": 5,
            "ascension_level": 0,
            "class": "IRONCLAD",
            "map": [],
            "room_type": "EventRoom",
        }
        return GameState(
            {
                "available_commands": ["choose", "key", "click", "wait", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": game_state,
            },
            TheBotsMemoryBook.new_default(),
        )

    @staticmethod
    def _wheel_of_change_state() -> GameState:
        game_state = {
            "choice_list": ["leave"],
            "screen_type": "EVENT",
            "screen_state": {
                "event_id": "Wheel of Change",
                "body_text": "",
                "options": [
                    {"choice_index": 0, "disabled": False, "text": "[Leave]", "label": "Leave"},
                ],
                "event_name": "Wheel of Change",
            },
            "seed": 1,
            "deck": [],
            "relics": [{"name": "Burning Blood", "id": "Burning Blood", "counter": -1}],
            "max_hp": 80,
            "act_boss": "Collector",
            "gold": 100,
            "action_phase": "EXECUTING_ACTIONS",
            "act": 2,
            "screen_name": "NONE",
            "room_phase": "COMPLETE",
            "is_screen_up": False,
            "potions": [],
            "current_hp": 80,
            "floor": 24,
            "ascension_level": 0,
            "class": "IRONCLAD",
            "map": [],
            "room_type": "EventRoom",
        }
        return GameState(
            {
                "available_commands": ["choose", "key", "click", "wait", "state"],
                "ready_for_command": True,
                "in_game": True,
                "game_state": game_state,
            },
            TheBotsMemoryBook.new_default(),
        )


if __name__ == '__main__':
    unittest.main()
