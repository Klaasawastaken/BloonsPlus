# Bloons+ Preview 36

## Cash HUD and medal matching

- Fix the shifted-cash layout detector for a recorded alternate Sauda skin. A strong currency-location match now survives slight rendering differences while requiring greater separation from the other HUD location. This prevents the observed life-count-as-cash stall; broader live cash validation remains open.
- Share exact TownCentre and ThreeMinesAround save-name aliases between the UI and sweep. Owned medals still skip; unreadable medals remain unknown.
- Ignore old OCR map fragments absent from the navigation catalog without removing saved configuration.
- Repair garbled symbols in sweep and farming logs.

Offline checks cover the aliases, medal states, pool filtering, cash anchor confidence and panel transitions. This is a preview, not proof that every strategy wins. No game or save files were edited. Original CHIMPS recordings remain unchanged. Deploy between replays only.
