ROUND 2 GANG SHEETS (2026-11-01)

Sheets (46 px cells, 12 columns, rows = build x types + type; both builds use the same figure):
  gang_irish.png   2 types (A: green jacket, flat cap. B: the extra green-jacket male). 552x184.
  gang_barrio.png  1 type (tan leather jacket, gold trim).                             552x92.
  gang_brack.png   1 type (burnt-orange jacket).                                        552x92.
  gang_sec.png     1 type (teal uniform, peaked cap, amber belt).                       552x92.
  gang_chi.png     1 type (dark red jacket).                                            552x92.
  gang_deuce.png   1 type (yellow jacket, gold shirt, black trousers). NEW sheet.       552x92.
  gang_gomez.png   1 type (dark grey suit, white shirt, slicked hair). NEW sheet.       552x92.
  gang_bratva.png  1 type (black leather jacket, red piping). NEW sheet.                552x92.

Placement: every figure sits on the old bottom line and centre (same as the sheets they replace).

GANGTOP changes needed when wired (game.jsx):
  irish:  types: 2   (old sheet had 5 types; the 3 old types are no longer in this sheet)
  barrio: types: 1   (was 5)
  brack:  types: 1   (was 5)
  sec:    types: 1   (was 4)
  chi:    types: 1   (was 5)
  deuce, gomez, bratva: new GANGTOP entries, lift 0 to start.

Known fit issues
  brack: 33 px wide (old 26). Chi: 32 px wide (old 26-28). Sec: 23 px wide (old 30-32).
  bratva: 24 px wide (target 28). Deuce: 31 px wide (target 28).
All frames are the same image. No walk, punch, aim or fire frames yet.
