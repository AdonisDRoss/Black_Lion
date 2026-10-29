# Layer 712: no calls in Runner Mode (crime, radio, rogue fights, raids), the other modes back on the title, the bar shrunk, juice is now cred

Upload order: everything in assets/ first, then game.jsx last. The assets are the same as layer 710, so if 710's assets are already up, only game.jsx has to change. This zip has everything.

## What changed
- **No calls in Runner Mode.** Crime calls are the original mode's work: stopping the rogues. They kept coming up in Runner Mode. Now off while Runner Mode is on: the crime calls (the scanner, "THE CALL" on the map, the scenes with thugs), the radio calls from the station, the rogue crews' turf fights, and the police raids. The other modes still get all of them. A call already on the radio when Runner Mode starts waits until you are back in the other mode.
- **The other modes are back on the title screen**: NEW GAME, DETECTIVE MODE, STUDENT MODE and FOOTBALL MODE, with RUNNER MODE. The switch is TITLE_OTHER_MODES at the top of the file. Set it to false to shelve them again. These modes were shelved and have not been played since, so expect rough edges.
- **The bar furniture is smaller.** Every piece is drawn at 70% of its art size (PMB_SHRINK in the bar block), keeping its centre and its floor line. D and Dex now look right beside the stools, tables and booths. The counter is shorter, so D and Dex stand a little closer to it. Tune PMB_SHRINK to taste.
- **JUICE is CRED on screen.** The HUD counter, the pickup flashes ("+10 CRED"), the prices on the radio and house menus, the BUST and SWAT buttons, and the lines the characters say all say CRED now. Only the words the player sees changed. The code names (g.juice, JUICE, the save data) are the same as before.

## Checks run
- Game bundles with esbuild, no errors.
- Call gates, headless: crime calls (4 checks), radio, rogue fights and raids (5 checks). Runner Mode starts none of them; the other modes still do.
- Roof guns: 17 checks pass. Rival targeting: 6 checks pass. Pheromone logic: all checks pass.
- Bar room, rendered in a browser harness at the new scale.
- Not yet run in the full game in a browser: the title screen with the other modes, and the crime-call gate in play.

## Open
- D's portrait is labeled 27. D is 31. Re-generate the portrait or relabel it.
- Turret art: assets/carwpn/wx_mg.png is optional. Without it a drawn barrel is used.
- Bar floors 2 to 4, what a rented room does, the roof plate (not wired), walking animation, motel marquee text.
