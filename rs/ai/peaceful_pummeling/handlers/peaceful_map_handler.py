"""
Watcher-specific map handler with dynamic path scoring.

Uses estimate_deck_power() to adjust expected elite/hallway damage,
so paths are chosen based on actual deck strength rather than static assumptions.
"""

from rs.ai.peaceful_pummeling.map_picker import build_dynamic_config
from rs.common.handlers.common_map_handler import CommonMapHandler


class PeacefulMapHandler(CommonMapHandler):
    """
    Extends CommonMapHandler with state-aware path scoring.

    Key improvements over the default config:
      - Elite danger scales with deck power score (stronger deck = lower expected damage)
      - Hallway danger scales similarly
      - Survivability calculation considers boss damage thresholds per act
      - Low-HP danger is weighted more heavily
    """

    def handle(self, state):
        # Rebuild config on each decision so deck state is always fresh
        self.config = build_dynamic_config(state)
        return super().handle(state)
