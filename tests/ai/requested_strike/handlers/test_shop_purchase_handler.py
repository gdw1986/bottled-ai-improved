import unittest

from rs.ai.requested_strike.handlers.shop_purchase_handler import ShopPurchaseHandler
from rs.machine.state import GameState
from rs.machine.the_bots_memory_book import TheBotsMemoryBook


def _card(card_id: str, card_type: str = "ATTACK"):
    return {
        "exhausts": False,
        "cost": 1,
        "name": card_id,
        "id": card_id,
        "type": card_type,
        "ethereal": False,
        "uuid": card_id,
        "upgrades": 0,
        "rarity": "BASIC" if card_type != "CURSE" else "CURSE",
        "has_target": card_type == "ATTACK",
    }


class RequestedStrikeShopPurchaseHandlerTestCase(unittest.TestCase):

    def test_buys_perfected_strike_before_ordinary_purge(self):
        state = self._shop_state(
            gold=188,
            choice_list=["purge", "Perfected Strike"],
            cards=[{"id": "Perfected Strike", "name": "Perfected Strike", "price": 49}],
            deck=[_card("Strike_R")],
        )

        self.assertEqual(["choose 1", "wait 30"], ShopPurchaseHandler().handle(state).commands)

    def test_purges_removable_curse_before_perfected_strike(self):
        state = self._shop_state(
            gold=188,
            choice_list=["purge", "Perfected Strike"],
            cards=[{"id": "Perfected Strike", "name": "Perfected Strike", "price": 49}],
            deck=[_card("Doubt", "CURSE")],
        )

        self.assertEqual(["choose 0", "wait 30"], ShopPurchaseHandler().handle(state).commands)

    def test_keeps_release_03_ordinary_purge_before_non_baseline_card_buy(self):
        state = self._shop_state(
            gold=188,
            choice_list=["purge", "Apotheosis"],
            cards=[{"id": "Apotheosis", "name": "Apotheosis", "price": 180}],
            deck=[_card("Strike_R")],
        )

        self.assertEqual(["choose 0", "wait 30"], ShopPurchaseHandler().handle(state).commands)

    @staticmethod
    def _shop_state(gold: int, choice_list: list[str], cards: list[dict], deck: list[dict]) -> GameState:
        raw = {
            "available_commands": ["choose", "potion", "leave", "key", "click", "wait", "state"],
            "ready_for_command": True,
            "in_game": True,
            "game_state": {
                "choice_list": choice_list,
                "screen_type": "SHOP_SCREEN",
                "screen_state": {
                    "purge_available": True,
                    "purge_cost": 75,
                    "cards": cards,
                    "relics": [],
                    "potions": [],
                },
                "deck": deck,
                "relics": [],
                "potions": [{"id": "Potion Slot"}],
                "gold": gold,
                "floor": 7,
                "act": 1,
                "current_hp": 60,
                "max_hp": 80,
                "room_type": "ShopRoom",
                "room_phase": "COMPLETE",
            },
        }
        return GameState(raw, TheBotsMemoryBook.new_default())


if __name__ == "__main__":
    unittest.main()
