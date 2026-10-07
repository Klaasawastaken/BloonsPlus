# Green hero title repair — 7 October 2026

Bazaar's missing-medal attempt stopped before gameplay because the picker could not read Rosalia's name. The retained, redacted name/button frame visibly says ROSALIA in green. Existing cyan, warm, violet and magenta masks all omitted those glyphs; the natural read was malformed. The picker moved to another map without charging a defeat.

A separate green title mask now feeds the existing candidate list. It reads actual text instead of inferring identity from portrait order or save stats. The requested-hero comparison and independently observed Select/Selected button remain unchanged. Yellow/red ribbon, white border and dark scenery samples are excluded by regression checks.

The synthetic color test failed before implementation because the Rosalia candidate was absent. All three focused hero-title/button checks then passed; an independent reviewer reran them and found no actionable issue. Running the full helper on the retained real image returns `rosalia` among title candidates and `select` for the button, correctly leaving selection unconfirmed. No gameplay was launched for validation and no private images are published.

Deploy only at the current healthy replay's completion boundary, then resume missing-medal gameplay with ownership and failures retained. A successful live Rosalia selection remains a separate acceptance observation.
