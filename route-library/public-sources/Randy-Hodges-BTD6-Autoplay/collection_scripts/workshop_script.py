from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3'

workshop_script = [
    Action(place, name='dart1', action='dart', position=(124, 625)), # Dart1
    Action(target, name = 'dart1', action='Strong'),
    Action(place, name='dart2', action='dart', position=(563, 496)), # Dart2
    Action(place, name='dart3', action='dart', position=(633, 493)), # Dart3
    Action('start', action='start', cost=0),

    Action(place, name='dart4', action='dart', position=(700, 497)), # Dart4
    Action(place, name='dart4', action='dart', position=(768, 492)), # Dart5

    Action(place, name='ninja1', action='ninja', position=(1021, 492)), # Ninja
    Action(upgrade, name='ninja1', action=top), # 100
    Action(upgrade, name='ninja1', action=bottom), # 101
    Action(upgrade, name='ninja1', action=top), # 201

    Action(place, name='Psi', action='Hero', position=(1410, 67)), # Psi
    Action(target, name = 'Psi', action='Strong'), # Psi Strong

    Action(upgrade, name='ninja1', action=top), # 301

    Action(place, name='alch1', action='alch', position=(1024, 382)), # Alchemist
    Action(target, name = 'alch1', action='Strong'),
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200

    Action(upgrade, name='ninja1', action=top), # 401 Ninja
    Action(upgrade, name='ninja1', action=bottom), # 402

    Action(upgrade, name='alch1', action=top), # 300 (Alch)
    Action(upgrade, name='alch1', action=top), # 400 

    Action(place, name='spike1', action='spike', position=(1507, 634)), # Spike Factory
    Action(upgrade, name='spike1', action=middle), # 010
    Action(upgrade, name='spike1', action=middle), # 020

    Action(upgrade, name='alch1', action=bottom), # 401 (Alch)

    Action(place, name='ace1', action='ace', position=(1221, 326)), # Ace 
    Action(upgrade, name='ace1', action= bottom), # 001
    Action(upgrade, name='ace1', action=bottom), # 002
    Action(upgrade, name='ace1', action=bottom), # 003
    Action(upgrade, name='ace1', action=top), # 103
    Action(upgrade, name='ace1', action=top), # 203

    Action(upgrade, name='spike1', action=bottom), # 021 Spike Fac
    Action(upgrade, name='spike1', action=bottom), # 022 
    Action(upgrade, name='spike1', action=bottom), # 023 
    Action(target, name = 'spike1', action='Strong'), # Smart Targeting
    Action(upgrade, name='spike1', action=bottom), # 024 

    Action(upgrade, name='ace1', action=bottom), # 204 Ace

    Action(place, name='sniper1', action='sniper', position=(1196, 251)), # Sniper
    Action(upgrade, name='sniper1', action= top), # 100
    Action(target, name = 'sniper1', action='Strong'),
    Action(upgrade, name='sniper1', action=top), # 200 Sniper
    Action(upgrade, name='sniper1', action=top), # 300 Sniper
    Action(upgrade, name='sniper1', action=top), # 400 Sniper
    Action(upgrade, name='sniper1', action=bottom), # 401 Sniper
    Action(upgrade, name='sniper1', action=bottom), # 402 Sniper

    Action(place, name='village1', action='Village', position=(1285, 189)), # Village
    Action(upgrade, name='village1', action= middle), # 010
    Action(upgrade, name='village1', action= middle), # 020
    Action(upgrade, name='village1', action= top), # 120
    Action(upgrade, name='village1', action= top), # 220

    Action('finish', action='finish', cost=0)

]