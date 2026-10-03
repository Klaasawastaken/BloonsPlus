from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3'

bloody_puddles_script = [
    Action(place, name='sub1', action='sub', position=(988, 936)), # Sub
    Action(place, name='dart1', action='dart', position=(400, 304)), # Dart
    Action('start', action='start', cost=0),
    Action(place, name='dart2', action='dart', position=(405, 505)), # Dart2
    Action(place, name='sub2', action='sub', position=(1214, 176)), # Sub2

    Action(place, name='Psi', action='Hero', position=(1395, 946)), # Psi
    Action(target, name = 'Psi', action='Strong'), # Psi Strong

    Action(place, name='sub3', action='sub', position=(606, 694)), # Sub3
    Action(place, name='dart3', action='dart', position=(957, 560)), # Dart3

    Action(upgrade, name='sub2', action=top), # Sub2 100
    Action(upgrade, name='sub2', action=top), # 200
    Action(upgrade, name='sub2', action=bottom), # 201
    Action(upgrade, name='sub2', action=bottom), # 202

    Action(place, name='alch1', action='alch', position=(1177, 252)), # Alchemist
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200

    Action(upgrade, name='sub2', action=bottom), # 203 (Sub2)
    Action(upgrade, name='sub2', action=bottom), # 204 

    Action(place, name='sniper1', action='sniper', position=(839, 214)), # Sniper
    Action(upgrade, name='sniper1', action= top), # 100
    Action(target, name = 'sniper1', action='Strong'),

    Action(upgrade, name='dart2', action=bottom), # 001 (dart2)
    Action(upgrade, name='dart2', action=bottom), # 002

    Action(upgrade, name='alch1', action=top), # 300 (Alch)
    Action(upgrade, name='alch1', action=top), # 400 
    Action(upgrade, name='alch1', action=bottom), # 401

    Action(place, name='dart4', action='dart', position=(1302, 909)), # Dart4
    Action(upgrade, name='dart4', action=bottom), # 001 
    Action(upgrade, name='dart4', action=bottom), # 002

    Action(place, name='ace1', action='ace', position=(976, 286)), # Ace 
    Action(upgrade, name='ace1', action= bottom), # 001
    Action(upgrade, name='ace1', action=bottom), # 002
    Action(upgrade, name='ace1', action=bottom), # 003
    Action(upgrade, name='ace1', action=top), # 103
    Action(upgrade, name='ace1', action=top), # 203

    Action(place, name='village1', action='Village', position=(990, 189)), # Village
    Action(upgrade, name='village1', action= middle), # 010
    Action(upgrade, name='village1', action= middle), # 020
    Action(upgrade, name='village1', action= top), # 120
    Action(upgrade, name='village1', action= top), # 220

    Action(upgrade, name='ace1', action=bottom), # 204 Ace

    Action(upgrade, name='sniper1', action=top), # 200 Sniper
    Action(upgrade, name='sniper1', action=top), # 300 Sniper
    Action(upgrade, name='sniper1', action=top), # 400 Sniper
    Action(upgrade, name='sniper1', action=bottom), # 401 Sniper
    Action(upgrade, name='sniper1', action=bottom), # 402 Sniper

    Action('finish', action='finish', cost=0)

]