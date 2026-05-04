"""
Data-driven card selection for Ironclad Requested Strike.
Generated from 35,691 cleaned runs (overall wr 10.8%).
Cards sorted by upgraded winrate. Copy counts set by practical limits.
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

# == Data-Driven DESIRED_CARDS_FOR_DECK ==
# Format: {card_name: max_copies}, sorted by upgraded winrate contribution
# Notation: "base_wr% → upgraded_wr%" shows winrate impact
DESIRED_CARDS_FOR_DECK: dict[str, int] = {
    # S-tier: 36-42% upgraded winrate — auto-pick first copy
    'offering': 1,           # 20% → 42%
    'impervious': 1,         # 21% → 41%
    'battle trance': 2,      # 16% → 37% (exhausts, 2 max)
    'limit break': 1,        # 15% → 36%

    # A-tier: 31-34% upgraded winrate
    'armaments': 2,          # 20% → 32% (upgrades whole hand, top 5 picked)
    'exhume': 1,             # 18% → 34%
    'sentinel': 1,           # 15% → 34%
    'warcry': 2,             # 13% → 34%
    'shockwave': 1,          # 15% → 33%
    'power through': 2,      # 14% → 33%
    'feel no pain': 1,       # 14% → 33%
    'apotheosis': 1,         # 25% → 32%
    'shrug it off': 2,       # 15% → 32%
    'burning pact': 2,       # 13% → 31%
    'brutality': 1,          # 16% → 31%
    'double tap': 1,         # 15% → 31%
    'corruption': 1,         # 15% → 31%
    'disarm': 1,             # 15% → 31%

    # B-tier: 28-31% upgraded winrate
    'barricade': 1,          # 11% → 30%
    'demon form': 1,         # 12% → 30%
    'sword boomerang': 2,    # 12% → 30%
    'dark embrace': 1,       # 13% → 29%
    'reaper': 1,             # 22% → 29%
    'dropkick': 2,           # 14% → 29%
    'ghostly armor': 1,      # 14% → 29%
    'heavy blade': 2,        # 11% → 29%
    'pommel strike': 2,      # 12% → 29%
    'intimidate': 1,         # 14% → 29%
    'second wind': 1,        # 13% → 29%
    'juggernaut': 1,         # 15% → 28%
    'entrench': 1,           # 12% → 28%
    'metallicize': 1,        # 15% → 27%
    'spot weakness': 2,      # 14% → 27%
    'body slam': 2,          # 12% → 27%
    'iron wave': 2,          # 11% → 27%
    'dual wield': 2,         # 10% → 27%
    'inflame': 1,            # 14% → 27%
    'flame barrier': 1,      # 13% → 27%
    'fiend fire': 1,         # 17% → 26%
    'evolve': 1,             # 11% → 26%
    'true grit': 2,          # 10% → 25%
    'uppercut': 1,           # 12% → 25%
    'pummel': 2,             # 14% → 25% (scales w/str, 2 max)

    # Perfected Strike archetype (strategy-defining core, 11%→26%)
    'twin strike': 2,        # 14% → 25%
    'perfected strike': 5,   # 10% → 26% (needs copies for scaling)
    'clash': 2,              # 13% → 26%

    # Colorless / Shop (high base wr, pick opportunistically)
    'master of strategy': 1, # 36% base
    'dark shackles': 1,      # 33% base
    'flash of steel': 1,     # 29% base
    'panache': 1,            # 25% base
    'panacea': 1,            # 25% base
    'finesse': 1,            # 25% base
    'mayhem': 1,             # 25% → 30%
    'bandage up': 1,         # 23% base
    'trip': 1,               # 22% → 30%
    'blind': 1,              # 21% base
    'handofgreed': 1,        # 17% base

    # Act 1 commons for early survival
    'cleave': 1,             # 13% → 23%
    'clothesline': 1,        # 12% → 25%
    'thunderclap': 1,        # 13% → 24%
    'anger': 1,              # 11% → 20%
    'headbutt': 2,           # 14% → 25%

    # AoE & burst (high appearance in A15+ wins, formerly missing)
    'whirlwind': 2,          # 12% → 30%
    'flex': 2,               # 13% → 28%
}

HIGH_PRIORITY_UPGRADES = [
    'Apotheosis',
    'Armaments',      # upgrades every card in hand when Armaments+ — massive value
    'Perfected Strike',
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
