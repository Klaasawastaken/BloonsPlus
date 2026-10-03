from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3'

ravine_script = [
    Action(place, name='Psi', action='Hero', position=(502, 778)), # Psi
    Action(target, name = 'Psi', action='Strong'),
    Action('start', action='start', cost=0),
    Action(place, name='dart1', action='dart', position=(1051, 344)), # dart

    Action(place, name = 'ninjar', action='ninja', position=(740,813)), # Ninja
    Action(place, name= 'ninjal', action='ninja', position=(281,666)), # Ninja

    Action(upgrade, name='ninjar', action=top),
    Action(upgrade, name='ninjal', action=top),

    Action(upgrade, name='ninjar', action=bottom),
    Action(upgrade, name='ninjal', action=bottom),

    Action(upgrade, name='ninjar', action=top), # 201
    Action(upgrade, name='ninjal', action=top), # 201

    Action(upgrade, name='ninjar', action=top), # 301
    Action(upgrade, name='ninjal', action=top), # 301

    Action(upgrade, name='ninjar', action=bottom), # 302

    Action(place, name='alch1', action='alch', position=(549, 861)), # Alchemist
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200

    Action(place, name='ace1', action='ace', position=(420, 896)), # Ace.  might be wrong
    Action(upgrade, name='ace1', action=bottom), # 001
    Action(upgrade, name='ace1', action=bottom), # 002
    Action(upgrade, name='ace1', action=bottom), # 003
    Action(upgrade, name='ace1', action=top), # 103
    Action(upgrade, name='ace1', action=top), # 203

    Action(upgrade, name='ninjal', action=bottom), # 302 Ninja (Left)
    Action(upgrade, name='alch1', action=bottom), # 201 Alch

    Action(place, name='sniper1', action='sniper', position=(262, 733)), # Sniper
    Action(upgrade, name='sniper1', action=top), # 200
    Action(target, name = 'sniper1', action='Strong'),

    Action(upgrade, name='alch1', action=top), # 301 Alch

    Action(place, name='village1', action='Village', position=(397, 799)), # Village
    Action(upgrade, name='village1', action=middle), # 010
    Action(upgrade, name='village1', action=middle), # 020
    Action(upgrade, name='village1', action=top), # 120
    Action(upgrade, name='village1', action=top), # 220

    Action(place, name='ace2', action='ace', position=(261, 805)), # Ace2
    Action(upgrade, name='ace2', action=bottom), # 001
    Action(upgrade, name='ace2', action=bottom), # 002
    Action(upgrade, name='ace2', action=bottom), # 003
    Action(upgrade, name='ace2', action=top), # 103
    Action(upgrade, name='ace2', action=top), # 203

    Action(place, name='heli1', action='heli', position=(266, 925)), # Heli
    Action(upgrade, name='heli1', action=top), # 100
    Action(upgrade, name='heli1', action=top), # 200
    Action(upgrade, name='heli1', action=bottom), # 201
    Action(upgrade, name='heli1', action=bottom), # 202
    Action(upgrade, name='heli1', action=bottom), # 203
    Action(upgrade, name='heli1', action=bottom), # 203

    Action(upgrade, name='alch1', action=top), # Alch 302
    Action(upgrade, name='ace2', action=bottom), # Ace 204
    Action('finish', action='finish', cost = 0)

    
]