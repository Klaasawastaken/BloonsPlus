from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3'

quad_script = [
    Action(place, name='sub1', action='sub', position=(946, 638)), # Sub
    Action(place, name='dart1', action='dart', position=(399, 565)), # Dart
    Action('start', action='start', cost=0),
    Action(place, name='dart2', action='dart', position=(836, 269)), # Dart2
    Action(place, name='dart3', action='dart', position=(1287, 577)), # Dart3

    Action(place, name='Psi', action='Hero', position=(778, 856)), # Psi
    Action(target, name = 'Psi', action='Strong'), # Psi Strong

    Action(upgrade, name='sub1', action=top), # Sub1 100
    Action(upgrade, name='sub1', action=top), # 200
    Action(upgrade, name='sub1', action=bottom), # 201
    Action(upgrade, name='sub1', action=bottom), # 202

    Action(place, name='alch1', action='alch', position=(1002, 684)), # Alchemist
    Action(target, name = 'alch1', action='Strong'),
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200

    Action(upgrade, name='sub1', action=bottom), # 203 Sub1
    Action(upgrade, name='sub1', action=bottom), # 204 

    Action(place, name='sniper1', action='sniper', position=(533, 798)), # Sniper
    Action(upgrade, name='sniper1', action= top), # 100
    Action(target, name = 'sniper1', action='Strong'),

    Action(upgrade, name='alch1', action=top), # 300 (Alch)
    Action(upgrade, name='alch1', action=top), # 400 
    Action(upgrade, name='alch1', action=bottom), # 401

    Action(place, name='ace1', action='ace', position=(943, 757)), # Ace 
    Action(upgrade, name='ace1', action= bottom), # 001
    Action(upgrade, name='ace1', action=bottom), # 002
    Action(upgrade, name='ace1', action=bottom), # 003
    Action(upgrade, name='ace1', action=top), # 103
    Action(upgrade, name='ace1', action=top), # 203

    Action(place, name='village1', action='Village', position=(805, 737)), # Village
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