// Boss catalog is an index only. A type is not considered playable until dedicated, current-event
// Normal and Elite routes have been added and independently verified.
// Boss routes are event-specific (map, modifiers, and boss rules all matter). Empty slots mean
// there is no safe executable route; only set verified=true after a confirmed in-game clear.
window.BLOONS_BOSSES = [
  { id: 'bloonarius', name: 'Bloonarius', subtitle: 'The Inflator', mechanic: 'Spawns minion bloons while taking damage and releases larger waves at skull thresholds.', routes: { normal: null, elite: null } },
  { id: 'lych', name: 'Lych', subtitle: 'The Gravelord', mechanic: 'Can absorb eligible tower buffs, heal, and create tombstones and Lych-Souls.', routes: { normal: null, elite: null } },
  { id: 'vortex', name: 'Vortex', subtitle: 'Deadly Master of Air', mechanic: 'Moves quickly, pushes itself back at skulls, and stuns nearby towers.', routes: { normal: null, elite: null } },
  { id: 'dreadbloon', name: 'Dreadbloon', subtitle: 'Armored Behemoth', mechanic: 'Uses a shield with changing tower-class immunities and sends rock bloons.', routes: { normal: null, elite: null } },
  { id: 'phayze', name: 'Phayze', subtitle: 'Reality Warper', mechanic: 'Uses camo and a reality shield, then shifts its portal and the bloon spawn point.', routes: { normal: null, elite: null } },
  { id: 'blastapopoulos', name: 'Blastapopoulos', subtitle: 'Demon of the Core', mechanic: 'Builds heat, disrupts tower range and ability cooldowns, and launches fire and rocks.', routes: { normal: null, elite: null } },
  { id: 'diamondback', name: 'Diamondback', subtitle: 'The Village Devourer', mechanic: 'Has multiple body segments, a shielded tail, and spawns Diamond Bloons.', routes: { normal: null, elite: null } },
];
