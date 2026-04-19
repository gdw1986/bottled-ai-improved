"""
Potion decision logic for combat.

POTION_DECISIONS entries: (id_substring, effect_type, condition_fn, urgency)
condition_fn(state, monsters, hp_pct) -> bool
urgency: 1=normal use, 2=use aggressively
"""

from rs.machine.state import GameState
from typing import Callable

# Type alias
UseCondition = Callable[[GameState, list, float], bool]


# ---- Helpers ----

def _has_power(state: GameState, power_id: str) -> bool:
    for p in state.get_player_combat().get("powers", []):
        if p.get("id", "").lower() == power_id.lower():
            return True
    return False


def _enemy_has_vulnerable(monsters: list) -> bool:
    return any(p.get("id") == "Vulnerable"
               for m in monsters
               for p in m.get("powers", []))


def _enemy_block(monster: dict) -> int:
    return monster.get("block", 0)


def _enemy_intent_damage(monster: dict) -> int:
    intent = monster.get("intent", {})
    if isinstance(intent, dict) and intent.get("type") in ("ATTACK", "DEBUFF"):
        return intent.get("damage", 0)
    return 0


def _enemy_intent_type(monster: dict) -> str | None:
    intent = monster.get("intent", {})
    if isinstance(intent, dict):
        return intent.get("type")
    return None


# ---- Condition factories ----

def when_low_hp(threshold_pct: float = 0.35) -> UseCondition:
    def cond(_s, _m, hp_pct: float) -> bool:
        return hp_pct < threshold_pct
    return cond


def when_vulnerable_high_hp(min_hp: int = 20) -> UseCondition:
    def cond(_s, monsters, _h) -> bool:
        return _enemy_has_vulnerable(monsters) and any(
            m.get("hp", 0) >= min_hp
            for m in monsters if not m.get("is_gone")
        )
    return cond


def when_attack_intent_low_block(threshold: int = 10) -> UseCondition:
    def cond(state, monsters, _h) -> bool:
        has_attack = any(_enemy_intent_type(m) == "ATTACK"
                         for m in monsters if not m.get("is_gone"))
        return has_attack and state.get_player_block() < threshold
    return cond


def when_has_strength() -> UseCondition:
    def cond(state, _m, _h) -> bool:
        return _has_power(state, "Strength")
    return cond


def when_has_orbs(min_count: int = 1) -> UseCondition:
    def cond(state, _m, _h) -> bool:
        return len(state.get_player_orbs()) >= min_count
    return cond


def when_no_vulnerable() -> UseCondition:
    def cond(_s, monsters, _h) -> bool:
        return not _enemy_has_vulnerable(monsters)
    return cond


def when_enemy_has_block(min_block: int = 1) -> UseCondition:
    def cond(_s, monsters, _h) -> bool:
        return any(_enemy_block(e) >= min_block for e in monsters if not e.get("is_gone"))
    return cond


def when_high_incoming_damage(damage_threshold: int = 15) -> UseCondition:
    def cond(_s, monsters, _h) -> bool:
        total = sum(_enemy_intent_damage(m) for m in monsters if not m.get("is_gone"))
        return total >= damage_threshold
    return cond


# ---- Potion definitions ----
# (id_substring, effect_type, condition_fn, urgency)
# effect_type: HEAL | DEFENSE | ATTACK | BUFF | DEBUFF | UTILITY

POTION_DECISIONS: list[tuple[str, str, UseCondition, int]] = [

    # ---- HEAL ----
    # Fruit Juice: Heal 5 HP
    ("fruit juice", "HEAL", when_low_hp(0.4), 1),

    # ---- DEFENSE ----
    # Block Potion: Gain 12 block
    ("block potion", "DEFENSE", when_attack_intent_low_block(8), 1),

    # Ghost in a Jar: Intangible 1 turn
    ("ghost in a jar", "DEFENSE", when_high_incoming_damage(15), 1),

    # Stance Potion (Watcher): Enter Calm
    ("stance potion", "DEFENSE",
     lambda s, _m, _h: s.floor() >= 15 and len(s.hand.cards) <= 3, 1),

    # ---- ATTACK ----
    # Fire Potion: Deal 8 damage
    ("fire potion", "ATTACK", when_vulnerable_high_hp(20), 1),
    ("fire potion", "ATTACK", when_low_hp(0.2), 2),

    # Speed Potion: Remove all enemy block
    ("speed potion", "ATTACK", when_enemy_has_block(1), 1),

    # Poison Potion: Apply 12 poison
    ("poison potion", "ATTACK", when_vulnerable_high_hp(40), 1),

    # Oil Potion: 4 damage + 2 vulnerable
    ("oil potion", "ATTACK", when_no_vulnerable(), 1),

    # ---- BUFF ----
    # Strength Potion: +2 Strength
    ("strength potion", "BUFF", when_has_strength(), 1),
    ("strength potion", "BUFF",
     lambda _s, monsters, _h: any(m.get("hp", 0) >= 40 for m in monsters if not m.get("is_gone")), 2),

    # Dexterity Potion: +2 Dexterity
    ("dexterity potion", "BUFF",
     lambda s, _m, _h: len([c for c in s.deck.cards if c.type.value == "SKILL"]) >= 5, 1),

    # Elixir of the Dragon: +3 Strength
    ("elixir of the dragon", "BUFF", when_has_strength(), 1),

    # Steroid Potion: +2 Strength
    ("steroid potion", "BUFF", when_has_strength(), 1),

    # ---- UTILITY ----
    # Swift Potion: Draw 2
    ("swift potion", "UTILITY",
     lambda s, _m, _h: len(s.hand.cards) <= 3, 1),

    # Essence of Darkness: Evoke orb twice
    ("essence of darkness", "UTILITY", when_has_orbs(1), 1),

    # Distilled Chaos: Evoke orbs 3 times
    ("distilled chaos", "UTILITY", when_has_orbs(2), 1),

    # ---- WATCHER special ----
    # White Beast Potion: +2 Mantra
    ("white beast potion", "BUFF",
     lambda s, _m, _h: _has_power(s, "Mantra") or s.has_relic("Teardrop"), 2),

    # Mind Potion: Apply 3 Weak
    ("mind potion", "DEBUFF",
     lambda _s, monsters, _h: any(_enemy_intent_damage(e) >= 15 for e in monsters if not e.get("is_gone")), 1),
]


def _get_potion_slot(state: GameState, potion_substr: str) -> int | None:
    """Return slot index of first potion matching substring, or None."""
    for idx, pot in enumerate(state.get_potions()):
        if pot["id"] != "Potion Slot" and potion_substr in pot["id"].lower():
            return idx
    return None


def decide_potion_use(state: GameState) -> tuple[int, str] | None:
    """
    Decide which potion to use in the current combat state.
    Returns (slot_index, description) or None if no potion should be used.
    """
    available = state.json.get("available_commands", [])
    if "potion" not in available:
        return None

    monsters = [m for m in state.get_monsters() if not m.get("is_gone")]
    hp_pct = state.get_player_health_percentage()

    for potion_substr, effect_type, cond_fn, _urgency in POTION_DECISIONS:
        slot = _get_potion_slot(state, potion_substr)
        if slot is not None:
            try:
                if cond_fn(state, monsters, hp_pct):
                    return slot, f"{effect_type} potion [{potion_substr}]"
            except Exception:
                pass

    return None
