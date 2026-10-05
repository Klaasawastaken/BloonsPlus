# Bloons+ Preview 26

## Progress and diagnostics

- Ordinary level progress now comes from cumulative XP in the read-only game save, with rank and threshold consistency checks.
- XP/hr keeps its sampling window across ordinary rank-ups. Switching profiles resets it.
- The overview correctly labels its acquired-upgrade count as **Upgrades unlocked**.
- Map guidance and issue-report redaction load from public assets again. Server modules remain blocked from static access.

## Checks and limits

All ordinary level boundaries, the 180 million XP level-cap threshold, invalid inputs and rank-up/profile-isolation rate behavior were checked offline. The host app showed 493,535 XP remaining and opened the local issue-report dialog; no issue or log was submitted.

Level thresholds were checked against [Blooncyclopedia's BTD6 level table](https://www.bloonswiki.com/Level). Veteran rollover and ETA require further live save evidence. Winter Park Hard continued uninterrupted; no new victory is claimed. V1.0 remains in progress.
