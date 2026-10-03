import json
from helper import getAllAvailablePlaythroughs

# Reuses AutoBTD6's own compatibility logic (helper.py's getAllAvailablePlaythroughs +
# listBTD6InstructionsFileCompatability): a single recorded playthrough is already valid for
# several gamemodes (e.g. a "chimps" clear also counts for hard/medium/easy, and for
# magic_monkeys_only/military_only/primary_only if it only used towers from that one group) —
# so the map/gamemode choices we expose don't need one recording per combination.
raw = getAllAvailablePlaythroughs(["own_playthroughs"], considerUserConfig=True)

out = {}
for mapname, gamemodes in raw.items():
    out[mapname] = {}
    for gamemode, entries in gamemodes.items():
        out[mapname][gamemode] = [
            {
                "filename": entry["filename"].split("/")[-1],
                "isOriginalGamemode": entry["isOriginalGamemode"],
                "resolution": entry["fileConfig"]["resolution"],
            }
            for entry in entries
        ]

print(json.dumps(out))
