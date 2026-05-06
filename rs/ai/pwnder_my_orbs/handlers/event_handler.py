from rs.common.handlers.common_event_handler import CommonEventHandler
from rs.game.event import Event
from rs.machine.state import GameState


class EventHandler(CommonEventHandler):
    def __init__(self, removal_priority_list, cards_desired_for_deck):
        super().__init__(removal_priority_list=removal_priority_list, cards_desired_for_deck=cards_desired_for_deck)

    def find_event_choice(self, state: GameState) -> str | None:
        hp_per = state.get_player_health_percentage() * 100
        event = state.get_event()

        # Changes vs common handler: mainly a few health thresholds are lower
        match event:
            case Event.MYSTERIOUS_SPHERE:
                if hp_per >= 60:
                    return "choose 0"  # Get 'em!
                else:
                    return "choose 1"  # Leave

        return super().find_event_choice(state)
