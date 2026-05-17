"""
Data-driven card selection for Ironclad Requested Strike.
Generated from 35,691 cleaned runs (overall wr 10.8%).

Act 1 survival-focused revision:
- Reduced from 56 to ~30 card types for faster deck convergence
- Prioritized Act 1 performers (11-18% act_1 winrate)
- Removed slow scaling cards (Barricade, Corruption, Demon Form, etc.)
- Increased copies of core damage cards (Perfected Strike, Twin Strike)
- AoE is critical: Cleave (delta -1.0%, best Act 1 consistency), Whirlwind, Thunderclap
"""

CARD_REMOVAL_PRIORITY_LIST = [
    # Curses — remove unconditionally
    'regret',
    'doubt',
    'injury',
    'pain',
    'decay',
    'shame',
    'writhe',
    'normality',
    'parasite',
    'clumsy',
    'curseofthebell',
    'necronomicurse',
    'ascendersbane',

    # Starters — replace with better cards (Bash is KEEPER!)
    'strike_r',
    'defend_r',
    'strike',
    'defend',
    'strike_r+1',
    'defend_r+1',
    'strike+1',
    'defend+1',

    # Bad ceiling (<19% wr even when upgraded)
    'rampage',
    'rampage+1',
    'handofgreed',
    'handofgreed+1',
    'wild strike',
    'wild strike+1',
    'hemokinesis',
    'hemokinesis+1',
    'combust',
    'combust+1',
    'carnage',
    'carnage+1',
    'anger',
    'anger+1',
    'fire breathing',
    'fire breathing+1',
    'searing blow',
    'searing blow+1',
]

# == Act 1 Focused DESIRED_CARDS_FOR_DECK ==
# Reduced pool (~30 types) for faster convergence on core damage/block.
# Act 1 winrate in comments where available.
# Sorted by strategic importance, not raw winrate.
DESIRED_CARDS_FOR_DECK: dict[str, int] = {
    # ═══ S-tier: Core Engine (auto-pick first copy) ═══
    'offering': 1,             # 18.4% Act 1 — draw + energy
    'impervious': 1,           # 16.6% Act 1 — burst block
    'battle trance': 1,        # 14.5% Act 1 — draw (1 copy, exhausts)
    'limit break': 1,          # 17.7% Act 1 — strength multiplier
    'shrug it off': 3,         # 13.4% Act 1 — universal block + draw

    # ═══ A-tier: Core Damage (high priority) ═══
    'perfected strike': 2,     # 13.0% Act 1 — best common damage engine
    'twin strike': 2,          # 12.3% Act 1 — cheap, scales w/str
    'pommel strike': 2,        # 11.9% Act 1 — draw + damage
    'clash': 1,                # 12.9% Act 1 — 0-cost conditional
    'sword boomerang': 1,      # 11.7% Act 1 — multi-hit, scales w/str
    'whirlwind': 2,            # 12.5% Act 1 — AoE, scales w/energy
    'thunderclap': 1,          # 11.5% Act 1 — AoE + Vulnerable
    'cleave': 1,               # 11.1% Act 1 — AoE, best delta (-1.0%)

    # ═══ A-tier: Core Block ═══
    'power through': 2,        # 13.3% Act 1 — high block (wound cost)
    'flame barrier': 1,        # early block vs multi-hit
    'shockwave': 1,            # 15.2% Act 1 — AoE Vuln+Weak
    'armaments': 2,            # upgrade engine
    'ghostly armor': 1,        # large early block without wounds
    'metallicize': 1,          # steady block for boss/elite fights
    'feel no pain': 1,         # exhaust block payoff

    # ═══ B-tier: Strength Scaling ═══
    'inflame': 1,              # 12.9% Act 1 — strength source
    'spot weakness': 1,        # conditional strength
    'flex': 1,                 # 0-cost temp strength

    # ═══ B-tier: Sustain & Growth ═══
    'reaper': 1,               # 17.9% Act 1 — AoE + healing
    'feed': 1,                 # 15.3% Act 1 — max HP growth
    'immolate': 1,             # 14.7% Act 1 — premium AoE

    # ═══ B-tier: Utility ═══
    'disarm': 2,               # 12.7% Act 1 — enemy strength reduction
    'uppercut': 1,             # weak + vulnerable for Act 1/2 anchors
    'clothesline': 1,          # weak plus damage
    'intimidate': 1,           # 0-cost AoE weak
    'headbutt': 1,             # 11.3% Act 1 — deck manipulation
    'true grit': 1,            # exhaust utility
    'burning pact': 1,         # exhaust + draw
    'second wind': 1,          # exhaust + block

    # ═══ Colorless / Shop (opportunistic) ═══
    'j.a.x.': 1,              # 0-cost +2 STR
    'master of strategy': 1,  # draw
    'dark shackles': 1,       # emergency block
    'apotheosis': 1,          # upgrade everything
    'finesse': 1,             # 0-cost block + draw
}

HIGH_PRIORITY_UPGRADES = [
    'Apotheosis',
    'Limit Break',     # #1 upgrade: exhaust → non-exhaust, enables infinite strength scaling
    'Armaments',      # upgrades every card in hand when Armaments+ — massive value
]

DESIRED_POTIONS = [
    'fruit juice',
    'fairy in a bottle',
    'cultist potion',
    'power potion',
    'potion of capacity',
    'heart of iron',
    'duplication potion',
    'distilled chaos',
    'blessing of the forge',
    'attack potion',
    'dexterity potion',
    'ambrosia',
    'fear potion',
    'essence of steel',
    'strength potion',
    'regen potion',
    'blood potion',
    'entropic brew',
    'liquid bronze',
    'energy potion',
    'skill potion',
    'ancient potion',
    'weak potion',
    'gambler\u0027s brew',
    'poison potion',
    'colorless potion',
    'flex potion',
    'swift potion',
    'bottled miracle',
    'fire potion',
    'explosive potion',
    'speed potion',
    'block potion',
    'stance potion',
    'smoke bomb',
    'elixir potion',
    'liquid memories',
    'snecko oil',
]
