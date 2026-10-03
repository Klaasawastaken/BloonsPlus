// Map catalog by category, single source of truth shared by the frontend (app.js) and the backend
// (automation.js parses this the same regex way scanner.js/scan-achievements.js parse their own
// catalog files) — used to order both the map picker and the black border sweep Beginner first,
// then Intermediate, Advanced, Expert, matching the game's own map-select screen.
window.BLOONS_MAP_CATEGORIES = {
  "Beginner": ["Monkey Meadow", "In the Loop", "Skulltweak", "Three Mines 'Round", "Spa Pits", "Tinkerton", "Tree Stump", "Town Center", "Middle of the Road", "One Two Tree", "Scrapyard", "The Cabin", "Resort", "Skates", "Lotus Island", "Candy Falls", "Winter Park", "Carved", "Park Path", "Alpine Run", "Frozen Over", "Cubism", "Four Circles", "Hedge", "End of the Road", "Logs"],
  "Intermediate": ["Lost Crevasse", "Luminous Cove", "Ancient Portal", "Sulfur Springs", "Water Park", "Polyphemus", "Covered Garden", "Quarry", "Quiet Street", "Bloonarius Prime", "Balance", "Encrypted", "Bazaar", "Adora's Temple", "Spring Spring", "KartsNDarts", "Moon Landing", "Haunted", "Downstream", "Firing Range", "Cracked", "Streambed", "Chutes", "Rake", "Spice Islands"],
  "Advanced": ["Mushroom Grotto", "Party Parade", "Sunset Gulch", "Enchanted Glade", "Last Resort", "Castle Revenge", "Dark Path", "Erosion", "Midnight Mansion", "Sunken Columns", "X Factor", "Mesa", "Geared", "Spillway", "Cargo", "Pat's Pond", "Peninsula", "High Finance", "Another Brick", "Off the Coast", "Cornfield", "Underground"],
  "Expert": ["Tricky Tracks", "Glacial Trail", "Dark Dungeons", "Sanctuary", "Ravine", "Flooded Valley", "Infernal", "Bloody Puddles", "Workshop", "Quad", "Dark Castle", "Muddy Puddles", "#Ouch"]
};
