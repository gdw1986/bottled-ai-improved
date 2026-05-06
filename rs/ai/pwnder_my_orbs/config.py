CARD_REMOVAL_PRIORITY_LIST = ['strike', 'strike+', 'defend', 'defend+']

DESIRED_CARDS_FOR_DECK: dict[str, int] = {
    # Group 1: Core powers and high-value cards (always want)
    'electrodynamics': 1, 'echo form': 2, 'defragment': 5, 'biased cognition': 5,
    'capacitor': 2, 'loop': 2, 'core surge': 2, 'fission': 1, 'buffer': 1, 'skim': 1,
    # Group 2: Orb attack cards
    'ball lightning': 2, 'cold snap': 2, 'doom and gloom': 1,
    # Group 3: General attack cards
    'sunder': 1, 'streamline': 1, 'ftl': 1, 'sweeping beam': 1,
    'bullseye': 1, 'compile driver': 2,
    # Group 4: Frost orb cards
    'glacier': 2, 'coolheaded': 5, 'chill': 1,
    # Group 5: General defend cards (lowest priority among desired)
    'charge battery': 2, 'autoshields': 1, 'equilibrium': 1, 'reinforced body': 2,
}

HIGH_PRIORITY_UPGRADES = [
    'Apotheosis',
    'Fission',
    'Defragment',
    'Biased Cognition',
]

DESIRED_POTIONS = [
    'fruit juice',
    'fairy in a bottle',
    'focus potion',
    'cultist potion',
    # 'power potion',  # we don't currently pick cards from potions with pwnder
    'potion of capacity',
    'duplication potion',
    'blessing of the forge',
    # 'attack potion',  # we don't currently pick cards from potions with pwnder
    'dexterity potion',
    'ambrosia',
    'fear potion',
    'essence of steel',
    'strength potion',
    'regen potion',
    'entropic brew',
    'liquid bronze',
    'energy potion',
    # 'skill potion',  # we don't currently pick cards from potions with pwnder
    'ancient potion',
    'weak potion',
    'gambler\u0027s brew',
    'poison potion',
    # 'colorless potion',   # we don't currently pick cards from potions with pwnder
    'flex potion',
    'swift potion',
    'essence of darkness',
    'fire potion',
    'explosive potion',
    'speed potion',
    'block potion',
    'cunning potion',
    'smoke bomb',
    'elixir potion',
    'distilled chaos',  # We don't want to accidentally play Biased Cog way too early
    'liquid memories',
    'snecko oil',
]
