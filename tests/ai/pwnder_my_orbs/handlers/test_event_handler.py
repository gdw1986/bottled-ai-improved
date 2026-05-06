from ai.pwnder_my_orbs.pmo_test_handler_fixture import PmoTestHandlerFixture
from rs.ai.pwnder_my_orbs.handlers.event_handler import EventHandler


class TestEventHandler(PmoTestHandlerFixture):
    handler = EventHandler

    def test_falling(self):
        # Now uses CommonEventHandler's priority-based Falling logic instead of hardcoded "choose 2".
        # With correct card name mapping, "strike" matches removal_priority_list → choose 1.
        # This is better than the old blind "lose the attack" approach because it respects
        # strategy priorities (e.g., won't lose a valuable attack card if a basic Strike is available).
        self.execute_handler_tests('/event/event_falling_pmo.json', ['choose 1', 'wait 30'])
