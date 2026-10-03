from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3' 


infernal_script = [
    Action(place, name='dart1', action='dart', position=(835, 387)), # Dart
    Action(place, name='boom1', action='boom', position=(835, 697)), # Boom
    
    # Change boom throwing side
    # Action('click', name='click', action='click', cost=0, position=(835, 697)),
    # Action('click', name='click', action='click', cost=0, position=(357, 283)),
    # Action('click', name='click', action='click', cost=0, position=(1600, 1040)),

    Action(upgrade, name='boom1', action=bottom), # 001
    Action(upgrade, name='boom1', action=middle), # 011
    Action('start', action='start', cost=0),

    Action(upgrade, name='boom1', action=middle), # 021
    Action(upgrade, name='dart1', action=bottom), # 001 (dart)
    Action(upgrade, name='dart1', action=bottom), # 002
    Action(upgrade, name='dart1', action=middle), # 012

    Action(place, name='Psi', action='Hero', position=(1595, 682)), # Psi
    Action(upgrade, name='dart1', action=middle), # 022
    Action(upgrade, name='dart1', action=bottom), # 023

    Action(upgrade, name='boom1', action=middle), # 031 (boom)
    Action(target, name = 'Psi', action='Strong'), # Psi Strong
    Action(upgrade, name='boom1', action=bottom), # 032 

    Action(place, name='heli1', action='heli', position=(102, 571), cost=1070), # Heli
    Action(upgrade, name='heli1', action=top), # 100
    Action(upgrade, name='heli1', action=top), # 200
    Action(upgrade, name='heli1', action=middle), # 210
    Action(upgrade, name='heli1', action=middle), # 220
    Action(upgrade, name='heli1', action=top), # 320

    Action(upgrade, name='dart1', action=bottom), # 024 (dart)

    Action(place, name='alch1', action='alch', position=(85, 475)), # Alchemist
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200
    Action(upgrade, name='alch1', action=top), # 300

    Action(upgrade, name='heli1', action=top), # 420 (Heli)

    Action(upgrade, name='alch1', action=top), # 400 (Alch)
    Action(upgrade, name='alch1', action=middle), # 410
    Action(upgrade, name='alch1', action=middle), # 420

    Action(place, name='sniper1', action='sniper', position=(477, 231)), # Sniper
    Action(upgrade, name='sniper1', action= top), # 100
    Action(target, name = 'sniper1', action='Strong'),
    Action(upgrade, name='sniper1', action=top), # 200 Sniper
    Action(upgrade, name='sniper1', action=top), # 300 Sniper
    Action(upgrade, name='sniper1', action=top), # 400 Sniper
    Action(upgrade, name='sniper1', action=bottom), # 401 Sniper
    Action(upgrade, name='sniper1', action=bottom), # 402 Sniper

    Action('finish', action='finish', cost=0)

]
