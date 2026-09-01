IRON LION — HOSTED ASSETS
=========================

The build is HYBRID. Everything you see in the first ten seconds -- the player, his car and
bike, road and building textures, street props, the Kings -- is embedded in the .jsx and works
with no setup at all. That is roughly 130 files.

The other ~410 live here: comic pages, faction sheets, the fire department, casino furniture,
the waterfront set, prison props, music. The game fetches them as "assets/<name>", relative to
the page.

TO DEPLOY
---------
Put this folder next to index.html:

    /index.html
    /assets/mk_malc.webp
    /assets/title.mp3
    ...

WITHOUT IT
----------
The game runs and looks broadly right -- streets, cars, the player, buildings. Missing pieces
simply do not draw, and the HUD says how many were not found. Nothing throws.
