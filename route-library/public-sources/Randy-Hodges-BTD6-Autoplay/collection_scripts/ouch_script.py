from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3'

ouch_script = [
    Action(place, name='sub1', action='sub', position=(708, 540)), # Sub
    Action(place, name='sub2', action='sub', position=(984, 545)), # Sub2
    Action('start', action='start', cost=0),

    Action(place, name='dart1', action='dart', position=(303, 671)), # Dart

    Action(place, name='Psi', action='Hero', position=(546, 309)), # Psi
    Action(target, name = 'Psi', action='Strong'), # Psi Strong

    Action(upgrade, name='sub1', action=bottom), # 001
    Action(upgrade, name='sub2', action=bottom), # 001

    Action(upgrade, name='sub1', action=middle), # 011
    Action(upgrade, name='sub2', action=top), # 101

    Action(upgrade, name='sub1', action=middle), # 021
    Action(upgrade, name='sub2', action=top), # 201


    Action(upgrade, name='sub1', action=bottom), # 022
    Action(upgrade, name='sub2', action=bottom), # 202

    Action(place, name='alch1', action='alch', position=(1009, 411)), # Alchemist
    Action(target, name = 'alch1', action='Strong'), # Strong
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200

    Action(upgrade, name='sub2', action=bottom), # 203 Sub2

    Action(place, name='ace1', action='ace', position=(845, 310)), # Ace 
    Action(upgrade, name='ace1', action= bottom), # 001
    Action(upgrade, name='ace1', action=bottom), # 002
    Action(upgrade, name='ace1', action=bottom), # 003
  
    Action(place, name='village1', action='Village', position=(990, 295)), # Village
    Action(upgrade, name='village1', action= middle), # 010
    Action(upgrade, name='village1', action= middle), # 020

    Action(upgrade, name='ace1', action=top), # 103 Ace
    Action(upgrade, name='ace1', action=top), # 203

    Action(upgrade, name='sub2', action=bottom), # 204 Sub2
    Action(upgrade, name='sub1', action=middle), # 023 Sub2

    Action(upgrade, name='alch1', action=top), # 300 Alch
    Action(upgrade, name='alch1', action=top), # 400 
    Action(upgrade, name='alch1', action=bottom), # 401

    Action(upgrade, name='ace1', action=bottom), # 204 Ace
    
    Action(place, name='sniper1', action='sniper', position=(85, 676)), # Sniper
    Action(upgrade, name='sniper1', action= top), # 100
    Action(target, name = 'sniper1', action='Strong'),
    Action(upgrade, name='sniper1', action=top), # 200 
    Action(upgrade, name='sniper1', action=top), # 300 
    Action(upgrade, name='sniper1', action=top), # 400 
    Action(upgrade, name='sniper1', action=bottom), # 401 
    Action(upgrade, name='sniper1', action=bottom), # 402 

    Action('finish', action='finish', cost=0)


]