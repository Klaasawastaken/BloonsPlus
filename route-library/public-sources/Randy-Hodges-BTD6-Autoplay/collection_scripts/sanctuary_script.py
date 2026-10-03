from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3'

sanctuary_script = [

    Action(place, name='dart1', action='dart', position=(262, 276)), # Dart
    Action(place, name='dart2', action='dart', position=(1244, 429)), # Dart
    Action(place, name='sniper0', action='sniper', position=(746, 925)), # Sniper
    Action('start', action='start', cost=0),

    Action(place, name='Psi', action='Hero', position=(760, 106)), # Psi
    Action(target, name = 'Psi', action='Strong'), # Psi Strong

    Action(place, name='sub1', action='sub', position=(942, 181)), # Sub
    Action(upgrade, name='sub1', action=top), # 100 
    Action(upgrade, name='sub1', action=top), # 200 
    Action(upgrade, name='sub1', action=bottom), # 201 
    Action(upgrade, name='sub1', action=bottom), # 202 

    Action(place, name='ace1', action='ace', position=(864, 259)), # Ace 
    Action(upgrade, name='ace1', action= bottom), # 001
    Action(upgrade, name='ace1', action=bottom), # 002
    Action(upgrade, name='ace1', action=bottom), # 003

    Action(place, name='alch1', action='alch', position=(747, 239)), # Alchemist
    Action(target, name = 'alch1', action='Strong'), # Strong
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200

    Action(upgrade, name='ace1', action=top), # 103 Ace
    Action(upgrade, name='ace1', action=top), # 203

    Action(place, name='village1', action='Village', position=(844, 160)), # Village
    Action(upgrade, name='village1', action= middle), # 010
    Action(upgrade, name='village1', action= middle), # 020

    Action(upgrade, name='alch1', action=top), # 300 Alch
    Action(upgrade, name='alch1', action=top), # 400 
    Action(upgrade, name='alch1', action=bottom), # 401

    Action(upgrade, name='sub1', action=bottom), # 203 Sub
    Action(upgrade, name='ace1', action=bottom), # 204 Ace
    
    Action(place, name='sniper1', action='sniper', position=(930, 100)), # Sniper2
    Action(upgrade, name='sniper1', action= top), # 100
    Action(target, name = 'sniper1', action='Strong'),
    Action(upgrade, name='sniper1', action=top), # 200 
    Action(upgrade, name='sniper1', action=top), # 300 
    Action(upgrade, name='sniper1', action=top), # 400 
    Action(upgrade, name='sniper1', action=bottom), # 401 
    Action(upgrade, name='sniper1', action=bottom), # 402 

    Action('finish', action='finish', cost=0)
]
