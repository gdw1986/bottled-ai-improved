"""
PeacefulPotionHandler — uses potions strategically during combat.

Inserted BEFORE PeacefulBattleHandler so potion use happens before cards are played.
One potion per call; the rest are preserved for later in the fight.
"""

from rs.ai.peaceful_pummeling.potion_picker import decide_potion_use
from rs.machine.handlers.handler import Handler
from rs.machine.handlers.handler_action import HandlerAction
from rs.machine.state import GameState


class PeacefulPotionHandler(Handler):
    """
    Evaluates held potions and uses the best one when conditions are met.
    Only fires once per potion-use window; the battle handler takes over after.
    """

    def can_handle(self, state: GameState) -> bool:
        available = state.json.get("available_commands", [])
        return "potion" in available

    def handle(self, state: GameState) -> HandlerAction | None:
        decision = decide_potion_use(state)
        if decision is None:
            return None  # Nothing worth using; let next handler go

        slot, description = decision
        return HandlerAction(commands=[f"potion {slot}"])
