from action_class import Action

place = 'place'
upgrade = 'upgrade'
target = 'target'

top = 'upgrade 1'
middle = 'upgrade 2'
bottom = 'upgrade 3'

flooded_valley_script = [
    Action(place, name='sub1', action='sub', position=(939, 167)), # Sub
    Action(place, name='sub2', action='sub', position=(1035, 920)), # Sub2
    Action('start', action='start', cost=0),
      
    Action(place, name='Psi', action='Hero', position=(216, 744)), # Psi
    Action(target, name = 'Psi', action='Strong'), # Psi Strong

    Action(place, name='sub3', action='sub', position=(1116, 533)), # Sub3

    Action(upgrade, name='sub1', action=bottom), # 001
    Action(upgrade, name='sub2', action=bottom), 

    Action(upgrade, name='sub1', action=top), # 101
    Action(upgrade, name='sub2', action=top), 

    Action(upgrade, name='sub1', action=top), # 201
    Action(upgrade, name='sub2', action=top), # 201

    Action(place, name='sniper1', action='sniper', position=(458, 136)), # Sniper
    Action(upgrade, name='sniper1', action= top), # 100
    Action(target, name = 'sniper1', action='Strong'),

    Action(upgrade, name='sub1', action=bottom), # 202
    Action(upgrade, name='sub2', action=bottom), # 202
    Action(upgrade, name='sub2', action=bottom), # 203 Sub1

    Action(place, name='ace1', action='ace', position=(452, 426)), # Ace 
    Action(upgrade, name='ace1', action= bottom), # 001
    Action(upgrade, name='ace1', action=bottom), # 002
    Action(upgrade, name='ace1', action=bottom), # 003

    Action(place, name='alch1', action='alch', position=(580, 285)), # Alchemist
    Action(upgrade, name='alch1', action=top), # 100
    Action(upgrade, name='alch1', action=top), # 200

    Action(upgrade, name='ace1', action=top), # 103 Ace
    Action(upgrade, name='ace1', action=top), # 203

    Action(place, name='village1', action='Village', position=(448, 293)), # Village
    Action(upgrade, name='village1', action= middle), # 010
    Action(upgrade, name='village1', action= middle), # 020

    Action(upgrade, name='sub1', action=bottom), # 203 Sub1

    Action(upgrade, name='alch1', action=top), # 300 Alch
    Action(upgrade, name='alch1', action=top), # 400 
    Action(upgrade, name='alch1', action=middle), # 410
    Action(upgrade, name='alch1', action=middle), # 420

    Action(upgrade, name='ace1', action=bottom), # 204 Ace

    Action(upgrade, name='sniper1', action=top), # 200 Sniper
    Action(upgrade, name='sniper1', action=top), # 300 
    Action(upgrade, name='sniper1', action=top), # 400 
    Action(upgrade, name='sniper1', action=bottom), # 401 
    Action(upgrade, name='sniper1', action=bottom), # 402 

    Action('finish', action='finish', cost=0)


]