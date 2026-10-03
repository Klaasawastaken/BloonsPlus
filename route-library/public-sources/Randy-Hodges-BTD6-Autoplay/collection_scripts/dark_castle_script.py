from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3'

dark_castle_script = [
    Action(place, name='sub1', action='sub', position=(1100, 691)), # Sub
    Action(place, name='dart1', action='dart', position=(730, 658)), # Dart
    Action('start', action='start', cost=0),

    Action(place, name='dart1', action='dart', position=(908, 657)), # Dart2

    Action(place, name='ninja1', action='ninja', position=(749, 450)), # Ninja
    Action(upgrade, name='ninja1', action=top), # 100
    Action(upgrade, name='ninja1', action=bottom), # 101

    Action(place, name='Psi', action='Hero', position=(1456, 350)), # Psi
    Action(target, name = 'Psi', action='Strong'), # Psi Strong

    Action(upgrade, name='ninja1', action=top), # 201
    Action(upgrade, name='ninja1', action=top), # 301

    Action(place, name='alch1', action='alch', position=(713, 261)), # Alchemist
    Action(target, name = 'alch1', action='Strong'), # Alch Strong
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200

    Action(upgrade, name='ninja1', action=top), # 401 Ninja
    Action(upgrade, name='ninja1', action=bottom), # 402 Ninja

    Action(upgrade, name='alch1', action=top), # 300 (Alch)
    Action(upgrade, name='alch1', action=top), # 400 
    Action(upgrade, name='alch1', action=bottom), # 401

    Action(place, name='ace1', action='ace', position=(875, 221)), # Ace 
    Action(upgrade, name='ace1', action= bottom), # 001
    Action(upgrade, name='ace1', action=bottom), # 002
    Action(upgrade, name='ace1', action=bottom), # 003
    Action(upgrade, name='ace1', action=top), # 103
    Action(upgrade, name='ace1', action=top), # 203

    Action(place, name='village1', action='Village', position=(861, 325)), # Village
    Action(upgrade, name='village1', action= middle), # 010
    Action(upgrade, name='village1', action= middle), # 020
    Action(upgrade, name='village1', action= top), # 120
    Action(upgrade, name='village1', action= top), # 220

    Action(upgrade, name='ace1', action=bottom), # 204 Ace

    Action(place, name='sniper1', action='sniper', position=(1452, 751)), # Sniper
    Action(upgrade, name='sniper1', action= top), # 100
    Action(target, name = 'sniper1', action='Strong'),
    Action(upgrade, name='sniper1', action=top), # 200 Sniper
    Action(upgrade, name='sniper1', action=top), # 300 Sniper
    Action(upgrade, name='sniper1', action=top), # 400 Sniper
    Action(upgrade, name='sniper1', action=bottom), # 401 Sniper
    Action(upgrade, name='sniper1', action=bottom), # 402 Sniper

    Action('finish', action='finish', cost=0)

]