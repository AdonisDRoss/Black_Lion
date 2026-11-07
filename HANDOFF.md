# IRON LION / RAVEN HOOK 1986 — HANDOFF

Continues the LAYER 575 handoff. LAYERS 787-791 are this session (790 is a touch-controls rework still in progress,
not yet finished or documented here); LAYERS 576 through 786 were built independently (not in this file -- that run
of sessions isn't in my copy of this handoff, so there's a gap here rather than a guess at what changed in it).
Everything from LAYER 575 down is the older history, with STILL OPEN updated in place.
Current build: `game.jsx` is **71,663 lines**.

---

## LAYER 791 -- MISSION TWO, THIRD TIME: THE "YOUR KIT" CARD IN THE OPENING NEVER LISTED THE BAG EITHER

Follow-up to LAYER 789. The player came back after that fix with "there's still no sleeping bag in my inventory
for me to put down." LAYER 789's fix was correct -- `sleepOwned` really does get set `true` now, same as the gas
mask -- but it only touched the game-state flag. It never touched the opening cutscene's "YOUR KIT" card (`RoKit`,
shown when the opening's beat hits `sc === 'kit'`), which lists the starting gear from a separate, hardcoded array
(`RO_KIT`) that has nothing to do with `sleepOwned` at all. That array was never updated when the sleeping bag
became part of the starting kit, so the card the player actually watches during the opening still read BACKPACK,
GAS MASK, HOLO PHONE, LASER PISTOL (ON STUN), DEBIT CARD, DIRT BIKE, CALL REMOTE -- no bag -- regardless of what
LAYER 789 fixed underneath it. Fair complaint: the one place that tells the player what they're starting with
didn't match what they actually got.

Fix: added `'SLEEPING BAG'` to `RO_KIT` (now: BACKPACK, GAS MASK, SLEEPING BAG, HOLO PHONE, LASER PISTOL (ON
STUN), DEBIT CARD, DIRT BIKE, CALL REMOTE). Checked for any other place the starting kit is listed as a
hardcoded array (searched for the other item names) -- `RO_KIT` is the only one.

Test: start a new run, watch the opening through to the kit card -- SLEEPING BAG should be listed. In-game,
`runInventory()` and the equipment wheel were already correct as of LAYER 789 and are unchanged here.

BUILD_TAG bumped to `LAYER 791` (`LAYER 790` is reserved for the in-progress touch-controls work below, not
finished this session).

### STILL OPEN
- Two LAYER-789-adjacent bugs in a row from the same hardcoded-list-vs-flag split (`sleepOwned` vs `RO_KIT`) is a
  pattern worth remembering: any place the game *describes* the starting kit in text/UI, separately from the
  flags that actually grant it, is a place that can drift out of sync the next time the kit changes. Nothing else
  found this time, but worth a glance if the kit changes again.
- LAYER 790 (touch controls, below) is mid-implementation: the input plumbing is in but the on-screen buttons
  aren't wired up yet. Not shipped as a finished layer -- see the TOUCH CONTROLS note after this entry for what's
  done and what's left.

---

## LAYER 787 -- RUNNER MODE: THE DIRT BIKE NOW MOVES, AND THE LASER PISTOL FIRES ON FOOT AND FROM THE BIKE

Follow-up to LAYER 788. The player came back after that fix with the actual root cause: "I wasn't getting the bag
in my inventory." LAYER 788 fixed a real bug (the hint fired while still indoors, where the bag can't be laid out)
but it assumed `sleepOwned` was already `true` by the time mission two starts. For most players it wasn't.

There are two ways into the story's opening kit. `pickLaser()` -- walking up to the dumpster stash yourself --
grants the pistol, a gas mask, AND a sleeping bag (`gasOwned = true; sleepOwned = true;`, LAYER 690). But
`RUNNER_API.startFirstMission()` -- what the opening cutscene actually calls to drop the player straight into
`'teammate'` stage with their kit already "in hand," skipping the dumpster walk-up entirely -- only ever set
`LASER.has` and `gasOwned`. Its own inline comment said as much: "the kit (laser on stun, gas mask) is in hand" --
no mention of the bag, because it was never in the kit it granted. So for anyone who went through the opening (the
normal, intended way to start), `sleepOwned` stayed `false` for the entire game: no bag on the equipment list, no
bag option on the wheel ever (not indoors, not outdoors), nothing to lay out at mission two no matter where they
stood. LAYER 788's fix was correct but couldn't matter -- the condition it was timing (`sleepOwned && !runnerInside`)
was never going to be true on the `sleepOwned` side.

Fix: `startFirstMission()` now also sets `sleepOwned = true`, matching `pickLaser()`'s grant exactly.

Test: start a new run through the normal opening (not the dumpster stash), check the equipment wheel any time
after the opening hands off -- SLEEPING BAG should already be listed. Clear the house, go through LAYER 788's
flow (head outside, "LAY THE BAG OUT" fires, wheel has `PUT DOWN SLEEPING BAG` this time) and it should actually
place.

BUILD_TAG bumped to `LAYER 789`.

### STILL OPEN
- Same caution as LAYER 788: didn't audit every other item the opening's shortcut might be under-granting relative
  to its "pick it up yourself" equivalent elsewhere in the code. This was the one reported; there could be a
  sibling bug (vest, pack, something else) following the same pattern -- opening grants A and B, the manual pickup
  grants A, B and C -- that just hasn't been hit by a player yet.

---

## LAYER 788 -- MISSION TWO: THE "LAY THE BAG OUT" LINE WAS FIRING WHILE HE WAS STILL INSIDE THE HOUSE

Bug report: "Mission two is broken there's no sleeping bag for me to put down."

`partnerSaved()` -- the scene where the thugs are cleared and the partner is found -- is triggered by
`missionHouse()` while `inHouse()` is true, i.e. while the player is still standing inside the house building.
Its closing line told the player to open the wheel and lay the sleeping bag out right then: `THE PARTNER IS WITH
YOU NOW. LAY THE BAG OUT: WHEEL (Y) > EQUIPMENT > PUT DOWN SLEEPING BAG.` But the equipment wheel's bag entries are
gated on `!runnerInside` (LAYER 746: "indoors... the bag... are outside things"), by design -- you can't lay a
bedroll out inside someone's house. So at the exact moment the game told the player to do it, the option the
instruction pointed at did not exist on the wheel. That's "mission two is broken, no bag to put down" exactly as
reported: not a missing feature, a line firing one room too early. (`MISSION.stage` goes `'house'` -> `'bed'` here,
and `'bed'` is the stage that blocks on the bag going down and him lying on it -- so this wasn't a cosmetic hint,
it's the actual gate mission two can't get past without it.)

Fix: `partnerSaved()` no longer promises the bag instruction up front -- its line is now just `THE PARTNER IS WITH
YOU NOW. HEAD OUTSIDE.` The real instruction (`LAY THE BAG OUT: WHEEL (Y) > EQUIPMENT > PUT DOWN SLEEPING BAG.`)
moved into `missionStoryTick()`'s `'bed'` branch, which already runs every frame during this stage: it now fires
once, the first frame the player is both outside (`!runnerInside`) and hasn't placed the bag yet (`!sleepDown`),
using the same one-shot-hint pattern the stage already used for the following "NOW LIE DOWN ON IT" line
(`bedHint`) -- a new `bagOutHint` flag, reset to 0 alongside `bedHint` when `partnerSaved()` runs. The mission
arrow was already pointing at the door's *outside* spot the whole time (`houseSpot` is the point just outside the
door, not the inside of the building), so following the arrow now lines up with when the instruction actually
fires.

Test: clear the house, listen for "HEAD OUTSIDE" while still inside -- opening the wheel's equipment tab in there
correctly still has no bag option (that part was never wrong). Walk out the door: "LAY THE BAG OUT" fires once;
the wheel now has `PUT DOWN SLEEPING BAG`. Lay it down, "NOW LIE DOWN ON IT" fires as before, stand on it and press
A/E to sleep through to midnight, which should still roll into `tutorialStart()` same as before this fix.

BUILD_TAG bumped to `LAYER 788`.

### STILL OPEN
- Didn't check whether any other story-stage message has the same shape (an instruction that names a wheel/menu
  action gated on a world-state condition -- indoors/outdoors, mounted/on foot -- that isn't true yet at the
  moment the line is said). This one was found because it was reported; there could be others later in the chain
  (store, doctor, chain of informants) that haven't been hit yet.

---

## LAYER 787 -- RUNNER MODE: THE DIRT BIKE NOW MOVES, AND THE LASER PISTOL FIRES ON FOOT AND FROM THE BIKE

Bug report: "Players dirt Bike not moving laser pistol not shooting" (Runner Mode).

**The dirt bike.** Every spot that places the player's own dirt bike (`trapdoorExit()` and the two other bike-spawn
sites) sets `car.mode = 'landed'` -- the same mode the *hover* bike uses to mean "touched down, sitting still,
E to get out." `updateCar()`'s `'landed'` branch unconditionally zeroes speed/lean and returns before a single
line of throttle/steering code runs, every frame, no exceptions. For the hover bike that's correct: `toggleLand()`
(L/B) is what lifts it back into `'up'`/`'air'`. But `toggleLand()` explicitly refuses for the dirt bike ("THE DIRT
BIKE DOESN'T FLY") and nothing else ever moved its mode out of `'landed'` -- so the dirt bike could be boarded, but
never actually driven. It wasn't stuck in a corner case; it was stuck *always*, from the very first spawn.

Fix, in `boardBike()` and `getOffBike()`: both now check whether the mounted vehicle is a dirt bike
(`/^rtbike_/.test(CAR_FILES[car.sprite])`) and handle it on its own path instead of falling into the hover bike's
fly/land logic.
- Boarding a dirt bike sets `car.mode = 'ground'` immediately (no "lift off" step -- it drives the second you're on),
  with its own message: `ON THE BIKE · WASD TO RIDE · E TO GET OFF`.
- Getting off a dirt bike requires it be stopped (`Math.abs(car.speed) <= TEAM_CAR_STOP`, same stop-speed the team
  car uses) rather than `'landed'`, then sets `car.mode` back to `'landed'` (parked) so re-boarding sees it as ready
  again -- `STOP THE BIKE FIRST.` if you try to hop off while still rolling.
- The hover bike's own board/dismount path (mode checks against `'landed'`, the fly/land messaging) is untouched.

**The laser pistol.** On foot, firing was never actually broken -- `fire()`'s gating (has the pistol, first press
draws it, 450ms cooldown, etc.) all checked out fine in isolation. The real gap: there was no way to fire *while
riding the dirt bike*. `fire()` only had two paths that work off foot: the FIS car's turret (`fireTurret()`, its own
special case), and otherwise anything not on foot falls through to `houseThugPunch()` -- so mounted on the (until
now, permanently stationary) dirt bike, pressing RB/F never reached the pistol at all. Given the two bug reports
came in together, this is almost certainly what was being tested: board the bike, it doesn't move, try to shoot
back at the hunters chasing you, nothing happens either.

Added `fireFromBike()`: a new case in `fire()`, checked right after the FIS car's turret case, for `!walker.on`,
`car.mode === 'ground'`, and the mounted vehicle being a dirt bike. It reuses the exact same beam/hit logic as the
on-foot shot (drones, hunters, mates, house thugs, stun vs. HARM, the 450ms cooldown, `LASER.beams` for the draw)
but sources the beam from the bike's nose (`car.x`/`car.y`, offset 30px along `car.heading`) instead of the walker,
and fires straight ahead along the bike's heading -- no draw step, no aim-lock (aim-lock already stands down off
foot; this doesn't change that, it just doesn't need it to fire forward).

No art, no new state, no save-format changes. Test: board the dirt bike (`E` near it after `trapdoorExit()`), WASD
should drive it immediately; `RB`/`F` while riding should fire the pistol straight ahead if it's already in hand
(has + drawn); `E` again while stopped gets you off.

BUILD_TAG bumped to `LAYER 787` (was `LAYER 785`, which collided with this build's own subway layer -- the new code
here uses `LAYER 787` throughout to stay clear of the existing 785/786 content).

### STILL OPEN
- The gap between LAYER 575 and LAYER 786 (hunters, teams, drones, the subway, sleep/save, the C.A.N. lobby, and
  the rest of Runner Mode) isn't documented in this file -- it was built in sessions this handoff never saw. Worth
  a proper changelog pass if there's ever a reason to hand this off to someone else cold.
- Firing from the bike has no aim-lock and no turning turret -- it's strictly "whatever direction you're driving."
  Fine for a first pass; revisit if riding-and-strafing-your-shot turns out to matter.
- Didn't touch the hover bike's own fly/land flow at all -- if it has a similar "stuck" edge case somewhere, it
  wasn't in scope for this bug report and wasn't checked.

---

## LAYER 575 -- MIX-AND-MATCH CIVILIANS: HEADS, BODIES AND A SMALL SHARED LEG POOL, GENERALISED FROM REY'S OWN HEAD-SWAP; PROMPTS_575

No new art yet -- pure groundwork, falls back quietly until art lands (same convention as every other
optional plate in this project).
- **Generalised `reyInTorso569`**: that function glues one specific head onto one specific body, cached once.
  `civTorsoKey575(bodyKey, headKey)` does the same thing for ANY pair -- same 355x407 canvas, body full-width
  at y 92, head 136 wide centred at y 2 -- and writes the result straight into `imgs.current` under a synthetic
  key (`civ2_<body>_<head>`), so `drawYouth0`'s existing `imgs.current[AP.torso]` lookup needs no changes at
  all. `civRig575(bIdx, hIdx)` wraps that into an ARM_BY_YT-shaped descriptor (torso/set/skin/sleeve/wid/legSet),
  cached by index pair. `drawYouth0`'s arms line now also checks `p.civ2 && civRig575(p.civ2.b, p.civ2.h)` as a
  third fallback after `p.arms` and `ARM_BY_YT[p.yt]`.
- **The registries**: `CIV_HEAD_KEYS` (12, `assets/civ2/cv_head_1..12.png`), `CIV_BODIES` (8, headless/armless
  outfit plates, `assets/civ2/cv_body_1..8.png`, each naming its arm-pose set, skin/sleeve tint, and which shared
  leg style it's drawn to go with). 12x8 = 96 distinct people off 20 pieces of art.
  **`CIV_LEG_STYLES`**: jeans/chinos/sweats/shorts/skirt/overalls -- SIX styles, shared across all 8 bodies (and
  meant to stay shared as more bodies get added), real walking art via the exact mechanism Rey's own
  `lg_walk_<style>_0/1/2` already uses (layer 549) -- nothing new there but the file names.
- **Test hook**: `G.civT575()` -- how many heads/bodies/leg-frame-sets have actually loaded, and how many of the
  96 head/body pairs are composited and ready.
- **PROMPTS_575.md**: full art spec (canvas sizes, the 355/92/136/2 anchor numbers spelled out, the 8-body
  outfit/sleeve/leg-style table, what each leg frame is for).
- **STILL OPEN, the real decision**: this already covers named street people (pin a specific head+body+leg combo
  instead of a one-off plate per person, same slot `HL_PEOPLE` uses) for free. The anonymous background CROWD
  is a separate, bigger step -- it renders off baked 8-direction walk-cycle sprite sheets (`civPool`/`pickCiv`/
  `drawPed`), a fundamentally different technique from this rig's rotated-plate-plus-glued-limbs approach (how
  Rey moves). Moving the crowd onto this rig trades real directional walk-cycle animation for shape variety
  (actual different faces/builds instead of just palette swaps) -- a real visual call, not just a refactor.
  Didn't make that call blind with no art to look at; flagged for a decision once there's something to see.

---

## LAYER 574 -- RETRY WAS OVERWRITING THE BUILDING YOU WERE IN (THE HAPPY HIPPY BUG); PROMPTS_574

`t_574.py` (start ALL IN, go down, sit with Victor, fail, retry: the Hippy must survive), `t_574b.py` (simulate an old
corrupted save, round-trip it, the Hippy must come back on its own lot). Test hooks: G.hippyB574, hippyIn574,
storyFail574, cellB574, corrupt574, snapRT574, snapDbg574, aliasDbg574.
- **The bug** (any mission, worst at the Hippy): applySnap fills top-level g objects IN PLACE (Object.assign + delete
  missing keys). g.inside is a live building, so on RETRY the building you were in at the checkpoint (Palm Court -- the
  mission starts at home) was copied over the building you were in NOW (the Happy Hippy): wrong name, no happyHippy,
  no laundromat art, no club, no door men, nobody to talk to -- "the basement isn't under the Hippy".
- **Fix**: in applySnap, any value that is a live building (has `__orig`) or a live city cell is pointed at, never
  merged (`live()` guard in both passes).
- **Repair for saves made before the fix** (`repairBlds574`, end of applySnap): a building whose middle is outside its own
  cell is reset to its `__orig` (marked `_fix574`); if that leaves no Happy Hippy, the Hippy is set up again, preferring
  the repaired lot (same scoring as bozFronts, ratio 1.7, `mine` if g.hippyOwned). Verified: back at 24278,13043.
- PROMPTS_574.md (sent earlier): 8 colour-coded headless bodies + 15 heads for the gang mix-and-match rig.

---

## LAYER 573 -- A DEAD COP IS A BODY

`t_572d.py` (two officers set to hp 0 beside the player, shot at 1 s and 7 s). No new art: the rig already had
ar_torso_cop_m/f/sgt in five tones, the police arm set and lg_lie_slacks.
- `drawDeadCop572(u)`: the street police draw (drawList kind 5) sends hp <= 0 here instead of drawCop. Seeds once per
  body (deadSeed, deadAng, deadT0; race/sex when the unit has none), draws a two-lobe blood pool that spreads over
  6 s, then `drawCopPlate` with dead/lying/legK "lg_lie_slacks" at the angle he fell. drawCopPlate passes
  dead/lying/legK/deadSeed through to drawYouth.
- `drawArms525`: with `p.dead`, both punch arms are thrown out from the shoulders at seeded angles (+-0.8 rad around
  straight out), drawn BEFORE the torso, and nothing else.
- Falls back to the old KO frame (drawActorTop) if the rig art isn't loaded.
- NOT done: gang members, civilians and federals still use the stretched-frame + shadow; the same function works for
  anyone on the torso rig (pass their own torso/arm set).

---

## LAYER 572 -- COPS: THEY DIE, AND THEY SHOOT FROM COVER

`t_572.py` (dispatch a car beside the player via `G.dispatchPolice572`, kill one officer, watch for 5 s). Also shipped
`zx_art_catchup.zip`: every asset changed since 2026-10-19 12:00 (367 files) -- Donny was missing el_roof2.png (it was
in zx_art_566).
- **Dead officers stayed up.** The g.police loop only guarded firing/cover with hp > 0, so a dead cop went on walking
  his canvass route; the g.policeMore loop had no check at all, so dead backup officers kept taking cover AND firing.
  Both loops now stop a unit at hp <= 0.
- **Cover never fired.** Three stacked bugs: (1) copCover fires only when `u.stun <= 0`, and stun starts undefined
  (undefined <= 0 is false) and was never counted down anywhere -- now `(u.stun || 0)` and both loops decay it;
  (2) the peek spot is 30 from the cruiser's middle and a car's bullet circle is 32, so every round went into their own
  door -- bullets now carry `ox/oy` and skip any car within rr+6 of where they were fired (fixes the player crouched
  at a bumper too); (3) once that was fixed they shot THEMSELVES and each other -- bullets carry `src` and never hit
  it, and police/cop rounds skip policeUnits/federals.
- Result in the test: dead officer moves 0, the live one works the car and lands rounds on the player.
- NOT done: cops only use their own cruiser as cover (no walls, parked cars); the dead-body look is still the
  stretched frame + soft shadow (downedPose) -- Donny is weighing a laid-out body from the torso/arms/legs rig.

---

## LAYER 571 -- STEAM OFF THE MANHOLES; THE REAL COVER EVERYWHERE; ROW-HOUSE ROOFS; BEDROLLS

`zx_art_571.zip` (assets/, 11 files). Test `t_571.py` (a manhole at junction 8,8 by day, by night, and from below).
- **Manhole covers**: sv_manhole was only a ring (transparent middle). The "CITY SEWER 1982" cover (sw_00) and the
  open-hole-with-cover-aside (sw_01) are cut clean of their baked grid as `assets/sewer/mh_cover.png` /
  `mh_cover_open.png` (PD_ART). `mhArt571()` = mh_cover, else sv_manhole: used for the street entrances (drawManholes
  and the ground pass), the culvert outfall, and the street's decorative manholes (were black discs; skipped on
  entrance junctions so there is never two). Under the ladder in the sewer: mh_cover_open, 52 wide.
- **Steam** (`drawSteam571`, called before drawFly, not inside or underground): one baked 64px puff, five per
  entrance, rising 46 and drifting with a slow wind, alpha up to 0.36. Entrances only (and the culvert outfall).
- **Row-house roof** (Donny's six-house terrace): full = row_a_wide, mirrored = row_b_wide (640 wide); three-house
  halves = row_a_sq / row_b_sq / row_c_sq (middle, mirrored). Rows now draw _sq on square-ish lots (386 _sq city-wide).
- **Bedrolls**: hl_bedroll_a = patched blue blanket (h/w 0.50), _b = green quilt (1.06), _c = brown roll, new _d = blue
  roll; `TDW571` scales the group pick (b 0.78, the rolls 0.5) inside td546.

---

## LAYER 570 -- DONNY'S BATCH-3 ART IN: ROOF CUTS, THE SHED, ALLEY PROPS, THE RED CAB, REY'S JUMPSUIT AND HEAD

`zx_art_570.zip` (assets/, 55 files). Tests `t_569b.py` (roof cuts: 388 of 989 plated buildings now draw a cut -- 337 _sq,
29 _tall, 22 _wide), `t_569c.py` (Rey in the jumpsuit, standing and walking).
- **Roof cuts**: Donny's 27-roof sheet + the 7 with storefronts (walls cut off at the parapet) mapped by material onto
  plates as `<plate>_sq / _tall / _wide` (the sheet was generic, not per-plate, so the mapping is by look: tar/HVAC roofs to
  shop/office/bar/down, gables to house1/farmhouse/town_c, red tile to barn_a/shophouse_c, the curved grey barn (wall cut)
  to barn_b, the Virgin to barrio_c_tall, the long slate (wall cut) and the two wide storefront roofs to row_a/b/c_wide).
  `roofVar569` now also tries `_wide`. The shop cuts have no GROCERY/LIQUOR signs -- the base plate keeps them.
- **rf_g_shed_b** (NOT shed_a -- PROMPTS_569 named the wrong file; the brick office with the door is shed_b): replaced
  with Donny's top-down one, 427 wide.
- **Alley props** replaced (al2_mattress, al_dumpster, al_dumpster_open, al2_crates, al_can, al_can_open), and their
  boxes follow the new shapes: cans 21x21 (open 26x25), dumpsters 64x48 closed / 64x62 open (closing one fixes its h),
  CLS mattress 62x42, crates 58x35, the camp mattress aspect 0.67.
- **tr_cab_red**: Donny's 80s cab-over, turned 180 at bake time to the tractors' nose-DOWN convention (TRACTOR_FLIP),
  back in TRACTORS. **tr_cab_brown** was the same squashed modern landscape cab as the old red (drawn 44x104 from an
  827x504 plate), so it is now the red one recoloured brown. Originals kept out of the build.
- **Rey in the jumpsuit** (`reyInTorso569`): yt_player_in is now the orange top with no head or arms; with yt_rey_head
  (new PD_ART key) it is composed onto a 355x407 canvas (top at y 92, head 136 wide at y 2) cached as
  `ar_torso_rey_in569`, which reyArms("yt_player_in") returns with orange sleeves; until both load, the Kestrel blues.
  Legs: new set `lg_walk_orange_0..2` (work trousers recoloured), picked when that torso is on.
- **pt_rey** replaced (360x374; every user draws it cover-fit).
- STILL OPEN: Jose's pickup at the curb (unverified); bedrolls (hl_bedroll_a/b/c) never came; rows have no _sq cut.

---

## LAYER 569 -- BATCH 3: ROOF CUTS, HEADLIGHTS, THE RED SEMI OUT; PROMPTS_569

`t_569.py` (night headlight shot), `t_569b.py` (roof cut pick, tested with a throwaway rf_g_barn_a_sq.png: 32 of 41 barns switched).
- **Roof cuts** (`roofVar569`, `rvImg569`, called at the end of `platedRoof`): when a plate is more than ~28% off its footprint's
  aspect (turned plates measured turned), the game tries `assets/roofs/<plate>_sq.png` and `<plate>_tall.png` and draws
  whichever of the three is closest. Missing cuts fail to load once and are never asked for again. Landmark roofKeys
  (anything not rf_g_/rf_z_) are exempt. The minimap gets the same pick through `G.mapRoof564`.
- **Headlights** (`beam569`): the cone starts AT the front bumper, as wide as the car's nose, and opens out from there --
  player car (`c._L569` / `c._W569` set in drawCar) and traffic (`v.len` / `v.w`). It used to start inside the hood and
  paint across the car.
- **Red semi** (`tr_cab_red`) removed from the TRACTORS pool until the new art lands (it was a modern cab at an angle).
- **PROMPTS_569.md**: roof cuts per plate (table, from a footprint audit), rf_g_shed_a redo (the brick office was drawn
  front-on), mattress / dumpsters / crates / cans / bedrolls top-down, the red semi, Rey head (`yt_rey_head`, NOT wired
  yet), prison top with no tattoos, new pt_rey portrait.
- STILL OPEN from the long list: Jose's pickup parking at the curb (unverified), wiring `yt_rey_head` when it arrives,
  putting tr_cab_red back in TRACTORS.

---

## LAYER 568 -- BATCH 2: THE TRAFFIC STOP AND THE LICENSE; DRIVERS; THE STATION'S WALLS; THE LOT; THE CLOSET; YOUR ID

`l568a.py` + inline. No new art (cop faces are assets/police/pt_cop_1..12).
- **The traffic stop** (`G.tsInfraction568`, `update568`, `draw568`, `G.tsPanel568` / `G.tsPick568`, panel `ts568`): a car
  bump (-dot > 150) seen by a cop (`copsWatching`) with no heat and no stop running -> a cruiser 420 behind follows the
  road you drove (your trail) and PULL OVER · 10 counts over you. Stop (under 14 for 0.8 s) -> he pulls in 150 behind,
  two officers walk to your windows (drawCop) -> the wheel (`stay: 1`, the centre doesn't close it): WHY (one of three
  right +1, I DON'T KNOW 0, wrong -1) -> LICENSE (valid +1, suspended / none -2, forged: passes at its quality % (+1)
  or "this isn't you" = heat + the fake's taken) -> three answers, 8 s each (timeout -1), from five styles; each cop is
  one of `TS_PERS` (by the book / end of shift / hothead / rookie / on the take) with a style he likes (+1, a bribe to
  the crooked one +2, $20) and one he hates (-1; a bribe to by-the-book = heat). Score >= 2 a warning; 0-1 $75; under
  0 $150. Can't pay: the car is TOWED to the precinct lot (`g.car.impound568` = fine + 100; E at it pays). Drive off
  (or don't stop in 10 s): he chases on your trail; 6 s over 1100 away (or 90 s) and he's lost -- another bump while
  he's on you = real heat (witnessed 1). Each ticket is a point; 3 suspends a real license. `G.ts568T()`.
- **The license** (`g.lic568`: Rey starts SUSPENDED): a card LEFT of the car card -- KESTREL · DRIVER, the name, points,
  the stamp (VALID / SUSPENDED / NO LICENSE / Q n). The forger now also does MAKE ME A DRIVER'S LICENSE · $300 (quality
  from hands/brains).
- **Drivers**: your driver (autopilot) checks for anyone on foot in his path (40 wide, 120 + speed*0.7 ahead) and stops
  short -- always, chase or not. Street traffic looks further (108 + speed*0.45) and wider (40). DRIVE TO pulls in at
  the KERB ACROSS the street, parked along it the right way round (`curbAcross568`, `A.park568`).
- **People don't walk through each other** (`separatePeds568`: a 40 grid, anyone within 20 eased apart; they step
  round you).
- **The station shop has walls** (`gasWalls568`, solid in collideBuildings, drawn) with the door on the front by the
  counter -- nothing drives through it now.
- **The car lot**: the lot's cars are solid (collideBuildings, from `g.dealersB`), and the one you hot-wire on First Day
  Out is on the outside row at an end, so you can drive it off.
- **The closet**: the 1969 clothes and Leroy's are gone; the arms-in-the-plate fits (work vest, leather, shorts) drawn
  1.42x -- they'd shrunk. **No bald Rey**: in prison he's his own head on the work torso in Kestrel blues
  (`REY_CODED.yt_player_in`) until the new prison outfit lands.
- **Your ID** opens on the card art (`drawReyId568`): the blank card, your picture (pt_rey), name, number, PAROLED (or the
  fake's quality).
- Test `t/t_568.py`.

---

## LAYER 567 -- BATCH 1 OF DONNY'S LIST: SIZES, WHAT'S OVER WHAT, THE MINIMAP, THE ZOOM

Inline reps. No new art.
- **Nobody bigger than Rey** (drawYouth0): an armless-torso plate (AS, own `wid`) ignores `tall` > 1 unless `p.hero` / `p.big`
  -- Jose (1.25), and everyone drawn at 1.2, are Rey's size now. A whole-body plate is capped at 40 across (Tony was
  54). Eddie 0.84. The alley dice crews and the court dice drawn at 0.74 (58 x 72). Hook `G.ytSizeT(yt, tall)`.
- **Wrecks**: Joe's yard wrecks 50 wide (were 84) -- the scrap car outside Joe's / on the drive from Kestrel.
- **Tables** (`drawTableOver567`): sat at a table/desk/counter/bar PROP within 46 of your seat, it's drawn again over
  you; the chair stays under. (Tables painted into a floor picture can't be lifted out -- those still sit under you.)
- **Ground under you**: every lot's parking/drive (`drawParking`) is drawn in a ground pass before the sorted list
  (`g.parkDone567` skips it in drawBuildingExt) -- driveways, sidewalks of lots, the scrapyard's stalls. Alley graffiti
  (`flat`) drawn first in drawAlleys so crates and cans sit on it.
- **Stoplights under the expressway** aren't drawn over the deck (only from street level right underneath).
- **Talk on top** (`bubble` queues; `flushBubbles567` after the night pass and before the vignette).
- **Rey's walking legs** tucked under the torso (0.06h instead of 0.2h).
- **A bike that blows** throws 1-2 tyres and its engine (sy_motors_a), six flamelets.
- **Minimap**: drawn from `mapBase` (the big map's picture: streets, water, every roof) so it follows the city; the El
  and the spur in red; no dots for cars and walkers (police only, flashing); shapes per kind (gas square, shop and club
  diamond, garage triangle, home house, race flag, your car square) and YOU a blinking star.
- **Zoom**: a vertical slider under the money and juice (up = closer); the old one at the top is hidden.
- **Manholes** on the street use the cover art (sv_manhole). **Free gas** with a driver at the wheel or riding with you.
  **Sleeping** clears heat and any chase. **Drivers' faces**: crewFace uses pt_<name> (Eddie's talking picture).
- **No car parks on a roof**: spawnParked rejects a spot inside any building (+30) or in water.

---

## LAYER 566 -- YOUR TRAIN, TRUCK AND ROOF ART IN; RIDERS CROUCHED; EVERY BIKE A BIKE'S SIZE

Inline + `l566`-style reps. Art `zx_art_566.zip` (54 files).
- **Train**: `el_eng_roof.png`, `el_roof.png`, `el_roof2.png`, `el_roof3.png` (the registry now points at the .png; el_roof4
  = el_roof), `sp_shuttle_roof.png` (all three shuttle cars), `sp_platform.png` -- a side-platform strip tiled down
  EVERY station's side platforms by `platStrip566` (yellow line turned to the track; the loop's eight and the spur's two),
  `sp_stairs.png` at the spur's stair feet. The little corner piece on the sheet wasn't used.
- **Food trucks**: your six top-down trucks -> `assets/city/ft_*_top.png` (drawn 150 long). The side-view trucks on the
  roof sheet were not used.
- **Roofs** (fitted to the OLD file's pixel size so footprints don't change; turned 90 where the new one came the other
  way round: ct_ot_church, ct_ot_tavern, ct_ot_ten2, rf_g_walkup_b/c, rf_z_down_b; the dome set on a flat stone roof to
  the old wide shape): rf_g_walkup_a/b/c, rf_brick_apt, ct_walkup, ct_ot_ten1/2, rf_g_shophouse_c, rf_z_up_c,
  rf_z_down_b/c, rf_union_terminal, rf_one_asylum, rf_one_cityhall, rf_one_kestrel, ct_gomez, ct_ot_church, ct_dome,
  ct_ot_tavern, ct_works, rf_z_barrio_c, rf_po_gate, rf_ard_colonial_a-d, rf_g_house1_a-c, rf_g_tower_c, rf_z_ind_a-c,
  rf_z_proj_a, rf_z_irish_a. (b/c/d variants of colonial, house1 and ind are the new one mirrored and tinted.) Still
  the old art: ct_church, rf_g_cabin_d.
- **Bikes**: `RIDE_K566` 0.7 -- anyone on a bike is drawn crouched at 0.7 of standing, back on the saddle (you, gang
  riders, motor cops). Every bike 56-66 long: yours 62 (was 50), motor cops 62 (was 88), Kuru's 66 (was 96), any bike
  skin clamped. A bike that wrecks or burns becomes `MOTO_WRECK566` (top-down rusted bike, `wk_moto_*_v`, 62 long)
  instead of a car shell, and burns smaller.
- Tests `t/t_566.py` (bikes), `t_566b.py` (truck, station strips).

---

## LAYER 565 -- CARS BURN; WRECKS TOP-DOWN AND CAR-SIZED; THE AIRPORT SPUR; SEATS ON THE TRAIN

`l565a.py`, `l565b.py` + inline. Art `zx_art_565.zip` (26 files). Prompts: `PROMPTS_565.md`.
- **Your flame sheet** -> `assets/fx/fx_fire16.png` (16 frames, 96 square: 0-4 catching, 5-12 burning (ping-pong), 13-15
  dying; `flame565(x, y, size, t, left, seed)` picks the frame). **Your car parts** (GrabCut, then charred: 80% soot
  tint, soot blotches, embers on the rim) -> `assets/fx/db_{tire_a,tire_b,door,steer,fan,battery,disc,muffler}.png`
  (`DEB565`). The hood and the bumper didn't cut clean off the grid and were left out.
- **A car that goes up** (`carBoom` -> `fire565Boom`): the nearest car within 60 becomes a HUSK (`v.husk565`, dead,
  parked, drawn darkened -- or the burnt wreck shell once `makeWreck` takes it, its life raised to 240) with four flames
  along it for **120 s** (`F565.car`), then smoke 60 s. Throws 5-8 parts (`g.deb565`: arc, one bounce, land, burn 22-40 s,
  lie charred 150 s) and 14 flamelets (`g.flm565`, burn 7-16 s). Anything burning on the ground (`ignite565`): you
  (5 hp/s / TOUGH, flames on you), people (`p.burn565` 6 s, they panic), cars (dmg +0.05/s -> they cook toward going up
  themselves), and a part or flamelet that LANDS on a building starts a roof fire there (`g.bfire565`, 30-60 s, up to 40)
  -- drawn only, the building takes no damage. No car under the blast: a ground fire 60 s. `G.boom565T(x, y)`,
  `G.fire565T()`. A cooked-off car no longer vanishes (the splice is gone; it husks).
- **Wrecks**: the scrapyard's `sy_wreck_*` were side-on photos -> top-down plates `assets/scrap/wk_sy_*` (the bs_wreck
  shells, the sov burnt shells, a crushed one, the crew van rusted), props resized to a car (118 x 52; crushed 80 x 58) and
  nudged off each other. The trailer court's `tc_deadcar_*` -> rusted top-down sedan / wagon / pickup (`wk_tc_*`) drawn
  112 long (they were 46). The body shops' `bs_wreck` drawn 50 wide (was 84 -- twice a car). `moto_wreck_a/b` ->
  top-down rusted bikes (`wk_moto_*`). `vh_arson_van.png` had its magenta still on -- keyed.
- **Food trucks**: the side-on pictures are out. `drawFoodTrucks` takes `<k>_top` (assets/city/ft_*_top.png -- PROMPTS_565
  section 1) and until they land the old top-down plates (`<k>_old`, the .webp: four vans, two carts), van-length.
- **THE AIRPORT SPUR** (`spur()`, `spurPos`, `updateSpur`, `drawSpur`): from the loop's SE corner east along 21st St to
  26th Ave and south to the terminal (15.3k long). SPUR JUNCTION (a walk from SOUTH CROSS) and AIRPORT. Stairs: walk in =
  up, E at a stair top = down, walking off the edge = the drop. The clerk (E) opens the talk wheel: SHUTTLE TO ... $2 ->
  you sit in the middle car (`g.spurRide`, no control), the three-car shuttle (`g.spurT`, t.d = middle car) runs at 320,
  arrives, and you're on that platform. E while riding skips to arrival. Shuttle shuttles end to end on its own the rest
  of the time. `sp_shuttle_roof` / `sp_platform` are drawn if they land. `G.spurT565()`.
- **Seats on the loop train**: riders sit on the seat rows (v +-19, 24 apart; 1 in 5 stands in the aisle). Aboard and
  moving, E sits you on the nearest seat facing the aisle (`g.trainSit565`, no walking), E again stands; stopped and
  standing, E steps off as before.
- Tests `t/t_565.py` (spur ride), `t_565a` (a car going up), `t_565c` (sitting), `t_565e` (roof fires).

---

## LAYER 564 -- TALK ON A WHEEL; THE SKATE PARK FILLED; THE TERMINAL'S MARKINGS; THE CITY ON THE MAP

`l564a.py`, `l564b.py` + inline.
- **Talk wheel** (`talkWheel564(P)`, render before the old pick panel): any panel with a `face` (and no card options) or
  with `wheel: 1`, 1-15 options, draws as a ring -- what they said in a box above, the options round the edge as pills
  (a card/icon shows its picture), the face in the centre with the leave line (`close` / NOT NOW / LEAVE / BACK / OK...).
  Same pad code as the action wheel (`[data-pickradial]`; stick points, A takes, B = `pickFn("close")` via
  `[data-talkwheel]`). Over 15 options or card tables stay the list.
- **Driver**: WHO DRIVES is a wheel of faces (`wheel: 1`); the orders are 7-10 slots -- DRIVE TO…, WHICH WAY… (N/E/S/W,
  circle, just drive: `ccView "head"`), HOW FAST… (faster/normal/slower/crawl: `"speed"`), gas, Stan's, lose 'em, get us
  out, pull over, switch driver; CARRY ON in the centre. `ccar:v:<view>` opens a sub-wheel, BACK returns.
- **Skate park**: the east and south were bare slab. Added a street section (two ledges, a manual pad, a pyramid, a bank,
  a stair set with its rail, a kicker), a mini ramp west, a long north quarter, a long ledge on the way out (all
  rideable); bleachers, 8 light poles (pools of light at night), three painted walls, the SNACKS · WAX · TAPE shack by the
  gate, picnic tables, planters, more benches/bins (solid). The slab has patches, wheel arcs, oil and a painted SK8 logo.
- **Terminal forecourt** (`drawTerminalSurface`): a BUS ONLY lane in front of the bays (dashed centre, arrows, stop bars,
  three zebras), a kerbed island with planters, the TAXI rank, the car park in double rows with aisle arrows, P · SHORT
  STAY, IN / OUT, a footpath round the edge.
- **The map** (`mapBase(roofFn)`, 2048): pavements, centre lines, trees in the parks/cemetery/county, and every building
  with art drawn with its own roof plate (`G.mapRoof564` = platedRoof); the rest a roof tone by kind. Rebuilt up to six
  times, 4 s apart, while plates are still loading. Turf wash 0x55 -> 0x2e so the city shows through.
- **Signs**: a north-facing plated building was FLIPPED (scale 1,-1) -- GROCERY read backwards. It's turned 180 now.
- Expressway entrance signs skip a ramp with no finite foot. (The green street-name toast at the top of the screen is
  `drawStreetPop`, by design.)
- Test `t/t_564.py` (driver wheel + sub-wheel).

---

## LAYER 563 -- THE FLASHBACK'S SIZES; NOTHING STANDS IN ANYTHING ELSE; THE MISSIONS CHECKED

`l563a.py`, `l563b.py` + inline.
- **Sizes, 1969**: the cast's armless torsos were AS() at full W532 while young Rey (yt_rey69, an un-coded full plate) drew at
  0.82 -- Rochelle stood a head over him. Now `ARM_BY_YT` wid: Rochelle W532*0.8, Tiny / Damian / Julian / the cops W532*0.8;
  `YT_SCALE.yt_rey69` 1.3; Rochelle's bedroom `tall` 1.15 -> 1.1.
- **Overlaps** (`settle563(c)`, module level; run at the end of getCell and over every mark cell after placeMarks): a plain
  generated building inside another is dropped; a decor-mark store (`mark_ct_*`: ct_church, ct_walkup, ct_laundro,
  ct_policehq, ct_offices) inside a real building is dropped. The flashback's warehouse WAS `mark_ct_church`, half under
  the Old Town pawn (ot_pawn) -- the door took you into the pawn, no body. Also fixed: alley-block buildings under the Neon
  Flats houses (6,15)/(7,15), uptown's tower+wing stacking (9,0)/(11,0), civic (12,5)/(13,4), Hazelbrook houses in its
  stores. Left alone: two NAMED Old Town marks in each other -- the gym/church (2,1) and Gomez/tavern (2,2), as they've
  always been. (Sliding marks to a free spot was tried: Old Town's stone lanes put them on the paths.)
- `suWare` now prefers generated buildings over marks (+3000 for a mark key), and if the saved warehouse is gone it picks
  again and drops the cached body spot / box. Fresh pick: a store at (4,1).
- **Mission check** `t/t_563.py`: all 17 Rey story ids, every step's map target, tested against every building and fence in
  reach -- none inside anything.

---

## LAYER 562 -- CAN'T RUN ON THE PALM COURT CONCRETE

`l562.py`. Running itself was fine on the lot (232 by key, same as the street; no water, weight or NaN there). What stops
running is SNEAK: Y / C with no cover crouches you (layer 478), and coverFn never checked `g.inside`, so a Y in the flat
crouched Rey and he walked out still crouched -- slow, no run -- until a car stood him up (stepFoot clears it only off
foot). Now: a door (any change of `g.inside`) stands you up, RUN while moving stands you up, and a crouched hero has
"SNEAKING · Y / RUN TO STAND" under his feet. Test `t/t_562.py`.

---

## LAYER 561a-d -- KESTREL INTERMODAL; LIFE IN THE OLD TOWN COURTS; ALLEYS IN THE FOUR DISTRICTS; THE STATION SHOP

`l561a.py` .. `l561d.py` + inline. No new art.
- **#1 The old inland port** (PORT_CELLS 15-16 x 6-7) is KESTREL INTERMODAL: `yard561(c)` (cached) lays out two rail tracks
  with flatcars carrying 40-ft boxes, container stacks either side (drawStack538 depth trick, SOLID via collideBuildings),
  semis waiting (some loaded), a straddle carrier, lamps, the name board; `drawYard561` replaces drawPort. One 2-floor
  yard office ("KESTREL INTERMODAL") on (15,6); the other cells build nothing of their own. `G.yardT561()`.
- **#2 Old Town courts** (`drawCourts561`, overhead pass after drawMom560; `G.courtFn561` in the E chain): every court has a
  neighbour on her step 7am-10pm (`COURT_LADY561`): WHAT'S THE WORD (nearest alley dealer / dice), ANYBODY ASKING ABOUT ME
  (reads your heat), YOU NEVER SAW ME ($20, heat -1). By the hour (`courtScene561`, hashed per court): stickball kids in the
  turning circle (day), a man washing his car (day; WASH MY CAR $10 -- clears blood / `v.hit`, if your car is within 400),
  a cookout (evening; GRAB A PLATE once a day, +25 health), a dice game (late; the craps table). `G.courtT561()`.
- **#3 Alley blocks in Chinatown, the Sixth Ward (irish), La Perla (barrio) and Uptown**: 60% of their blocks (hash 561)
  skip their own branch and take the alley block, built in their own kinds -- shophouse terraces (retail), row houses,
  walk-ups (2-4 floors), a tower or office + retail wing with a lot. Back doors and fire escapes come with it.
  ALLEY_ZONES now includes chinatown|irish|barrio (trash, alley people, camps).
- **#4 The station shop** (`drawGasClerk561` from drawGasRoofs, `G.gasFn561`, panel `gas561`): a clerk behind the counter;
  coffee (stamina full), candy (+10 hp), smokes, a scratcher ($1: 2% $500, 8% $20, 15% $2), a filled gas can (your car's tank
  full); with a gun out ROB THE TILL ($120-300, refills each day, witnessed -- the police come). `G.gasT561()`.
- Test `t/t_561.py`.

---

## LAYER 560 -- CLEAR FLOOR AT THE SHOP BACK DOORS; FIRE ESCAPES OVERHEAD; REY'S MOM

Inline. Art `zx_art_560.zip`: the ten int_* shop floors re-saved with a patch of their own clean floor tiled over each back door
spot (`PATCH560`, fractions; sources `cut/s560/patch.json`), assets/arms/ar_torso_rey_mom (Donny's sheet), assets/crew/pt_rey_mom.
- `carve560(solids, patch)` cuts the patched rectangle out of a shop's solids, so the way to the back door is clear.
- **Fire escapes overhead**: on the ground only the landing's shadow and the drop ladder (`drawFireFoot560`, E still at its
  foot); the landing (`fe_landing`) is drawn AFTER the people (`drawFireOver560`, after drawBizExtras), hung off the wall,
  45% see-through when you're within 80 of it. Hidden from the building you're standing on the roof of.
- **Rey's Mom**: `yt_rey_mom` (long sleeves, blue cardigan) + `pt_rey_mom`, in DAD'S CAR; drawn in the overhead pass
  (`drawMom560`) 60 out from her door -- the house plate used to cover her.
- Test `t/t_560.py`.

---

## LAYER 559a-b -- STAIRS ARE PICTURES; THE CROPPED SHOP DOOR; SIDE JOB: DAD'S CAR

Inline + `l559b.py`. Art `zx_art_559.zip`: assets/interiors/st_wood_up, st_wood_2 (dark half down / light half up), st_conc,
st_lino (cropped off Donny's stair sheet, the white landing cut off), dr_shop_door (cropped from int_pawn_b's door),
dr_shop_double (int_diner_b's kitchen doors).
- `drawStair559(st, floor, b)` draws EVERY building's stair box from the pictures (left half = the flight down, right
  half = up, a half that goes nowhere = a landing; turned along a tall box); `stairSet559`: wood for homes / bars /
  diners / clubs, concrete for towers / offices / civic, lino for the rest. Falls back to the drawn flight.
- The painted shops' back door draws `dr_shop_door`.
- **DAD'S CAR** (side job): available once THE SCRAPYARD is done and Mom's first letter was read in (`g.aptMailIn`). A
  second letter arrives. MOM'S HOUSE (`reyMomB`: a hood house with a driveway near Palm Court), Mom on the front step
  (`yt_hire_forger_4` plate for now -- a Mom portrait/torso is owed). E: three lines about his father, TAKE THE KEYS.
  The garage on her driveway (`dadGarage559`, drawn shut / open): E opens it, the grey convertible's inside, nose to the
  door; drive it 230 out -> SIDE JOB COMPLETE, `g.dadCarDone`. Only then does the convertible live in the Palm Court
  stalls (`convHome551` gated). Hooks `G.dadT559()`. Test `t/t_559.py`.

---

## LAYER 558 -- PAINTED SHOPS: SMALLER, A BACK DOOR, SLIM STAIRS BY THE ENTRANCE

Inline. No art (stair art prompt given; `STAIR558` is drawn with the plan's flight until then).
- `SHOP557` 820 x 448 -> 690 x 377 (furniture read too big against the people).
- **Back doors** (`BACK558[key]` = [wall top|left|right, how far along]): a spot on each picture's back / side wall that is
  floor (diner_b's kitchen doors, the pawn shops' back corners, the bars' side gaps...). Drawn as a doorway (`drawBack558`,
  from drawShopMask557), E within 70 (`G.back558Fn`, in the E chain after the jukebox) puts you outside the BUILDING's back
  wall (`backSide`), 36 out. `G.back558T()`.
- **Stairs** (`STAIR558[key]` = a slim strip along the entrance wall, fractions): a shop with floors above has its ground
  floor `pl.stair` moved there (left half down, right half up as ever; `toStairFn` puts you on the upper floor's own stair),
  the old stair props dropped.
- FIX: the big-room branch now sets `pl.artRot` BEFORE placing anything with `artAt` (the back door / stairs were being
  placed for an unturned picture).
- Tests `t/t_558.py`, `t_558b.py`.

---

## LAYER 557a-b -- THE TEN PAINTED SHOPS ARE IN; BIGGER INSIDE; THE JUKEBOX

`l557a.py`, `l557b.py` + inline. Art `zx_art_557.zip`: assets/interiors/int_{grocery,bar,liquor,diner,pawn}_{a,b} (Donny's ten
floors; diner_a's "ENTRANCE DOOR" lettering painted out). Sources `cut/s557/`. Loaded at boot (BOOT_ART_RE).
- `INT556` now holds all ten measured: solids, seats [fx, fy, facing, kind], counter, browse points, `jukebox` (bar_a, diner_a).
- **Bigger inside** (`SHOP557` = 820 x 448, the pictures' proportion): a painted shop's floor is laid out at that size (or
  the footprint's, if bigger), its entrance edge centred on the street door and running back from it -- past the
  footprint; `pl.walls` become four walls round it with a 76 gap at the door. `drawShopMask557` (from drawBizExtras)
  blacks out everything outside it. The door / E-to-leave is unchanged. The generated plan's stairs stay where they were
  (multi-floor shops), drawn over the picture.
- If the picture loads after you walked in, the shop refits and its people are rebuilt (`g.shop = null`).
- Painted seats don't get a drawn seat under them (`seatK "painted"`).
- **THE JUKEBOX**: E within 70 -> panel `juke557`: six records ($1 each -- band1-3, barrio, irish, uptown tracks with
  invented titles), PULL THE PLUG. `g.juke557 = { b, k }` overrides the music (ahead of prison/det) while you're in that
  building; a few customers react. `G.jukeT557()`.
- STILL OPEN: back doors for the painted shops (Donny: a small side room cut in where the back wall has no opening,
  or a door painted in); jukebox in bar_b / diner_b (none in the art).
- Tests `t/t_557.py` (all eight found shops), `t_557b.py` (jukebox, leaving).

---

## LAYER 556a-b -- PEOPLE SIT DOWN; THE PAINTED-SHOP SYSTEM (art owed)

`l556a.py`, `l556b.py` + inline. No art yet.
- **Seated**: `bizSeats(pl, r, cr)` returns [x, y, facing, kind] -- chairs either side of a table (by its long axis) facing
  it, stools facing the counter room, booths. Seated customers keep `seatA` / `seatK`, never wander (home = seat), can't be
  shoved by the player, and draw with their seat under them (`drawSeat556`: stool / chair with its back away from the
  table / booth shadow), turned to face the table (civ `ang` / `dir8` set), 0.9 size, standing frame.
- **Painted shops** (`INT556_KEYS`: grocery, bar (bar/pub/tavern), liquor, diner (BIZ_ARCH diner), pawn; two pictures each,
  `int_<a>_a/b`, OPTIONAL_ART): `shopArt556(b)` from `makeBizFolk` gives a shop its painted floor ONLY when the picture is
  loaded AND `INT556[key]` holds its measurements { solids, seats [[fx,fy,a,kind]], counter [fx,fy], pts }. Then the
  floor turns so the picture's bottom edge (the entrance) meets the door (`b.intFace556`), the whole picture is one room
  (`shop556`), staff are clamped into it, seats / browse points come from the table. Tested with a stand-in picture.
  NEXT: when the 10 pictures come, measure each into INT556 (+ ART2_SOLID via shopArt556).
- Hooks `G.shopArtT556(key, meta)`. Tests `t/t_556.py` (a bar, pawn, grocery, diner), `t_556b.py` (stand-in painted diner).

---

## LAYER 555a -- SUNSET POINT (the freeway's end is a lookout)

`l555a.py` + inline. `drawFwyEnd554` now draws the last 520 of each dead-end leg as a car park on the deck: lanes painted out,
angled stalls both sides, an aisle line, chain-link along the shore edge (fn_post caps), two lamps that glow at night, two
benches facing the water, two parked cars (a third at night), and a SUNSET POINT / CLOSED AFTER DARK board (lettering
counter-rotated so it reads the right way at either end). The barrier at the end (layer 554) stays. Test `t/t_555.py`.

---

## LAYER 554a-c -- THE FREEWAY ENDS AT THE SHORE; A RESPRAY YOU CAN SEE (AND CHOOSE)

`l554a.py` .. `l554c.py` + inline. No art.
- **Freeway ends** (`fwyEnds554(vert, L)` -> [lo, hi] along the leg; cached; `fwyDry554`): walked in from both map edges
  until the deck's centre and both edges are on land (`waterDepth`). `drawViaduct` only draws [lo, hi] and puts a closed
  end on each (`drawFwyEnd554`: concrete wall, yellow/black stripes, ROAD ENDS board); the cell generator adds a
  barrier across the deck there (`fwyEnd: 1`); `rampList` drops any ramp that starts, lands or runs over water or off the
  dry stretch; freeway traffic past an end is despawned. Before: both E/W legs ran out over the west and east water and
  the west interchange's ramps came down in the sea.
- **Respray** (`carTint554(img, hex)`, cached per plate per colour): the commonest saturated hue on the plate is the
  body colour and is re-lit in the new one (shading kept); a white / grey / black car has its neutral mid-tones re-lit.
  `drawBody` uses it for any vehicle with `v.tint` (traffic, parked, yours). Entering a car takes ITS tint, not the last
  car's. Stan's garage has RESPRAY ($400) back (plates had replaced it in 511) with a colour list (`PAINT554`, 14
  colours; `rep:paintmenu`, `rep:paint:<hex>`). The convertible still uses its grey plate path. `G.carTintT554(k, hex)`.
- Tests `t/t_554.py`, `t_554b.py`.

---

## LAYER 553 -- TEN MEN REDRAWN ARMLESS

Inline. Donny's sheet (sources `cut/s553/`) replaces the machine cuts of enforcer_1/2, fence_1/2/3, locksmith_1/2/3, thief_2,
dealer_1 (assets/arms/ar_torso_hire_*). They have shoulder caps like the women, so `HIRE_R553` re-registers them with their
own set / skin / sleeve, wid W532*0.72 and the default arm position (no armX). Portraits unchanged.
`zx_art_today.zip` = every asset file touched on 2026-10-19 (layers 543-553) in one zip.

---

## LAYER 552 -- THE MEN OF THE TRADES ON THE SHARED ARMS; THE WOMEN'S LAST FACES

Inline patches (no lNNN script). Art `zx_art_552.zip`: assets/arms/ar_torso_hire_<role>_1/2/3 (42 -- every man except the
hacker), assets/hires/pt_hire_<role>_4/5 for enforcer..locksmith (sheet B's portraits, replacing the torso placeholders).
- The men were RECUT BY MACHINE from their own plates (`cut/armless552.py`, `armless552b.py`): below 30% of the height the
  outer columns are cleared at the arm/torso gap (coverage dip in the lower body, else 17.5% each side), the shoulders
  rounded over the 10% above, the largest piece kept. Skin and sleeve sampled from the old plate's hands and arms (skin
  x0.85), set "bare" when sleeve ~ skin else "jacket" -> `HIRE_M552` -> ARM_BY_YT "yt_hire_<role>_<v>" (wid W532*0.8,
  `armX: 0.5`). `drawArms525` takes `A.armX` (default 0.40): a plate cut at the sleeve needs its arms at its edge.
- The old yt_hire plates stay (the fallback while the torsos load, and the source if a recut needs redoing). Men holding
  things across the chest (the forger's book, the fence's watch, the locksmith's tools) keep them.

---

## LAYER 551a-b -- THE WOMEN OF THE TRADES; REY'S CONVERTIBLE; THE NEW VEST

`l551a.py`, `l551b.py` + inline (seated legs, women's wid). Art `zx_art_551.zip`: assets/arms/ar_torso_hire_<role>_4/5 (28 armless
torsos, two sheets), assets/hires/pt_hire_<role>_4/5 (sheet A's 14 faces cut from their frames; sheet B's 14 are the torso on a
dark plate -- PORTRAITS OWED for enforcer, safecracker, fence, fixer, chemist, thief, locksmith), assets/vehicles/vh_conv_up /
vh_conv_down (rotated so the front is up), assets/arms/ar_vest_kevlar (the new flat vest; the old one kept as _old,
_kevlar2 = the new one's source cut). Sources `cut/s551/`. The leg pieces on the misc sheet were not used (the 549 sets are
the same trousers).
- **Hires 4 and 5 are women** (`HIRE_W551[role]` = [set, skin, sleeve] x2 -> ARM_BY_YT "yt_hire_<role>_4/5", wid W532*0.72
  since the plates are narrower). The board's pool rolls 1-5 (the hacker still 1-3), women get `HIRE_FIRST_F551` names
  (hireName too), the payroll "hire" path rolls 1-5. `basePeople` no longer swaps v4/5 for a near trade's plate.
- **THE CONVERTIBLE** (`g.convM` = { k "vh_conv", len 118, w 45, conv, roofDown }): parked in the Palm Court stalls
  (`convHome551`, from drawAptLot) whenever it isn't on the street and isn't the car you left somewhere; owner "player"
  (no lock wheel), plate REY 1. `drawBody` swaps in `convImg551(roofDown, tint)` -- the grey plate re-lit in the colour
  (v.tint / M.tint / g.convTint), chrome, the black top and the red seats left alone. ROOF DOWN / ROOF UP on the action
  wheel when you're in it or beside it (`G.convNear551`, id `conv:roof`). Roof down: you at the wheel and up to three of
  your people (g.pfol) drawn small (0.72) in the seats (`drawConvSeats551`, `CONV_SEATS551`; no legs while seated --
  `carSeat` / `g.convSeat`). The respray shop gives it one of twelve colours and keeps it (g.convTint).
- Hooks `G.convT551()`, `G.convNear551()`. Tests `t/t_551.py` (stall, in, roof, paint), `t_551b.py` (eight women).

---

## LAYER 550a -- BARE LEGS TAKE THE WEARER'S SKIN

`l550a.py`. `legTint550(key, skin)`: every warm skin pixel of a leg plate (R > G > B, R-B 45..150) re-lit in the wearer's
skin, keeping its shading against the plate's own average skin; cached per key+skin. Used for the leg plates whose key
says boxers / skirt / ripped, with the skin of the man's arm set (AS skins un-done from their 0.78). Rey in shorts now has
Rey's legs.

---

## LAYER 549a -- THE SUPPRESSED .22'S ART, THE VEST PLATE, REY'S WALKING LEGS, PABLO'S SIZE, THE NEST'S SIGN

`l549a.py` + inline (stamina NaN guard, VEST549 / LEGW549 tuned). Art `zx_art_549.zip`: assets/weapons/hw_pistol_sd (top-down,
MIRRORED so the muzzle points left like every hw plate), assets/ui/wi_pistol_sd (side view), assets/arms/ar_vest_kevlar,
assets/arms/lg_walk_{jeansblk, track, slacks, work, jeansblue, boxers}_{0,1,2} (1 = feet together). Sources `cut/s549/`.
- pistol_sd draws its own plate now (HW_K 1.9, alias removed), wheel / overhead icon wi_pistol_sd.
- The vest plate (`VEST549` = [0.50 of the torso width, top at 0.08h above the middle]) -- over the chest, under the chin.
- **Walking legs**: `p.legSet` in drawYouth0 picks `lg_walk_<set>_<0|1|2>` by the stride (standing: 1), sized `LEGW549`
  [0.44 of the torso width, top 0.36]. Rey's outfits -> sets (`REY_LEGS548`): street & leather black jeans, track, suit
  slacks, work tan work pants, work vest blue jeans, boxers. Passed in Rey's drawYouth call.
- ARM_SETS leroy / pablo scale 1.24 -> 0.99 (they never got 540's shrink: "the new Pablo's too big"). BOOT_ART_RE now
  loads ar_torso_*, the hang / punch / gun arms and the walking legs at boot -- the old plate showed until they loaded.
- The Boznov fronts (Nest, Happy Hippy, Raven Auto) prefer a building with its door on the SOUTH side (+2400 otherwise):
  a north door mirrored the plate and the NEST's sign read backwards. Picked per session, so it moves in old saves too.
- `stepFoot`: maxStamina / stamina repaired if not finite (a NaN stamina never runs). Running near the apartment did NOT
  reproduce here (1A's rooms are just small) -- open.

---

## LAYER 548a-b -- REY CAN DRAW HIS GUNS; THE SUPPRESSED .22; THE KEVLAR VEST YOU WEAR; THE CLOSET'S SHORTS AND DEFAULTS

`l548a.py`, `l548b.py` + inline (vest-on-player check, boxers key, OPTIONAL_ART).
- **THE BUG**: the weapon wheel and `G.wheelWeapon` gated guns with `lionPowersOn()` (the Lion, NOT prison mode) -- so in
  Rey's game every gun on the rack (bought, the back room's .22) was filtered off the wheel and refused. New
  `gunsOk548()` = the Lion, or prison mode that isn't the student / the kid. Used by the wheel, wheelWeapon and applyItem.
- **pistol_sd, THE SUPPRESSED .22**: WPN_STAT {rate .38, range 330, dmg 1.9, spread .09}, 10 rounds, WPN_SCALE 1.2.
  Borrows the 9mm's plates (WPN / WPN2 / WPN_ICON getter / OVERHEAD_ICON / HW_ALIAS) until its art comes. Firing it: no
  witness unless a cop's cone has you (`copSeesPt537`), scatter 110 not 460, a 0.13 cough, small flash. RIGHT TO ARMS
  now gives pistol_sd (old saves with `silencerHave` get it on the rack when the wheel opens). The gun counter sells it
  UNDER THE COUNTER, $650.
- **THE VEST** (`vestWear548(on)`, `G.vestWear548`): `g.vestHave` owned, `g.vestOn` worn -- +50 max/current health while on.
  Put on / take off: the weapon wheel ("PUT ON THE VEST", id `wsel:vest`) or the closet ("KEVLAR"). Bought at RIGHT TO
  ARMS (worn at once) or the gun counter ("KEVLAR VEST", $400, type `vest`). Drawn on him (`drawVest548`): a dark panel,
  straps, velcro band -- or the `ar_vest_kevlar` plate when it exists (OPTIONAL_ART, prompt given). Old saves: a vest
  bought before 548 (maxHp >= 150) counts as worn.
- **Closet**: UNDERSHIRT & SHORTS added (`REY_FITS.boxers`, the coded full plate). Defaults picked (`REY_COL0`): street
  black/grey, track maroon/white, suit charcoal/white, work tan/brown, work vest olive/white, leather black/grey, shorts
  royal blue. Only for outfits not yet recoloured -- a save keeps its own colours.
- Test `t/t_548.py`.

---

## LAYER 547a-b -- THE STREET PEOPLE (TORSOS + ARMS + LEG PLATES), MORE CAMP PROPS

`l547a.py`, `l547b.py` + an inline fix (TDZ: `TD546.sc_shelter` moved after TD546, the HL_PEOPLE loop after ARM_BY_YT --
the first build died at load with a blank title). Art: `zx_art_547.zip`:
- assets/arms/ar_torso_hl_{oldman, woman, vet, drunk, grey, junkie, hood, dealer, dealer2, girl} -- armless torsos in the
  ar_torso format (the shared arm sets do the arms, tinted per man: `HL_PEOPLE[k]` set / skin / sleeve);
- assets/dock/pt_hl_{oldman, woman, vet, drunk, junkie, hood, dealer, girl} -- faces (grey uses junkie's, dealer2 dealer's);
- assets/arms/lg_lie_{jeans, work, slacks, sweats, ripped, blanket, bag, skirt} (row 1 of the lying sheet; row 2 is a
  duplicate, not cut), lg_sit_{cross, knees, blanket}, lg_stand_{tan, jeans, green} (spare);
- assets/sewer/hl_{box, leanto, chair, papers, cans, tv, jug, dogbowl}. Sources `cut/s547/`.
- **Leg plates in `drawYouth0`**: `p.legK` (a key in `LEG547` = [width as share of the torso plate width, top as share of
  its height]) draws that plate under the torso instead of the drawn legs -- sized DOWN to the torso (lying ~0.46-0.54 of
  the plate's width). Without a loaded plate it falls back to the drawn legs.
- **Camps**: the sitters are street people (oldman / woman / vet / drunk / grey / junkie, no repeats in a camp) on sitting
  legs (`SIT_LEGS`), named from their own list, with their face in the camp panel; 60% of camps with a mattress have a
  SLEEPER lying along it (`lying`, `LIE_LEGS`) -- E: "Asleep on the mattress", leave $5 or let them sleep. New camp pieces:
  lawn chair, newspapers, cans, TV on a crate (solid), milk jug, dog bowl; sc_shelter now draws as the box shelter or the
  door lean-to.
- **The alley people** (`ALP547`): alp_homeless / alp_drunk / alp_junkie sit (sitting legs), alp_lookout / alp_dealer /
  alp_girl stand; they turn to watch you inside 160. The dealer's panel shows his face. The old pictures are the fallback.
- Test `t/t_547.py`.

---

## LAYER 546a -- THE CAMP KIT FROM DIRECTLY ABOVE

`l546a.py` (+ an inline fix: `it` is the for-of const in drawCamps, so the swapped width is `iw`). Art: `zx_art_546.zip` ->
assets/sewer/hl_* (21 plates from Donny's two top-down sheets, cut with `cut/keylib.py`, pink fringe killed; sources in
`cut/s546/`): hl_barrel_fire, hl_barrel_cold, hl_barrel_lid, hl_bucket_blue/white, hl_cart, hl_cardboard, hl_tarp,
hl_cookpot, hl_crate_radio, hl_case, hl_battery, hl_lantern, hl_lights_s, hl_lights_l, hl_bedroll_a/b/c, hl_sign,
hl_rags, hl_dog. `HL_ASP` holds their aspect ratios.
- `TD546` maps every old 3/4 camp plate (sc_*, and the alley clutter's al2_barrel / al2_cart) to its top-down plate and
  a width factor; `td546(k, w, x, y)` -> [key, width] (bedrolls pick a/b/c by position). Used by the SEWER camps
  (`drawCamps`), the ALLEY camps and the alley clutter (`drawAlleys`). Falls back to the old plate if the new one is
  missing. The alley camp's collision boxes are sized to the new plates; alley camps can now have the sleeping dog
  (hl_dog) and a rag pile (hl_rags). sc_shelter has no top-down plate -- it draws as a tarp.
- NOT USED YET: hl_case, hl_lights_l (spare).
- STILL OPEN: the camp PEOPLE (prompts given for armless torsos in the ar_torso format + faces + a lying-legs strip);
  until then the camps sit Sky plates.

---

## LAYER 545a-c -- STREET CRAPS AT THE TABLE; ARRESTED = MISSION FAILED; DRAWN DOORS; FENCES AND GATES; THE NEW LANDING

`l545a.py` .. `l545c.py` (+ small inline fixes). Art: `zx_art_545.zip` -> assets/alley: fe_landing_stair, fe_landing,
fe_dropladder (from the top-down fire-escape sheet, mesh holes keyed out, brick stripped), fn_post (post cap), fn_razor
(coil, greyed), and the door TEXTURES tx_door_wood / tx_door_steel / tx_door_rollup / tx_door_plate / tx_step (crops of
Donny's front-view door sheet, used as paint, not as plates). Sources kept in `cut/s545/`.
- **THE DICE GAME is a table** (`openTable("craps", ...)`, the card rooms' overlay): bet $5-$200 (-$25 -$5 +$5 +$25),
  ROLL = the come-out (7/11 natural pays even money, 2/3/12 craps, else THE POINT), then ROLL until the point (win) or a
  seven (seven-out). Dice tumble 0.5 s (`crapsRoll`), drawn dice with pips in the overlay, POINT shown. A street crew
  (`CRAPS_FOLK`, the card rooms' habits) bet beside you and leave when they're broke. Three wins running can bring
  "Them dice is loaded" from Big Tony. LEAVE / WALK AWAY as at the cards (mid-point walking forfeits the bet).
  The old `aldice` panel is unused.
- **ARRESTED ON A MISSION**: `arrestPlayer()` (and `downHero("arrest")`) with a story running -> `storyFail(..., "MISSION
  FAILED · ARRESTED")`. The panel: RETRY FROM CHECKPOINT, RESTART MISSION (new: `storyCk0`, the snapshot at the mission's
  start -- shown when a checkpoint has moved past it), QUIT MISSION (the arrest stands). The fail panel title now uses
  the slam's title. A crew job (`g.mis`) arrested ends as failed, "ARRESTED · THE JOB'S BLOWN".
- **Doors are DRAWN** (`doorLine544(x, y, side, open, k)`): local frame along the wall / out of it -- a dark frame, the door
  face foreshortened and painted with the texture (k 0 wood, 1 steel, 2 plate; alley blocks pick by hash), the gold sill
  line, the concrete step (tx_step). Open = black gap and the leaf swung out. Jobs' back doors are steel.
- **Fences** (`drawFence545`): mesh band with diamonds, a rail, a post cap every 64, razor coil on about a third of the
  non-hood runs. An ALLEY END is a GATE: two heavy posts, two leaves with an X brace, chain and padlock; E says OVER THE
  GATE. FIX: hood cells never drew their fences (the hood branch `continue`d before `drawFence`) -- they collided unseen.
- **Fire escapes** use `fe_landing_stair` (92 wide), fallback al_fire_escape.
- Tests `t/t_545.py` (craps rounds, arrest -> fail -> retry, city, gate), `t_545b.py` (arrest in WASH DAY -> fail ->
  restart), `t_545c.py` (doors close up).
- STILL OPEN: homeless / camp art that isn't top-down (prompts given: barrels, buckets, cart, shelter, tarp, sign,
  lantern, cookpot, radio crate, lamps, bedrolls, and the standing alley people).

---

## LAYER 544a-f -- THE ALLEY CAMPS; THE DICE CREWS FROM ABOVE; DOORS AS LINES; THE FIRE-ESCAPE PLATE

`l544a.py` .. `l544f.py` (after `l543f.py`). Art: `zx_art_544.zip` -> assets/alley/alp_dice2_a/b/c (three crews round a game,
from above, each on its own patch of ground -- cut from Donny's sheet with `cut/keylib.py`, 1px alpha erode + pink fringe killed).
- **The dice game** (`alp_dice` in `cellAlley`) now draws one of the three crews (`q.dv`), 78x96, set up 130-180 off the trash
  corner and clear of anything solid, one crew per 140. Every 4.5 s a pair of dice goes out across the ground and settles
  (`drawDice544`). Same E / panel as 543.
- **THE ALLEY CAMP** (`ALLEY_CAMP544`, `campIn544`, about one alley block in four): the sewer camp kit (`sc_*`) plus the alley
  mattress, laid against one wall -- cardboard, a shelter or tarp, mattress, bedrolls, cart, radio crate, bottles, sign, lantern
  (each rolled), a fire (barrel or cookpot, solid) with two buckets, and 1-3 people (Sky plates, facing the fire) with names
  (`CAMP_NAMES544`). Goes on the side under the LOWER roofs (tall roofs lean out over the alley with the depth trick and
  hid it); none where both sides are 4+ floors. Kept with the cell's alley list (the garbage truck leaves it be).
  The fire glows at night (`drawCampGlow544`, in the night-light pass after `drawLights`), sparks always.
  **E at a camper** -> panel `alcamp`: GIVE $1 / $5 (a line, a bubble), GIVE $20 = "WHAT'S THE WORD?" (`campWord544`: the
  nearest alley dealer or dice game within 4 cells, by blocks and compass), at night WARM YOUR HANDS (stamina full). ids `alm:*`.
- **Doors are lines** (`doorLine544(x, y, side, open)`): the alley back doors and the jobs' back doors (store / safe / racket)
  are a dark gap in the wall, a gold sill line and a worn step -- the apartments' doorway look -- instead of the standing
  `dr_backdoor` plate. Inside, the back door gets the same gold mark as the front door on the entry floor.
- **Fire escapes** draw the `al_fire_escape` plate (`drawFireEscape544`), landing on the wall and the stair coming off it,
  turned to the wall (side 2 as drawn, 0 = pi, 1 = -pi/2, 3 = pi/2), 86 wide, with a shadow.
- Hooks `G.campT544()`, `G.campWordT544()`. Tests `t/t_544.py` (camp E, give, warm, dice crew, fire escape), `t_544b.py`.
- STILL OPEN: the door / fire-escape / fence plates in assets/alley (`dr_*`) are front views -- prompts for top-down redraws
  were given; the other alley people (alp_drunk, alp_junkie, alp_girl, alp_lookout, alp_dealer) are still standing pictures.

---

## LAYER 543a-f -- THE DOCK'S PEOPLE; THE ALLEY BLOCK (#5); BACK DOORS, FIRE ESCAPES, FENCES, THE DEALER, THE DICE (#4)

`l543a.py` .. `l543f.py` (after `l542c.py`). Art: `zx_art_543.zip` -> assets/dock (yt_dock_1..8 top-down longshoremen, pt_dock_1..6
their photos, yt_guard_1 / _2 / _stop, pt_guard (the big guard cropped to head and shoulders), vh_semi_blue, vh_semi_orange).
Cutter helper: `cut/keylib.py` (magenta + dark-pink keys, `comps`, `take`).
- **Dock**: the nine workers are `yt_dock_*` with names and photos; PORT SECURITY `yt_guard_1` (holds a hand up --
  `yt_guard_stop` -- as the rig comes through the gate), `yt_guard_2` at night. The rig is one of the two semis on an
  EMPTY chassis coming in and leaves with a 40-ft box on it. **E** at a dockworker or a guard: his photo and a line
  (WHAT ELSE? for another) -- `G.dockTalkFn`, panel `docktalk`.
- **THE ALLEY BLOCK** (`genBuildings`, before the hood branch): ordinary HOOD and CITY cells (not Old Town, not the club,
  lot over 760 square) split round a 92-wide alley across the middle, open onto the side streets. Hood: three houses a
  side facing their street (front and back yards). City: one or two businesses a side, front on the street, with a
  concrete lot beside (stalls painted) -- 2-4 a block. Every building: `b.back543 = { side, pos }` (the alley wall);
  two floors and up `b.fire543`. Half the alleys are fenced at one end (`alleyFence`, in `c.walls`, collides and draws
  as chain-link). The cell keeps `c.alley543` / `c.lots543`; `drawAlley543` paints them (gravel or cobbles, a drain and
  grates, the lots, back doors with a step, fire-escape landings) -- in the hood after `drawHoodYard`. A landmark
  dropped over the alley removes it. 76 such blocks on the map. Trash corners and alley people now stand IN the alley.
- **E in the alley** (`G.alley543Fn`, first in the E chain; `alleyHint543` puts the prompt over it):
  BACK DOOR -- in to the ground floor at the back wall, and out again from there ("OUT THE BACK");
  UP THE FIRE ESCAPE -- onto the roof (the roof system: walk, jump, rope) and DOWN THE FIRE ESCAPE from its top;
  OVER THE FENCE -- any chain-link (the alley ends and the old fenced lots) -- you're put over the other side;
  the DEALER -- the turf gang's product, 1 or 5 bags at `DRUG_PRICE` (12% chance the buy is `witnessed`);
  THE DICE GAME -- street craps for $10 / $50 / $100 (7 or 11 wins, 2 / 3 / 12 loses, else a point rolled out).
- NOTE: the city's layout changed in these cells, so a save made before 543 may have the old buildings' state on
  the wrong ones; start a new game to see it clean. Hooks `G.alleyT()`, `G.alleyCellsT()`, `G.alleyHintT()`,
  `G.quayLifeT()`. Tests `t/t_543.py`, `t_543c.py` (back door, fire escape), `t_543d.py` (dealer, dice), `t_543a.py` (dock).
- STILL OPEN from #4/#5: the alley people are still the old still pictures (alp_*); back doors only for the alley-block
  buildings; climbing other buildings' fire escapes; irish / barrio / chinatown / uptown blocks keep their own layouts.

---

## LAYER 542 / 542b-c -- THE STREETS STOP AT THE SHORE, THE QUAY AT WORK, EVERY GUN KEY HAS ITS PLATE

`l542.py` .. `l542c.py` (after `l541b.py`). No new art.
- **The west water**: `vCut` / `hCut` now also cut a road piece on the map's west/east edges (cols 0 / 28-29, and off
  the map, which counts as water -- `edgeWater542`) when there's open water on both sides of it. So the streets, their
  lights, poles and traffic stop at the shore; rivers and lakes inside the map keep their roads (those are bridges).
  `spawnPed` won't put anyone in the water, and after `updatePeds` anyone standing in water is put back where he was
  last dry (`q.dryX/dryY`) and turned round (a new ped with no dry spot is removed). STILL OPEN: the expressway on-ramps
  along the west edge still run down into the sea -- that's the expressway, separate from the street grid.
- **The quay at work** (`stepQuay542` / `drawQuayLife542`, only within 3,000): nine dockworkers (`fis_ped_1..3`) walk
  between waypoints on open ground (`quayWaypoints542`: the road edges, the berth, the row ends) and go round the boxes;
  three at night. PORT SECURITY at the gate booth, a second guard at night (prison-guard plates until there's art). A rig
  comes in off 18th St every 40-80 s, stops under the north crane for 9 s, goes back out (`g.quay542.truck`); the parked
  rig moved to the other lane. The straddle carrier runs the berth. Hook `G.quayLifeT()`.
- **Held guns**: `hwKey542(wp)` maps any key to a plate (revolver_snub / revolver_long / .38 / sixgun -> revolver;
  pistol_* / colt / beretta / zip -> pistol_auto; sniper / hunting / bolt -> rifle_bolt; ...). The shop's SNUB-NOSE .38
  (`revolver_snub`) and the gangs' revolver_long / pistol_compact / pistol_large / pistol_saw had no plate -- now they do,
  in your hand and in theirs. Hook `G.hwKeyT(k)`. Tests `t/t_542.py`, `t/t_542w.py`.

---

## LAYER 541 / 541b -- AIM TO PICK A TARGET (RIGHT STICK), LEGS ON A BED

`l541.py`, `l541b.py` (after `l540d.py`). No art.
- **Aim to pick**: with a gun out, the RIGHT STICK points: `G.aimTargetFn(sx, sy)` locks whoever's bearing is nearest the
  stick (within 0.9 rad; the fight first -- hostiles, cops if you have heat, the job's boss -- then anyone/anything
  else; a nearer one wins a close call). It re-picks each time the stick swings 0.3 rad, so sweeping it walks the lock
  round them; letting go keeps the lock. With hands empty the right stick is still zoom / the old flick-to-switch. RB
  still cycles. Hooks `G.hostileT541(n)`, `G.lockT541()`; test `t/t_541.py`.
- **Lying down**: legs 0.56 of his height (were 0.95), feet at 0.64 -- inside the bed.

---

## LAYER 540 / 540b-d -- THE DRIVER STAYS ON THE ROAD, ONE FACE PER SEAT, REY'S OTHER OUTFITS COLOURABLE, PEOPLE A SIZE DOWN

`l540.py` .. `l540d.py` (after `l539e.py`). Art: `zx_art_540.zip` (assets/prison/yt_rey_workvest_c, yt_rey_leather_c,
yt_rey_boxers_c -- colour-coded copies made by `cut/reycode540.py`: blue = the vest / shorts, green = the T-shirt).
- **The diagonal drive**: 536's line-follower kept `A.p0` (where the leg started) from the FIRST leg; every new cruise /
  lose leg (`A.pts` replaced, `A.i = 0`) followed a line from that old start -- straight across the city. `A.p0for`
  ties p0 to the leg it belongs to. Knocked more than 170 off his line he re-routes from where he is (`A.reroutes`), and
  `collideBuildings` now stops an autopilot car. Test `t/t_lane.py`: 45 s cruising, every leg on its lane, 0 re-routes.
  Hook `G.autoT()`.
- **L3 faces**: the driver was matched by object, and `carCrew()` builds new objects -- so he showed in his seat AND in a
  back seat. Matched by key / name now.
- **Rey's outfits**: `REY_CODED` adds `yt_rey_workvest`, `yt_rey_leather`, `yt_rey_boxers` as set `"full"` (arms are
  in the plate): `reyArms` returns `{ torso: <key>_c, full: 1, outer, inner, scale }`, `armsReady` only needs the plate,
  `drawYouth0` skips `drawArms525` for them. Defaults (`REY_COL0`): work vest navy / white tee, leather black / white tee,
  boxers navy. The closet says VEST / T-SHIRT / SHORTS COLOUR. (In a car, the window arm uses his street arm set.)
- **Sizes**: everyone drawn with the new torsos (`AP.wid` -- Rey, the story people, the police) x0.8; the full outfits
  at their old YT_SCALE x0.8; crouching now takes 0.88 off that (was 0.82), so standing Rey is a hair under what crouching
  Rey used to be.
- Test: `t/t_540.py` (outfits, colours, crouch).

---

## LAYER 539 / 539b-e -- THE NORTH EDGE IN DONNY'S ART; THE QUAY'S NEW TOP-DOWN BOXES AND PROPS

`l539.py` .. `l539e.py` (after `l538.py`). Art: `zx_art_539.zip` (assets/city: nc_cliff, br_deck, br_broken, br_girder,
br_tcrane, br_closed, br_scaffold; assets/port2: px_c20_1..7, px_c40_1..4 (turned long-way), and the eight dock props
re-cut from the new sheet). Cutter: `cut/sheet539.py`.
- **The edge**: `drawNorth539` (538's painted one is the fallback). The cliff strip (the left one on the sheet, the far
  bank and river cropped, flipped so the rail is on our side) runs along the top road, 400 tall, every other tile
  mirrored so it joins. North of it: water to the end of the world, with glints and a fog bank further out. No far bank.
- **The bridges**, pieces laid north from the barrier (lengths x0.42 so the story is in view from the road):
  WEST (repairs): a deck span over the cliff, open water, a broken slab (jagged both ends), wider water, then deck
  carrying on into the fog. EAST (construction): a deck span, then bare girders with the scaffold platform on the first
  and the tower crane over them. Both: the BRIDGE CLOSED barrier, cones, the sign.
- **Quay**: the stacks use the top-down roofs (40-ft 250 x 119, 20-ft 125 x 91; rows 130 / 190 apart); bollards, roped
  bollards, rope, pallets, barriers (now lying along the road), drums, light bases and the gate booth from the new sheet.

---

## LAYER 538 -- THE QUAY REBUILT (TOP-DOWN CRANE, STACKED BOXES WITH DEPTH, DOCK PROPS, TO SCALE), WHEEL ICONS, COPS' FACES, HEADS IN THE WATER, THE NORTH EDGE

`l538.py` (after `l537c.py`). Art: `zx_art_538.zip` -> assets/port2 (px_crane_top, px_ct_1..16, px_bollard, px_bollard_rope,
px_rope, px_pallets, px_barrier, px_drums, px_lampbase, px_booth), assets/police/pt_cop_1..12, assets/ui/ui_wh_lockpicks,
ui_wh_glass, ui_wh_walk. Cut by `cut/sheet538.py` (keys magenta AND the dark-pink #AC3474 backgrounds).
- **Quay** (`quayLayout537` now caches `g.quayL538`): to scale against a 112 car -- freighter 2,500, 40-ft box 250, 20-ft 118,
  crane 877 with legs on two rails along the berth (x0+40, x0+250) and the boom out over the ship. Container STACKS 1-3
  high drawn with the buildings' depth trick (`drawStack538`: top lifted by `DEPTH.k * 0.62 * height` away from the
  camera, sides extruded in the box's own colour darkened, a line per container, a ground shadow). Cranes
  (`drawCrane538`): lifted `DEPTH.k * 6`, a silhouette shadow on the apron, the four legs drawn from rail to top.
  Bollards (every third roped) along the edge, rope coils, pallets, drums, barriers along the road, light-mast bases,
  the gate booth at the east end. Stacks, machines, crane legs and props are solid.
- **Wheel icons** on the locked-car wheel. **L3** shows cops' faces (`pt_cop_*`, two per car, picked by the car).
- **In the water**: `drawYouth` and `drawCivilian` are wrappers now (`drawYouth0` / `drawCivilian0` are the old bodies):
  where `waterDepth > 0.14` (and not inside / on a roof / on the freeway) the figure is clipped to a head-sized circle
  and two ripple rings go round it (`swimClip538`, `swimRing538`).
- **The north edge** (`NORTH538`, `drawNorth538`, after the lake/river/quay): north of the top road -- guard rail, a rock
  cliff, the gorge with a river, the far cliff and scrub. WEST BRIDGE (Fourth Ave, x 6000): a span missing in the middle,
  rebar over the gap, "BRIDGE CLOSED · DOWN FOR REPAIRS". EAST BRIDGE (20th Ave, x 30000 -- the Yards Spur runs over it):
  decks out from each side, bare girders between, a tower crane on the far bank, "UNDER CONSTRUCTION · NO ENTRY". Both:
  barriers and cones at the city end. Procedural paint for now (art prompt given). The WORLD_MIN clamp is still the
  actual stop. Hooks `G.northT()`, `G.quayT()`. Test `t/t_538.py`.

---

## LAYER 537 / 537a-c -- THE LOCKED-CAR WHEEL, POLICE SIGHT CONES, CALLS BY NEIGHBOURHOOD + THE METER, L3 FACES, THE QUAY

`l537a.py`, `l537b0.py`, `l537.py`, `l537c.py` (after `l536e.py`). No new art (the quay uses the px_* port set already in assets/port).
- **Locked car**: E at a parked car (Rey) opens a wheel: PICK THE LOCK (the old 505 pick, needs LOCKPICKS) / BREAK THE GLASS
  (opens it at once, 50% alarm, `witnessed(...,0)` -- seen or called in) / LEAVE IT. `G.carInPick`, ids `carin:*`.
  A broken window is `v.glass537` (cracks drawn by `drawGlass537`); while you drive it, a cop whose cone has the car puts
  heat 1 on you ("A COP CLOCKS THE BROKEN WINDOW", 30 s cooldown, `stepGlass537`). Stan's and Joe's: JUST THE WINDOW ($80);
  a full fix clears it too.
- **Police sight**: `copCones537()` -- beat cars and dispatched cars look ahead (520, +-0.62 rad), cops on foot where
  they walk / aim / look round (400, +-0.85); within 85 they hear you. Sneaking cuts all of it to 0.7. `copsWatching` now
  goes through `copSeesPt537`, so `witnessed()` only counts a crime a cop could actually see. Cones are drawn (red when
  they have you) only while you SNEAK or are in cover (`drawCopCones537`). Hooks `G.copSeesT(x,y)`, `G.copConesT()`.
- **Calls**: unseen, `radioCall537` -- `RESP537[zone] = [chance, seconds]` (civic .95/16 ... downtown .9/22 ... hood .3/75,
  projects .2/95, farm .15/140); serious crimes are likelier to be called and come faster. One call at a time
  (`g.call537`). When it lands and you're within 900 of the scene: heat, `escalatePolice`. **Meter** (left column,
  `hud.copMeter` from `copMeter537`): "A CALL'S IN · Ns" counting down, then "POLICE INCOMING" by the car's distance left.
  Hook `G.callT()`.
- **L3** now also pops a face over every occupied seat in the cars near you for 2.6 s (`drawOccFaces537`): your car (you,
  your driver and crew -- `crewFace`), traffic (1-4 people, faces from the civ and inmate photo sets), cop cars (badges).
  Hook `G.occT()`.
- **THE QUAY** (`QUAY537` x 300-1600, y 22650-25350, the 18th St road through at y 24000): on the west water. `waterDepth`
  returns 0 on it (so you walk and drive on it); `dryOut` keeps buildings off it. `quayLayout537()` (once, seeded):
  the freighter (`px_ship`) on the west berth, two gantries (`px_gantry`) over her, a tug, container blocks (`px_box_*`)
  either side of the road, the rig, straddle carrier, forklift, port pickup; boxes and machines are SOLID
  (`collideBuildings`). `drawQuay537` after the lake/river. The BOAT gun heist now happens on the berth, and the map's
  THE PORT target is the quay. (The old inland "port" cells at 15-16 / 6-7 are left as they were: a container yard.)
  Hook `G.quayT()`.
- Test: `t/t_537.py`.

---

## LAYER 536 / 536b-e -- LANES, FOLLOWING DISTANCE, CAR WEIGHT, CAR HUD + L3, ARMS OUT OF THE WINDOW, IDs

`l536.py`, `l536b.py` .. `l536e.py` (after `l535f.py`). Art: `zx_art_536.zip` (assets/ui/ui_id_real.png, ui_id_fake.png -- placeholders I drew).
- **Your driver keeps his lane**: `laneRoute(P)` puts any centreline route on the right-hand lane (one offset going
  straight on, both at a corner, two points at a U-turn). `roadRoute` = `laneRoute(roadRouteC(...))`; `loseLeg` (cruise /
  lose 'em) stitches the two centreline routes FIRST and lanes once -- the old stitched route dropped its joining corner
  and he drove a block down the middle line. `stepAutopilot` now follows the leg's line (aims 150 ahead ON it, not at the
  next corner) and only passes when in a hurry (lose / escape / FAST); a pass moves a full lane (128) over and back.
  Test `t/t_lane.py`: lateral offset holds at 59 every leg.
- **Traffic leaves room**: the follow check is as wide as the two cars (was 26), looks `150 + speed*0.6` ahead, matches
  the speed of the car in front, and sees police cars (`g.pc536`). The pairwise push splits by weight.
- **Weight**: `carMass(c)` (module scope; 1.0 = mid-size sedan, ~3,200 lb) from the footprint and the kind (trucks,
  vans, wagons x1.2; hatches x0.86; bikes 0.42), cached `c.mass536`. `stepCar`: accel / M^0.55, coast roll x M^-0.35,
  brake / M^0.45, grip x M^-0.15, turn x M^-0.3. The car card shows `carLbs(V)` ("3,350 LB").
- **Car HUD**: the money sits under the plate in a car/bike; the fuel gauge is in the left column beside the watch (it
  used to be absolute bottom-left and landed on the objectives on a short screen). **L3** hides/shows the objectives
  (the HIDE button says "(L3)" on a pad); L3 no longer toggles sprint -- RT is run.
- **Arms out of the window**: `drawCarArm536(car, tx, ty, wp, A, flash)` -- the window on the target's side, the arm
  turned to him (clamped so it never points back into the car), the gun from the sheet in the fist. Yours: in a car with a
  gun out (target: the lock, else the nearest hostile/police in range, else where you last aimed); theirs: gang
  drive-bys (set "long", skin varied, sleeve in the gang colour). Test hook `G.carArmT()`.
- **NPC weapons**: `drawWeapon` (every gang member, guard, boss) uses the `hw_` plates first (aliases pistol, shotgun,
  smg, rifle, uzi, ak, tommy).
- **IDs**: `g.ids` (`idsOf()`): Rey's real STATE ID (`REY_ID_NAME` = "REY" -- put his surname there) and fakes
  `{k, nm, no, q, by, day}`; `g.idUse` = the one carried; `G.idCarried()` for later (cops, bar doors). POCKETS lists them
  (`idc:n` -> the `idcard` panel: CARRY THIS ONE / GET RID OF IT). Fakes: a FORGER on the payroll (YOUR PEOPLE -> him ->
  MAKE ME A FAKE ID, $200, quality 18 + HANDS*5 + BRAINS*3 +-7) or a PAWN SHOP counter ("YOU DO PAPERS?", the man in the
  back's skill 22-68 by the shop, price 150 + 4 x skill). Test hooks `G.idsT()`, `G.idMakeT(q, by)`.
- Test: `t/t_536.py` (rear-end contacts 0 over 12 s with 55 cars; arm; HUD; pockets; ID panel).

---

## LAYER 535 / 535b-f -- HELD WEAPONS FROM ABOVE, SHELTER ROOFS, KITCHENS TURNED, WATCH ART SWAPPED, SHOP PEOPLE GO ROUND THINGS

`l535.py`, then `l535b.py` .. `l535f.py` (after `l534.py`). Art: `zx_art_535.zip` (assets/weapons, assets/city, assets/interiors).
- **Held weapons**: `assets/weapons/hw_<key>.png`, 18 top-down plates cut from Donny's sheet, turned muzzle LEFT
  (drawHeld's convention). `heldImg` checks `hw_` first (`HW_ALIAS`: beretta->pistol_auto, smg_hk->mac10, sixgun->revolver ...),
  `HW_K` lengthens the slim pistols. New melee keys have art and scale (crowbar, pipe, cue, tire_iron, switchblade,
  knuckles; machete now drawn): `WPN_SCALE`, `WPN_MELEE`, `MELEE_RX` know them. NOT yet in any gang kit or shop.
- **Bus shelters**: `stop_roof` / `stop_roof_glass` (glass made see-through grey; the sheet's glass was magenta-tinted).
  `drawShelter533` draws the roof long-way along the kerb, plate edge to the road, set back 8 so the bench shows; the stop
  number goes on a lit plate on the roof's front edge. About one stop in three gets glass. Old drawn shelter is the fallback.
- **Kitchens**: the four `int_apt_*` pictures edited (`cut/apt_kitchen.py`, originals in `art/orig535/`): both units'
  stoves turned a quarter so the control panel is on the wall, both fridges turned round so the door faces the room.
- **Watch**: the pockets item now shows `ui_watch_davies.png`; the on-screen watch is `ui_watch_icon.png` (LCD face, time
  printed on the LCD at 26.7% / 44.9%, 48.8% x 17.6%).
- **Shop people**: `folkBump(f, ox, oy, dt)` pushes a walking shop person out of walls and anything `SOLID_PROP`/`hard`
  (art blocks included) after every step, in `stepBizFolk` and the plain shop loop; walking into something for 0.6 s means
  they give up that spot. `solidsOf(pl)` caches per props list (an art floor swaps the list).
- Test hooks: `G.findPropT(rx, kind)`, `G.propsT(rx)`, `G.stoveAtT()`, `G.folkBumpT()` (folk standing inside a solid),
  `g.dbgSolids = 1` outlines the solids. Tests: `t/t_535s.py`, `t_535w.py`, `t_535b.py`.

---

## LAYER 534 -- HEAT AS BADGES AND CARDS, CELL BEDS TO THE WALL, SIT AT THE DESK, LIE ON A BED, SOAP BUBBLES

`l534.py` (after `l533c.py`).
- **Heat HUD**: police heat shows as up to 5 RHPD badges, gang heat as up to 5 gang cards (the gang chasing you: `pursuerNear`
  now returns `gk`, kept in `g.gangGK`). Each slot is full, half (clipped) or a faint ghost, so heat falls 5 -> 4.5 -> 4 ...
  `setHud` computes `copHeatV`, `gangHeatV`, `gangCard`.
- **Cells**: bunk headboard against the cell's back wall (`back0`), bottom-row bunks get `flip = 1` and draw rotated 180.
  Desk bigger: `dw = min(40, W2 - bw - 8)`, `dh = 30`.
- **Seats**: `deskSeat`, `bedSpot`, `lieNear`, `deskNear`. Wheels add SIT AT THE DESK (`dsit`) and LIE DOWN (`lie`).
  Sleeping calls `sitAt(lieNear(90))` first, so you sleep in the bed.
- **Lying**: `drawYouth` takes `p.lying` (long straight legs, no stride); hero lies when `g.p.sit.k === "bed"`.
- **Bubbles**: washing at a sink spawns `g.bubbles`; `drawBubbles534` runs at the start of `drawPrisonFx`.
- Test: `t/t_534.py` (lie -> bed, desk -> desk, wash -> 14 bubbles).

---

## LAYER 533 / 533b / 533c (+ 531d) -- TABLE CHAIRS, SIT DOWN FOR A SIT-DOWN, RIDING THE BUS, BUS SHELTERS

`l531d.py` then `l533.py`, `l533b.py`, `l533c.py` (after `l532c.py`). **531d**: layer 531's seat step was named
`stepSit`, which the gang SIT-DOWN step already was -- one hid the other. Mine is `stepSeat531` now.
**TABLE CHAIRS**: 1A's kitchen table and its four chairs are in APT_OBJ (`APT_DINE`, mirrored for the other flat,
both floors of the long block) as `dtable`/`dchair`; E at a chair sits you facing the table. The object wheel skips them.
**THE SIT-DOWN**: `sitTable(S)` sets a round table 150 out from the meeting place's door, their boss
(`LEADER_ART[gk][0]`) seated facing you, two of his men standing behind, your empty chair opposite (`drawSitTable`,
ground pass). Arriving no longer opens it: you sit in your chair (E, `G.sitFn` checks the table first, `k: "sitdown"`)
and THEN the talk opens (war agenda too). Test hooks `G.sitCallT`, `G.sitTableT`.
**THE BUS**: `G.busBoardFn` -- E within 90 of a city bus's door (`busDoor`: kerb side, front third) while it stands at a
stop: `g.onBus = { v, seat }`, a passenger counted. `stepBusRide` (first thing in `stepFoot`) keeps you in your seat
(`busSeat`, two columns of five), facing forward; `drawBusRide` (overhead pass) draws the floor, aisle, red seats, the
others aboard and you, and puts you back in your seat at draw time (the traffic pass pushes you out); `drawHero` skips
while you ride. E while it's stopped: `G.busOffFn` puts you at the kerb by the door. Test hook `G.cityBusT` (`G.busT`
is the school bus's).
**BUS SHELTERS**: `drawShelter533` replaces the old stop marker: a bench on the road side under a green striped awning,
the route number in a lit box on the roof. Up to two people wait on the bench (`g.stopFolk`, baked civilians); when a
bus stands at the stop they walk to its door and get on (counted in `pax`), and more turn up 40-90 s later. People
getting off still come out of `serviceStop`. Test: `t/t_533.py`.

## LAYER 532 / 532b / 532c -- EVERYONE GETS ARMS; REY'S OUTFIT COLOURS

`l532.py`, `l532b.py`, `l532c.py` (after `l531c.py`). Art: `art_arms2.zip` -> `assets/arms/` (armless torsos for Rey's
four coded outfits, Dread, Nicky, Mimi, Jose, Yuri, Silas, Drummond, Alonzo, Ramos, Malcolm, Rochelle '69, Tiny '69,
Damian '69, Julian '69, the two '69 patrolmen; police m/f/sergeant/SWAT in four skin tones each, pre-tinted from the
grey-faced sheet; police and SWAT arm sets).
`ARM_BY_YT` maps a sprite key to {torso, arm set, skin, sleeve, wid}: `drawYouth` uses it whenever it draws that key,
so the story characters get arms everywhere they appear (Leroy and Pablo too, on their pilot torsos). `wid` sizes a
torso by its WIDTH (these are taller than the pilot torsos); arm lengths follow the shoulders. `drawCopPlate` now draws
torso + police arms (tone from COP_TONE; black officers split brown/dark; `u.swat`, sergeant by rank), with the gun arm
(the pistol is in the art) when a cop's weapon is drawn. SWAT `yt_swat_1-8` use the SWAT torso.
REY'S COLOURS: `REY_CODED` -- street, track, suit, work are the new blue/green coded torsos; `codedTorso` tints blue to
the OUTER colour and green to the INNER (`g.pcol[fit] = {o, i}`, indexes into `CLOTH_COLS`, 14 colours; defaults in
`REY_COL0`). Sleeves follow the outer colour. The closet wheel's first two items are JACKET/SUIT COLOUR and
SHIRT/HOODIE COLOUR for what you're wearing (`fitcol:o`/`fitcol:i`, each press the next colour). Work vest, leather vest
and boxers still use their old plates until sheet 2 comes back. Test hooks `G.lineupT`; tests `t/t_lineup.py`,
`t/t_lineup2.py`.

## LAYER 530 -- FIGHTING WITH THE ARMS

`l530.py` (after `l529.py`). `drawArms525` rewritten. Unarmed, strikes alternate JAB (right arm out, `ar_*_punch`) and
HOOK (left arm sweeping across, the punch art mirrored): `g.p.atkN` counts strikes (a rising `g.p.atk`), the hero
call passes `move` jab/hook. A melee weapon (`MELEE_RX`: bat, knife, pipe, crowbar, machete, sword...) is held in the
right hand at his side and a strike is a SWING: the arm sweeps from his right across the front with the weapon in the
fist. A gun out of the holster (`p.held`, `p.aim`) is held out in front all the time, the gun in the fist; a long gun
(`LONG_RX`) brings the left hand up under it. `heldImg`/`drawHeld` use the same weapon art as `drawWeapon` (wpn2
atlas, weapon atlas, or `wp_<key>`). Anything thrown out in front is drawn over the torso; hanging arms under it.
Only on Rey in street clothes so far (the arms pilot). Test: `t/t_fight.py`.

## LAYER 531 / 531b / 531c -- SITTING, KESTREL'S TOILETS, PEOPLE A HAIR SMALLER INDOORS

`l531.py`, `l531b.py`, `l531c.py` (after `l530.py`). New art: `assets/props/pr_toilet_apt.png` (cut out of
`int_apt_long_f0`, registered `pr_toilet_apt`).
**SITTING**: `seatsNear` finds seats -- art floors from APT_OBJ (sofa: three spots, facing its TV; toilet), prop rooms
from any sofa/couch, chair/stool/bench/pew/seat, or toilet prop (a sofa gets 1-4 spots along it). E at a sofa or chair
sits you straight down (`G.sitFn`, before the object wheel, prison path too); the sofa wheel's SIT DOWN and the toilet's
USE IT sit you too. `g.p.sit` holds you there, facing the way the seat faces (`stepSit` in `stepFoot`); any movement
stands you up a step in front of it. Facing: away from the nearest room wall; toilets to the cell's top/bottom wall.
**KESTREL'S TOILETS**: every `toilet` prop in a prison building draws as 1A's toilet, tank to the nearer of the cell's
top and bottom walls.
**INDOORS**: everyone drawn through `drawYouth` is 0.9 size inside a building, so tables, stoves and sofas -- painted
into the art floors, so they can't be scaled themselves -- read their size. Tests: `t/t_sit.py`, `t/t_ptoilet.py`.

## LAYER 529 -- THE NEW TOP-DOWN CARS

`l529.py` (after `l528b.py`) + `art_cars.zip` (23 files in `assets/cars/`, same names and sizes; old ones in
`scratch/old_cars_529`). Donny's strict top-down sheets: the red/yellow sedans, coupe, fastback; the three turbo coupes
and the navy turbo; the three stainless coupes + the student's mom's wagon; Leroy's, Ras's and Pablo's cars + the red
hatchback; the four 1969 cars; the 1969 cruiser, the crew van and the City Express box truck (those three came nose-down
and were turned round). Still on the old art (sheets not made yet): the blue/green/grey/orange sedans, the parked
911s/white coupe/green wagon, the parked light-blue/navy/red sedans. The 1969 cars came back narrower, so they're drawn
112 x 44 now (was 54) in `suEra` and the Setup's car, or the new art stretches fat.

## LAYER 528 / 528b -- GUN HEISTS

`l528.py` then `l528b.py` (after `l527b.py`). No new art (crates are drawn; the truck is `truckM()`'s box truck).
Three jobs in `GH`, harder = more men, crates, heat, cash and kinds of gun: THE GUN STORE (1 star: 3 men, 2 crates, heat
1, $2-4.5K; pistol, shotgun, vest -- the back of RIGHT TO ARMS), THE ARMS TRUCK (2: 5 men, 3 crates, heat 2, $6-12K; +SMG
-- a Boznov box truck parked on a street 2-3 blocks off), THE BOAT SHIPMENT (3: 8 men, 4 crates, heat 3, $15-30K; +rifle
-- THE PORT's hub point). Started from the MAP menu ("GUN HEISTS", orange) or the board ("GUN HEISTS · THE STORE, THE
TRUCK, THE BOAT"); panel `gunheist`, ids `gh:go:<k>` / `gh:quit`. State `g.gh` (not a story slot; runs beside the
story): step go -> (within 700) hit: `hostile("rus", ...)` guards, hp x1.25 per star -> E at a crate (`g.bagsOn`, the
first crate sets the heat) -> E at YOUR car (`g.car`) to put it in the trunk -> all in: home -> at the scrapyard or the
Hippie (`ghHome`, within 460 of the front), heat gone, E by the car: UNLOAD (`ghPayout`). Payout: 5-12 of EACH item on
the job into the armory locker (`g.board2.armory`, GEAR keys), the cash, +10 respect per star, side XP; panel `ghtake`.
Objective: `storyObjective()` returns `ghObjective()` while a heist is on; the arrow (`ghTarget`) leads. E handler
`G.ghActFn` runs before the trunk/fuel-can one. Test hooks `G.ghT`, `G.ghHomeT`. Test: `t/t_gh.py` (all three, start to
stash). Known: the port point is the hub's street corner by the port landmark, not the water's edge; no boat drawn yet.

## LAYER 527 / 527b -- SKIP PRISON FROM THE START; NO LION POWERS FOR REY OR THE KID; REY'S ROPE

`l527.py` then `l527b.py` (after `l526.py`).
**THE CHEAT FROM THE START** (Donny: skip prison to test): `G.skipPrisonFn` / `G.skipPrisonOk` (story setup, lastday or
dayout; not detective or student mode). On the first 1969 panel (`su_morning`: "CHEAT · SKIP PRISON (TO FIRST DAY OUT)",
`su_cheat`) and on the MAP menu (same purple button as 526; it reads "SKIP TO THE NEXT MORNING" once Eddie has dropped
you). It runs `setupSkipT` if still in 1969, marks setup + lastday done, starts DAY OUT (`dayOutBegin`: civvies,
released), jumps it to step 3 with Eddie's cab gone, then `skipMornFn` (526): sleep fade, 1A, DAY OUT complete, FIRST DAY
OUT at 4:30.
**NO LION POWERS** for Rey (`g.prisonMode`) or the kid (`g.studentMode`): `hud.plainMan` hides LION, OFF/SUIT/MASK,
the guard button (BRACE), FIS and ROAR, and the HOOK; `lionPowersOn`, `G.guardFn`, `G.fisHuntFn`, `G.roarFn` and
`fireGrapple` refuse in those modes. The pad's action wheel reads the buttons, so they're gone there too.
**REY'S ROPE**: button ROPE ("climb up" / "find a wall") for Rey only (`hud.stuMode` hides it for the kid). `ropeTarget`
= a building of `GRAP_MIN_FLOORS`+ whose wall is within `ROPE_REACH` (70) of him; `G.ropeFn` sets `g.grap` with `.rope`:
`updateRoof` climbs him to the wall at 0.7/s (~1.4 s) and puts him on the roof at the edge; `drawRoof` draws a rope
from where he stood to the roof's drawn edge with a hook over the parapet. On a roof the button is JUMP (a short gap,
`roofJump`) or DOWN (climb down). No hook-and-swing. Test hook `G.ropeTargetT`. Tests: `t/t_rope.py`.

## LAYER 526 -- CHEAT: SKIP TO THE NEXT MORNING

`l526.py` (after `l525.py`). On the MAP menu, while DAY OUT is at step 3+ (Eddie has dropped you at Palm Court) and no
banner or sleep fade is up (`G.skipMornOk`): "CHEAT · SKIP TO THE NEXT MORNING" (`hud.skipMorn`, `G.skipMornFn`). It
marks the closet/phone/mail done, fades to sleep, puts you in 1A by the bed, adds a day, completes DAY OUT
(+ its pay), and FIRST DAY OUT starts at 4:30 AM as normal. Test: `t/t_skip.py`.

## LAYER 525 -- THE ARMS PILOT (REY)

`l525.py` (after `l524.py`). New art: `assets/arms/` (`art_arms.zip`) -- `ar_torso_rey/leroy/pablo` (armless torsos) and
`ar_<bare|short|long|jacket>_<hang|punch|gun|fwd|back>` (grey skin, blue sleeve, right arms). `ARM_SETS` (next to
REY_FITS) says who wears what: Rey = jacket sleeves, Leroy = long, Pablo = short, each with a skin and sleeve RGB and a
torso scale. `armTint` makes a tinted copy of each arm per man once (grey -> skin by brightness, blue -> sleeve; the
round shoulder joint is sleeve on a sleeved arm). `drawYouth` takes `p.arms` (an ARM_SETS entry): it draws the torso
instead of the plate, and `drawArms525` draws both arms hanging under it, swinging against the legs. On a JAB the right
arm (`ar_*_punch`) shoots out over his chest to ~1.3h and back (the old drawn jab is skipped); while a gun is out
(`p.aim`: `drawnT` > 0 with a firearm) it's `ar_*_gun` pointing forward. Uppercuts and weapon swings still use the old
drawn arm. ON NOW for Rey in his STREET clothes only (`pkey === "yt_player_civ"`); every other plate and man is
unchanged. `g.noArms = 1` turns it off. Not yet: Leroy/Pablo (their sets are in ARM_SETS), the fwd/back walk poses, a
gun in the gun hand. The long-sleeve/jacket "back" poses are broken art (two arms); the long-sleeve "gun" is a fist.
Tests: `t/t_arms.py`, `t/t_armgif.py`.

## LAYER 524 -- TOP-DOWN TRAFFIC SIGNALS; CARS THAT COAST

`l524.py` (after `l523b.py`). No new art.
**SIGNALS** (Donny): the coloured squares at the junction corners are gone. `sigHeads(i, j)` gives four heads per
junction (NW/SE face the north-south traffic, NE/SW the east-west): a grey pole on the corner, a grey mast arm out over
the lane it controls, and the head's grey top seen straight down with just the front edge of the lit lens showing
under a dark visor, facing the traffic coming at it. `drawSignalHeads` draws in the overhead pass beside the poles and
wires (over cars); `drawTrafficLights` (ground pass) now only throws the lens colour on the road, stronger at night.
`sigState(i, j, axis)` runs greenFor's 17 s cycle with the last 2 s of each green shown AMBER (AI traffic still treats
amber as go -- greenFor is unchanged).
**MOMENTUM** (`stepCar`): off the gas the car rolls on, bleeding speed through rolling resistance + air
(`roll` = 22 + 0.1*speed, x3.2 on grass; bikes 26 + 0.13*speed), about 520 down to 340 in 4 s, where the old engine
braking halved your speed in half a second. The gas pulls hard off the line and tapers (`pull` = 1.3*(1-0.82*r^1.6),
r = speed/MAX), so holding it keeps building toward top speed (0 to ~520 in 2.5 s) and a tap holds a cruise. The brake
is 820/s (x brakeMul), then reverse as before. The handbrake and steering are unchanged. Autopilot drives move the
car directly, so they're unaffected. Test: `t/t_sig.py`.

## LAYER 523 / 523b -- THE PRISON CULVERT; THE ROOF ART REDO

`l523.py` then `l523b.py` (after `l513b.py`). **THE BUG** (Donny: tunnelling out of Kestrel, all black, trapped): Kestrel
sits at j~24-25, south of the sewer's last line (`SEWER_MAX` 22). The shower drain (`G.drainFn`) and the warden PC's
SEWER exit (`wardenPcGo('sewer')`) asked `nearestManhole` for a hole near the south wall, got none, and set you down where
no tunnel exists. Now a 1931 storm culvert (`CULVERT`, module scope beside `nearestManhole`) runs from under the south
wall (`dropY`, where both exits land you) straight north up the i16 line to the network's stub at SX(22); narrower brick,
a trickle, the shower grate's light at the dead end (`drawCulvert`, drawn before the dark closes in). Its OUTFALL ladder
(`exitY`, ~1,900 north of the north fence) counts as a manhole in `nearestManhole` (E up), with a plate on the street
(523b, `drawManholes`). Past it the culvert joins the city sewer.
**SEWER WALLS** (`inSewerNet`): the old test let a vertical tunnel run on forever past the drawn end -- walk south far
enough and you were in the black. Movement is bounded to what's drawn, and you slide along the last good spot
(`g.sewLast`) instead of snapping. The yard DIG (layer 437) still comes up outside the south wall, unchanged.
Test: `t/t_culvert.py`.
**ROOF ART** (`art_roofs_redo.zip`, same file names and sizes, already in `assets/`): 55 roofs from Donny's top-down
sheets, keyed, retargeted (seam carving, not stretching) and fitted -- the `rf_z_*`, `rf_g_*` house/cabin/farm/barn/shop/
shophouse sets, bank_major, brick_apt, cityhall, union_terminal, air_hangar, and the `ct_*` civic/Old Town set incl.
ten1-5. Old ones backed up in `scratch/old_roofs_518`. The zip also has `chars_arms_pilot/` (3 armless torsos, 20 grey/
blue arms) for the arm system -- not wired yet. The long-sleeve and jacket "back" poses came out as two arms, so they
need making again, and the long-sleeve "gun" pose is a fist.

## LAYER 513b -- GROUND THINGS UNDER THE PLAYER; THE CITY ART LIST

`l513b.py` only (after `l513.py`). The parking-stall paint (`drawLotPaint`), the graves, cold-case evidence marks and the
schools' grounds (`drawSchoolsOutside`: fields, walks, props) were drawn after everyone standing -- over you. They're
drawn on the ground now, beside the alleys and the Old Town props (layer 510). Anything else that's a floor (a painted
driveway or walk inside a building's own art, like the prison gate was) still needs pointing out in a screenshot.
**THE CITY ART REDO**: the story doc now has "City art redo (Oct 18)" -- every building whose art shows its FRONT WALL
(54 files, three priorities, the Virgin Mary wall is `rf_z_barrio_c`), a master top-down prompt, a line per file, the
size each must keep; "Still planned in the city, not built yet"; and "Characters: the arms plan".

## LAYER 513 -- HEAT THAT COOLS (AND WORKS IN A CAR), ONE PABLO, STORY DRIVES WITHOUT CHASES, STATS THAT COUNT, LEVEL 4

Block `b513.js` + `l513.py` (after `l512d.py`). No new art.
**THE HEAT BUG** (Donny: heat never went down, cops kept ramming): `stepPursuit` -- the "lost them" clock -- was only ever
called from `stepFoot`, so in a car it never ran and heat in a car never came down. It runs after `stepCar` now too.
And heat COOLS on its own (`stepHeat513`, called from stepPursuit): no new crime for 40 s (20 s with Dread's Corner at
level 4) and it drops a level, however close they are; at 0 everyone stands down (patrols stop chasing, choppers leave).
Cops only ram at heat 2+ (layer 506's ram).
**STORY DRIVES**: while a story driver drives (`g.auto.who` and a story), heat can't rise above what it was when he set
off (`A.h0`) unless you're firing (`g.p.drawnT`). **THE ARROW**: `g.lastDest` (the end of the last `g.auto` route, for this
story step) -- `drawTargetArrow` points at it when the story gives no target and nobody's driving; cleared in 220 or
when the step changes.
**ONE PABLO** (Donny: after the scrapyard, two lowriders and Pablo outside): `G.pabloCarFn` turned YOUR car into
Pablo's lowrider and never gave it back, then Friday's `scrapBegin` parked another lowrider. Now your car is kept
(`g.carWas513`) and `pabloHome513()` -- at `scrapBegin` and when the scrapyard or Friday completes -- removes his
lowrider and his follower and puts your car back where you left it.
**STATS** (Rey, `st513`): DRIVING +3% top speed / acceleration, +5% grip a point over 2 (your car, not when driven);
STEALTH -6% every cone's range and the 70-unit "he hears you" a point over 1 (min 60%); CHARISMA -4% buying (shop menus,
guns, the hire pool) and +4% selling (`sellList` wraps `sellListRaw513`) a point over 1. CREW: a business boss's SMARTS
+5% its take a point over 2 (`bossMul513`); a story driver's DRIVING +4% his speed (`crewDrv513`).
**XP FROM SIDE JOBS** (`G.sideXP(xp, why)`): board jobs (30 / 60 if you rode, + pay/50 up to 120), Rusty Nail jobs
(60 + pay/50), races won (80), Kestrel's side jobs (50). The heat case already paid 150.
**LEVEL 4 BUSINESSES** (+15% take each): HIPPIE -- Drummond's case fills half as fast; CORNER -- heat cools twice as
fast; NEST -- hires 20% cheaper; RAVEN AUTO -- your car mends while you're on foot (`stepGarage513`). Shown on the
business screen (`L4_PERK513`). Test hook `G.stats513T`. Test `t_513`.

## LAYER 512d -- THE XBOX BUTTONS ON A LOADED SAVE, ONE PABLO, SPRITE SIZES

`l512d.py` only (after `l512c.py`).
**THE PAD ON A SAVE** (Donny: on his save the stick moved but no button worked): a save made from the map screen kept
`g.mapOpen = true`. Loaded, the map isn't up but the pad loop still sent every button to it. `applySnap` now clears
every on-screen state (map, stats, talk, locker, travel, lift, Malcolm, race talk, truck, ID card, leader talk, table,
arcade cab, cutscene, sleep fade, the cursor prompt), and the pad loop drops a `g.mapOpen` when no map is on screen
(no `[data-mapopt]`). RULE: anything new that "opens" on screen and sets a g flag goes in that reset list too.
**ONE PABLO** at the scrapyard's back fence: the story's Pablo (`S.pab`) walks the line; your driver Pablo (`g.pfol`)
used to get out and follow too. The driver comes off `g.pfol` at step 7 (`S.pfolWas`) and back on at step 10.
**SIZES**: every plate is drawn the same height, so width = height x aspect. The Boznovs are BUSTS (head and shoulders):
at full height their heads were twice Rey's -- `YT_SCALE` vlad / grigori 0.72, victor 0.68, katya 0.74. Rey's outfit
plates are narrower than his street plate (aspect 1.19-1.32 vs 1.45), so changing shrank him -- suit 1.11, track 1.1,
work 1.18, workvest / leather 1.2, boxers 1.22. Test `t_512d`.

## LAYER 512c -- LEROY'S FIGHT: DUTCH WOLFE COMES FOR YOUR SEAT

`l512c.py` only (after `l512b.py`). Donny: nobody attacked for Leroy's side job. The man was picked from cons within 420
of you on your tier -- and since layer 510 the count clears at 7:30, breakfast empties the tier, so nobody was picked.
Now LAST DAY IN makes its own: DUTCH WOLFE, a Wolves con (`S.foeSpawn`, inmate no. WOLF-1), walks in the block door the
moment you're on your tier after talking to Leroy, says his line, and comes at you. He's put back in the folk list if a
phase change rebuilds it, and (`q.storyFoe` in `stepPrisonFx`) walks the tier to your x and then in, instead of into the
cell wall. Put him down (F) and it's done. Test `t_foe`.

## LAYER 512b -- 1A'S LIVING ROOM TURNED ROUND, THE ATARI, CHANNEL 6, REY'S BOXERS

`b512b.js` + `l512b.py` (after `l512.py`). Art: `art_512.zip` -- `assets/prison/yt_rey_boxers.png` (Donny's, magenta keyed,
cropped at the hip like the other outfit plates, 400 wide) and a new `assets/interiors/int_apt_long_f0.png`.
**THE LIVING ROOM** (Donny): in 1A the couch now sits against the top wall facing down and the TV (flipped to face it)
at the bottom where the couch was -- edited in the picture (the left flat only; 1B is as it was). `ART2_SOLID.int_apt_long_f0`
(couch block -> 0.486-0.588, TV block -> 0.872-0.964) and `APT_OBJ` (sofa fy 0.54, TV fy 0.92) follow, f0 only.
**THE ATARI** (`ap_atari`) on the floor left of the TV (`CONSOLE_AT512` 0.272, 0.93): E -> the same cartridge panel
("console") as Malcolm's and the kid's. `G.aptConsoleFn` in doAction after the flat doors.
**CHANNEL 6** (Donny): the TV's WATCH THE NEWS opens `sp_tv`: AD, AD, NEWS, AD, AD, NEWS... (`g.tvI`), KEEP WATCHING or
TURN IT OFF, ten minutes a segment. `TV_ADS`: 24 ads, nearly every business in town. `tvNews512()` is written fresh each
time from the game: the war on the east side (`kingsTurfHeat`), the Boznov house, your crew's name, your businesses (new
management), Drummond's case, a chase when you're hot, the bank job -- then the standing items (Kestrel, Vance Tower,
sports, weather). Test hook `G.tvT`. Test `t_512b`.
**REY'S BOXERS**: `yt_rey_boxers` is now in -- the morning scenes and Katya's bed draw him in it (layer 512).

## LAYER 512 -- PALM COURT'S DOORS AND THE RENT, THE MODESTY BLUR, QUICKER ON FOOT

Block `b512.js` + `l512.py` (after `l511b.py`). Art wanted: `assets/prison/yt_rey_boxers.png` (registered; falls back).
**THE FLAT DOORS** (Donny): each painted Palm Court floor (`int_apt_long_f0/f1`, `int_apt_side_f0/f1`) has two flats either
side of the hall; their doorways (fractions `DOOR_X512` x `DOOR_Y512` 0.732-0.868, from the ART2_SOLID gaps) get a sliding
wooden door (`aptDoors512`, cached on the plan as `pl.doors512`; a `hard` artblock prop shut, `artdoor_open` open).
Names: building A `1A/1B` (ground) `2A/2B` (up), B and C `1B-A`... 1A (A, floor 0, left) is yours: E opens / shuts it.
2B (A upstairs, right) is Mimi's: opens once `g.mimiHome` (or the dinner). Every other door: LOCKED ("NOT YOUR PLACE").
E goes through `G.aptDoorFn` (doAction, after the case). **THE RENT** (`stepRent512`, prison story after `dayout`): $25
every 7 game days (`g.day`) from the day it starts (`g.rent = { from, last, owed }`); taken from your cash on its own;
short, it goes on `owed` and 1A's door LOCKS (never shuts you in -- if you're inside it stays open) until you pay at the
door: E -> `sp_rent` -> PAY. Test hook `G.rentT`.
**THE $1,000** in 1A was always in the toilet tank (layer 481) and works; nothing told you. Leroy's line at the cake now
does ("lift the lid on the toilet tank").
**OUTFITS**: the closet wheel and the swap work here; Donny's copy was missing `assets/prison/yt_rey_*.png` --
resent as `art_outfits.zip`.
**THE MODESTY BLUR** (Donny, the love scenes): `drawModest512(p)` draws the sprite, then a soft blurred ellipse over the
body below the head in the character's SKIN COLOUR (`skinOf512`: `YT_ARMS[yt][1]`, else sampled off the sprite's warm
pixels). Used for Katya in the morning scenes (`drawMorning` -- her mosaic is gone) and in bed in A SEAT AT THE TABLE.
Rey: `g.reyBoxers` puts him in `yt_rey_boxers` (in the morning scenes till he's up, and in Katya's bed until the paper);
without the file his mosaic stays.
**ON FOOT**: walk 126 (was 116), run 232 (was 214). Test `t_512`.

## LAYER 511 -- THE LAST NIGHT AND THE WALK OUT, ROUTES ON REAL STREETS, CLOSER STATIONS, THE MINIMAP STREET BY STREET

Block `b511.js` + `l511.py` + `l511b.py` (after `l510b.py`). No new art.
**THE CAKE -> THE NEXT MORNING** (Donny): "SEVENTEEN YEARS. I'LL SEE YOU OUT THERE." now runs `partyBegin511` --
6.5 s of party (the crew bouncing round the cake, confetti, `PARTY_LINES` one by one), a 1.5 s fade to black, then
`escortBegin511`: the slam THE NEXT MORNING · 5:30 AM, clock 5:30, Harlan (`yt_harlan`) standing in your cell talking,
two C.O.s at the bars, the black lifting. Then the WALK: `walk511` along `inPts` (cell -> tier centre -> along the tier
-> the block door, the way the intro walked you in), then outside along `outPts` = `path511` -- grid A* (40-unit cells)
over the campus, every prison building and the yard fence blocked (inflated 22), the concrete walks cheap (0.5) and
grass dear (1.6), smoothed by line of sight. Harlan walks 36 ahead on the same path, a C.O. at each shoulder.
`stepCellDoors` leaves the doors open while `g.escort` is on. The old `escortBegin/stepEscort/drawEscort` stay but are
no longer called. Test hooks `G.escort511T`, `G.walk511`. Tests `t_511`, `t_511b`.
**EDDIE** is 22: drawn at tall 0.92 (was 1.25 -- bigger than Rey). His tour drives `sk "normal"` at 1.15x cruise (it
was "fast", which since layer 508 passes in the oncoming lane and stops braking for the car it's passing).
**NO REAR-ENDING** (`stepAutopilot`, every driver of yours): looks 300 ahead along the route and 200 along the way the
car is pointing (round corners), stops at 136 centre to centre (a car and a quarter) -- it stopped at 75, inside the
other car's bumper.
**ROUTES ON REAL STREETS** (`roadRouteC`, used by every autopilot route): was one L-turn, straight through anything --
the Union Terminal plaza, superblocks, cut county roads. Now A* over the intersections along segments that exist
(`!vCut` / `!hCut`), a turn costs 0.35 of a block so it doesn't staircase; an isolated start/end tries nodes within two
blocks; the old L is the last fallback. Test hooks `G.routeT`, `G.routeCutT`. Test `t_511c`.
**THE CAB TOUR CAMERA**: each stop's pan is 4.5 s (was 6) and comes back in 0.7 s (was 1.5).
**GAS STATIONS** (Donny): `gasCanopy` sits one drive lane (96) in front of the shop instead of mid-lot. Hook
`G.gasAllT`. Test `t_gas`.
**THE MINIMAP, STREET BY STREET** (Donny): drew every grid line edge to edge. Now one Path2D of streets and one of
avenues, block by block, only where `vCut`/`hCut` say the street exists (built once, `mmPaths511` -- NOT on g, a
Path2D doesn't survive the save), streets 70 / avenues 120 world units, the expressway legs on top in blue. Test `t_mm`.

## LAYER 510b -- THE CAKE LOADS, NO DETECTIVE'S CASE IN KESTREL

`l510b.py` only (after `l510.py`). **THE CAKE** (Donny): `PD_ART.pr_cake` was set inside the game body (layer 493),
after the image loader had collected PD_ART, so the art never loaded and the cake was the drawn fallback. It's
registered at the top now (beside `dt_drummond`). RULE: every `PD_ART.x = ...` goes at the top level, never inside.
**HUD ERROR "reading 'mood'"** (Donny, LAST DAY IN on the Xbox): a detective-mode `g.case` left in the game from an
earlier session; the detective's talk check (`nearTalk` -> `talkPanel` -> `willing`) found one of its people without
traits. Now: `nearTalk` is detective-only (not prison or student mode), `talkPanel` rolls traits for anyone missing
them, `startPrisonMode` drops `g.case`, and the story step clears it every frame in prison mode.
Also new: `t_door` / `t_door2` (walk in and out of a building, keyboard or a fake Xbox pad -- `navigator.getGamepads`
stubbed) -- Donny saw doors not working on the Xbox once; not reproduced. Test: `t_510b`.

## LAYER 510 -- THE COURT FACES THE BENCH, THE BODY ON THE FLOOR, BLOODY FOOTPRINTS, THE CELLS OPEN

Block `b510.js` + `l510.py` (after `l509b.py`). No new art.
**THE COURTROOM** (Donny: the jury and the crowd faced the wrong way): props can carry `turn` (radians) -- drawInterior
draws them rotated in their own footprint. The pews get `turn: PI` (backs to the door), the jury box goes in as 58x108
on the east wall with `turn: PI/2` (facing the room); `courtSpots` seats the jury two rows of three across the turned box
and the gallery on the seat side of the pew. Everybody in `courtPeople` looks at the JUDGE (jurors used to look at the
witness), and `p.faceTo` turns an idle civilian sprite (`faceCiv`: rotated sheets get `o.ang`, eight-way sheets
`o.dir8`) -- civilians standing still used to show their default (front) frame whatever `bang` said. The flashback's
Damian / Julian / Rochelle sit on the seat, not the back rail.
**UNDER YOU** (Donny): the flashback's body and its pool (`drawSetupGround`), the alley clutter and alley people
(`drawAlleys`) and the Old Town props (`drawOldTownProps`) are drawn before the sorted people now, so you walk over them.
**BLOODY FOOTPRINTS** (`stepPrints510` / `drawPrints510`): standing in blood (any `g.blood` pool in the same building --
pools now remember `in` -- or the flashback body's) sets `g.p.bloodT = 5`; while it lasts you leave a print every 20
units, alternating feet, each fading over 5 s. `g.bprints` = {x, y, a, t, in, fl} -- the building key and floor, for
detective mode later. Test hook `G.printsT`.
**THE LAST DAY** (Donny: the cell doors never opened after the wake-up): `stepWake510` -- 5 s into LAST DAY IN step 0
(no panel up) the clock jumps to 7:30 if it's still the 7:00 count, banner COUNT CLEAR, the doors roll back
(`stepCellDoors` opens them whenever the phase isn't "cells").
Test: `t_510` (body under you, prints, the court, the doors).

## LAYER 509b -- SEE-THROUGH DECKS, THE GATE ROAD ON THE GROUND, DRUMMOND IN PERSON

Block `b509b.js` + `l509b.py` (after `l509.py`); `b509.js` also gained the warrant's `g.rcDrum`. Art: `art_509b.zip`.
**UNDER THE EXPRESSWAY** (Donny): `fwyFade509(vert, L)` in `drawViaduct` -- when you (or the car you're in) are within
FWY_HW + 24 of a leg and not on the freeway, that leg eases to 30% alpha (`g.fwyFade["v"|"h" + L]`, 0.15 a frame) --
deck, rails, ramp marks. `drawFwyTraffic` sets `globalAlpha = fwyFadeAt(v.x, v.y)` per car; the overhead EXIT signs
use `fwyFadeMin()`. Back out and it fills in.
**THE PRISON GATE** (Donny): `pr_roof_gate.png` includes the road, gates and booths, and was drawn over people whole,
so you walked under the ROAD. Now the whole image goes on the ground in `drawPrison` and `drawPrisonOver` draws only
its top 41% (the roof). You walk on the road and disappear under the roof.
**DRUMMOND**: portrait `assets/crew/pt_det_drummond.png` (Donny's, frame cropped off), top-down `assets/crew/dt_drummond.png`
(magenta keyed, 115x128, faces down) as `PD_ART.dt_drummond`. After a warrant he stands at the raided business's front
(`empB(k)`, so not Dread's corner) for 90 s facing you (`drawDrum509`, label DET. DRUMMOND).
Fixed in passing: `PD_ART.pr_cone_side` / `tx_ivory_tile` had been swallowed by a `//` comment on the PD_ART line.
**STORY NOTE** (Donny): Malcolm's and the kid's stories start before Rey's, about four chapters each; the kid's ends
when he meets Rey; Malcolm's ends taking down the Asian gang, alongside Rey's with only brief encounters (may change).
In the doc under "The other two stories". Test: `t_509b` (fade under/out, gate, Drummond).

## LAYER 509 -- THE CASE: DETECTIVE DRUMMOND, PABLO'S JOBS, ALONZO, THE WARRANT

Block `b509.js` + `l509.py` (after `l508.py`). New art wanted: `assets/crew/pt_det_drummond.png` (falls back to no face).
**NAMES**: state is `g.rcase`, constants `RCASE` / `RCASE_JOBS`, functions `stepRcase` / `drawRcase` / `drawRcaseArrow`.
Detective mode already owns `g.case`, `CASE`, `stepCase`, `drawCase`, `drawCaseArrow` -- the first cut reused those
names, silently replaced detective's functions and broke STUDENT and DETECTIVE starts. Don't reuse them.
**OPENS** (`stepRcase`, prison-mode story only, after `storyDone.dayout`): heat 2+ and no case (or the last one closed
180 s ago) -> DETECTIVE HAL DRUMMOND (not Malcolm, not Ramos) opens one; Pablo phones 2.5 s later (`sp_case`).
**THE BAR**: fills `0.2 x heat` % a second while heat is 2+ (heat 2 = ~4 min to full, heat 5 = 100 s); shown under
JUICE top right (`hud.caseBar`) and as a map button (THE CASE · DRUMMOND x%).
**PABLO'S JOBS** (two on offer at a time, `caseOffer`): TAKE OUT THE SNITCH (a runner pushed into `g.bail506` with
`snitch`/`noShoot` -- he flees inside 280, isn't culled by distance), BRIBE THE WITNESS ($500 at her door, 1.8-6 k away),
THE MORGUE (hospital back wall, hold E 4 s), THE EVIDENCE ROOM (precinct back wall, hold E 4 s; walk off = start again).
Gold ring at the spot + screen-edge arrow. `caseDown`: -50%, or under 50% the case dies (cold, +150 XP, 180 s cooldown).
**ALONZO**: closes it at once for $2,000 + $80 a percent.
**THE WARRANT** at 100%: Drummond raids one of your businesses (its waiting cash goes to 0), heat held at 2+, the bar
drops to 70% and keeps going. Hooks: `stepRcase` in the story step line, `drawRcase` after `drawLedger`,
`drawRcaseArrow` after `drawMinimap`, `G.caseFn` in doAction after `G.ledgerFn`. Test hook `G.caseT`.
**Tests**: `t_509` (open, Pablo's call, witness, snitch, morgue hold, warrant, Alonzo + cooldown), `t_modes2`, `t_stu`,
`t_506`, `t_507`, `t_508`.

## LAYER 508 -- ROOM BETWEEN CARS, PASSING IN THE ONCOMING LANE, TIRE MARKS AND SMOKE

Block `b508.js` + `l508.py` (after `l507.py`). No new art.
**ROOM**: traffic used to follow to 44 units centre to centre -- cars are ~108 long, so they sat inside each other.
`gap508(v, o)` = half of each length + a quarter of its own length (AGGRESSIVE drivers: +6). The follow window looks
that far plus 130; queues at lights keep the gap; traffic keeps the same room behind your car.
**AGGRESSIVE DRIVERS** (`v.aggro`, 1 in 10, decided the first time a car is stepped, cruise x1.25): stuck behind a car
going under 80% of their speed, with 340+ to the next junction and the oncoming lane clear 520 ahead
(`clearAhead508`: anything ahead on the far side, your car included), they set `v.ovGo`; `v.ov` eases 0 -> 1 and
moves their lane line across by two lane offsets (`2 x dir x halfW x LANE`, the oncoming lane); they come back when
they're past it by 90% of a length, when a junction is under 200 away, or when the far lane stops being clear.
**YOUR DRIVER** (`stepAutopilot`): going fast (`sk "fast"`, losing someone, escaping, or 280+), a car within 200 in his
lane, 360+ to the next point and the far lane clear -> `A.ovGo`; `A.ov` swings the line he drives 110 to his left;
he stops braking for the car he's passing; back in after 1.2-4 s once it's clear behind or before a corner.
**COPS AND STREET-RACE RIVALS** (`dodge508`): a car within 170 ahead and 46 either side -> they steer round it (away
from the side it's on) instead of driving into it.
**TIRES** (`tireFx508`): anything (traffic, cops, rivals, your driver) turning faster than 0.95 rad/s above 190 speed
leaves two rubber marks on `g.skids` and a smoke puff (`g.puffs506`) every 0.09 s; the player's own skids smoke too.
Test hook `G.trafT`. **Tests**: `t_508` (stopped queues settle at +27 = a quarter of a car; aggressive drivers
passing; skids and smoke; your driver swings out past a slow car and back), `t_m13b`, `t_m14`, `t_m16c`, `t_506`.

## LAYER 507 -- SELLING WHERE IT MAKES SENSE, YOUR BUSINESSES' COUNTERS, THE LEDGER

Block `b507.js` + `l507.py` (after `l506.py`). No new art.
**SELLING** (`sellList507`, ahead of the old pawn list): PAWN SHOP as before (anything, half). GUN STORE ("SELL A
GUN" on its menu): guns only, 1.5 x what a pawn pays. JEWELLERS (`BIZ_MENU.jewel` now: gold ring $380, pearl
necklace $650, diamond earrings $1,200, SELL JEWELRY): jewellery only (`JEWEL_RX`: watch, chain, ring, gold...) at 80%.
DRUG CASHIERS (`isDrugCashier`: one corner store / grocer / bodega / liquor store / deli in four, by position):
"YOU HOLDING?" when you carry drugs -- 70% of street price, the whole stack of each kind. Gas stations and restaurants
never buy. The till still has to cover it.
**YOUR COUNTERS** (`BSTOCK`, THE COUNTER on every business screen -> `sp_bshop_<k>`; a locked line says its level):
THE HAPPY HIPPIE clean clothes $40 (heat -1, suspicion -30) / lockpicks $10 / fake plates $250 (the car you came in:
new plate, not stolen) / a clean record $5,000 (heat and suspicion 0). DREAD'S CORNER bags at cost: leaf $10, stone
$17, diamond $30, sky $60. THE RAVEN'S NEST a drink $5 (+2) / bottle service $50 (full health) / an Uzi $1,500 / an AR
$1,300. RAVEN AUTO fuel can $25 / lockpicks $8 / a full repair $300 / paint and plates $400. Bag things respect the
weight limit (504).
**THE LEDGER** (`ledgerAt`: a little table with a green book, 112 left of the scrapyard shelter's map table): E ->
`sp_ledger`: every business, level, take an hour, guards, cash waiting, the next level's price; COLLECT EVERYTHING;
OPEN any one (its screen, from anywhere). Business levels now cost $8,000 / $20,000 / $45,000 (`EMP_COST`).
Test hooks `G.ledgerT`, `G.sellT`. **Tests**: `t_507`.

## LAYER 506 -- COPS THAT RAM AND BACK OFF, CALLED SHOTS

Block `b506.js` + `l506.py` (after `l505.py`). No new art.
**THE RAM** (`updatePursuit`): it used to add a 120 shove and `applyDamage(240)` EVERY FRAME a cruiser was within
70 -- it pinned you and shredded the car, which ended the chase. Now: within 74, one shove (170) and one dent (150),
then `v.ramCd` = 2.6 s at 55% pursuit speed, so it drops back before it can come again. Cop top speed (250 + 55 a heat
level, 415 at most) stays under your car's (560 x its stats): on open road you pull away. Two cops a car (`v.crew`,
471) as before.
**CALLED SHOTS**: TARGET (RB) locks the nearest as before; when the lock lands on a car (`isCar506`: has `m`, no
`hp`) `g.lockPart` = 0 and each TARGET press steps round its parts (`G.partNext` runs first in `cycleTargetFn`) --
TIRES, ENGINE, GAS TANK, DRIVER, then each passenger (civilians: `occOf`, 505; cops: PARTNER) -- before moving on to
the next target. A red reticle sits on the part with its name and the odds (`partOdds` = base 38/42/12/22/26% +
4.5% a point of AIM, minus range past 120, minus 10% on the move). Each trigger pull at the locked car rolls once
(`G.calledShotFn`, from the on-foot fire code after the gunshot): TIRES `flat` for good (crawls at 70); ENGINE +0.15
damage a hit, smoke from 2 (`g.puffs506`), fire at 4, then it blows 4 s later; GAS TANK `carBoom` + a grenade blast,
done; DRIVER `driverDown` (the 471 roll-to-a-stop) plus a drift off line (`rollTurn`), and 1.4 s later everyone else
inside gets out (`g.bail506`: stand where they are, shoot at 380, never chase; on the bullet list, the blast list,
the TARGET cycle and the auto-aim); a PASSENGER hit is one fewer to get out. Missed shots say so. Test hook `G.calledT`.
**Tests**: `t_506` (lock -> 6 parts -> driver: 2 bail out; engine x4: on fire; tank: blown; one ram then ramCd),
`t_505`, `t_m13b`, `t_m16c`, `t_m12`.
**506b, SWITCH** (Donny: shoot one car, switch, the driver of another, swap back): TARGET on a locked car now WRAPS round
that car's parts (it doesn't fall through to the next target). SWITCH moves to the next / previous target without
touching parts: right stick left/right on the pad (a flick, latched; not while a menu is up), R / [ on the keyboard,
and a SWITCH button beside TGT while something's locked (`G.switchTargetFn(dir)` -> `G.cycleTargetFn(dir)`). Every car
remembers its part (`v.aimPart`), so coming back to a car puts the reticle where you left it. Test `t_506b`.

## LAYER 505 -- LOCKPICKS, BREAKING INTO PARKED CARS, CARJACKING; THE XBOX CURSOR FOR REAL; NO ACCIDENTAL REFRESH

Block `b505.js` + `l505.py` (after `l504.py`). No new art.
**THE GATE** (`G.stealGate(v)`, called in `mountNearest` right after it picks the nearest street car; Rey's story
only, `g.prisonMode`). Never locked: anything `named`, `storyCar`, `owner === "player"`, a bus, a police car, or a car
already `open`. PARKED (`parked`/`dead`): locked. No LOCKPICKS in the bag -> "IT'S LOCKED". With them: `g.pickCar`
{v, t, need = 3 s - 0.15 x STEALTH, at least 1.2}; stay within 120 (a gold bar over the car, `drawPick`); done ->
`v.open`, one use off the set (5 uses; the set's gone at 0), 1 in 5 the ALARM (flashing, `G.seenFn` = witnesses);
E again gets in through the normal path. DRIVEN: a carjacking. `occOf(v)` = 1-4 people (60/25/10/5%). Fight back
5/15/30/50% by that count: the car stops, `open`, and `hostile("wolves", ...)` crew of that size piles out (Rey isn't
in it; take it after). Otherwise the take goes ahead as before (the driver's panic ped and the witness call) plus a
line over the car (scared / angry / running, `JACK_LINES`) and the other passengers out and running.
LOCKPICKS: $15 at a pawn shop (`BIZ_MENU.pawn`); Leroy hands Rey a set as Mission 14 starts (`BEGIN98.ravenauto`
wrapped, once, `g.leroyPicks`). Weight 0.2 (504). Test hook `G.pickT`.
**THE XBOX CURSOR** (Donny: R3 said "locked" but the arrow stayed): a page can only hide the arrow (pointer lock) or go
full screen inside a real click. R3 now puts up "PRESS A TO HIDE THE CURSOR" over everything (`hud.lockAsk`, kept in the
0.15 s HUD refresh); the console's A is a click on it, and that click goes FULL SCREEN (no browser bar -- no refresh
button to hit by mistake) and locks the pointer (`G.cursorLockSet(true)`). B or R3 cancels, it times out after 7 s,
and the pad loop ignores A while it's up. R3 when locked frees the cursor and leaves full screen. If the browser drops
the lock (Esc), the game follows. **REFRESH / CLOSE** now asks first (`beforeunload`, after a save) whenever you're
past the title.
**Tests**: `t_505` (locked without picks, picking 2.85 s, open, in; a forced fight of 3; a scared carjack of 2; R3 ->
the prompt -> click -> locked and full screen), `t_m11`-`t_m15`, `t_m13b`, `t_504`.

## LAYER 504 -- THE FUEL CAN, THE TRUNK, WEIGHT

Block `b504.js` + `l504.py` (after `l503.py`). No new art.
**WEIGHT** (`itemKg`): guns by type (pistols 1.2, SMG 3, shotgun 4, rifle 4.5, melee 1, grenades 0.5); `g.p.bag`
things by name (FUEL CAN 9, radio 2, watch/chain/tickets/picks 0.2, a TV 12, else 1); prison pockets 0.2 each; the gun
in his hand counts. `carryKg()` against `carryMax()` = 20 + 2 x Rey's TOUGHNESS. Over it, `g.p.heavy` = 0.62 multiplies
his foot speed (`stepFoot`), and the shop counter won't sell him anything he'd carry. POCKETS shows what he's
carrying, each thing's weight and the total.
**THE FUEL CAN** (`CAN`: $40, 70% of a tank, 2.4 s to pour, 9 kg): on foot within 70 of any gas pump, E buys one
(`G.canBuyFn`; the label shows at the pump); the corner store and the bodega sell it too. E at the DRIVER'S DOOR of
your car (`carPts(c).door`, the left side; the car points along `ang`) with a can on you pours it (`g.pour`, a red bar
over the door; walk off and it stops); the empty can's gone after.
**THE TRUNK** (`trunkOf(c)`: a motor-pool car keeps its trunk on its pool slot, any other car on `c.tk` keyed by
plate/skin so a different car never inherits it; `trunkMax`: sports 40, sedans 80, wagons/vans/trucks 150 kg). E at
the BACK of the car (`carPts(c).back`) -> `sp_trunk`: TAKE OUT each thing (if he can carry it), PUT IN each thing he
carries (guns from the rack but not the one in his hand, anything in the bag), with both weights. `G.carryFn` runs
before getting in the car, so the back and the driver's door don't get you in -- anywhere else round the car still
does. Test hooks `G.carryT`, `G.pumpT`.
**Tests**: `t_504` (the can at a pump, the pour 10 -> 80, the trunk in and out, 3 TVs -> too heavy and slow),
`t_503`, `t_502`, `t_m16c`, `t_m14`.

## LAYER 503 -- THE CRUSHER MOVES OUT BACK, MONEY AND JUICE, THE TAKE DRAINS IN, REY & THE CREW (LEVELS AND STATS)

Block `b503.js` + `l503.py` (after `l502.py`); `b502.js`, `l502.py` and `b499.js` changed in place.
**THE CRUSHER, OUT BACK** (Donny): `crushPit()` now sits behind the building, `wallPt(H, back side, 0.5, 75)`, cached as
`H.pit503` (a fresh key, so a 502 save doesn't keep the front spot), with the switch box to its left. It's drawn in the
ground pass now (`drawYard; drawHill; drawCrush`), under the cars -- in 502 it was drawn over the parked car. Alley
trash stays out of it (`inCrushPit` in `inBozYard`, the cells' alley caches cleared when the pit is placed).
**MONEY AND JUICE**: bold, top right under the minimap (`hud.money` = cash minus whatever's still draining; `JUICE` =
`g.rep` for Rey, `g.juice` in detective mode). The small cash line top left is gone (STUDY still shows there).
**THE TAKE**: `storyComplete` now holds the pay back in `g.payDrain` {pay, left, t, k}; after 1.1 s it counts into the
money over ~2.6 s while the slam's +$ counts down and ten green $ fly from the middle of the screen to the money
(`rhCash`, looping until it's drained); the money turns green while it fills.
**LEVELS** (`g.lv[id]` = {lv, xp, pts, st}; `LV_WHO` = Rey, Leroy, Pablo, Ras, Dread, Katya, Jose, each shown once
they've joined, from the storyDone flags). XP: every mission win gives Rey 150 + pay/20 and every joined crew member
half (`lvWin`); a level needs 250 x level; Rey gets 2 points a level, crew 1. Stats 1-10: Rey AIM, DRIVING,
TOUGHNESS (+1 max health a point, live), STAMINA (+10 max stamina a point, live), STEALTH, CHARISMA; crew AIM,
DRIVING, TOUGHNESS, SMARTS (each starts with a strength: Ras tough, Leroy smarts, Jose driving, Katya aim). AIM is
for the called shots (507); the rest are stored for the layers that use them.
**THE SCREEN**: map (Start / MAP) -> REY & THE CREW (Y on the pad). Loading-screen art behind (`load_bg_2.jpg`), the
face, name, role, LEVEL, XP bar, points, ten pips a stat with a + each; left/right (d-pad left/right) cycles the
people; d-pad up/down + A spends; B or Y back to the map. React state `statsOpen/statsI/statsV`, `G.statsToggle`,
`G.statsCycle`, `G.lvList`, `G.lvSpend`. Test hooks `G.lvGiveT`, `G.storyCompleteT`.
**Tests**: `t_503` (the drain, XP to the crew, the stats screen, spending TOUGHNESS -> max health 11), `t_502` (the
crusher out back), `t_501`, `t_m16c`, `t_m15`.
**RUST** (503b, Donny's texture): `assets/tex/tx_rust_plate.png` (512x279, registered top level) on the pit's two
door leaves and the two rams (`rustFill`: a pattern at 0.32 scale anchored to each piece of steel, so it slides with
it; grey if the art isn't there). The leaves keep a dark rim, four bolts and the seam; the rams a worn steel face edge.

## LAYER 502 -- THE CAR CRUSHER, THE BUILDING PLATE

Block `b502.js` + `l502.py` (after `l501.py`). Art: `assets/scrap/sy_crush_pit.png` (454x244, Donny's pit) and
`assets/scrap/sy_crush_block.png` (113x112, the grey block), registered top level.
**THE CRUSHER** (`crushPit()` caches `H.pit` on the scrapyard building: 210x113, 300 px along the front wall from the
door, the inner box `ix/iy/iw/ih`, the switch box `sw` to its right). `yardFix502()` (once, `g.yard502`) takes the old
`sy_crusher` sprite and the `sy_crane` out of the front and puts the crane round the side (next to Mission 15's
`leakCrane` spot), moving `sy_wreck_b` out of its way. Closed: two grey diamond-plate leaves with a dashed yellow box.
Park so the car's centre is on the box (`carOnSpot`, under 30 speed), get out, E at the switch (`G.crushFn`) ->
`sp_crush` (worth, "comes out of the motor pool" for a pool car) -> `sp_crush_go`: `g.crush` = {t, k (skin), L, ang,
val (`CAR_PRICE` of the skin, else $6,000), col (`carColour`: the sprite's average, saturation weighted)}; the car is
sent to -90000 and its pool slot cleared. 0-1.2 s the leaves slide apart, 1.2-1.9 the car drops (14% smaller,
darker), 1.9-3.6 the rams press it along its short axis (shake), 3.6 the block (`tintBlock`: "color" blend of the
car's colour over the grey block, so the metal shading stays) and the rams pull back. Walk more than 1,100 px away
and the block sells for a quarter (`+$` flash, `g.crush = null`). `G.crushT()` test hook.
**THE BUILDING PLATE** (`stepBplate`): whenever `g.inside` changes to a building (not during a fade, the paper, a
dinner, Mission 0 or Katya's bedroom), `g.bplate` = {name (`b.name`, else `placeName`, else the kind), address
(`addressOf`)}; the HUD draws it 15% down, a size under MISSION COMPLETE, sliding in from the left, holding and
fading out over 3.8 s (CSS `rhPlate`).
**Tests**: `t_502` (crusher end to end: +$625 for a $2,500 car; the plate on entering the scrapyard), `t_m15`
(the Leak's crusher scene), `t_501`, `t_m16c`.

## LAYER 501 -- FOUR SAVE SLOTS AND THE NEW TITLE, THE MAP ON A PAD, THE PARKING COURT, THE PAPER TROPHY

Block `b501.js` + `l501.py` (after `l500.py`); `b500.js` was changed in place for the court. Rebuild: `cp
game_pre498.jsx work/game.jsx; python3 l498.py; python3 l499.py; python3 l500.py; python3 l501.py; bash build.sh`.
Art (top level): Donny's second yard sheet `assets/yard/yd_*` (lion patio, chairs, tables, kettle grill, cooler,
towel, pool shell/ladder/light...), `assets/items/it_paper_trophy.png`, `assets/props/pr_cone_side.png`,
`assets/tex/tx_ivory_tile.png`. Only the lion patio and the paper are used so far.
**SAVES**: `SAVE_SLOTS = 4`. `G.newestSlot()` (newest `t` across the slots, from `:lite` or the full save) and
`G.firstEmptySlot()`. TITLE: CONTINUE (only when a save exists) loads the newest slot; NEW GAME = the old PRISON MODE
start (`prisonStart`) into the first empty slot, or the selected slot when all four are full (the label says
OVERWRITES); tapping a slot card loads it; DETECTIVE / STUDENT MODE stay; the PRISON MODE button, BEGIN and START
OVER are gone (the tests now click "NEW GAME"). The map menu saves to 1-4.
**THE MAP ON A PAD**: A used to be FAST TRAVEL anywhere on the map (so SAVE asked where to travel). Now the d-pad
walks the `[data-mapopt]` buttons (gold outline, `g.mapSel`, reset when the map closes) and A clicks the lit one;
with nothing lit A does nothing. B / Start close.
**FUEL GAUGE**: with a controller (`padOn`, no touch stick) it sits in the bottom-left corner (bottom 14).
**THE PARKING COURT** (`hillOf` rewritten): the switchback is gone. Between the two hillside banks (104 px each:
brush, cypress, palms, contour lines) an asphalt court with 10 nose-in stalls (74 x ~132, wheel stops), an aisle
open to the street, a paver walk from the medallion (`yd_lion_patio`, centre of the stall row) up through the gate to
the door, and a zebra crossing over the aisle. `stepHillCars()` parks 7 crew cars (`HILL_CARS`, facing north) in the
nearest stalls during the BBQ (mansion 8-11) and breakfast (kings1 3-5), and re-parks them if traffic culls them.
`G.hillT()` test hook. Court lamps at night.
**THE PAPER TROPHY** (`trophyAt`, after `g.chapterOne`): a little wood table right of the map table in the
scrapyard shelter with `it_paper_trophy` on it; E reads it (`g.paper.read`, the same spin-in, `stepTrophy`: 6 s or E).
**Tests**: `t_501` (title states, NEW GAME, trophy, slot 3 save, court + cars, reload -> CONTINUE), `t_modes2`.
**NEXT** (the build queue is in the script doc, numbers moved up one for the crusher): 503-508 (done; 508 became the driving layer); 509 the heat case.

## LAYER 500 -- THE HILL, THE PAPER SPINS IN, DONNY'S NEWSPAPER AND CONE

Block `b500.js` + `l500.py` (runs after `l499.py`): `cp game_pre498.jsx work/game.jsx; python3 l498.py; python3
l499.py; python3 l500.py; bash build.sh`. Art: `assets/ui/ui_newspaper.png` (740x1017), `assets/props/pr_cone.png`
(64x64, registered top level; `drawCone2` uses it, code-drawn fallback).
**THE HILL** (`hillOf(M)` caches `M.hill`; `drawHill` in the ground pass after `drawYard`, before `drawBozHouse`): the
front of the Boznov lot, from the garden wall down to the street, stopping short of the North Spur deck
(`SX(1) - FWY_HW`). Inside the wall: lawns either side of the house and a paver motor court. Outside: grass with
each terrace lit at the top and shaded at the foot, wavy contour lines, a stone retaining wall (one terrace when the
slope is under 300 px, two above) with a drop shadow under it, the wall's own drop along the crest, a switchback drive
(`strokePath`, smoothed) from the gate to the street, 46 dry-brush clumps, cypress down both edges and at the gate,
palms at the kerb, long shadows for height. Nothing collides. At night `drawHillLights` (hooked into the night-lights
pass, "lighter"): lamps down the drive, palm uplights, the pool glow. `inBozHill` keeps alley trash off it.
**THE PAPER** moved and spins: the mansion now ends on the fireworks (8 s) -> MISSION COMPLETE -> `kings1`. In
`kings1` step 1, after Katya leaves the bedroom (14 s), `g.paper` spins in (tiny and turning three times, easing up
to full size in 1.4 s, a little bump as it lands), holds, fades at 7 s, then Damian's panel (`sp_deuce`, "THE SAME
MORNING") -> CHAPTER TWO (step 2). While the paper is up the game canvas is lifted over the HUD (`zIndex 45`,
reset when it's gone) and the dialogue line is cleared.
**Tests**: `t_m16c` (the new order through kings1 step 5), `t_hill` / `t_hilln` (day and night shots), `t_m13b`.

## LAYER 499 -- SUNSET AND SUNRISE, SHOP TIERS, THE RACE COURSE, THE BOZNOV BACKYARD, THE END OF CHAPTER ONE, CHAPTER TWO MISSION 1

Blocks `b499.js` (day/night, shop tiers, cones, shortcuts, backyard) and `b499end.js` (the ending + `STORY.kings1`),
inserted before LAYER 489 by `l499.py`, which runs after `l498.py`. Rebuild: `cp game_pre498.jsx work/game.jsx; python3
l498.py; python3 l499.py; bash build.sh`. The yard/newspaper art is registered at the TOP LEVEL (next to
`PD_ART.it_hippie_bag`), not in the block.
**DAY AND NIGHT** (`dayNight(clock)`, `stepDayNight()` just before the `g.night` lerp): 5:40 AM the sky warms orange,
6:00-7:00 it lightens, full day at 7; 6:40 PM orange, 7:00-8:00 it darkens, night at 8. `g.duskO` drives an orange
pass (multiply + screen) right before the night wash (40% indoors). Anything that sets `g.nightTarget` by hand (the N
key, a mission's begin) sets `g.nightLock`: it holds until the clock catches up with it or you sleep (`stepSleepFx`
clears it). Test hook `G.dayNightT(c)`.
**SHOP TIERS** (prison mode only): `PART_TIER(cat, part)` 1-4; `shopTier()` = 1 without a shop, Raven Auto level + 2
once `g.biz.auto` exists (Mission 14), so level 4 sells everything, at 15% off (`shopOff`). `garagePanel` shows locked
parts dimmed with `lockNote` ("NEEDS RAVEN AUTO LEVEL 3"); `garagePick` refuses them and charges the discounted price.
Drive up to Raven Auto's front and press E (`G.raShopFn`) for its parts wheel.
**M13 PINK SLIPS**: the driver suggests Stan's, `sp_parts` opens the real parts wheel, and the step moves on when the
car's mods change. The race marks are mid-side (mid east, mid south, the line), so the two corners can be cut.
`psCuts` finds a straight run across the lot inside each corner that misses every building/fence/drive-in wall
(`cutClear`) and keeps the one that saves most (> 200 px). It's drawn as a yellow dashed lane with moving arrows and
SHORTCUT (`drawCuts`), and counts as on-course for `offCourse`. Cones (`psCones`, every 150 px both sides, none at
corners or shortcut mouths). Off-course > 270 px for 2.5 s puts you back at the last mark.
**THE BACKYARD** (`yardOf(M)` caches `M.yard` = {x0, x1, top, deck, pool}; only when the house's back is north):
grass (`PAT.grass`), the ivory deck (`tx_ivory_deck` at half scale), the pool (`yd_pool` + moving `tx_pool_water` at
55%), `YARD_PROPS`, drawn by `drawYard` before `drawBozHouse`. The wall goes round the yard (`yardFences`, set in
`bozHouseInit`; the pool rect is a solid `nodraw` fence). Mission 16's charge goes off at the yard's top wall
(`mWall`) and `yardBreach` cuts a 170 px gap; `mEnd` puts the wall back. The back door: war-room art (0.935, 0.07)
<-> the yard just north of the house (`yardBackDoor`, `G.yardDoorFn`, labels both sides). `inBozYard` keeps alley
trash out of the yard (`cellAlley`'s `free`). Test hook `G.yardT()`.
**THE END OF CHAPTER ONE** (mansion steps 8-12, `endStep`/`endE`/`drawEnd` called from the mansion handlers):
8 `sp_kat_house` -> `sp_kat_next2` -> `sp_bbq` (fade, 8 PM, the yard). 9 talk to the 7 guests (`BBQ`, E within 70).
10 E at the grill: `sp_toast` (10 names, `GANG_NAMES` -> `g.gangName`) -> `sp_allies` -> `sp_cheers`. 11 fireworks
(`drawFireworks`, screen space, drawn after the minimap) for 7 s. 12 fade to the next morning (`nextDay(8,0)`),
`g.paper` = the Chronicle full screen (`drawPaper`; `ui_newspaper` if it's there, drawn in canvas if not) for 6.5 s,
then `sp_deuce` -> `storyComplete`, `g.chapterOne = 1`, `g.storyNext = kings1`. The old Mimi dinner ending is gone.
**CHAPTER TWO MISSION 1: A SEAT AT THE TABLE** (`STORY.kings1`): 0 CHAPTER ONE COMPLETE slam; 1 Katya's bed
(`putIn(M, 1, ...)`, `g.booze` blur, her two lines, she walks out); 2 CHAPTER TWO; 3 MISSION 1 -- out the back door to
breakfast; 4 E at the round table: `sp_top1` -> `sp_top2` (tap a seat to cycle who's in it, `TOP_WHO`; `g.topCrew`
{right, money, muscle, wheels}); THE MONEY = +10% in `empTick`, THE MUSCLE = guards $75 a day; 5 "find somebody who
can call a sit-down" (arrow to Dread's corner) -- the rest of the mission is the next build.
**Tests**: `t_m13b` (locked parts refused, tier-1 bought, two shortcuts found, on-cut stays on course, race won),
`t_m16b` (the whole mansion -> BBQ -> name -> fireworks -> paper -> kings1 step 5, lighting at 6:50 PM / 7:30 PM /
5:50 AM / 6:30 AM / noon, the N lock), `t_light`; the old `t_m0`, `t_m11`, `t_m12`, `t_m14`, `t_m15`, `t_sleep`,
`t_modes` still pass.
**STILL OPEN**: the sit-down half of Kings Mission 1. (The hill, the newspaper and the cone art are done in layer 500.) Top crew RIGHT HAND / WHEELS have no effect yet. Business L1-L4 bonuses (in the doc) are design only.


## 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 498 -- CHAPTER ONE FINISHED: MISSIONS 11-16, THE BUSINESSES, MIMI'S, THE SLEEP CARD

All in block `b498a-d` (before LAYER 489), wired by `l498.py`. Shared kit at the top of `b498a`: `SP`/`SPA` (story
panels `sp_*` and their buttons `story:sp_*`), `STEP98/OBJ98/TGT98/DRAW98/E98/BEGIN98` (per-mission step, objective,
arrow target, draw, E and start, dispatched from storyStep / storyObjective / storyTarget2 / the draw chain /
`G.storyEFn` (doAction, right after `setupEFn`) / the storyNext dispatcher and `G.storyStartT`), `NEXT98` (the chain
nest -> blowback -> pinkslips -> ravenauto -> leak -> mansion), helpers `putIn/putOut/artPt/person/ring/hostile/crewDead/
needHires/hiresMet/storyCarAt/takeStoryCar/keepStoryCar/parkCar/flashCruisers`.
**SLEEP CARD** (`G.sleepFade(apply, card)`, `stepSleepFx`, HUD `sleepCard`): every sleep (`G.sleepPick`, the student's
`stu:sleep`) fades to black, applies, shows the weekday and time (or a card the mission passes), fades back. Missions
use it for every time skip ("FRIDAY · 11:00 PM · THE RAVEN'S NEST").
**THE BUSINESSES** (`g.biz`, `empPanel`, `G.empPick`, ids `emp:<k>:<act>`, `G.empFn` = E inside a business near its
door, or on Dread's corner): hippie / corner / nest / auto; BOSS (Ras, Pablo, Leroy, Dread, Jose -- none = half, can't
level), LEVEL 1-4 (x1/1.6/2.4/3.5 of the base an hour; $5k/$12k/$25k), GUARDS 2/4/6/8 posts (FRONT DOOR, BACK DOOR, THE
FLOOR, FRONT LEFT/RIGHT, THE LOT, LEFT/RIGHT SIDE) from hired shooters/enforcers/dealers/lookouts, $100 a day each,
COLLECT. Guards are drawn standing their posts (`drawEmp`); they don't fight on their own yet. Rival attacks on businesses
are Chapter 2/3.
**MIMI'S**: 2B upstairs at Palm Court (floor 1 of Building A); E at her table = full health. `dinnerScene(lines, after,
guests)`: fade, the crew round her table, the lines, then `after` (Missions 12, 15, 16).
**M11 THE NEST (rebuilt)**: safecracker + 2 shooters + enforcer (no bomb); Leroy's cops lesson (`sp_cops`); E at any
booth calls Alonzo; Friday 11 PM raid out front (cruisers + siren); E at the back door (the locksmith); Victor's two men
with cones (E from behind = down, seen = fail); the safe (12 s); Pablo's car down the alley; the next noon Victor at the
Hippie signs; the business screen tutorial (Ras boss, 2 guards); Mimi and Jose move in. +$6k from the safe, +$8k pay.
**M12 BLOWBACK**: the school scene (camera holds, the boy and his grandmother walk out), Dread's corner hit (4 Bratva),
the Hippie: 3 waves, gas-can carriers walk for the door, FIRE meter (34% a can, 100 = fail), Pablo/Leroy/Ras fight;
Mimi with coffee; dinner. **M13 PINK SLIPS**: Jose; hire a driver; Stan's parts lesson fits a V8, a street wing and
3 nitro (`setMods`); a practice lap (marks round Stan's); Saturday: countdown, 3 marks + the line, Nicky runs the
route on a timer (`S.nk`, length/62 s); win = Nicky's car in the motor pool + `g.raGateKey`; lose = $2,000 and again.
**M14 RAVEN AUTO**: hire thief + fence; 1 AM, five chalked cars in a row, the night man walks the row (seen = alarm,
3 Bratva); E and stay 3 s per car, the crew drives four out, the fifth is yours; Grigori's men; the yard: Grigori
walks; the fence: 3 to the motor pool, 2 sold (+$8k). **M15 THE LEAK**: Katya at the Nest after hours; the fake job;
E at the crane: Tony's call; tail his car (scripted route, `tonyAt`; >1300 lost, <170 for 2.5 s made); the photo under
the freeway; the crusher (`sp_crusher`), Tony turned (`g.tonyTurned`); Katya's pact; dinner. **M16 THE MANSION**:
hire bomber + 2 shooters + enforcer (on top of what you have); 1 AM, the storm drain (`mDrain`, kept on the map);
the charge (6 s); the garden (4); the ground floor with Grigori (indoor crew, double hp); upstairs (3); Vlad's study
(Katya); Tony: CALL ALONZO (`g.tonyFate = "kestrel"`) or the BUS (`"bus"`, -$500); Katya keeps the house
(`g.katyaHouse`, `g.manorOurs`); dinner; the Deuce panel; CHAPTER ONE COMPLETE (+$25k).
Tests `t_m11`..`t_m16` (each starts from a skipped Mission 0 and fakes `storyDone`), `t_sleep`; helper `lib98.py`
(`fx` skips a fade -- headless frames are slow, so the tests also fast-forward timers like the safe and the hot-wire).

## 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 497 -- MISSION 0: THE SETUP (1969, FOUR BLOCKS) + THE VERDICT FOLDER + NEW CHARACTER ART

**Story change (Donny): Rey went in in 1969 and did SEVENTEEN years** (twenty-five, out in seventeen), so Rochelle was
pregnant when he went in and the boy is 17. Every "ten years" line in the game is now seventeen (regex pass in `l497b`,
except Katya's "ten years we have not moved one block" and Pablo's bar line), Eddie's gas joke is 35 cents, the 1976
clothes are 1969. A new Rey game opens in 1969 (`STORY.setup`, block `b497` before LAYER 489); `startPrisonMode` sets
the prison up, then (no `storyDone.setup`/`lastday`) calls `setupBegin()`, which borrows the out-of-prison city the way
DAY OUT does and turns on `g.flash1976` (sepia `backdrop-filter`, grain, vignette; the corner says 1969).
**Only about four blocks are open** (`S.box`, padded around Rochelle's house and the drop; `suClamp` holds you and
your car inside). Past the edge the city is dark and under construction (`drawSetupTop`, drawn over the roofs:
chain-link round the edge, sawhorses where the roads cross it, work lamps, dirt piles). Cars on the road wear 1969
bodies while it lasts (`suEra`, `v.m69` keeps the real one and gives it back). Young Rey is `yt_rey69` (hero pkey).
Steps: 0 ROCHELLE'S -- the biggest house in Old Town gets `rf_rochelle69` over its roof and a driveway, Rey wakes up
inside with Rochelle (`su_morning` -> `su_morning2`: she almost tells him she's pregnant; a horn; SKIP THE FLASHBACK
is there) -> 1 out to Tiny's 1969 sedan -> 2 Tiny drives (`g.auto`, who TINY) to the drop (`suWare`: a warehouse,
garage, store or office 1.4-3.6 blocks away, unnamed first -- there are no warehouses near Old Town, so it's usually a
shut-up store) -> 3 he drops you and pulls away -> 4 the body and the revolver, E -> 5 two 1969 cruisers
(`veh_cruiser69`), siren, a 1969 cop (`yt_cop69_a`) runs you down -> 6 black -> 7 the courtroom (Damian, Julian and
Rochelle in their 1969 sprites), an answer (`su_court` -> `su_said`), **THE VERDICT FOLDER**, the sentence
(`su_sentence`) -> 8 the bus: black, one line -> 9 Harlan's walk-in -> 10 E: LIE DOWN -> 11 SEVENTEEN YEARS LATER.
**The verdict folder** (`G.verdictShow({face, name, caseNo, charges, guilty, done})`, `stepVerdict`, `drawVerdict`):
ui_folder slides up, the photo on the left, the charges type out one by one, GUILTY / NOT GUILTY slams on; E skips to
the stamp, then closes. Built for every trial -- the detective trials can call it next.
**Mission 4:** Katya shoots the radio out of Tony's hand ("Sit. You work for him now."); his tag says HANDS UP.
**Fix:** layer 497's first cut registered Dread/Tony/Harlan/Nicky art INSIDE the component, after the loader had run,
so none of it loaded. All of it is registered at the top level now (beside `it_hippie_bag`).
Test hooks: `G.setupTT`, `G.setupEnterT`, `G.setupSkipT`, `G.setupInfoT`, `G.kindsNearT`. Tests `t_m0` (whole run),
`t_m0s` (skip), `t_m0z` (close-ups). Old tests that start a fresh PRISON MODE land in Mission 0 first (`story:su_skip`).

**Art:** art_497.zip (Dread, Tony, Harlan, Nicky, Rey's face, Mission 11 props, rh_roof_1..6) and art_497_1969.zip
(the 1969 cast: `yt/pt_rey69, rochelle69, damian69, julian69, tiny69, cop69_a, cop69_b`; `yt/pt_yuri`; `cars/veh_69_*`,
`veh_cruiser69`; `city/pr_sawhorse, pr_chainlink, pr_worklamp, pr_dirtpile`; `roofs/rf_rochelle69`; `ui/ui_folder,
ui_stamp_guilty, ui_stamp_notguilty`). Talk faces: REY (young in the flashback), ROCHELLE, TINY, RHPD, YURI, C.O.
HARLAN, TONY, NICKY, ALONZO, VLAD, GRIGORI, DAMIAN, JULIAN; DREAD uses `pt_dread`.

**Script doc:** 16 missions in Chapter 1; Chapter 2 is the Kings (earning their trust, learning to run the empire),
Chapter 3 is the Kings' war on Sanhe (the key: convince Don Vescari in Kestrel that Rey can take Sanhe's place), the
Deuce's final war in Chapter 5 or 6.

## 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 496 -- THE BANK SPLIT: $10,000 FOR ALONZO

Donny: the bank job pays for Alonzo's raid on the Nest (Mission 11). The take is still $50,000 (`S.take`), but at the
trunk Leroy holds $10,000 back for Alonzo and Rey keeps $40,000 (`STORY.bankjob.pay = 40000`; the split panel says so).
Script decisions recorded in the doc: after Mission 11 Leroy gives Pablo's family (Mimi and Jose) an apartment at Palm
Court; Tony LIVES in Mission 14 (his car goes in the crusher, he goes back to Vlad with a message).

## 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 495 -- THE LOADING SCREEN SHOWS THE KID

The load was over before the fourth lead (THE KID) ever came up. `LoadingScreen` now starts each launch on the next lead
round (`ironlion.loadLead` in localStorage; the very first launch starts on THE KID), and the screen holds 4.3s (two
leads) instead of 2.6s. The story script for missions 5-15 is in the script doc ("The Fall Guy: Game Script").

## 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 494 -- NEW TELEPHONE POLES, EDDIE'S JOKES, THE WING ON THE CAR, THE CAKE, SAVE SLOTS

- **TELEPHONE POLES** (Donny's top-down pole; `assets/city/pl_pole_arms.png` + `pl_pole_shaft.png`, split so the crossarm
  can turn): a grid along EVERY city street -- avenues down the east kerb, cross streets along the south kerb -- one
  mid-block every POLE_STEP (half a block), so never in an intersection, never in the road, and none on or under the
  freeway (FWY_V / FWY_H legs, `onDeckSpan`). Crossarms sit across the line (on a cross street the crossarm piece is
  turned 90 degrees over an unturned shaft); six wires, insulator to insulator, pole to pole down the street. The old
  side-on pole sprites (pl_pole_single/double/...) are no longer drawn. Size: `POLE2.W` (88 world units across).
- **EDDIE'S MATERIAL** (`EDDIE_JOKES`, 30 one-liners, 1986, no brand names): a line every 9-14 seconds on the Day Out
  tour while he's driving and nobody else is talking, and one when you take his cab by phone.
- **THE WING** (Stan's / the parts shop `wing` slot): was never drawn on the car. Now `drawCarWing`: the wing art is a
  view from behind, so it's turned round -- blade across the very back, stands reaching forward onto the trunk, as wide as
  the car; the lip spoilers (wg_1_*) sit flat on the trunk lid.
- **THE CAKE**: `assets/prison/pr_cake.png` (Donny's sheet cake, "FREE", the slice gone and the fork) -- in the mess hall
  kitchen and on the table in your cell.
- **SAVE SLOTS**: three. Slot 1 is the old save (same key, nothing lost); 2 and 3 are new. The title shows all three (mode
  / story mission, cash, when) -- tap one, then CONTINUE (or BEGIN if it's empty); START OVER wipes only the selected
  slot. In the menu: SAVE NOW (to the slot you're on) and SAVE TO 1 / 2 / 3. Autosave and the bed save write to the
  current slot. Hooks: G.slotsFn, G.slotPick(n), G.saveToFn(n). Test: `h/t/t_slots.py`.

## 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 493 -- LAST DAY IN, EDDIE'S CAB, JOSE'S RECON (+ EDDIE, JOSE, MIMI ART)

**ART** (Donny's three sheets, order reversed on the page): `assets/crew/pt_eddie / yt_eddie` (EDDIE MORALES, the cab
driver, the mustache -- the "Ricardo" sheet), `pt_jose / yt_jose` (JOSE DIAZ, Pablo's nephew -- the "Eli" sheet),
`pt_mimi / yt_mimi` (MIMI, Pablo's sister, Jose's mom -- the "Lorena" sheet). Top-down plates cut at the waist so the
walking legs show. Mimi is registered but has no scene yet. **The cab driver is EDDIE now** (every "Earl" in the Day Out /
phone code renamed; `g.earlNum`, `stepEarlCab`, `earlCab` keep their old internal names).

**TALK FACES**: every driveTalk line shows the speaker's face beside the box (`TALK_FACE`: EDDIE, JOSE, MIMI, PABLO,
LEROY, RAS, KATYA, VICTOR, DREAD -- matched on the start of `who`).

**CAMERA PAN** (`camPanTo(x, y, 6)`): the follow camera eases to a spot, holds, and comes back (1.5s in, 1.5s out).

**STREETS** (`streetStop`, `streetRoute`): a driven stop is a kerb on the nearest real road on the place's side -- the
cab and Jose never cut across a lot to reach a door any more.

**LAST DAY IN**: Leroy, Ras and Pablo stay in their cells beside yours all day (no schedule) so you can find them. Each
side job you finish SLAMS: "SIDE JOB COMPLETE · RAS · THE STASH · 1 / 3" (new slam kind "side", green, 3s). When all
three are done they're in YOUR cell round the cake (`drawCellParty`; the cake is procedural until `assets/prison/pr_cake.png`
exists -- it's registered and drawn the moment it does). The goodbye -> fade -> 5:00 AM, two C.O.s at the cell, and they
WALK you out (`g.escort`: down the block to its door, across the yard to the gate, a C.O. on each side) -> MISSION
COMPLETE -> Day Out at the gate. (No more sleeping to end it.)

**DAY OUT**: Eddie stands by his cab at the gate. E: he introduces himself (`do_eddie`), gets in and waits; you get in.
At every stop he pulls up at the kerb and the camera pans to the place for six seconds while he explains it.

**FIRST DAY OUT** now opens with JOSE: honking outside Palm Court, his hatchback at the kerb (`josePrep`). E: "Pablo's
nephew, his sister Mimi's my mom -- Tío says you need wheels." He drives you toward the lot explaining the plan, stops
round the corner; you get out (E), steal one (unchanged), drive to the marked corner where he's standing and STOP -- he
runs over and gets in, and DRIVES YOUR CAR place to place (`joseLeg` / `JOSE_LINES`): each Boznov place he pulls up,
says what it's for, the camera pans to it, it goes in the book (Victor, Grigori and the house now show the family's own
plates). Then he drives you home ("I'll walk back for mine") and Pablo's on the sofa as before.
Hooks: G.escortT, G.joseT. Tests: `h/t/t_ld.py` (the last day, the walk out, Eddie), `h/t/t_jose.py`.

## 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 492 -- THE BRATVA CARD

- `assets/cards/card_rus.png` (Donny's art: the double-headed eagle with the chain and the razor, "BRATVA") is in, registered
  with the other gang cards, and `CARD_OF.rus = "rus"` -- the Boznovs' card on the map table (PLAN A JOB -> any gang job ->
  the BOZNOV card) and anywhere else `cardFor` is used.
- Mission 11 note from Donny: you DRIVE to a sewer entrance and the crew blows its way in from there. Not built yet.

## 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 491 -- MISSION 10 (THE CORNER) AND THE OPENING OF MISSION 11 (THE RAVEN'S NEST)

**MISSION 10 · THE CORNER** (`STORY.corner`, $2,500; starts 5s after the bank job). Ras phones: come to the Hippie.
0 inside the Hippie: Ras explains dealers and brings DESMOND "DREAD" MORGAN (his friend, his own Uzi, free -- Ras vouches):
`co_hire` puts him on the board (`B.men`, dealer, gear smg_uzi) and unlocks "dealer" in the hire lock -> 1 GET STRAPPED
(a gun in your hand) -> 2 Pablo's car at the Hippie (Pablo, Ras, Dread) -> 3 the gas station nearest the Hippie
(`cornerGas()` = gasNear): a Bratva dealer + two men (`warCrew("rus")`, angry at you) behind the pumps -- put them down ->
4 walk Dread to the marked corner behind the station, he takes it: WEED (ROCK / POWDER shown LOCKED) -- `g.dreadCorner`,
`B.corners++`, rusTake on it; drawn there, and after 10 game hours with a crew of three round him (`drawDreadCorner`) ->
5 back to the laundromat (the Hippie's street floor): Leroy says the Russians' crown jewel is THE RAVEN'S NEST. Complete.
- Not done: Dread's corner pays nothing yet (he isn't a B.spots corner -- it's drawn on its own so he isn't doubled); the
  drug swap is only the locked buttons.

**MISSION 11 · THE RAVEN'S NEST (opening only)** (`STORY.nest`). Starts with the same morning-after scene, second time
(`g.morning.after = "nest"`: "AGAIN?", "This ALSO never happened"), then "...What the hell." -> 1 the yard -> 2 E at the
map table: Leroy's plan (`ne_plan`: bomb maker in the storm sewer under the Nest, blow the floor, up through the hole,
take down Victor's men, force his office, he SIGNS; Katya's rule -- Victor lives) -> 3 HIRE a BOMB MAKER, TWO SHOOTERS,
an ENFORCER (`g.hireNeed` puts them at the front of the hire pool and lets them past the respect cap) -> 4 "the crew is
set". **Donny's message was cut off here ("I should have to drive t...") -- the rest of the job is the next build.**

## 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 490 -- THE BANK JOB REDONE: MASKS, THE ROOM, TALK THE MANAGER, THE ALARM, THE BAGS, $50,000

Mission 9 now: 0 yard briefing -> 1 the lowrider -> 2 drive to the bank -> pulling up, Pablo hands out **MASKS**
(`g.masks`: drawYouth draws a black ski mask with eye slits over the hero and every crew follower) -> 3 in (back door with
the locksmith, or the front) -> **the crew takes the room**: every person in the bank put hands-up (back plan: just the
manager and the guard) -> 4 E at the MANAGER: **the talk** (`bk_talk`): he's a FAMILY MAN (the photo on the desk), a
COMPANY MAN (procedures, time locks) or a COWARD (shaking) -- the intro tells you which; THREATEN works on the coward,
REASON ("it's insured") on the company man, CALM ("you're going home to your girls") on the family man. Two right: he
walks to the vault and opens it (`g.bankJob.coop`: stepBank no longer needs a gun on him). Two wrong: SILENT ALARM --
3:00 on the objective, and the locksmith drills the vault: `BK_CRACK` by his stars (fitStars on locksmith): 4-5 = 1:00,
3 = 1:50, else 3:04 (the cops beat him). At 0:00 the cops come (heat 3). -> 6 E at the vault: **THE BAGS** (`g.bagsOn`:
the Happy Hippie duffel, `it_hippie_bag`, bobbing over you, Leroy and the locksmith) -> 7 out to Pablo, E at the car: LOAD
THE BAGS -> 8 lose any heat (Pablo tells you: DRIVER -> LOSE 'EM, or shoot their tires) and get to the Hippie -> 9 out, E
at the car's trunk: UNLOAD -> $50,000, MISSION COMPLETE. The vault's own random money isn't paid in story mode.
- Hooks: G.hippyFrontT, G.vaultT. Tests: `h/t/t_m9b.py` (win) and `t_m9b.py lose` (the alarm and the drill).

## 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 489 -- STORY-ONLY HUD, THE STORY ARROW AND ROUTE, PABLO AT THE HIPPIE, THE BOZNOVS ON THEIR FEET

- **STORY-ONLY HUD** (`storyOnly()`: Kestrel mode, out): no scanner calls (spawnCrime), no street races (spawnRace), no
  SKY bar, no JUICE, no SAVED/LOST, no DETECTIVES line, and the RHPD line only while YOU are wanted. The gold arrow points
  only at the story (or a job you started yourself).
- **THE STORY ARROW + MINIMAP ROUTE**: `storyTarget()` (+ `storyTarget2` for missions 9-11) gives the spot for every step
  of every mission; drawTargetArrow points at it and the minimap draws the road route (`roadRoute`, refreshed every
  second) in gold with a pulsing pip, or an edge arrow when it's off the map. Hook: G.storyTargetT.
- **PABLO AT THE HIPPIE**: when he isn't riding with you (`g.pabloAt === "hippy"`) he sits at the first hookah table in
  the club. E: a line, or RIDE WITH ME (he joins as your driver).
- **THE FAMILY'S TOP-DOWN PLATES**: Donny's top row (the busts, `bust_bozni_*`, already in the assets) are now
  `yt_bozni_vlad / victor / grigori / katya`; the bottom row stays their profile pictures (`pt_bozni_*`). A bust has no
  arms, so drawYouth draws arms (jacket colour + hands, swinging against the legs) for anything in `YT_ARMS`. Victor at
  his poker table, Katya everywhere she appears (the yard office, the Hippie, the party, the morning after) now use them.
  Vlad and Grigori stand at the war room table in the Boznov house, Victor and Katya at the Raven's Nest bar
  (`drawBozFolk`).
- **NEW ART**: `assets/items/it_hippie_bag.png` (Donny's Happy Hippie duffel). Waiting on: `assets/cards/card_rus.png`
  (the Bratva's card for the map table -- `cardFor` uses it the moment it exists).

## 00000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 488 -- MISSION 8 (THE MAP TABLE) AND MISSION 9 (THE BANK JOB)

**MISSION 8 · THE MAP TABLE** (`STORY.maptable`, $1,000; starts 5s after Wash Day). Leroy phones: everybody at the yard.
- 0 the yard -> 1 E at the map table (`G.opsBoardFn` is intercepted): Leroy's five-page tutorial (`MT_PAGES`: the board,
  HIRE PEOPLE + respect, PLAN A JOB + send/lead + YOUR PEOPLE, the yard: motor pool / armory / gangs / Kestrel, the job).
- 2 HIRE: Leroy fronts $1,200 and the board opens on HIRE. **HIRE LOCK** (`hireLock()`): in story mode (prisonMode +
  preleased, until `g.hireFree`) only the trades in `g.hireOK` appear -- Mission 8 sets `["locksmith","lookout"]`;
  `roleOpen` and `hirePool` respect it (the pool alternates the open trades so both are always there). `g.hireFree`
  is set when Mission 9 is done -- the whole board opens.
- 3 Pablo's lowrider out front of the yard (`mtCar`, E: `G.mtCarFn`) with Pablo, the lookout and the locksmith ->
  4 FIRST MERCHANTS BANK (`theBank()`; DRIVER -> WHERE TO has it) -> the lookout gets out across the street ->
  5 CASE THE FLOOR, no gun drawn (fail if you pull one): stand by the TELLERS, MANAGER, GUARD and the VAULT door
  1.4s each -> 6 round the BACK with the locksmith (marked ring, 4s) -> 7 back to the yard -> 8 E at the table:
  **PICK THE PLAN** (`g.bankPlan`: "back" = before opening, quiet; "front" = at opening, loud) -> 9 sleep.
- Crew stands round the table in the shelter (drawMaptable).

**MISSION 9 · THE BANK JOB** (`STORY.bankjob`, $5,000 + whatever's in the vault). Starts at 6:30 (back) or 8:20 (front).
- 0 the yard: Leroy's briefing (`bk_go`; hands you a pistol if you have none) -> 1 the lowrider (Pablo, Leroy, the
  locksmith; the lookout's already on the corner) -> 2 drive to the front or the back -> 3 out of the car (it parks as
  `bkCar`, Pablo waits in it). BACK: stand at the back door 6s, the locksmith opens it, you're put inside by the vault
  and the bank is just the MANAGER (customers, tellers and the guard filtered out); the drawers are skipped and the heat
  stays low. FRONT: walk in the front door; the full layer-496 stick-up (drawers + vault, heat 3).
- 4 THE STICK-UP: gun out by a teller/the manager, **E** (story only -- `G.bankFn` was touch-button-only; now E works,
  so the gamepad can do it) -> 5 the manager walks to the vault and opens it (stepBank) -> E at the vault (`G.vaultFn`,
  which now moves the story on) -> 6 out to Pablo (E at the car, `G.bkCarFn`) -> 7 to the yard (or DRIVER -> GET US OUT)
  -> 8 THE SPLIT at the yard -> MISSION COMPLETE.
- The vault pays what the bank system pays (a downtown bank: $60-120k). That's a lot for the first job -- if it should
  be smaller in story mode, cap `take` in G.vaultFn when `g.story.id === "bankjob"`.
- Test hooks: G.mtTableT, G.yardFrontT, G.bankT, G.vaultT, G.vaultDoorT. Test: `h/t/t_m89.py` (both missions, back plan).

## 0000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 487 -- WASH DAY REDONE, DRINKING, THE PARTY, THE MORNING AFTER

**WASH DAY** (Mission 7) steps are now: 0 Leroy at the yard -> 1 work blues -> 2 THE TRUCK (Pablo and Leroy are waiting
beside it; getting in puts both in the cab -- `washBoard`) -> 3 THE DOCK -> 4 loading -> 5 back to THE HAPPY HIPPY
(not the yard) -> Ras climbs out in the lot (`wash_ras`) -> 6 DOWNSTAIRS (the club, floor 0) -> 7 THE PARTY ->
blackout -> 8 THE MORNING AFTER -> MISSION COMPLETE. (The old "sleep to finish" is gone.)
- **BACK IT IN.** At the dock, `truckBacked()` (nose pointing north, tail to the prison). Nose-in: a guard walks round
  to the cab -- 50% he knows your face (MISSION FAILED), 50% "back it in next time, genius". `g.noseRoll` forces the
  roll in tests. Pablo warns you when you're within 700 and driving yourself. Give Pablo the wheel (DRIVER -> WHERE
  TO -> "KESTREL · THE LAUNDRY DOCK · BACK IT IN"): the dest has `after: "backin"` and ccarLegEnd -> `washBackIn()`
  backs the truck in for you.
- **THE PARTY** (`PARTY`, drawParty, G.partyFn on E -- nearest thing wins, bar included): Pablo, Leroy, Ras (street
  clothes) at the first hookah table, Katya at the end of the bar, six regulars. The bar: beer / vodka / whiskey. Pablo:
  HIT THE JOINT (the old PFX.weed effect). Katya: DRINK WITH HER. Leroy, Ras: talk. Once the Hippy is yours
  (`g.hippyOwned`) the bar works any time.
- **THE MORNING AFTER** (`morningBegin`, stepMorning, drawMorning): Palm Court 1A, 9:40 next day. Both of them on the
  bed under the shower-style mosaic (Rey's darker), "...Rey? REY?!", she runs to the bathroom, "Blyat'!", comes out
  dressed (`yt_dn_7`, the stand-in until Katya has a top-down plate) and walks out: "This never happened." Complete.

**DRINKING** (`BOOZE`, layer 487, every mode): each drink blurs the screen. The first lasts 10s and every one after
DOUBLES it (10, 20, 40, 80, 160); the blur gets heavier, from three drinks the screen sways. Sober up and it resets.
The SIXTH while still drunk = **BLACKOUT**: fade to black, wake up 4-6 hours later beside a phone booth somewhere
else, up to a quarter of your cash gone (in the cells: same spot, time gone). At the party the blackout is the
morning-after scene instead. Counted: bar drinks with a drink in the name (BOOZE_RX; SHOT AND A BEER / SIX-PACK = 2),
liquor-store bottles, a beer or flask picked up, prison hooch, the Hippy's bar. Weed is unchanged and stacks with it.
HUD: `hud.blackA` (the black overlay). Hooks: G.drinkT(n), G.boozeT(), G.partyT(), G.morningT(). Tests: `h/t/t_m7b.py`,
`h/t/t_morn.py`, `h/t/t_misc487.py`.

## 000000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 486 -- THE BRATVA GET BODIES (BOZNOV HENCHMAN PLATES)

Donny's three Boznov sheets. Who's who, checked against the game: Victor (denim jacket, burgundy shirt, gold chain),
Vlad to his left (grey suit, green eyes), Katya (blonde, black leather), Grigori "Medved" Orlov (grey buzz cut, tactical
vest). The family portraits (`pt_bozni_*`), busts (`bust_bozni_*`) and the four henchman faces (`pt_bratva_1..4`)
on the other two sheets are the SAME art already in the game, so they were left alone.

- **NEW: `assets/crew/yt_bratva_1..6.png`**, the six top-down henchmen: 1 spiky hair and grey bomber, 2 buzz cut and grey
  bomber, 3 beanie and leather, 4 brown corduroy blazer, 5 striped sweater, 6 maroon blazer. Registered as `BRATVA_YT`
  (module level, beside the HIRE_ROLES PD_ART loop).
- **THE BRATVA ARE ON THE STREET.** `warCrew("rus")` used to return before `g.crews.push` (layer 475, "no street art").
  That return is gone. Every rus member gets `hxArt` = a Bratva plate (rotating from a random start per crew, so a crew
  of six is six different men), and `rankKit` gives one to any other rus body. drawKing already draws `hxArt` through
  drawYouth, so they walk, shoot and swing like the villain henchmen.
- **STAND-INS REPLACED:** the card-room door men (`yt_bratva_<R.v>`, same number as their `pt_bratva` face), the
  scrapyard guards in Mission 4 (one each, rotating), the laundromat muscle in Mission 6 (`yt_bratva_2`), and the
  men minding the Russian businesses in Mission 3 (`yt_bratva_4..6`).
- Test hook `G.bratvaT(n)` puts a rus crew of n next to you and returns their plates. Test: `h/t/t_brat.py`.
- **STILL NO TOP-DOWN** for Vlad, Victor, Katya, Grigori or Tony: Victor still borrows `yt_hire_fixer_3`, Katya
  `yt_dn_7`, Tony `yt_hire_fixer_2`.

## 00000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 485 -- ALL IN (MISSION 6) AND WASH DAY (MISSION 7)

Continues LAYER 484. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run headless: both missions start to finish; all
modes boot. Art: `art_485.zip` -- the Happy Hippie Laundry Co. truck (`vh_hippy_truck`, turned nose-up, 160 x 61).

- **ALL IN** (`STORY.allin`, chained after Friday Night): 7 PM, Katya on the phone -- put on **THE SUIT** (closet wheel / any
  dresser) -> the Happy Hippy: Katya fronts **$20,000** -> the laundromat muscle by the basement stairs (E, `G.muscleFn`) ->
  downstairs, the red room's door man seats you at **VICTOR'S TABLE** (`victorTable`: high stakes, $500-$5,000 in $500 steps --
  `t.lo / t.hi / t.step` on any table now). **Beat Victor 3 times** (`G.onPoker`, called after every poker hand) without going
  broke (broke = MISSION FAILED). Katya talks him into putting **the club on the line**: one hand at $5,000 -- win it or MISSION
  FAILED (retry from the checkpoint before it). Win: `g.hippyOwned`, the Hippy is no longer the Boznovs' (`bozni` cleared), Katya
  takes her $20,000 back. Cut: the Boznov house -- Victor tells Vlad; Vlad: “He is someone I will be keeping my eye on.”
  Back at the Hippy, just guests; **Pablo runs it** (`g.pabloAt = "hippy"`). MISSION COMPLETE.
- **OWNED** (`stepHippyCars`): whenever you're near the Hippy, the **laundry truck** waits in its lot (yours: E gets you in --
  `G.truckFn` runs first in the E chain), **Pablo's lowrider** out back when he's not with you; **Leroy's car** at the yard.
  Both doormen offer **HIGH STAKES** any night: $500 to sit, $1,000-$5,000 hands.
- **WASH DAY** (`STORY.washday`, 4 s after All In): see Leroy at the yard -> his plan (Ras in a laundry cart) -> run home and
  put on **THE WORK JACKET** -> the Hippy's truck -> the **laundry dock** outside the Kestrel gate (`washDock`, marked) -> stop in
  it and **stay in the truck** 9 s while they load (get out within 700 of it = MISSION FAILED: “a guard looked at you twice”)
  -> the yard: Ras climbs out of the sheets (`g.rasJoined`, `g.crewJoin.ras`) -> home -> sleep -> +$1,500.
- Not done: clearing other cars out of the scrapyard (the motor pool is the escape-route system's -- left alone).
- Hooks: `G.washDockT`. Tests: `t/t_m67.py`, `t/t_m7.py`.

---

## 0000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 484 -- FRIDAY NIGHT (MISSION 5): THE RUNNER, ALONZO, LEROY'S OUT

Continues LAYER 483. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run headless: Friday Night start to finish; all
modes boot. No new art.

- Chained after The Scrapyard (`STORY.friday`, `fridayBegin/Step/Objective/Panel`, `drawFriday`). 9:30 PM: Katya on the phone --
  Grigori's runner takes the week's cash from Raven Auto to the Happy Hippy. Pablo at the kerb (`G.pabloCarFn` now serves both
  missions). DRIVER -> **RAVEN AUTO · ACROSS THE STREET** -> the runner pulls out (a brown Corvane Cresta, moved along the road
  route by hand) -> take the wheel (DRIVER -> I'LL DRIVE) and **RAM** it (within 110) before it reaches the Hippy (it gets there =
  MISSION FAILED) -> E at his car: **+$6,000**, heat 2 -> get 1,300 away.
- **DET. ALONZO** (the vice detective who's for sale -- `yt_alonzo` / `pt_alonzo`, drawn in the alley) in the alley behind the
  station (`friAlley`): $5,000 and Leroy's parole goes through Monday. Two days pass; 9 AM.
- **KESTREL STATE · THE GATE**: Leroy gets in (`g.pfol`). **THE SCRAPYARD**: he'd rather stay and build something than lie around
  an apartment -- `g.leroyJoined`, `g.crewJoin.leroy = "the yard"`; “I might know a way to get Ras out. Come back tomorrow. Bring
  guns.” -> HOME -> sleep -> MISSION COMPLETE +$1,000.
- Every leg has a DRIVER destination (`FRI_D`). Test: `t/t_m5.py`.

**NEXT**: Mission 6 (Ras) -- Leroy's plan, with guns.

---

## 000000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 483 -- REY'S OUTFITS (THE CLOSET WHEEL)

Continues LAYER 482. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Tested: the closet wheel, the tracksuit on Rey in 1A.
Art: `art_483.zip` -- Donny's five outfits cut to 400 wide (`assets/prison/yt_rey_track|suit|work|workvest|leather.png`), Rey's skin taken
a shade darker in each (warm skin tones only, x0.80).

- `REY_FITS` (module level): STREET CLOTHES (`yt_player_civ`), THE TRACKSUIT, THE SUIT, THE WORK JACKET, THE WORK VEST, THE LEATHER
  VEST. `g.pfit` picks the plate Rey wears when in street clothes (the player draw tries `REY_FITS[g.pfit].k` first).
- **THE CLOSET in 1A is a wheel now** (`G.closetWheel`, the outfits as their own pictures round the ring); a dresser anywhere (and
  the nightstand at home) has CHANGE CLOTHES on its object wheel. The phone spot in 1A opens the phone wheel too.
- Note: `yt_player_civ` / `yt_pr_player` (the old plates) were NOT darkened -- the jumpsuit orange sits in the same hues as the skin.

---

## 00000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 482 -- MISSION 4 FINISHED: THE BACK ROOM, THE FENCE, THE HOOK, KATYA

Continues LAYER 481. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run headless: Mission 4 from the stakeout to
MISSION COMPLETE (+$500); all modes boot. No new art.

- After the stakeout: DRIVER -> **RIGHT TO ARMS** (a story destination). Inside any RIGHT TO ARMS, E at the clerk ->
  `r2aPanel`: **PAY TO SEE THE BACK ($200)**, then the **GRAPPLING HOOK** ($300, needed: `g.hookHave`), a **KEVLAR VEST** ($400,
  +50 max health: `g.vestHave`), a **SUPPRESSED .22** ($450, `pistol_auto` on the rack). Short of cash, Pablo covers ONE thing.
- **TONIGHT**: DRIVER -> **THE SCRAPYARD · THE BACK FENCE** (`yardBack()`: behind the yard, off to one side). Arrive -> 11 PM, on
  foot, sneaking, Pablo walks a path along the back to the marked wall and holds while a cone is on his next leg; three
  Boznov guards circle the yard (4 s of grace first). **Seen = THE LOUD ROUTE** (no fail): they turn and shoot, you still
  run for the wall. **E at the wall = GRAPPLE** (1.6 s, the line drawn) -> the top floor (the office).
- **THE OFFICE**: Tony at the desk, Katya at the window (stand-in plates: fixer / waitress). Tony reaches for the radio,
  Katya shoots him (panels `katya1` -> `katya2`). “Then you work for me” -> `g.katyaSpy`, `g.crewJoin.katya = "spy"`,
  `g.yardOurs`; you're back out front in Pablo's car -> DRIVER -> HOME -> sleep -> **MISSION COMPLETE · THE SCRAPYARD +$500**.
- Fix: the health bar is clamped (the vest took it past 100%).
- Hooks: `G.yardBackT`. Test: `t/t_m4b.py`. `rep.py` (the patcher) now also matches strings whose \uXXXX escapes were
  written as the characters.

**NEXT**: what the yard being yours turns on (the board, the crew coming out -- Leroy? Ras?), Katya's spy work, the talk
wheel, the alley/plot rebuild, Rey's outfits (prompt given), Boznov/Tony/Katya plates.

---

## 0000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 481 -- EVERY THING HAS A WHEEL, THE STASH, THE PHONE WHEEL, HEALTH / STAMINA, THE WATCH, MISSION 4 OPENS

Continues LAYER 480. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run headless: Mission 4's opening (horn, Pablo's
car, the watch, DRIVER -> STAKEOUT, the stakeout talk), the toilet stash in 1A (+$1,000), the bed and phone wheels; all modes boot.
Art: `art_481.zip` (ui_watch_davies -- its LCD digits painted out so the game draws the time; ui_watch_icon -- the RETRO-TEK face,
the watch's icon in POCKETS).

- **OBJECT WHEELS** (`G.objWheelFn`, `objNear`, `OBJ_DO`, `APT_OBJ`): walk up to a thing, E, its wheel: **STASH** (beds, sinks,
  toilets, tubs, fridges, stoves, nightstands, desks, dressers) + what it's for -- bed SLEEP (a second wheel: dawn / noon /
  dusk) and SAVE at home, sink WASH YOUR HANDS, toilet USE IT, tub SHOWER (stamina full), fridge EAT (+20), stove COOK (+35,
  20 min), TV WATCH THE NEWS (an hour), sofa SIT DOWN. Painted floors (Palm Court) read their things from `APT_OBJ` (the
  generator now exports every bed/sink/toilet/tub/fridge/stove/TV/sofa/nightstand with the floors); other buildings read
  their plan props (`kindOfProp`). In Kestrel the hiding places go through the same wheel (STASH -> the old stash list,
  SLEEP at your own bunk, THE MAIL at your desk, WASH / USE).
- **THE STASH** (`g.ostash`, `osGet`, `stashWheel`): per thing; holds cash, pocket items and guns. TAKE / HIDE in a wheel.
  **$1,000 is in the toilet tank in 1A.**
- **THE PHONE WHEEL** (`G.phoneWheel`, `G.phPick`): booths and the home phone -- faces round the ring: EARL (the cab, a second
  wheel of destinations), LEROY, PABLO (once he's in), POLICE, AMBULANCE ($150, health full, 30 min), FIRE.
- **HEALTH and STAMINA** written inside their bars (taller bars).
- **THE DAVIES WATCH**: under the bars, the time drawn on its LCD (`hud.watch`), only while it's on (`g.watchOn`);
  `g.watchHave` puts it in POCKETS (WATCH ON / OFF).
- **THE SCRAPYARD (Mission 4) -- the opening** (`scrapBegin/Step/Objective`, chained after First Day Out): 7:52 AM, a horn;
  Pablo's lowrider at the kerb -- E gets you in as the passenger (`G.pabloCarFn`: your car body becomes his car, Pablo in
  `g.pfol` as the DRIVER); “You're late, mijo” -> the watch. DRIVER -> DRIVE TO… -> **STAKEOUT · THE SCRAPYARD** (a
  `ccarDests` entry across from the yard) -> parked, the morning runs on, Pablo counts the guards and sees the roof ->
  **TO BE CONTINUED** (objective says so).
- Test: `t/t_m4.py`.

**NEXT**: Mission 4's rest -- RIGHT TO ARMS (PAY TO SEE THE BACK: the hook, a vest), night, the stealth follow, the grappling
hook to the roof, the office: Tony, Katya; the loud route. Then the talk wheel and the alley rebuild.

---

## 000000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 480 -- FIRST DAY OUT (MISSION 3), EARL'S CAB IS EARL'S, PHONES

Continues LAYER 479. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run headless: First Day Out played start to finish
(the lot, the hot-wire, the getaway, all four Boznov cases and the house, Pablo, sleep, +$300); a phone booth and the cab menu; all
modes boot. Art: `art_480.zip` (pr_phone_booth, fu_phone).

- **NO CAR TILL YOU STEAL ONE** (Donny): from Day Out the car, the bike and the sedan bodies are put out of the world
  (`storyHideRides`; `g.storyRides` keeps where they were; `storyGiveRides` is there for later). **The cab is EARL'S**: when
  you get out at Palm Court it drives off on its own (`earlCab`, moved by hand for 9 s by `stepEarlCab`, then removed) and
  Earl gives you his number (`g.earlNum`, a book note). He's never crew.
- **PHONES** (Donny's art): a booth on a corner of every other crossing (`phoneBooths`, ~98, `pr_phone_booth`, drawn in the
  roof pass), and the beige phone in 1A (`fu_phone`). E -> `phonePanel`: **CALL EARL'S CAB** ($12, twenty minutes: home,
  the Rusty Nail, RIGHT TO ARMS, Stan's, and every Boznov place you've cased -- `cabDests`), **CALL LEROY**.
- **FIRST DAY OUT** (`STORY.firstout`, `firstOutBegin/Step/Objective`, `drawFirstOut`), chained after Day Out: **4:30 AM**,
  night. **STEAL A CAR** off the nearest car lot (not Raven Auto): THE NIGHT MAN (cone 250, walks the lot's edge) and THE
  DOG (wide short cone + it SMELLS you within 85 whichever way it faces) -- seen/smelled = MISSION FAILED. The car is
  ringed: E and HOLD STILL 3 s to hot-wire it (`G.lotStealFn`; move and you let go of the wires); it comes off the lot as a
  car you can take; E gets you in. **GO**: 900 from the lot. **CASE THE BOZNOVS**: one man out front of each -- VICTOR (the
  Raven's Nest), GRIGORI (Raven Auto), YURI (the Happy Hippy), TONY (the scrapyard); stop between 150 and 520 away and hold
  still -- the ring fills in 5 s and his name goes in the book; closer than 150 his men notice and it resets. Then **THE
  HOUSE** (Vlad and Katya at the gate). **GO HOME**: Pablo's lowrider in your stall, Pablo on your sofa -> “YOU'RE IN” ->
  `g.pabloJoined`, `g.crewJoin.viejo = "driver"` (he goes home; Mission 4 he picks you up) -> SLEEP -> +$300.
  The Boznov men are drawn with the enforcer plates until their own top-down plates exist.
- Test: `t/t_first.py`, `t/t_booth.py`.

**NEXT**: Mission 4 (the horn, the driver tutorial, the stakeout, RIGHT TO ARMS' back room, the grappling hook, the roof,
Katya), the talk wheel, the alley/plot rebuild.

---

## 00000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 479 -- DAY OUT (MISSION 2), LEROY'S FLAT, RAS'S CAB

Continues LAYER 478. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run headless: Day Out played start to finish (the
cab, four stops, Palm Court, the closet / phone / mail, sleep, MISSION COMPLETE +$100); all modes boot.
Donny: **Leroy gets the apartment** (his sister's man), **Ras pays for the cab** (twenty packs). Lines changed to match.

- **CHAINED**: Last Day In's MISSION COMPLETE hands on to DAY OUT 1.5 s after its slam (`g.storyNext`).
- **DAY OUT** (`dayOutBegin`, `dayOutStep`, `dayOutObjective`, `STORY.dayout`): 5:00 AM, street clothes (`g.pcivvies`), out
  legally (`g.pescaped` + `g.preleased`, heat cleared, crew NOT out yet), standing outside the gate. C.O. Harlan: Ras paid
  for the cab. **The cab is your car re-skinned** (`taxi`, Holloway Checker; its old look and place kept in
  `g.story.carWas` and put back when you get out). Get in (E) and EARL drives (`g.auto`, fast) a tour, nearest-first:
  a GAS STATION, THE RUSTY NAIL, RIGHT TO ARMS, STAN'S (`cabStops`, `cabLeg`) -- at each he stops 7 s and says what the place
  does (`EARL`), and it goes in the book -- then the kerb under PALM COURT. Get out -> FIND YOUR APARTMENT (Building A) ->
  YOUR PLACE: E at THE CLOSET (bedroom wall), THE PHONE (by the sofa: Leroy at his sister's), THE MAIL (the hall boxes: a
  letter from Mom) -- drawn in 1A (`APT_SPOTS`, `drawAptSpots`, `G.aptSpotFn`), ringed while they're objectives, usable any
  time after -> SLEEP at your bed -> MISSION COMPLETE, +$100. Getting out of the cab mid-ride, he waits.
- Test: `t/t_dayout.py` (it hops the cab along each leg to save time).

**NEXT**: Mission 3 (First Day Out: steal a car, case the Boznov places for the book, Pablo in the flat), the talk wheel + E
for all speech, the alley/plot rebuild.

---

## 0000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 478 -- MISSIONS (LAST DAY IN), THE SLAMS, CHECKPOINTS, VISION CONES, SNEAK, THE FUEL GAUGE

Continues LAYER 477. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run headless: Last Day In played start to finish (all
three side jobs, a fail, a retry from the checkpoint, the goodbyes, sleep, MISSION COMPLETE, +$250); all four modes boot clean.
Story decisions (Donny): the player is **REY**, the Fall Guy; **Ras Campbell** (was Ras Leroy); Katya Boznova is the brothers'
sister; the scrapyard man is **Tony** (Anton Volkov), a Russian asset; the student was 7 when Rey went in -- Rochelle hid him
(she thought Rey would leave) and her mother has custody. The script is the doc "Raven Hook 1986 -- The Fall Guy".

- **THE STORY SYSTEM** (`STORY`, `g.story`, `storyStart`, `storyMark`, `storyComplete`, `storyFail`, `storyCk`): a mission
  is a list of objectives; finishing one is a CHECKPOINT -- the whole game snapshotted with `collectSnap()` (the exact-save
  snapshot) into `storyCk`, which lives OUTSIDE g so a checkpoint never contains the one before it.
  **MISSION COMPLETE** slams in (mission name, the pay in green) and the money goes on you; **MISSION FAILED** slams in with
  the reason and a panel: RETRY FROM CHECKPOINT (`applySnap`, then 2.5 s of grace) or QUIT MISSION. A mission's name slams in
  when it starts. The slams are `g.slam` -> `hud.slam` (CSS keyframes rhSlam). The objective box shows the story objective
  first (`storyObjective` at the top of `prisonObjective`).
- **LAST DAY IN** (Prison Mode now starts it; the fish walk-in is skipped -- it's his last day, not his first): TALK TO YOUR
  PEOPLE (E on Leroy, Ras, Pablo -- lines written as ten years of friends; the crew panel is `storyCrewPanel`), then each one's
  side job: **RAS -- THE STASH** (he slips you a shank: POCKETS, hide it at your bunk; done when it's in a stash and not on
  you), **LEROY -- THE FIGHT** (a con on your tier comes for your seat; put him down; going down or the SHU = MISSION FAILED),
  **PABLO -- THE CAKE** (the mess hall kitchen: THE COOK walks the line, C.O. DUNN sweeps from the kitchen door; checkpoint
  as you walk in; seen = MISSION FAILED; touch the cake to carry it; bring it back to your block). Then GO BACK TO YOUR CELL
  -> the cake and the goodbyes -> LIGHTS OUT (your bunk offers only SLEEP) -> MISSION COMPLETE, +$250.
- **VISION CONES** (`coneSees`, `drawCone`, `drawSiteCones`): a watcher has a facing, a field (radians either side) and a
  range; walls block it (indoors), FULL cover hides you, and walking (not sneaking) within 70 of anyone means they hear you.
  The cones are DRAWN only while you're sneaking or in cover (yellow, red where they have you). The guarded places' guards
  (distros, towers, leaders) now look about slowly (`q.lookA`): standing up they see you all round as before; sneaking or in
  cover they have to be looking your way.
- **SNEAK**: C / Y / the COVER button with nothing to get behind = SNEAK (crouched, 55% speed, no running); again to stand.
  The button reads SNEAK while you are.
- **THE FUEL GAUGE** (Donny's art, `assets/ui/ui_fuel_gauge.png`): lower left, 78% opaque, a red needle E to F, LOW FUEL under
  it below 15% -- only in a vehicle. The fuel bar and FUEL % text are gone (the pump notes stay).
- Hooks: `G.storyT`, `G.storyStartT`, `G.storyFoeT(down)`. Tests: `t/t_story.py`, `t/t_fuel.py`.

**NEXT**: Mission 2 (DAY OUT: release, the cab tour, Palm Court's closet/phone/mail), the talk wheel + E for all speech,
the alley/plot rebuild. Known: a cone is drawn through walls (it only SEES through doorways).

---

## 000000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 477 -- PALM COURT, RIGHT TO ARMS, THE HAPPY HIPPY'S BACK ROOMS, THE STAN'S CRASH

Continues LAYER 476. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run headless: BEGIN, DETECTIVE, PRISON and STUDENT all
boot clean; every new place was entered and screenshotted; the Stan's crash was reproduced three times and is gone after the fix.

- **BUG: THE STAN'S CRASH** (prison mode, Pablo drives you to Stan's, the screen goes black). A gang's car that came out of a
  drive-by went back into ordinary traffic with no `cruise` speed, so its speed became NaN, its position NaN, and
  `resolveTrafficOverlap` (where `NaN || 1e-3` is `1e-3`) pushed NaN into every car it touched -- yours included. Fixed three
  ways: a drive-by car is skipped by the traffic AI (`updateDriveBys` drives it), a car with no cruise gets one, and
  `resolveTrafficOverlap` puts any non-finite car back where it last was (or removes it) before anything is compared.
  `g.nanCarWhat` records the first bad car, if it ever happens again.
- **FACES**: the Boznov leadership (Vlad, Victor, Grigori, Katya) use `pt_bozni_*`; the regular soldiers use `pt_bratva_1..4`
  (the back-room doormen are the first ones to appear). **The locksmith is back to his own face** (`pt_hire_locksmith_1..3` from
  layer 510, re-shipped in art_477.zip; the layer-476 override in `basePeople` is gone).
- **THE MANOR ROOF** `rf_bozni_manor` is in (removed from OPTIONAL_ART).
- **PALM COURT** (`aptCell`, `aptLot`, `aptC`, `drawAptLot`, `APTC`): YOUR apartment complex, on the nearest plain block to the
  den. BUILDING A across the top, B and C standing down from each end of it, none touching; a concrete yard with walks from
  each door to the pool deck, the POOL in the middle (`ap_pool` with `tx_pool_water` over it at 55% so you see the bottom, and it
  moves a little), the round planter with its tree (`ap_tree_big`) below it, residents' stalls at the bottom. The pool and
  the planter are solid (`fences` on Building A). Roofs `rf_apartment`, turned to face each door.
  Inside, every building is two floors, two flats a floor, the hall up the middle with the stairs at the top end and
  mailboxes on the wall: the floors are **generated pictures** (`int_apt_long_f0/f1`, `int_apt_side_f0/f1`), built from Donny's
  furniture, bathroom and carpet sheets (cut to `assets/home2/fu_*` and `ba_*`) -- each flat has a bedroom (two in the long
  building), bath, kitchen with a dining table, and a living room with a sofa, TV and rug. Walls and furniture are exact solids
  (the generator wrote ART2_SOLID). Flats are numbered on the hall doors (1A, 2A, 3A...). **1A is yours**: E at your bed ->
  SLEEP UNTIL DAWN / NOON / DUSK, SAVE THE GAME. **A brand-new game (BEGIN with no save, or START OVER) wakes up in 1A** with
  the car in the stalls (`aptStart`; the bike and the sedan stay at the den).
- **PICTURES FACE THEIR DOORS** (`b.artFace`, `artTurn`, `artFrac`): a painted floor or roof plate is drawn with its front at the
  bottom; a building flagged artFace turns it so the bottom is on the door side (0, a quarter, a half, a quarter back). The
  plate is turned, not mirrored, so lettering reads. `pl.artRot` is now 0-3.
- **RIGHT TO ARMS** (the four GUN_CELLS shops, renamed from Raven Hook Firearms): footprint to the art (about 2.1:1, long side on
  the street, door in the middle), roof `rf_gun_store`, floor `int_gun_store` with solids over the racks, cases and counter, the
  clerk stands behind the painted counter (`b.artCounter`). The BIZ_MENU.guns counter works as before.
- **THE HAPPY HIPPY'S CLUB**: the basement (floor 0) is Donny's picture now (`int_happy_hippy`: the bar, the stage, hookah
  lounges, two pool tables, two card rooms). The stairs sit bottom-middle on both floors. **The card rooms are sealed**: a
  Boznov soldier minds each door (E). PAY $100 (half on their good side, nothing doing at war) -> you are AT the table, five
  card draw. Walk away from the game -> you're back on the club floor by his door (`HIPPY_ROOMS`, `G.hippyFn`, `hippyOut`).
  Three card players sit at each table.
- Hooks: `G.aptT`, `G.aptHomeT`, `G.hippyT`. Tests (harness rebuilt, esbuild): `t/t_apt.py`, `t/t_apt2.py`, `t/t_hh.py`,
  `t/t_stan.py`, `t/t_modes.py`.

**STILL OPEN**: the Boznov top-down plates (the doormen wear the enforcer's plate for now); where the cul-de-sac goes; swap all
poles for `pl_pole_top`; the story missions, the talk wheel and the alley/plot rebuild are the next layers.

---

## 00000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 476 -- THE BOZNOV BROTHERS, THEIR FRONTS, THE HOUSE, PAINTED FLOORS

Continues LAYER 475. Current build: `game.jsx` is **4.98 MB / 53,795 lines**. Run in a browser (headless): every new interior was
entered and screenshotted; prison, student, CONTINUE and the 475 tests all pass; the fronts survive a save/load.

- **THE BOZNOV BRATVA** (was the placeholder Bratva): Donny's Bozni brothers, Russified -- **VLAD BOZNOV** (boss: patient,
  ruthless, the suit), **VICTOR BOZNOV** (underboss: the charmer, gold chains, runs the club), **GRIGORI 'MEDVED' ORLOV**
  (captain, the enforcer), and **KATYA** (manages the Raven's Nest). Label BOZNOV. Faces: `pt_bozni_*` (portraits) and
  `bust_bozni_*` (busts, not yet used), crew faces `pt_bratva_1..4`. Still no top-down street plates, so their crews
  stay off the street (layer 475).
- **THE FRONTS round the scrapyard** (`bozFronts`, once, right after `rusClaim`): the ordinary buildings nearest the
  scrapyard that best fit each roof's shape, trimmed to it (`fit`):
  **THE RAVEN'S NEST** -- Victor's strip club, roof `rf_ravens_nest`, the whole floor is `int_strip_club` (oval room,
  red booths, the pole stage, dressing room); **THE HAPPY HIPPY** -- roof `rf_happy_hippy`, a laundromat on the street
  floor (store plan) with a CLUB IN THE BASEMENT (nightclub plan; `floorKind` checks `b.happyHippy`; entry = floor 1);
  **RAVEN AUTO** -- a car lot that launders their money: roof `rf_raven_auto`, a real for-sale lot beside it (cars you
  can buy, same as the other lots), the inside is `int_raven_auto` (showroom with three display cars, offices,
  counter, three bays).
- **THE BOZNOV HOUSE** (Old Town, MARK `ot_bozni` at cell (5,0); the station that was there moved to (7,2)): kind
  mansion, two painted floors -- ground `int_bozni_f0` (armoury, lounge and bar, the war room, kitchen), upstairs
  `int_bozni_f1` (bedroom, gym, study, bath, storage) -- a stone WALL round it with a gate on the street side
  (`bozHouseInit` fences, they collide), no lanes through the yard. **Roof `rf_bozni_manor` still to come** (it's in
  OPTIONAL_ART so the missing-art banner stays quiet; a generated roof stands in).
- **THE BROTHERS** (`G.bozFn`, E): at the war-room table in the house (Vlad) or at the club's dressing-room end of the
  Raven's Nest (Victor or Katya). Panel "boznov": PAY YOUR RESPECTS ($2,000, standing +20), ASK ABOUT THE BLOCKS, TALK.
- **PAINTED FLOORS** (`fitArtFloor`, `drawArtFloor`, `b.artFloors = { floor: key }`, `ART2_SOLID`): a picture is a
  whole floor, any floor of any building. Inside walls go, props go except stairs/doors/`b.artKeep` (redrawn over the
  art), invisible `artblock` solids over the painted furniture, the stair drawn on top. A tall room gets the (wide)
  picture turned a quarter (`pl.artRot`; `artAt(pl, fx, fy)` maps picture fractions to the world either way).
  `b.artCarsF` = cars parked on the painted floor.
- **THE RUSTY NAIL**: roof `rf_rusty_nail`; inside is Donny's long bar (`int_bar_long`: the bar, booths, the band's stage,
  two pool tables, the poker room). Silas stands behind the bar, the pool game is at the first table, his computer
  sits in the poker room.
- **CARS**: eight new ones (`pk_*`, nose up) in BUY_CARS -- for sale on the lots and parked at the stations -- with
  MODELS entries (Holloway Estate GL, Vantry Sprite GTI, Brandt 500 SE / Saloon / Speedster x2, Corvane Cresta, Marrow
  Consul GL).
- **RAVEN HOOK UTILITIES**: a utility truck (`vh_rhu_truck`, parked traffic, can be taken) and a man in a hard hat
  (`yt_rhu_worker`) at four corners (`RHU_SITES`); walk up and he says something.
- **TEXTURES**: Old Town's sidewalks and lanes use Donny's cobbles (`tx_ot_cobble`, 460 world units a tile); the court
  alleys use his gravel (`tx_alley_gravel`) and the cobbles (`tx_alley_cobble`).
- **THE LOCKSMITH** has his own faces now (`pt_hire_locksmith_1..3`, cut from the photo sheet -- photographs, not
  pixel art; the sheet's "top-down plates" were front-on photos, so the locksmith still wears the safecracker's plate).
- Refactor: the car lot builder is `dealerLotOf` / `dealerLot` (pulled out of `dealers()`).
- Hooks: `G.bozT`, `G.enterNamedT(name, floor)`, `G.artAtT(fx, fy)`. Tests: j_boz.js, j_boz3.js, j_bozsave.js; `shots.py sp8.json`.

**STILL OPEN**: the manor roof `rf_bozni_manor`; Boznov top-down plates (street crew, the brothers standing in their
rooms); `pl_pole_top` is cut but NOT used (the game's poles are drawn standing at an angle; the new one is straight
top-down -- needs Donny's call on swapping all poles); the Happy Hippy basement club has no art of its own yet.

---

## 0000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 475 -- STAN'S AND JOE'S REBUILT, THE STATIONS, OLD TOWN ROADS, THE BRATVA

Continues LAYER 474 (Donny's merged file). Current build: `game.jsx` is **4.98 MB / 53,795 lines**. This one WAS run in a browser
(headless Chromium): prison mode, student mode, CONTINUE, and every system below with screenshots.

- **BUG: the HUD error "Cannot read properties of undefined (reading 'x')"** on every frame. Two functions were both named
  `gasNear` after the merge (the station counter's and the crew-dispatch pump finder); the second won and the counter's
  caller passed no car. The counter's is now `gasShopNear`. (`g.hudErrStack` keeps the stack of any future HUD crash.)
- **STAN'S** (`stanLot`, `stanCell`, `stanC`, `STAN`): its own lot now, on the nearest plain block to the first car lot
  (no landmark, mark, special cell, or garage/warehouse the scrapyard could pick). Concrete, customer stalls, and two
  buildings: **STAN'S OFFICE** (small, `st_roof_office`, kind `office` = reception + office + conference + WC, walk in by its
  door) and **STAN'S GARAGE** (big, 620x330, `st_roof_garage`), a **DRIVE-IN** (`b.driveIn`): walls on three sides
  (`driveWalls`, collision for cars and people), the front open, three lift bays drawn on the floor (`drawDriveInFloor`),
  the roof drawn as an overlay that fades to 16% when you or your car are under it (`drawDriveInRoofs`). Drive in, stop,
  **E** -> FIX IT / UPGRADE & TUNE MY CAR / SWAP THE PLATES (`G.repairFn` now tests "inside the garage"). Drive-ins are left
  out of the depth-sorted building pass and the door list. Rebuilt from the cell if a load hands back a fresh cell.
- **JOE'S REPAIR SHOP** (the SHOP_CELLS body shops): one building, 460x230, the **office on the left** (31%, the
  round-window strip of `jo_roof`: counter, chairs, plant, its own door) and the **garage on the right with two bays**
  (`joeOffice`, `joeGarage`, `joeWalls` -- walls with the garage front open, the office door, a man-door between them).
  **Repairs only**: in a bay, **E** -> JOE'S panel with FIX IT (15% under Stan's price) and nothing else; the old slow
  "sit in the bay and pay by the second" repair still works too.
- **GAS STATIONS** (`drawGasStation`, `gasShop`, `gasCanopy`, `gasStalls`, `gasParked`): **concrete lot** (tx_concrete,
  joints every 120), the brand's stained floor only under the canopy; the shop set 130 in from the back with a strip
  behind it (dumpster) where **the turf owner's dealer is always stationed** (`gasDealers`, no longer night-only); a
  **row of parking** beside the shop with **real parked cars** in about a third of the stalls (traffic, `parked`, `named`,
  `gasLot` -- they block and can be stolen); the canopy + pumps mid-forecourt, its roof still fading when you're under it.
  **Nine stations moved** a block or two (GAS_CELLS): five sat on ground already owned -- (2,1) Old Town gym + church,
  (4,1) the store, (6,15) Neon Flats houses, (0,6) the lake, (6,7) the skate park -- and four were on half-width lots
  beside an expressway leg. New cells: (13,3) (6,13) (5,0) (6,3) (18,1) (2,6) (7,7) (21,10) (18,14). Stations in the hood
  ((3,3), (2,6)) were being painted over by the hood yard: stations / firehouses / body shops are now drawn before it.
  No alley trash on stations, Joe's or Stan's (`cellAlley`).
- **OLD TOWN**: the **roads are roads** -- ordinary asphalt and city markings. **Cobbles are the sidewalk only**
  (`drawOldTownGround`: the band between each block's kerb and its lot, a stone kerb line) plus the narrow lanes through
  the blocks. **BUG: the yellow lines that slid while you drove** were the hand-drawn centre dashes on the old blacktop
  strips -- they started at the edge of the VIEW, so they moved with the camera. The strips and their dashes are gone.
- **ROW HOUSES / CUL-DE-SACS**: the art was missing -- `rh_roof_1..6` are cut from Donny's new roof sheet (344x200) and
  `tx_alley_gravel` / `tx_alley_cobble` made from the gravel and cobble textures (all in art_475.zip, `assets/city/`).
  With them the courts at (4,2) draw: two cul-de-sacs, turning circles, parking bays, one row house a side (the market
  takes the rest). **Only (4,2) gets courts**: rows j0 and j1 have lots 416-488 tall (the North Spur squeezes them) and a
  court needs 464; (3,2) is full of landmarks; (4,1) is taken. See STILL OPEN.
- **THE BRATVA** (`WAR_GANGS.rus`, label BRATVA, red #b8343a; placeholder names VIKTOR VOLKOV / ILYA 'THE ACCOUNTANT'
  SOKOLOV / DIMA ORLOV): `claimOnly` -- no ground at the start. When you're out (`rusClaim`, once), the turf the scrapyard
  sits on and the two nearest become theirs, with a diamond house (and maybe stone) on each. Every corner or shop you open
  on their ground (`rusTake`, from both the board's corner/racket ops and a dealer sent to a corner) was theirs: -$1500
  off them, their house there drops a level, standing -8, and the first time a banner says so. **Three of your spots on one
  of their turfs with no house left = YOUR FIRST TURF** (`t.owner = null`, `t.mine`, `g.myTurfs`). No street-crew art:
  `warCrew("rus")` returns a crew that's never put on the street, so nothing invisible shoots at you.
- Test hooks: `G.gasT`, `G.plainCellsT`, `G.courtsT`, `G.stanT`, `G.rusT`. Tests: j_stan.js, j_joe.js, j_rus.js, j_gas.js, j_ct.js
  and the screenshot runner `shots.py` (spot list json + prefix).

**STILL OPEN**: (1) where the cul-de-sac neighbourhood should go -- it needs a block with ~1100 of clear depth (asked
Donny); (2) Bratva art: street crews (a `gang_rus` sheet + GANGTOP entry), leaders (`yt_ld_rus_*`), a front building; real
names; (3) the bar art Donny mentioned hasn't arrived; (4) Stan's office has no Stan behind the counter yet (E there does
nothing special); (5) carried from 474: courts have no AI traffic / parked cars / lamps.

---

## 000000000000000000000000000000000000000000000000000000000000000000000000. LAYER 474 — A MISSING BRACE FOUND, THE NEW RIGS AND STAN'S OFFICE MERGED BACK IN

Continues LAYER 473. Current build: `game.jsx` is **4.98 MB / 53,795 lines**.

**Where this sits.** Two different continuations had branched off a common ancestor: one line added
the garage parts/Stan's/gas-brand foundation and stopped there (what got handed off and documented
as layers 468-470 further down this file); the other (this session, starting from a `game.jsx` a
little further along that same line) added the semi cab liveries, the chopper-mission flatbed
dressing, and Joe's roof wiring. Then layers 471-473 below (car weapons, old town grass, the
row-house courts) were built on the FIRST line, without the second line's additions. This section
folds the second line's work back into the file that already has 471-473, so nothing from either
side is lost. If you were tracking two `game.jsx` files, you can go back to just the one this zip
contains.

- **BUG FOUND AND FIXED: the game wouldn't load at all.** `dealers()`'s repair-shop block (the bit
  that finds a nearby building and renames it STAN'S GARAGE) was missing one closing brace -- the
  `if (D0) { ... }` that wraps the whole thing never actually closed. esbuild didn't trip on it
  until ~900 lines later, at an unrelated `}, [ready]);` on a `useEffect`, which is why the error
  message pointed nowhere near the real problem. Exact fix: in that block, `if (bc) { bc.type = 4;
  bc.lawn = false; } }` needed a third `}` before the trailing comment to close `if (D0)` -- it only
  had two (one for `if (bc)`, one for `if (best)`). Lesson for next time a "random line way past
  everything" error shows up: it's very rarely that line's fault; it's almost always an unclosed
  brace/paren somewhere earlier that the parser didn't choke on until it ran out of road.
- **TRACTORS pool**: reskinned to the three cab liveries (`tr_cab_blue`, `tr_cab_red`,
  `tr_cab_brown`) in place of `hv_00..04`. Trailers (`hv_05..10`) untouched, same pairing system.
- **Two flatbed trailers** (`tr_flatbed_wood`, `tr_flatbed_metal`), registered under
  `assets/vehicles/`. Used specifically as scene dressing for Steal a Chopper: a cab+flatbed pair
  (`M.rigTrailer`/`M.rigCab`) spawns parked next to the chopper when the mission starts, picked
  randomly, cleaned up with the rest of the mission's props on completion/failure. Not coupled to
  the chopper, not driveable.
- **JOE'S REPAIR SHOP roof**: `jo_roof` was registered in `CITY_ART` (from the earlier line's
  layer 469 work) but never drawn. Wired into `drawShopRoofs` (the `SHOP_CELLS` body-shop system --
  separate multi-building lots, not Stan's) with a plate-first, procedural-shed-fallback pattern.
- **STAN'S OFFICE, now actually placed.** Per this session's clarification: the SMALLER building
  (`st_roof_office`, the "STAN'S" wordmark sign art) is the office/reception/storefront; the BIGGER
  one (`st_roof_garage`) is the vehicle-bays garage -- confirming the original "two pages, the
  garage and the store" request meant two physical buildings, not two panels in one. A second
  building is now found near the garage the same way the garage itself is found (nearest qualifying
  building, excluding the garage, within 30-200 units) and reskinned `STAN'S OFFICE` /
  `st_roof_office`, tracked on `g.repairOfficeB`. Purely cosmetic -- repair + parts/tuning still
  both live at `g.repairB`, the garage. If a given map seed doesn't happen to have a second
  qualifying building nearby, `g.repairOfficeB` just stays unset and only the garage shows.
- **Every leftover "EDDIE'S" renamed to STAN'S**: the crew-dispatch "DRIVE TO" rolodex entry, the
  "GET IT FIXED" option and its confirmation flashes, and the on-screen building tag over the
  garage's door. (`drawShopRoofs`'s fallback shed drawing now only runs when `jo_roof` hasn't
  loaded -- see above.)

### Assets added this session

Same chroma-key/opaque-crop split as before -- vehicle sprites alpha-keyed (need real transparency
over roads/traffic), signage/roof plates left as plain opaque crops (so pink/magenta lettering in
the actual designs, like the "STAN'S"/"JOE'S" wordmarks, isn't punched transparent).

| File | What |
|---|---|
| `assets/vehicles/tr_cab_blue.png` | Blue semi cab, TRACTORS pool |
| `assets/vehicles/tr_cab_red.png` | Red semi cab, TRACTORS pool |
| `assets/vehicles/tr_cab_brown.png` | Brown semi cab, TRACTORS pool |
| `assets/vehicles/tr_flatbed_wood.png` | Wood flatbed, chopper-mission dressing |
| `assets/vehicles/tr_flatbed_metal.png` | Metal/tilt flatbed, chopper-mission dressing |
| `assets/city/st_roof_garage.png` | Stan's Garage roof |
| `assets/city/st_roof_office.png` | Stan's Office roof -- now actually placed (see above) |
| `assets/city/jo_roof.png` | Joe's Repair Shop roof (SHOP_CELLS body shops) |
| `assets/city/km_roof.png`, `km_canopy.png`, `km_pump1.png`, `km_pumps2.png`, `km_tires.png`, `km_ext.png` | Kum n Pay station art |
| `assets/city/tt_roof.png`, `tt_pump.png`, `tt_pump_2.png`, `tt_pump_b.png`, `tt_tire.png` | Tasty's station art |

**Not in this zip, and not needed from this side**: `assets/carwpn/*` (car weapons icons),
`assets/city/rh_roof_1..6.png` + `tx_alley_gravel.png`/`tx_alley_cobble.png` (row-house roofs +
alley textures), and `assets/parts/wx_*.png` (weapons-wheel part cards) are all referenced by code
that came from the other line of work (layers 471-473 below) -- that art lives wherever that work's
own asset pipeline put it, not here. This zip's `assets/` only has what changed in this session.

### STILL OPEN

- `km_floor.png` / `tt_canopy.png` -- unchanged from before, still falling back to the procedural/
  generic texture. Happy to build dedicated art for either if wanted.
- `tt_truck` -- registered in `CITY_ART`, still not drawn anywhere. Still unclear what it's for.
- `assets/parts/*.png` (engine/brakes/plating/wing/lights/nitro cards) -- prompt list in
  `PARTS_ICON_PROMPTS.md`, system plays fine without them.
- Everything already flagged further down this file under layers 470-473 (sky bag art, the seven
  remaining `wi_*` weapon-wheel icons, row-house attic plan, AI traffic on the court stubs, etc.)
  is unchanged and still open.

## 00000000000000000000000000000000000000000000000000000000000000000000000. LAYER 473 -- THE OLD TOWN ROW-HOUSE COURTS

- **Main road** = the avenue on grid line 4 (halfW 200: two lanes each way, already there). **Courts** (`planCourts`, module level, constants in `RH`) run off it into the six
  cells beside it ((3,0..2) west, (4,0..2) east): a two-lane stub (192 wide, `road` 96 each side) with a 36 pavement, a turning circle (r 130) at the end, a painted parking bay on
  both kerbs, row houses facing the stub on BOTH sides (172 x 100 each, 3 to a side on a 700 court, 2 on 560, 1 on 420), and a 90-wide alley behind each court (open to the avenue)
  shared with the next court's backs. Gravel alley on even courts, cobbles on odd (`tx_alley_gravel`, `tx_alley_cobble`, drawn at 1/4 scale).
- **Run once** from `placeMarks()` -> `rowHouseInit()`: for each target cell it collects what is already standing there (every MARKS rect in the cell + every capPlate / landmark
  building), greedily packs courts from the top of the lot skipping those, clears generated buildings off the court rects, sets `c.type = 0` (grass in Old Town), empties `c.det`, and
  pushes one MARK per house. Result with today's landmarks: west (3,0) 2 courts; (3,1) and (3,2) none (civic hall, church, pawn shop sit across the whole width); east (4,1) 2 courts,
  (4,2) 2 short courts (the market limits them to one house a side); (4,0) none (tenement + walk-up). To get four a side the civic hall / pawn / church / tenements must move.
- **The houses** are ordinary marks: `kind house, floors 3` -> `house_g2` (living room, kitchen, bath), `house_u` (bedrooms) on floors 1 AND 2, a door on the stub side
  (`doorSide`), collision, and the roofs are `rh_roof_1..6`. `b.rowhouse` is set in `placeMarks` and `hatchOK` now allows it, so the existing top-floor ladder + roof hatch work.
- **Ground** is painted in the cell loop right after the lot fill: `if (c.courts) drawCourtGround(c)`.
- **NOT DONE**: (1) the attic is not its own plan -- floor 2 uses the bedroom layout, the ladder to the roof is the generic one at `roofHatchPt`; (2) no AI cars drive the stubs / loop the circle
  (the player can; traffic still only follows the grid); (3) no parked cars, lamps, trees or bins on the courts; (4) a house's inside is small (172 x 100 is about 8 m x 5 m); (5) a
  generated building that was set up as a distro or job site and got cleared is not re-sited (placeMarks does that for its own `clear`); (6) never run in a browser -- the planner,
  placement and ground draw were exercised with stubs only; if a court looks wrong the numbers to change are in `RH` and `planCourts`.

## 00000000000000000000000000000000000000000000000000000000000000000000000. LAYER 472 -- OLD TOWN GRASS, STAN'S ON CONCRETE, ROW-HOUSE GROUNDWORK

- **Old Town grass**: in the block ground fill (the line with `c.lawn ? PF("grass") ...`) any Old Town cell (`inOldTown(i, j)`) whose type is gravel (0), dirt (2) or
  rubble (3) now fills with grass. The cobbles under the lanes and the circle are untouched. Lawn trees / hedges still only draw for `c.lawn` cells.
- **Stan's on concrete**: the cell holding `g.repairB` is set to `type 4` (slab) and `lawn = false` when the repair shop is chosen. The gas stations' forecourt
  fill already covers their whole lot (the pavement ring is the SW=64 strip around it) -- NEED A SCREENSHOT of where the grass shows around a station.
- **Registered, not placed**: `tx_alley_gravel`, `tx_alley_cobble` (704x384, from the textures supplied) and `rh_roof_1..6` (the six brick roofs with chimneys, cut from the
  sheet). Files in `assets/city/`.
- **Row-house neighbourhood: NOT BUILT.** Findings for whoever does it: the road network is the cell grid (laneX / AVE_EVERY, lanes follow it), so a cul-de-sac
  is a dead-end drawn inside a cell's lot rect (lx0..lx1, inset SW=64), not a new AI road -- parked cars only. Old Town's `marks` list (the `ct_ot_*` and `ot_ten*` entries) leaves
  cells (0,0), (3,0), (5,0), (0,2) empty. The generic `house` kind already gives living / kitchen / bath on the ground floor (`house_g2`) and bedrooms above
  (`house_u`); a `rowhouse` kind needs a third `attic` plan with a ladder to the roof and a roof hatch (`rf_hatch`, `rf_ladder` art exist) and mkB with floors = 3.
  The existing "alleys" (`cellAlley`) are only trash clutter, not drivable lanes -- a real alley is new geometry (>= 70 wide for one car).

## 00000000000000000000000000000000000000000000000000000000000000000000000. LAYER 471 -- CAR WEAPONS, SKY BAG, TWO COPS TO A CAR

- **Sky bag**: `assets/drugs/dr_sky_bag.png` + `dr_sky.png` (same art, 420x486 -- big, scale down if it looks oversized), registered in the `dr_` loop.
- **WEAPONS slot** on the parts wheel (`PARTS.weapons`; mechanic at the yard and Stan's). Kept on `mods.wpn = { oil, cal, smoke, missile, turret, mg }` =
  uses / rounds left (a missing key = not fitted). Price in `PARTS`; a refill costs 30% of the kit price (`gpWpnOpts`, `garagePick("buy:weapons:k")`).
  Oil $1500 x3, caltrops $1800 x3, smoke $2000 x3, missile $6000 x3, hood mini-turrets $7500 x300 rds, roof machine gun $9000 x500 rds.
- **Controls**: Z oil, X caltrops, V smoke (dropped behind), M missile (forward), G toggles AUTO GUNS. Touch buttons appear beside BOOST for whatever is fitted.
  The two hood turrets (one each side, forward) fire only at a threat inside a ~22 degree cone ahead, 540 range; the roof gun turns to the nearest threat
  (police car, cop on foot, chasing patrol car, hostile crew) within 470 and fires at it. `wpnTargets` decides who counts.
- **Hazards** (`g.hz`, `stepCarWeapons`, `drawHazards`): oil = other cars inside spin and lose speed; caltrops = `v.flat` caps them to 70; smoke = cars inside slow
  and cops lose the chase, and `copLost` drains 3x faster while YOU are in or next to it. None of them touch the player's own car. Missile = `g.msl`, 760/s,
  blows on the first car / body it meets or at 950 range: `carBoom` + `blastAt(grenade)` + 0.6 car damage in 130.
- **TWO COPS TO A CAR / THE CAR STOPS** (`crewHit`, hooked into the bullet-vs-car loop and the missile blast): any police car (model cruiser / pd_*) you hit gets
  `v.crew = [driver, passenger]`, 5 hp each, bullets spread to a random living one. Driver down = `driverDown`: the chase flag drops, cruise 0, it rolls to a stop
  (spd decays, then `dead`, `brake`, `patrol` 0). The passenger does not climb out or take the wheel yet. Only YOUR bullets / missiles do this; a car hit by traffic doesn't.
- **Draw**: hood turrets + roof gun are drawn on the player's car (`drawCarWeapons`); art in `assets/carwpn/wx_*.png` (14 files; the turret is the big top-down
  pose, the gun a side view rotated to aim; `wx_turret_fire` and the other oil / caltrop / smoke sizes are cut but only some used).
- **NOT DONE**: no sound; no ammo shown on screen for the guns beyond the buttons; the response car (`g.police.car`) stops but its two on-foot officers are a
  separate pair of bodies that don't die with the car; AI cars (gang chasers) don't get the crew treatment, only police cars. Not run in a browser -- stub-tested only.

## 00000000000000000000000000000000000000000000000000000000000000000000000. LAYER 470 -- THE GAS STATION COUNTER AND THE CORNER

- **The counter.** On foot, at the shop counter of any station (within 90 of `sh.x+68, sh.y+33`): `[E] BUY SNACKS & DRINKS` (`G.gasShopFn`,
  hooked into `doAction` right after the food-truck line). Panel `gs:shop` -> SNACKS & DRINKS reuses the food-truck overlay + `G.buyFn` + `ITEM_FX`
  (soda, chips, chocolate, coffee, hot dog, sandwich, apple, beer -- `GAS_MENU`, edit prices there), titled TASTY'S or KUM N PAY.
- **Dealers working near a station** (`gasDealers(c)`): (a) any of YOUR corners (`board2.spots`, kind corner) within 700 of the station -> "YOUR DEALER",
  prices x0.8; (b) the war turf the station is on has an owner -> that gang's dealer stands at the front-left of the shop
  (`drawGasDealers`, red label) at night (`g.night > 0.15`) and by day at one station in three. Walk up (58 px) -> `[E]`, or ask the clerk:
  WHO'S WORKING THE LOT? (only shows when somebody is). Panel `gs:deal`.
- **What he sells** (`areaDrugs`): the owner's `WAR_GANGS[k].drugs` plus the drugs of every house on that turf; unowned turf = leaf; `deuce` = sky + stone.
  `DRUG_PRICE` = leaf 20, stone 35, diamond 60, sky 120 a bag; buy 1 or 5. Bags go to `g.p.drugs = { leaf, stone, diamond, sky }`; the panel
  shows what you hold.
- **NOT DONE**: nothing USES or SELLS the bags yet (no use effect, no street sale, no pockets screen), buying raises no heat and does not care
  if you are at war with that gang, and a corner you own that is within 700 of two stations sells at both. `sky` has no bag art (the loop only cut
  stone / leaf / diamond) so its icon is blank. Not run in a browser; the block was exercised with stubs (buy, can't afford, snacks, day / night).

## 00000000000000000000000000000000000000000000000000000000000000000000000. LAYER 469 -- HEADLIGHT / NEON COLOURS, HOOD BLOWER, OFF-ROAD TIRES, THE NEW STATIONS, STAN'S

Corrects LAYER 468: the 41 coloured cylinders are **headlight and neon colours, not paint**. PAINT is gone from the wheel; **LIGHTS** replaced it.

- **LIGHTS** (`PARTS.light`, $250): the chosen colour tints the player's night headlight beam (`hlc` in the night pass) and puts a soft
  glow under the car (`drawUnderglow`, additive, brighter at night). Lives on `car.lightHex`, set by `partsApply`.
- **Supercharger on the hood** (`drawHoodBlower`): the four `en_s_*` sprites, drawn over the centre of the hood, 0.36 x car length long,
  belt end toward the nose. Turbo and factory engines stay under the hood (not drawn). Player car only.
- **TIRES** (`PARTS.tires`): one entry, OFF-ROAD TIRES $1800 -> `offroadTires(c)` lifts the off-road speed factor in `stepCar` from 0.62 to 0.97
  (the Jeep / ATV table still wins). No art was supplied for the tire card, so it uses the Tasty's spare-tire sprite as a stand-in.
- **Mods now live on any car**: `modsOf(c)` = the pool slot's mods, else `c.mods`. A stolen / street car can be upgraded at Stan's but loses
  the parts when you leave it (only pool cars carry them back into a stall). `partsApply` is idempotent (`car.toughBase`).
- **STAN'S GARAGE** replaces Eddie's: same building (`g.repairB`), name and roof (`st_roof_garage`) changed; the panel gets
  **UPGRADE & TUNE MY CAR** (opens the parts wheel on the car you drove up in). `st_roof_office` is cut and registered but not placed yet.
- **GAS STATIONS**: every station is Tasty's or Kum n Pay by cell (`gasBrand`, checkerboard). Brand roof over the shop rect, brand awning over
  the canopy rect (Kum n Pay's awning art is square, so a 2:1 band is cropped out of its middle), brand pumps on the islands, Kum n Pay's oil-stain
  floor tile for its forecourt. Tasty's shop roof is 1.6:1 art squeezed into a 2:1 rect -- ask for a wider cut if it looks squashed.
  The shop INTERIOR (counter, coolers, shelves) is unchanged and shows when you walk in. Selling snacks and drinks is not built yet.
- **JOE'S REPAIR SHOP**: `jo_roof` cut and registered, NOT placed. Art reads as: left strip = two round-window rooms (reception + break room),
  right = two vehicle bays under the name. It needs its own building + interior pass (and a second `g.repairB`-style slot).
- **Cut but unused**: `tt_truck`, `tt_tire`, `tt_pump_b` (grey/blue pump variants), `km_pumps2`, `km_tires`, `km_ext`.
- Art: `assets/city/` (17 files), `assets/parts/` (the supercharger sprites are loaded by the game now as well).
- **Not run in a browser**; the new logic was syntax-checked and exercised with stubs. Check first: pump sprite placement on the islands, and
  the Tasty's roof stretch.

## 00000000000000000000000000000000000000000000000000000000000000000000000. LAYER 468 -- GARAGE PARTS: THE MECHANIC'S PARTS WHEEL, BOS / NOS

Continues LAYER 467. `game.jsx` is now ~4.5 MB.

- **Talk to a hired MECHANIC at the scrapyard** -> `WORK ON A CAR · PARTS & TUNING` (added in `bmExtraOpts`). One car in the
  motor pool goes straight to the wheel; more than one asks which stall first (`garagePanel("cars")`).
- **THE WHEEL** (`garageWheel`, a `G.radialOpen` ring): ENGINE / BRAKES / PLATING / WING / PAINT / NITROUS, each slot showing what's
  installed. Pick one -> the SHOP for that part (`garagePanel(cat)`): a card per option with its sprite, name, price and what it does;
  the installed one is dimmed with a tick; BACK TO THE WHEEL / DONE. Buying = `garagePick("buy:<cat>:<key>")`, cash straight off `g.p.cash`.
- **Catalogue = `PARTS`** (module level, next to `PD_ART.ac_*`). Tune every number there: engines (3 factory defaults, 4 turbo, 4
  supercharger -- each its own `s` top speed / `a` accel / `th` thirst / price; turbos lean top speed, superchargers lean accel),
  brakes x3 (`br`), plating x3 (`tough`, small `s`/`a` weight penalty), wings 4 tiers x 4 colours (`g` grip), paint x41 (`hex`),
  nitrous BOS / NOS. Plating is 3 levels: `pt_1_1`, `pt_2_4`, `pt_3_2` -- swap the `img` to use another tile from the sheet.
- **Where it lives**: `slot.mods = { engine, brakes, plating, wing, paint, nitro: {t, n} }` on the motor-pool slot. `carStat` / `carThirst`
  (module level, now wrappers over `carStat0` / `carThirst0`) read it via `c.pool`; the brake line in `stepCar` uses `brakeMul(c)`;
  `partsApply` puts armour (`tough`) and paint (`tint`) on the car as it leaves the stall; `G.motorParkFn` copies `mods` onto the new
  slot when it's parked again. Cars not from the pool (stolen, street) have no mods.
- **BOS / NOS** (tank = 3 shots; refill $400 BOS / $700 NOS a shot): fire with the BOOST button or **B**. BOS = 7 s, NOS = 11 s,
  REAL seconds (`g.nitroT` is drained on `rdt`, not the slowed dt). While it runs the world goes to half speed (main loop,
  just above the existing `turboSlow` branch) and your car gets x1.7 top speed / x1.6 accel (`nitroMul`). A car with a tank wins over
  the SHO STOPPER boost check in `turboBoost`.
- **Art**: `assets/parts/` -- 87 keyed sprites cut from the 10 sheets. `en_f_*` factory, `en_t_*` turbo, `en_s_*` supercharger,
  `br_1..3` brake panels (NOT keyed -- the purple card is part of the art), `pt_L_n` plating, `wg_tier_n` wings, `pl_01..41` paint,
  `nx_bos` / `nx_nos`. All registered as `PD_ART["pa_<name>"]`.
- **NOT DONE / STILL OPEN**: (1) the gas stations and Eddie's are untouched -- the stands that replace them need their own building art;
  parts are only sold by the scrapyard mechanic for now. (2) Nothing is DRAWN on the car yet: wing, plating look and paint change
  stats / `tint` only (the game never renders `v.tint` on cars, it's the same dead field Eddie's respray sets). (3) Engines have no
  sound / HUD readout of shots left beyond the pop-up. (4) Not run in a browser -- the new blocks were syntax-checked and the shop flow
  simulated with stubs only.

## 0000000000000000000000000000000000000000000000000000000000000000000000. LAYER 467 — NOSE-FORWARD FLIGHT, THE PILOT, STEAL A CHOPPER, THE CREW'S PAD

Continues LAYER 466. Current build: `game.jsx` is **4.98 MB / 53,795 lines**.

- **BUG FIXED: the observer chopper (`__ironlion.fly()`) flew sideways.** `stepFly`/`drawFly` just
  translated on input with no rotation at all -- strafing left or right flew the disc sideways
  instead of turning to face where it was going. Fixed with a turn-toward-heading: on real stick
  input, `g.fly.ang` turns toward `atan2(ay,ax)` at `FLY.turn` rad/s (so a quick tap doesn't spin
  it on a dime; centred stick keeps the last heading rather than snapping to (0,0)), and `drawFly`
  rotates the plate by `ang + 90°` -- same nose-up-art convention `drawChopper` already used for
  the FIS transport bird, now applied here too.
- **THE PILOT** (`HIRES.pilot`, $3000, 300 rep): a new hire, same system as every other trade on
  the board.
- **STEAL A CHOPPER** (`OPS.stealchopper`, needs pilot + driver): a new job, LED IT like any heist.
  Built on the EXISTING "steal/chop" prize pattern (`MIS_KIND.stealchopper = "chopper"`) rather
  than inventing a new mission system from scratch -- a stealable chopper sits at a site
  (`misTarget`, same `streetPt` picker steal/chop already use), the PILOT preps it in place of the
  mechanic hot-wiring a car ("PREP THE ROTORS" -> `P.hot = 1`), and E climbs in.
  **Taking it off is a flag, not a new vehicle type**: boarding sets `g.car.flying = 1` on the SAME
  `g.car` body every other vehicle uses. `stepCar`/`drawCar` both branch on that flag at their very
  first line, straight to new `stepFlyingCar`/`drawFlyingCar` -- no road, no grip, no fuel, no
  collision, just the identical turn-toward-heading nose-forward flight as the `stepFly` fix above
  (its own copy, `FLY_CAR`, since a car body and `g.fly` are different objects). Everything else
  about the mission is UNCHANGED: `M.phase = "away"`, the arrow, and the scrapyard-door proximity
  check that finishes the job all read `g.p`/`g.car` exactly like driving one home does, and
  `g.p` tracks `g.car` every frame (`g.mode === "car"`) no matter how it's moving.
  `g.car.flying` is cleared (defensively, belt and suspenders) everywhere a DIFFERENT vehicle gets
  under the player -- carjacking, the motor pool, a mission's own lead car -- so it can never leak
  into an ordinary car and hand out free permanent flight; it's also cleared the instant
  `misFinish` runs, which is what "landing" means here (there's no altitude, so crossing the
  proximity threshold while flying over the scrapyard just IS touching down).
  **NOT reusing the `ride:` field** the other steal/chop/van/truck ops use -- a chopper doesn't fit
  a 20-stall motor-pool garage, so `stealchopper` has no `ride:` key at all and the generic
  rides/`motorAdd` code in `misFinish` never fires for it. Instead, success sets `g.crewChop = 1`.
- **THE CREW'S PAD** (`drawCrewChopPad`): once `g.crewChop` is set, a parked chopper + landing ring
  draws permanently at the SCRAPYARD (`hideoutB()`) -- separate from the Lion's own `drawChopPad`
  at his own place (`denOf()`), different building, different flag, same drawing trick, opposite
  corner of the lot from the `SCRAP_KEYS` prop placements so it doesn't stack on the crane/scrap
  pile already there.
  **STILL OPEN, same as the Lion's own chopper**: it's a showpiece, not re-enterable -- his
  personal one is `__ironlion.fly()`-only too (a debug/observer command, not a normal play path),
  so this follows the same precedent rather than cutting a new corner. Making it fly-again-on-
  demand later is cheap now that `stepFlyingCar`/`drawFlyingCar` exist: push a parked `g.traffic`
  entry at the pad (`crewChop: 1`) so the EXISTING carjack system finds it, and set
  `g.car.flying = 1` there the same one line everywhere else already clears it.
  **STILL OPEN**: the site a chopper is stolen from is generic (whatever street-adjacent spot
  `streetPt` finds, same as any car), not a bespoke guarded airfield/convoy. If what was actually
  wanted is closer to the existing ARMORED CAR / HIJACK pattern -- a truck on a fixed route you
  have to stop, then take what's on the back of it, rather than a parked pickup -- that's a
  second, larger pass reusing `MIS_KIND: "route"` instead, worth doing as its own layer.
- **Art, this session**: `vh_crew_chop.png` (`assets/vehicles/`) -- a second, distinct chopper
  plate from the Lion's own `vh_lion_chop` (`assets/heroes/`), re-cropped and rotated 90° from the
  user's reference render to the game's nose-up convention (the reference had it lying on its
  side). `px_pilot.png` (`assets/crew/`) -- the PILOT hire's face, picked as the lead of three
  portrait variants the user generated (brown leather jacket, flight helmet); the other two
  (`px_pilot_beret.png`, `px_pilot_vest.png`) are kept in `assets/crew/_spares/` as alternate
  looks, not wired to anything.


## 000000000000000000000000000000000000000000000000000000000000000000000. LAYER 466 — THE REAL MAP, MISSION ROUTING, NO COPS AT SCHOOL, PER-CHARACTER WEAPON WHEEL, ICON SET

Continues LAYER 465. Current build: `game.jsx` is **4.98 MB / 53,795 lines**.

- **The minimap is real art now.** Replaced the procedural grid-line minimap with the hand-painted city
  map (`assets/map_atlas.png`, from Donny's upload). Fit by measuring both expressway crossings on each
  axis against known world-grid values and cross-checking a third landmark: `MM_SX = 0.0265, MM_OX = 27.5,
  MM_SY = 0.026242, MM_OY = 39` where `image_px = world_units * MM_S? + MM_O?`. Used on both the full map
  screen (the atlas is windowed/scaled into the panel) and the corner minimap (a `span`-sized window drawn
  around the player), with a fallback to the old procedural draw if `map_atlas` hasn't loaded yet.
- **Route lines**, on both map surfaces, dashed, same helper pattern (`routeLine` on the full map,
  `mmLine` on the corner one, both clipped/scoped to their own rect): to the **active crime call** (red),
  to the **active story mission** (gold — this was missing before, now reads `g.missions.find(m=>m.active)`),
  and the **remaining race checkpoints** (`R2.cps.slice(R2.at||0)`, not the ones already taken).
- **BUG FIXED: crime calls were showing up in school mode.** Four separate display call-sites all draw
  from `g.crime` independently and none of them checked `g.studentMode` -- the world-space pulsing dot, the
  corner minimap's line+pip, the full map's line+pip, and the off-screen edge arrow. Gated all four with
  `&& !g.studentMode`. Kids don't get police calls; cops don't show up on a kid's map either.
- **BUG FIXED: every character had the Lion's guns on their weapon wheel.** Root cause: `g.rack` (the den's
  weapon locker) is one shared array -- whatever the Lion stocks it with sits there for anyone. Pickup was
  already gated (`KID_OK`/`isGun`), but `G.weaponWheel()` read the whole rack straight through with no
  filter, so once the Lion had guns stashed, every kid's wheel showed them too, selectable. Fixed by
  filtering the wheel's item list (`lionPowersOn() || KID_OK[k]`) AND adding a matching hard gate in
  `G.wheelWeapon(k)` itself (refuses + `pickupFlash` "kid_wont_carry_that" if a kid somehow sends a gun's
  key through), so there's no second path in, consistent with the "hard gate, not just a hidden button"
  rule already on the pickup/gear-up gates.
- **Weapon wheel icon set.** The HOLSTER/bare-hands slot never had an icon (`PD_ART.wi_empty`, now wired
  to both the main wheel's HOLSTER item and the prison pockets wheel's BARE HANDS item). This session's
  batch delivered **25 of the 32 wheel icons** as finished, chroma-keyed PNGs (pixel-art, magenta-keyed to
  transparent same as every other sheet in this pipeline, no fringe):
  `wi_empty, wi_zipgun, wi_cryo, wi_laser, wi_grenade, wi_molotov, wi_crowbar, wi_bat, wi_pencil, wi_razor,
  wi_bayonet, wi_machete, wi_beretta, wi_colt, wi_pistol, wi_revolver, wi_snub, wi_uzi, wi_mac10, wi_pump,
  wi_sawnoff, wi_shotgun, wi_hunting, wi_ar15, wi_tommy` -- dropped at `assets/ui/` (and `assets/weapons/`
  for `wi_cryo`, `wi_laser`, `wi_tommy`, matching where the code already looks for them). All 25 are
  registered in code already (either from before, or `wi_empty` this session) -- no further wiring needed,
  just drop the PNGs in.
  **STILL OPEN**: 7 icons not generated yet -- `wi_nightstick, wi_taser, wi_mace, wi_tireiron, wi_knuckles,
  wi_bottle, wi_chain`. Prompts for these are in `WEAPON_WHEEL_ICON_PROMPTS.md` (trimmed down to just the
  remaining 7 this round). There's also one spare/unmatched pistol render in `assets/_spare/` that didn't
  correspond to any open icon slot -- not wired into the game, kept in case it's wanted as an alt skin for
  `wi_pistol` or `wi_beretta` later.

- **The action wheel got icon support too.** Its five fixed slots (WEAPONS, POCKETS, FAST
  TRAVEL, CREW RULES, SIT-DOWN -- DRIVER already shows a face) were text-only; wired
  `PD_ART.ac_weapons/ac_pockets/ac_fasttravel/ac_crewrules/ac_sitdown` in and passed `icon`
  on all five `list.push` calls in `openWheel()`. The ring's own render already handled an
  `icon` field (same `{o.icon && <img.../>}` as the weapon/pockets wheels) so this was pure
  wiring, no rendering change needed. Everything else on that wheel (TALK, RADIO, HYDRO, the
  hero powers, etc.) is context-dependent with no single fixed meaning, so left as text by
  design. **STILL OPEN**: art for all five -- prompts in `ACTION_WHEEL_ICON_PROMPTS.md`.

**STILL OPEN** (carried over, not touched this session): bus loop pathfinding, classroom ladder/chalkboard
layout, gym hoops + dodgeball class + weekday rotation, living-room TV/console art, full bike-riding
physics + usable-bikes roster, kid sprite resize.


## 00000000000000000000000000000000000000000000000000000000000000000000. LAYER 465 — THE WEEK, CURFEW, SNEAKING OUT, DEVON CALLS, HANGOUTS

- **The week**: day 1 is a Monday (DOW, dowOf, isSchoolDay, nextSchoolDay). Sat/Sun: no school (bellBlock "closed" in
  student mode). Tests Mon English ... Fri Art; homework studies the next SCHOOL day's subject. Dances: the Friday of
  every second week (days 12, 26, 40); PROM: Saturday of week 6 (day 41). The clock shows MON..SUN.
- **Upstairs**: his room, Mom's room AND a bathroom over the hall; the **ladder to the roof is in the hall**
  (roofHatchPt for b.stuHome = 70%, 80%; hatchOK allows the student's house even though it has a roof plate).
- **Curfew** (`curfewNow`): 10 PM school nights, midnight Fri/Sat, 6 PM while grounded. CAUGHT = the front door (in or
  out) after curfew while Mom is home, or not in the house when she checks your room (half the nights, once, some time
  after curfew). `stuGround`: grounded 3 days (no lunch money, 6 PM curfew, no calls), -5 popularity, Mom says so.
  **Sneaking out**: up the hall ladder to the roof, down the DRAINPIPE on the house's left side (`G.pipeFn`: E at the
  pipe outside / at the roof edge above it). NOTE `G.drainFn` is the PRISON drain -- this one is `G.pipeFn`.
- **Devon calls** (home, 6-8:30 PM, 45%, not grounded): the skate park, the arcade or Lovers' Lane, at 8:30 PM (10:30
  Fri/Sat). **Hangouts** (`hangSpots`: the skate park (SX(6),SX(8)), the arcade nearest home, LOVERS' LANE in the park
  (SX(9)+750, SX(13)+300) with three parked cars, night only): a crowd of kids; E -> HANG OUT (an hour, +3 popularity
  once a spot a day, double with Devon there as promised), and at the lane TAKE A BEER (+2) / A CIGARETTE (+1) --
  Mom smells it that night or the next morning. Verified: ladder, pipe, the front-door bust, a call, a hangout.

---

## 0000000000000000000000000000000000000000000000000000000000000000000. LAYER 464 — SLOW SCHOOL, SITTING DOWN, THE CLOCK, NO TELEPORTING

- **school_music_464.zip** -> assets/music/school.mp3 = "After the Final Bell" (the right song this time).
- **BUG FIXED**: the world clock (main loop, by stepAnimals) ALSO ran in student mode, so the student's clock went
  double speed. It now skips when `g.studentMode` -- student mode keeps its own.
- **Pace** (stepStudent): a period (50 game min) = 3 real minutes, lunch 3, passing time (5) = 1 real minute,
  arrival/dismissal 30 game min per 2 real minutes; outside school the usual CLOCK.rate. Verified 0.24 / 0.07 per s.
- **Sitting down** (myDesk, nextPeriod, G.stuSitFn, before stuClassFn): your desk = the last desk of your group's room;
  E there before the period starts = seated ON TIME (+1 at the bell); after it starts = TARDY (no point, readiness +6);
  never seated = ABSENT (-1). Leaving the room unseats you. Questions and tests need you seated.
- **The clock** (`drawStudentClock`, top-right): time, DAY n and the bell block.
- **No teleporting** (schoolFolk keeps the previous list on the same floor): at each bell people WALK from where they
  were to their new places (speed 70, collideCrew); new arrivals come up from the stairs (staggered); people leaving
  walk to the stairs (`g.sleave`). Verified: 64 walking at the start of 2nd period.
- **Logos** on the school roofs are pinned (no roofOffset).
- **Faces in talk panels**: the panel <img> had no key, so ONE failed load (display:none) hid every face after it.
  Now keyed by src, and 64 px.
- **Malcolm's building**: the stairs sit at the TOP of the corridor between the suites, same spot on every floor.
- **The student's TV**: moved 14 down -- inside the outer-wall margin it was being deleted.

---

## 000000000000000000000000000000000000000000000000000000000000000000. LAYER 463 — THE DRIVEWAY, THE BUS IN THE STREET, SCHOOL MUSIC

- **school_music_463.zip** -> assets/music/school.mp3. NOTE: Donny's upload "Before_the_Rain.mp4" was byte-for-byte
  the same file as the prison song (same md5); wired as MUSIC.school anyway -- if a different school song exists,
  just replace school.mp3. The chooser plays it in student mode.
- **The bus** (`busStop` now returns [x, y, angle]): in the curb lane of the road the door faces (SX(line) +- halfW/2),
  level with the door, lying along the road; E within 110. Same for the school.
- **Mom's driveway** (`driveway(H)`, cached on H.drive): a concrete strip beside the house (the side with room, clear
  of other buildings, inside the lot) from the house's front line out to the pavement; the wagon sits on it nose to
  the street when she is home. Verified on screen.

---

## 00000000000000000000000000000000000000000000000000000000000000000. LAYER 462 — THE STUDENT'S HOUSE REDONE

- The house is **two floors** (floors 2, entry 0). Downstairs `stuhome`: living room (sofa, a small TV 30x20,
  bookshelf) and kitchen (fridge, stove, table) -- Mom stands in the kitchen. Upstairs `stuupper`: a hall along the
  bottom (the stairs), HIS ROOM (bed, desk against the top wall, poster), MOM'S ROOM (bed, dresser), the BATHROOM
  (toilet, sink). Every piece against a wall; the middle of each room open.
- `clearHomePaths(b)` runs once after the plans are made: drops any prop within 75 of the front door, within 36 of the
  stairwell, or within 46 of any doorway between rooms.
- He wakes (and sleeps) upstairs beside his own bed (`stuBedRoom`, `stuBedPt`); E only works on the bed and desk in
  HIS room (Mom's bed is just a bed). Mom: floor 0 only. Verified: walked from the bed to the desk and opened it.

---

## 0000000000000000000000000000000000000000000000000000000000000000. LAYER 461 — QUESTIONS, BOOKS, STUDYING, POPULARITY, DANCES, PROM

- **STU_Q**: 15 questions a subject (English, Math, Science, History, Art), 1986-plausible, each [q, [3 answers], right].
- **Books** (g.stu.packed): the home desk PACK / UNPACK. In class without them: no questions; a test sat without
  them loses 60 readiness first. Homework needs them UNPACKED.
- **Studying** (desk after 2:45, books out): STUDY <tomorrow's test subject> 30 min / 1 / 1.5 / 2 hours. Readiness
  +min/10, and tomorrow's three test questions are drawn now (`U.nextTest`) -- one revealed per 40 minutes, shown in
  the desk text, and on the test marked "\u2605 (you studied this one)". Homework points +2 once a day.
- **Grading** changed: score = right x 30 + readiness / 10 (3 of 3 = A).
- **Popularity** (g.stu.pop, starts 30; `kidPop` for every kid 20-100, jocks and legacy +10): a won fight +3; a yes
  +5, a no -4; a dance +8 (+7 with a date); prom +15 (+7 with a date); prom stag -20; missing prom -20.
- **Dances** (DANCE): school days 10, 20; **PROM** day 30; 7-10 PM in the gym (36 dancing kids); curfew +30 min
  that night. ASK TO THE DANCE / PROM in any kid's panel: yes if disposition >= 50 + (their pop - yours) / 2.
  The morning banner and the desk announce it. Verified: a yes, the dance (+15 with a date).

---

## 000000000000000000000000000000000000000000000000000000000000000. LAYER 460 — MOM, DEVON AND THE CAR DRAWN; TESTS

- **family_460.zip**: assets/school/yt_/pt_stu_mom (IMG_4183), yt_/pt_stu_bestfriend (Devon, IMG_4185; the odd
  back-view on that sheet not used), assets/cars/car_stu_mom (IMG_4184, the burgundy wagon, rotated nose-up). The
  stand-ins swap out automatically.
- **Tests** (testSubj, GRADES, addReady, gradeTest, testPanel): one subject a school day in rotation (day 1 English,
  2 Math, 3 Science, 4 History, 5 Art, repeat), in that subject's period. READINESS per subject (g.stu.ready): in
  its class at the bell +10, a right answer there +10, homework +12 to the NEXT day's test subject. On test day E in
  that class = the test (3 questions; readiness 50+ crosses out one wrong answer on each). Grade = right x 25 +
  readiness / 4: A 90 (+10), B 75 (+6), C 60 (+3), D 45 (0), F (-3); absent = F; in the room but never sat it =
  graded on readiness alone. Readiness drops to 20 after. The morning banner names today's test; the desk shows
  the report card, readiness and the next test. STU.transfer raised 60 -> 90 (tests pay). Verified: an A in English.
- Only 3 questions a subject so far (STU_Q) -- a test uses all three; add more questions to vary it.

---

## 00000000000000000000000000000000000000000000000000000000000000. LAYER 459 — STUDENT MODE FILLED IN: MOM, BUS, HOMEWORK, DETENTION, CLIQUES, FIGHTS, DEVON

Block above `kestrelRoster()` (CLIQUES, RIVALS, KID_F/L, kidClique, kidRec, kidDisp, BF, busStop/busHere, G.busFn,
drawStudentWorld, momPt, drawMom, G.momFn, momPanel, stepStudentLife, G.kidFn, kidPanel, kidAct, stepBestFriend,
drawBestFriend, drawKidTags). Art keys waiting: yt_/pt_stu_mom, yt_/pt_stu_bestfriend (assets/school/),
car_stu_mom (assets/cars/) -- stand-ins until then: a public teacher's plate for Mom, kid #3's look for Devon,
buy_sedan_grey for her car.
- **Mom** in the kitchen before 7:50 and after 5:30 PM; E: LUNCH MONEY ($5, once a day, g.stu.cash) and a line that
  follows your record (detention, the scholarship coming, the streak, cutting). Her car out front when she is home.
- **The bus** 7:15-7:45 by the house, 2:20-3:00 at the school door: E -> there (clock to 7:50 / +15 min).
- **Homework**: the home desk after 2:45: +2, 1.5 hours; not done -> -1 at the first bell next day.
- **Detention**: a fight has a 50% chance of being seen -> tomorrow 2:30-3:30 in the library; skipped -> -3.
- **Cliques**: Central: BURNOUTS (stu_ch 1-14), B-BOYS (15-28), JOCKS (29-58), BRAINS (the first 24); St. Aldric's:
  CREW (sa 1-32), SCHOLARSHIP (33-44), A/V + CHOIR (45-60), THEATRE (61-76), LEGACY. RIVALS map. Each kid (`kidRec`):
  name, clique, trait, toughness, disposition (+ half your standing with his clique). E on a kid (hall, lunch, gym):
  TALK / JOKE / SPLIT YOUR LUNCH ($1) / TALK TRASH (-15, his clique -5, their rival +3) / FIGHT (odds from your
  RESPECT, his toughness, Devon at your side; win: respect +10+, his clique -15, the rival +5, he goes down; lose:
  respect -5). Names over kids you know: gold Devon, green 40+, blue, red -30.
- **Devon Greene**, best friend: kid #3 at Central (your group), disposition 100; WALK WITH ME AFTER SCHOOL -> he
  follows you after the bell (+12% in fights at school). Verified: mom's money, the bus, a talk and a lost fight,
  Devon walking behind you.
- NOT YET: two cuts -> detention; Devon when you transfer (he stays at Central); Mom's car drivable; the kid's story.

---

## 0000000000000000000000000000000000000000000000000000000000000. LAYER 458 — STUDENT MODE

Title screen: **STUDENT MODE** (`g.studentStart` -> `startStudentMode`, run from `stepStudent` in stepCase).
Block above `kestrelRoster()` (STU, STU_SUBJ, STU_Q, studentHome, startStudentMode, stuClassroom, stepStudent,
G.stuHomeFn, G.stuClassFn, G.stuPick, the stubed / studesk / stuq panels).
- **Home** (`studentHome`): the house/apartment 500+ from Central High and nearest it, re-planned (floorKind
  "stuhome": living room, his bedroom -- bed, desk, dresser, a basketball poster -- and kitchen). Day 1 starts 6:30 AM
  at his bed. E at the bed: SLEEP UNTIL 6:30 AM (next day, back in bed); E at the desk: grade points, streak, and
  the scholarship letter when it comes.
- **The day**: the clock runs in student mode (`stepStudent`, CLOCK.rate). The bell (BELL): each period his group
  (0) is in classroom (5 - p % 5) % 5 upstairs -- the HUD banner says PERIOD n · SUBJECT · ROOM k. In the room when
  the bell goes: +1 ("PRESENT"); not: -1. E in the room during a period: the teacher's question (STU_Q, 3 per subject,
  1986-plausible) -- right +3, once a period. Out of the house after 10 PM: -2. His seat (the last desk of his
  group's room) is left empty in `schoolFolk`. Player plates: yt_stu_player_ch / yt_stu_player_sa.
- **Advancing**: at STU.transfer (60) points the offer arrives; ACCEPT at the desk -> school "aldric" (the blazer,
  St. Aldric's rooms and rotation) from the next morning. Verified: present + a right answer = 4; the offer, the
  transfer, a new day at home.
- NOT YET: getting to school is on foot/by car across town (no bus), a mom at home, homework, detention, fights,
  friends/cliques, the player as a character in the wider story.

---

## 000000000000000000000000000000000000000000000000000000000000. LAYER 457 — THE WHOLE STUDENT BODY, AND THE PLAYER STUDENT

- **students_457_part1..3.zip** (assets/school/, <=100 each): yt_/pt_stu_ch_1..58 (metalheads IMG_4171, b-boys 4170,
  jocks-and-cheer 4172 + 4173 -- helmeted/back views kept: seated kids face the board, away from the camera) and
  yt_/pt_stu_sa_1..76 (4177 + 4176 the two rowing/lacrosse sheets -- both used, 4179 scholarship, 4178 A/V-debate-choir,
  4181 theatre/debate), plus yt_/pt_stu_player_ch / _sa / _sa2 (IMG_4168: varsity jacket, two blazer versions).
  Bodies hip-cut; a sheet's faces pair with its bodies when it has as many, else the school's face pool (the brains/
  band/loners sheet 4175 and the mixed-faces sheet 4182 fill it). Metalheads have 13 faces for 14 bodies (pooled).
- `STU_N`, `stuPool(sc)` (the numbered looks + the first 24); `schoolKids` gives each of the 60 kids a look out of
  the pool ((i*37+11) mod pool). Verified: a varied 3rd period.
- The player's student plates are registered, NOT used yet (student mode).

---

## 00000000000000000000000000000000000000000000000000000000000. LAYER 456 — THE SCHOOLS BUILT OUT: TWO FLOORS, THE DAY, THE TRACK AND FIELD

- **school_kit_456.zip** (46 sch_*: classroom, cafeteria, library, office/lounge/nurse, gym and field kits; the
  laptops painted out of both teacher's desk b and the principal's desk) and **school_people_456.zip** (88: yt_/pt_
  for 10 public staff stf_ch_*, 10 prep staff stf_sa_* -- the prep sheet was busts, so arms, hands and a torso were
  drawn on -- and 24 students stu_<ch|sa>_<m|f>_<1-6>). All in assets/school/. SCHOOL_KIT2, SCHOOL_PEOPLE register them.
- **Two floors** (schools() sets floors 2, entry 0): floorKind "school_g": hall across the middle; gym (court on the
  floor, side hoops, mats, vault), cafeteria (serving line, six tables, trays), library (shelf unit, reading table,
  circulation desk, cart, catalogue) above it; principal's office, teachers' lounge, nurse below. "school_c": hall
  (lockers, trophies) with FIVE classrooms (3 above, 2 below): chalkboard, flag, clock, teacher's desk, 12 desks in
  3 rows of 4, bookcase + world map (prep) or storage bins (public). Floors: prep marble / good wood / carpet / rug,
  public linoleum / tx_shack_wood / terrazzo; both gyms court wood.
- **The day** (BELL, bellBlock, schoolFolk, drawSchoolFolk): arrival 7:30, periods 1-6 (8:00-2:20) with 5-minute
  passing times, LUNCH 10:45-11:35, dismissal 2:20-2:45. Each period every classroom seats its rotating group of 12
  at the desks facing the board with its teacher at the desk; 6th period the fifth group is in the gym. Lunch: the
  whole school at the cafeteria tables (40 seats -- 20 stand, NOT fixed), the lunch lady at the line. Principal,
  nurse, coach, librarian, janitor at their posts in hours. Passing times: a third of the kids drift in the halls.
  Verified: 65 people upstairs in 3rd period, 45 at lunch downstairs.
- **Track and field** (schoolField / drawSchoolField): in the biggest open side of the school's lot: the oval track,
  a football field inside (field40 / field50 / field40, lined end zones), goalposts, bleachers, a scoreboard. Verified.
- NOT YET: students walking between floors at passing time, buses bringing them, student mode.

---

## 0000000000000000000000000000000000000000000000000000000000. LAYER 455 — THE GARBAGE TRUCK'S ROUNDS, OLD TOWN LANES, THE SCHOOLS WORKBOOK

- **raven_hook_schools.xlsx** (Donny's planning workbook): Schools, Rooms (both schools: 5 classrooms, hall, gym,
  cafeteria, library, principal's office, teachers' lounge, nurse, locker rooms, track + football field, bus loop;
  art keys + HAVE/NEED), Bell Schedule (game minutes), Rotation (5 groups of 12 through 5 rooms; everyone at lunch),
  Students (60 per school with group, grade, clique, trait, plate/face keys yt_/pt_stu_<ch|sa>_<m|f>_<1-6>),
  Assets (38 lines, 10 HAVE / 28 NEED, prompt #), Prompts (8).
- **The truck's rounds** (`truckRounds`, GT): within 260 of a trash corner that still has an open dumpster / open
  can / bags, the truck holds 3.5 s (pinned in place), then shuts them and takes the bags; 6 s cool-down. A corner
  emptied on an earlier game day is regenerated full (`cellAlley` checks `A.emptied`). Uses real frame time
  (it is driven from the draw pass). Verified: held, emptied, drove on.
- **Old Town lanes**: in `drawOldTownBlacktop`, each Old Town block gets a 56-wide darker cobbled lane each way
  through its middle with a gutter line each side, drawn on the ground (buildings cover it where they stand).
- Test hook `G.cellAlleyT(i, j)`.
- SCHOOL BUILD-OUT still to do (waiting on art): 5 classrooms of 12 desks, cafeteria, library, lounge, nurse,
  locker rooms, the track + football field outside, students on the bell schedule, student mode.

---

## 000000000000000000000000000000000000000000000000000000000. LAYER 454 — ALLEYS, THE GARBAGE TRUCK, OLD TOWN BLACKTOP, THE SCHOOLS

- **Alleys** (`cellAlley`, made per cell the first time on screen, deterministic by cell): in ALLEY_ZONES lots, 2-3
  trash corners in open ground (never under a building): a dumpster (open or shut) or two cans, a bag, sometimes
  pallets, often three pigeons. Pigeons scatter within 70 (fly frames) and settle back. Dumpsters and cans are
  solid (`alleyCollide`). Drawn after the Old Town props (`drawAlleys`). Verified in the hood.
- **The garbage truck** (`stepGarbageTruck`): one ordinary traffic car is always turned into `al_garbage_truck`
  (len 150), named, idn RAVEN HOOK SANITATION; if it goes, another takes the job. Verified.
- **Old Town blacktop** (`drawOldTownBlacktop`, after the cobble fill): avenues (i % AVE_EVERY) and the two streets
  through the circle's crossroads (ci / cj) are tx_blacktop with a worn yellow centre dash; the circle itself is
  clipped out; the other streets stay cobbled. Verified.
- **The schools** (`SCHOOLS`, `schools()` picks once: the biggest building in the hood -> RAVEN HOOK CENTRAL HIGH;
  uptown -> ST. ALDRIC'S): crest on the roof (through roofOffset), a yellow school bus parked at the door (traffic,
  idn "SCHOOL BUS"), bleachers and a goalpost in the lot (`g.schoolProps`). floorKind "school" on the entry floor:
  hall (`schhall`: lockers, trophy case), 2-4 `classroom`s (teacher's desk, rows of desks, that school's
  textbooks), `schgym` (bleachers, goalpost), `schoffice`. Verified: Central High at (7874,13962), inside and out.
- NOT YET: tight pedestrian lanes cut through Old Town lots; students; the garbage truck stopping at dumpsters.

---

## 00000000000000000000000000000000000000000000000000000000. LAYER 453 — NEW COPS, WEAPON ICONS OVER HEADS, ALLEY + SCHOOL ART

- **art_453.zip** (57 files): assets/heroes/ yt_/pt_ dale, chen, beck -- the NEW sheet (IMG_4144), knee cut, replaces
  the old ones; assets/ui/ 16 street + police weapon icons (WI_STREET: snub, beretta, colt, uzi, mac10, pump, sawnoff,
  hunting, ar15, nightstick, taser, mace, machete, crowbar, molotov, grenade); assets/alley/ (ALLEY_KEYS: cans,
  dumpsters, bags, garbage truck nose-up, pigeons, gate, fire escape, pallets -- no cats/dogs, the game has them);
  assets/school/ (SCHOOL_KEYS: both logos, bus, lockers, trophy case, bleachers, goalpost, varsity jacket, blazer,
  eight textbooks); assets/tex/tx_blacktop.png. IMG_4146 (an informant + cracked tiles) was not asked for -- not cut.
- **Weapon icons over heads**: `drawWeapon` (every man whose weapon is OUT this frame -- gangs, cops, rogues, the
  player) records him in g.wIcons; `drawWeaponIcons` (after drawBackup) draws `OVERHEAD_ICON[m.wpn]` upright over
  his head on a dark plate. NOTE `WPN_ICON` is the existing HUD atlas map -- the overhead map is OVERHEAD_ICON.
  Verified: Malcolm's Beretta over his head.
- Registered, NOT placed yet: the alley kit (alleys through the big lots, garbage truck route), the schools, blacktop.

---

## 0000000000000000000000000000000000000000000000000000000. LAYER 452 — MALCOLM'S SLIDING DOOR, A BIGGER GOMEZ MANOR

- **makeFloor**: two new room flags. `doorVia: "<kind>"` -- the room only connects to rooms of that kind (and
  apt_neighbor); `doorEnd` -- its doorway goes at the END of the shared wall (bottom / right) instead of the
  middle. A doorMark touching a room with `slide` gets `slide: true`. Malcolm's homeapt corridor: doorVia
  apt_kitchen, doorEnd, slide -> his only way out is the bottom of the kitchen's wall (the old gap from the
  bedroom is gone; furniture was blocking it). The neighbour's door off the corridor slides too.
- **Sliding doors** (slideDoors, G.slideDoorFn, stepSlideDoors, drawSlideDoors; g.sdoor by building:floor:x:y):
  shut by default; E within 55 toggles; the panel rolls into the wall over 0.35 s; while shut it holds you on
  your side. Verified: blocked shut, walked through open.
- **The Gomez manor** 1.3x (w 0.407, h 0.286, ox 0.15, oy -0.20); the Old Town tavern in the same cell moved
  (ox -0.12, oy 0.09) to clear it. Not looked at in the harness.
- **Prison "warp toward D block"**: NOT reproduced. Walking outdoors from B toward D and into D's door both
  worked. Need where exactly (from which door, what time) -- likely the count walk-back or a push out of a solid.
- Debug hooks: `__ironlion.wings()`, `G.slideDoorsT()`.

---

## 000000000000000000000000000000000000000000000000000000. LAYER 451 — THE BUNK, THE MAIL, WORK, NIGHT, SHOWERS

- **Your bunk** (`G.myCellFn` -> "mybunk" panel, before the other prison E handlers): SLEEP UNTIL DAWN (6:30) /
  NOON / DUSK (6 PM) -- the clock jumps (a new day if it wraps), hp and stamina restored; or THE MATTRESS (the
  hide, via G.stashFn). Verified: slept to 6:00 PM.
- **Your desk** (same hook) -> "mail" panel: `g.pmail`. Each new game day (`stepPrisonMail`): 40% a letter from MOM /
  YOUR BROTHER / YOUR SISTER (LETTERS), and -- once the crew are out or the board exists and you are inside -- a
  report from PABLO (corners, shops, payroll, any war, respect). "MAIL CALL" banner when unread. Verified.
- **Work loops**: in WORK_ROOMS (laundry, mess, library, ward, kitchen) a free man walks station to station (the
  room's props) instead of drifting. **Night** (`isNight`: 21:30-6:00): every inmate in a cell is laid on his
  bunk (drawn flat, a "z" rising). Verified 11 of 15 asleep at 23:00.
- **Showers** (`nightAndShowers`, `drawShowerCensor`): in "work" phases 2-3 men are in the block's pshowers room,
  drawn with a skin-tone mosaic over the body (SKIN by cast tone) and steam; they do not wander. Verified 3.
- NOT YET: whole-day routines across buildings (a man's job taking him to the laundry building, chow in the mess
  hall and back) are still per-floor snapshots with the walk-in/out transitions of layer 450.

---

## 00000000000000000000000000000000000000000000000000000. LAYER 450 — THE WALK IN, AND THE TIERS MOVE

- **The walk in** (replaces the caption-only intro; INTRO_OUT / INTRO_IN, prisonIntroStart, stepPrisonIntro,
  drawPrisonIntro, prisonIntroEnd): C.O. HARLAN (yt_pr_guard_1, blue name) leads from the bus through the gate
  (3 legs, a line each: the yard, the hub, the hole), then inside your block from its door: down to the tier, along
  it to your cell's bars (a line each: the counts, chow and work, the shot callers, "Cell A-19. In you go."), you
  step in, and control comes back. You follow him in a line (`followLine`), three other new fish follow you. NO
  CONTROL while `g.pintro` (stepFoot zeroes ix/iy); E still skips. Verified start to finish (~20 s).
- **The tiers move** (folkKey, folkTransition, stepFolkWalk, drawLeavers): prisonFolk keeps the previous list when
  only the PHASE changed on the same floor: men no longer on the floor walk to the door and go (`g.pleave`, 14 s
  max); men new to it walk in from the door to their place (staggered). In free time the men outside cells drift
  within ~60 of their spot (every 4-10 s); guards, store men, shot callers, men in cells stay put. All run
  collideCrew. Not watched through a phase change in the harness (inmate plates are not local).
- Kitchen: the KITCHEN job exists (PRISON_JOBS.kitchen: 5 packs, sugar and fruit for hooch, knives counted).

---

## 0000000000000000000000000000000000000000000000000000. LAYER 449 — THE PARALLAX SHELL'S WALLS

- **Where the 3D effect is used**: only on buildings WITHOUT a roof plate (`platedRoof(b)` null) -- they get the
  generated shell in `drawBuildingExt`: a roof lifted by `floors x FLOOR_RISE` toward the camera (clamped +-190)
  and side walls joining it to the footprint. Plated buildings (rf_one_*, the ROOF_SETS, roofKey) are flat art
  drawn on the footprint and do NOT lean.
- **BUG FIXED**: the shell's `face()` built each wall path under `translate(ox/2, oy/2)`, so every wall slid half
  the parallax off its base -- the roof looked unpinned. Faces are now drawn straight in world space.
- **The hospital** is `rf_one_hospital` (door side 0, so the plate is drawn flipped). If that plate is loaded it
  sits on the footprint and cannot drift; if it is missing, the generic shell draws -- which had the bug above.
  NOT confirmed which one Donny sees: ask for a screenshot if it still floats.
- Debug hook `__ironlion.findB(kind)` -> [x, y, w, h, floors, plate, roofKey, doorSide].

---

## 000000000000000000000000000000000000000000000000000. LAYER 448 — BLOCK LABELS, THE COURT, BASKETBALL, THE WING DOOR

- **Which block is which**: each wing's letter painted big on its roof with "BLOCK X" under it (`drawBlockLabels`,
  through roofOffset, outdoors in prison mode); "X BLOCK · TIER n" stencilled faint on the tier floor inside
  (`drawBlockStencil`); the HUD floor line adds "· X BLOCK". Verified on the roof.
- **Yard sizes**: court `YARD_COURT` 24% / max 250 (was 34% / 380); bleachers `YARD_BENCH_W` 110 (was 200); the
  picnic table 70 (was 100).
- **Basketball** (`BALL`, courtGeom, G.ballFn, stepBall, drawBasketball): in yard time four inmates play two-on-two
  on the court (a ball passed and bounced between them, inmate plates). A loose ball by the court: E picks it up,
  E within 320 of a hoop shoots (45% scaled by distance): the ball arcs in; a make = +1 respect from every inmate
  within 400. Verified pick-up and shot; the court art and the players' plates were not loaded locally.
- **The wing door**: the cellrow plan leaves a `tierdoor` gap in the bottom row; the door was at the south wall's
  middle, not the gap's, so it cut into the cell beside it. Wings now force door side 2 and `settleDoor` centres
  exactly on a touching `tierdoor` room (its narrow span used to be skipped). Verified: A block door pos 0.5417.
- Test hook `G.courtFn()`.

---

## 00000000000000000000000000000000000000000000000000. LAYER 446 — MAKES, MODELS, PLATES, HIT-AND-RUN DAMAGE

- **plates_446.zip** -> assets/ui/: ui_plate (the blank plate), car_dmg_front (not used -- the real crush does the
  deform), car_dmg_glass (spiderweb), car_dmg_blood.
- **carInfo(v)** (kept on `v.idn`): model from the sprite key where it says (CAR_BY_KEY: Grand National, DeLorean,
  Mustang GT, the crew's Impala / Mach 1 / Charger, police LTD, K-9 Blazer, van, truck, taxi), else from
  CAR_POOLS by length; colour from the key's name, else hashed; an Illinois plate "ABC 123" (police: MUNICIPAL);
  a registered owner (OWNER_F/OWNER_L); 4% reported stolen.
- **RUN PLATES**: detective mode, in a vehicle -> the PLATES button -> "plates" panel: the 7 nearest cars within
  700 (colour, model, distance, parked). Pick one: the plate comes up centre-screen (ui_plate with ILLINOIS /
  the number / LAND OF LINCOLN) with the model, owner and flag (stolen / hit-and-run damage / clean).
- **Hit-and-run marks**: NOTE `v.dmg` is the game's CRUSH number and `drawCarDamage()` already exists (smoke and
  fire) -- the new marks are `v.hit` / `drawHitMarks`. `markHitCar(v)` deforms the car with the real crush
  (`applyDamage` x4 at the nose, tough forced to 1) and adds the spiderweb and blood. Verified: dmg 0.22 on a
  civilian Concord, its plate run showing "FRONT-END DAMAGE REPORTED -- HIT-AND-RUN".
- NEXT: the hit-and-run CASE itself (scene with tyre marks, paint and glass; witnesses with colour and partial
  plate; the marked car parked somewhere; the driver). `G.markHitCarFn(v)` is the hook it will use.

---

## 0000000000000000000000000000000000000000000000000. LAYERS 444-445 — THE RUSTY NAIL FITTED OUT, POOL, THE PRISON SONG

- **art_445.zip**: assets/bar/ (18 mb_* fittings), assets/hires/ (the first five trades, 30 -- re-sent),
  assets/prison/ci_trowel.png (re-sent), assets/music/prison.mp3 ("Before the Rain", 128k, 2:48).
  **art_445b.zip**: assets/hires/ (the seven new trades, 42) + assets/heroes/ yt_dale/chen/beck (knee cut) -- re-sent.
  Silas: **silas_447.zip** -> assets/crew/yt_merc_silas.png (hip-cut, from IMG_4138) + pt_merc_silas.png; PD_ART points there.
- **The Rusty Nail is one open room**: floorKind -> "mercbar" on its entry floor (plan: one room `mbroom`,
  tx_shack_wood) -- the bar2/tavern layouts were too cut up. `fitRustyNail(b)` (run once when chosen, after
  `plans = null`): back shelf, counter and four stools top-left, booths + table top-right (Silas sits there,
  `b.mbSilas`), neon, dartboard on the right wall, jukebox / notice board / cigarette machine / crates along the
  bottom, the pool table in the middle unless the stairwell (`pl.stair`) is there (then +-70/120). MB_KEYS are
  PROP_ART; solid except stools, dartboard, notice, neon.
- **Pool** (cab game "pool": PTAB table, poolRack, stepPool, drawPool, poolEnd; NOTE a `const POOL` already
  exists elsewhere -- the table is PTAB): E at the table -> "pool" panel: SKINNY PETE (sloppy, $100), MARLENE
  (sharp, $500), THE DEACON (hustler, $2000). Stake paid up front; stick aims (up/down fine), HOLD fire to
  charge (the bar swings), release to shoot. Nine balls; sink = a point and shoot again; scratch = -1 and the
  turn. Table clear: more points wins 2x stake (+respect by his skill), a tie returns it; E quits = forfeit.
  The AI picks the straightest ghost-ball shot, error 0.115 / 0.07 / 0.025 rad by skill. Verified: pocketing,
  turns, scoring, a live game against Marlene progressing.
- **Prison music**: MUSIC.prison; the 1.5 s chooser plays it in prison mode (not in a cab game; once escaped,
  only while heat is 0). Not heard in the harness (no audio headless) -- listen for it.

---

## 000000000000000000000000000000000000000000000000. LAYER 443 — THE RUSTY NAIL, YOUR PEOPLE ON THE STREET, CASING IN PERSON

Block above `kestrelRoster()` (MERC_T, MERC_JOBS, mercBarB, silasPt, G.silasFn, mercPanel, G.mercPick, stepMerc,
drawSilas, drawTargetArrow, CORNER_DEF, spotNear, addSpot, stepCornerWar, drawStreetPeople, CASE_T,
G.caseShopFn, stepCasing). All escaped-only (`g.pescaped`).
- **The Rusty Nail**: the bar/tavern/pub nearest the scrapyard (`g.mercBar`, `.mercBar`). Until you have been
  in, a gold arrow points to it. SILAS (plate `yt_merc_silas`, ART TO COME; a dark circle stands in) at the
  middle of its entry floor; E by him -> "merc" panel: three jobs a game day (collect a debt, move a package,
  watch a deal, put down a gang man (-25 with that gang)) and a SIT-DOWN ($2000 + 40 per point of hate)
  with any gang below -10. Take one: its door is marked by the arrow; reach it within 5 game hours (else
  -5 respect). Some go bad (half pay, hp, heat). A sit-down lifts the gang to at least -10 +20.
- **Street spots** (`g.board2.spots`): every corner and protected shop the board wins becomes a man standing
  at a real door near the scrapyard ("YOUR CORNER" / "PROTECTED", your dealer's / enforcer's plate). A gang at
  war now hits a SPOT: "KINGS ARE HITTING YOUR CORNER", a red arrow, 90 real seconds; get there -> held,
  +10 respect; don't -> the spot and its corner/shop are gone.
- **Casing in person**: escaped and inside any shop (`b.biz`): the CASE button; stay 10 s -> it goes on the
  board's cased list (till, guard). The button becomes ROB: 70% (+15 armed, -20 if a guard) to take the till
  yourself (+12 respect, heat 2); fail = hp and heat 3. Or leave it for the board's ROB A STORE.
- Verified: the bar found and named, Silas's panel, a job taken and paid on arrival ($1718), a corner spot
  appearing, a war attack on it, defending it (+10). Casing in person was NOT run in the harness.
- Test hooks: `G.mercBarFn()`, `G.silasPtFn(b)`, `G.doorPtFn(b)`, `G.stepOpsT()`.

---

## 00000000000000000000000000000000000000000000000. LAYER 441 — RESPECT, NEW TRADES AND JOBS, THE GANGS AND YOU

**BUG FIXED (since layer 437):** the ops board's `function boardPanel()` / `function stepBoard()` had the SAME
names as the gang-war board's panel and the SKATEBOARD's step -- the later declaration won, so the war
board and skating were broken. Renamed: `opsPanel`, `stepOps`, pick kind `"opsboard"`, `G.opsBoardFn`,
`G.opsPick`. Lesson: grep a name before declaring a function in the big component scope.

- **Respect** (`g.rep`, `REP_TIERS`): NOBODY 0 (3 people), KNOWN 100 (6), RESPECTED 250 (10), FEARED 500 (16),
  A BOSS 800 (25). Caps hires (`peopleCount`, crew are extra), gates which trades will work for you
  (HIRES[k].rep) and which jobs appear (OPS[k].rep). Earned only by jobs going right (OPS.gain), half lost
  when they go wrong, -3 every game day. Shown in the board's title.
- **Seven new trades** (HIRE_ROLES now 12; hire art keys registered for all): mechanic, enforcer, fence,
  forger, bomb maker, safecracker, chemist, fixer.
- **Jobs** (OPS): corner; CASE A STORE (lookout -> a named store with its till and whether it has a guard;
  ROB A STORE now needs a cased target and takes its till, -10% risk); steal cars to order (mechanic+driver);
  protection racket (enforcer: +1 shop, $400/day); truck hijack (driver+shooter+fence); new papers (forger:
  heat gone, street clothes); sell papers; armored car; THE JEWELRY HEIST (case Aldridge's first; safecracker
  +driver+lookout, $15-30k); a celebrity's penthouse (safecracker+lookout+fixer, respect 600, $25-60k); buy a
  cop (fixer, $5000: heat gone); car bomb / hit on a gang; DO A JOB FOR a gang (+25 standing). A chemist on
  the payroll doubles what corners clear.
- **The gangs and you** (`g.gstand`, `g.gpact`, `PACT`): standing -100..100 per war gang -> WAR / HOSTILE /
  NEUTRAL / FRIENDLY. Bombs and hits lower it, favours and TRIBUTE ($1500, +15) raise it. A PACT (7 game
  days, $3000 + 25% of the gang's cash - standing x20) holds you at FRIENDLY+; a day before it ends you get
  word; lapse = -20; moving on a gang under pact = PACT BROKEN, -100, war. At war: every job +8% risk, and each
  day a 50% chance they take a corner / burn a shop / kill one of your people. Friendly: their jobs -5% risk.
- **trades_442.zip** -> assets/hires/: the seven new trades x 3 looks (42 files). Sheets: IMG_4124 mechanics,
  4125 enforcers, 4126 fences, 4127 forgers, 4128 safecrackers, 4129 chemists, 4130 fixers (the 4119-4123 .jpeg
  re-uploads are the original five, already in hires_439.zip).
- Verified: the 3-person cap for a nobody, safecracker locked at 0 respect, casing -> robbing the cased till
  ($5244), a pact, a car bomb breaking it into war.

---

## 0000000000000000000000000000000000000000000000. LAYER 440 — TALLER OFFICERS, SPECIALTIES, GETTING MEN OUT

- **officers_440.zip** -> assets/heroes/yt_dale, yt_chen, yt_beck re-cut at the KNEE (no hip-cut), STAFF
  tall 0.95 / 0.97 / 0.95 (was 0.8). They were far too short.
- **Specialties**: every inmate's `g.prel` record now carries `spec` (one of HIRE_ROLES, from his hash) plus
  name / yt / tall / face; the inmate panel shows "GOOD AS A <ROLE>" once met.
- **Getting a man out** (`SPRING`, the board's GET A MAN OUT OF KESTREL): anyone you MET inside and who is
  not your enemy. LAWYER $15,000, 3 game days, 55% (+0.2% per point of disposition); BREAKOUT $30,000,
  18 hours, 70% (+same), heat 2. Success: `R.out`, he joins the board in his specialty for free and stands
  in the shelter in his own plate with NAME · ROLE. Failure: money gone ("APPEAL DENIED" / "THE BREAKOUT
  FAILED"). Verified: a denied appeal, and a breakout that brought Walt "Tank" Krantz out as a dealer.

---

## 000000000000000000000000000000000000000000000. LAYER 438 — THE TROWEL ICON, THE HIRES' LOOKS

- **trowel_438.zip** -> assets/prison/ci_trowel.png (the taped spoon).
- **Hire art wired, not yet made**: `HIRE_ROLES` x 3 looks -> `assets/hires/yt_hire_<role>_<1-3>.png` (plate,
  hip-cut like every yt_) and `pt_hire_<role>_<1-3>.png` (face). Roles: dealer, driver, shooter, bomber,
  lookout. Each hire gets a random look (`g.board2.men`); the board panel shows the last hire's face; the
  hired men not out on a job stand in the shelter with their role in gold over their heads (`drawHires`).
  A man lost on a bad job leaves the list. Verified the bookkeeping.
- **hires_439.zip** -> assets/hires/: all 30 files (15 hip-cut plates + 15 faces). Sheets: IMG_4119 drivers,
  4120 dealers, 4121 shooters, 4122 bomb makers, 4123 lookouts; left to right = looks 1-3. Verified: six
  hires standing in the shelter with gold role labels, the last one's face on the board.

---

## 00000000000000000000000000000000000000000000. LAYER 437 — THE TUNNEL UNDER THE YARD, AND THE BOARD

Block above `kestrelRoster()` (TUNNEL, tunnelSpots, G.blueprintFn, G.digFn, drawTunnelSpots, HIRES, OPS,
G.opsBoardFn, boardPanel, G.opsPick, stepBoard).
- **The tunnel**: (1) BLUEPRINTS -- E anywhere in the `records` room (hub floor 1) in free time: 30 min, PGUARD
  odds -> 24 h; success sets `g.pblue`. (2) A TROWEL -- new CONTRABAND `trowel` (sev 3), the store man sells
  it (25 packs, 0-1 in stock). Its icon `ci_trowel.png` is MISSING art. (3) THE SPOTS -- `tunnelSpots()`: three
  points from beside the weights to the south fence, chalk X's once you have the blueprints (dirt pile when
  started, a black hole when open). Dig IN ORDER at yard time: 45 min a session, half PGUARD odds from the
  tower (-> 36 h, trowel lost), TUNNEL.work (2) sessions a spot. All three open: E at the last -> you come up
  220 past the south wall, escaped. Verified the whole chain.
- **The board** (`g.board2`; NOTE `G.boardFn` is the SKATEBOARD -- this one is `G.opsBoardFn`/`G.opsPick`):
  E at `bs_maptable` in the scrapyard shelter. HIRE (dealer $400, driver $600, shooter $800, bomb maker $1500,
  lookout $250; Ras deals, Pablo drives, Leroy shoots for free once out) and PLAN, gang-war style:
  corner (dealer; +1 corner, each corner pays $250 a game day), store robbery (driver+shooter, $1.5-4k),
  armored car (driver+2 shooters+lookout, $8-16k), car bomb on a gang (bomber+driver, -$6000 to that gang in
  g.gwar), hit on a gang man (shooter+lookout, -$2500). Each op ties its people up for its hours, then pays
  or goes wrong (risk 10-35%: a hired man lost, heat). Results in the banner and the book.
  Verified: hires, a robbery ($2351), a corner, people-free checks. The car bomb's war effect was not run
  (the driver was busy -- correct).
- Test hooks: `G.tunnelSpotsFn()`, `G.campusBFn(kind)`.

---

## 0000000000000000000000000000000000000000000. LAYER 436 — THE BUS IN, ROOF HATCHES, THE DRAIN (SEWER ESCAPE)

Block above `kestrelRoster()` (INTRO_LINES, stepPrisonIntro, prisonIntroStart/End, roofHatchPt, G.roofHatchFn,
G.ladderUpFn, drawRoofHatch, drawTopLadder, DRAIN, G.drainFn).
- **The bus in** (`g.pintro`): prison mode now opens outside the gate beside the white bus; C.O. HARLAN reads
  the rules in six subtitle lines (4.6 s each, the drive-talk box) ending with your cell number; then you
  are in your cell. E skips. The cell-door walk-back and convict-clothes heat wait for it. Verified.
- **Roof hatches**: every building of 2+ floors (not Kestrel/landmark caps/perimeter/the scrapyard) has a
  hatch on its roof at (72%, 28%) of its footprint, drawn when you are on that roof (`rf_hatch`, through
  roofOffset), and a ladder (`rf_ladder`) at the same spot on its top floor (nearest free point). E on the
  roof at the hatch -> top floor; E at the ladder -> the roof. Verified both ways on Malcolm's building.
- **The drain** (`DRAIN`): in free time, E at a `pr_drain` in the showers = an hour's work on the grate
  (clock +60 min); a guard may walk in (half PGUARD's search odds) -> 24 h, progress lost. Three sessions
  and it comes up; E again drops you into the city sewer at the manhole nearest Kestrel's south wall
  (`g.sewer`), escaped, scrapyard address in the note. No heat while underground; any manhole up
  (G.sewerFn) and the jumpsuit rules apply. Verified: 3 sessions, down into the sewer.

---

## 000000000000000000000000000000000000000000. LAYER 435 — RECAPTURE, THE CREW OUTSIDE, PLANTING EVIDENCE AND PAYING WITNESSES

- **Recapture** (`arrestPlayer`): an escaped convict (`g.pescaped`) who is taken goes BACK: jumpsuit, empty
  pockets, 72 h in the SHU ("the escape"); the crew keep the scrapyard. Verified: landed in the SHU (hub f2).
- **The crew outside**: E on Pablo/Leroy/Ras in the scrapyard garage (`G.hideCrewFn`) -> crew panel -> WITH ME
  builds a follower from `crewFolk(id)` (street plate yt_crew_<id>, face faceCiv). Followers now work after an
  escape (counts no longer send them off), RIDE with you in a car (hidden, snapped to you, out where you get
  out), and E on one outdoors opens his panel. Verified: two followed me out of the garage into the street.
- **Dirty work** (`PLANT`): in the interrogation room, PLANT EVIDENCE (once a case) and PAY A WITNESS
  ($200, twice). At trial: +30 jury for the plant, +14 per paid witness -- but a 22% chance (per plant; 11%
  per witness) the defence finds it: jury 5, -40 juice, "THE DEFENCE FOUND IT".
- **The framed man**: a WRONG man convicted (`!A.isPerp`) gets `framed` on his Kestrel record and at most
  2 years. The day he is released (`kestrelReleases`) he becomes a tier-3 rival on the bank-job track with
  his real identity ("HE'S OUT -- he knows it was you"). Verified the release -> rival; the trial numbers
  were read in code, not played through.
- Test hooks: `G.arrestPlayerFn()`, `G.kestrelReleasesFn()`.

---

## 00000000000000000000000000000000000000000. LAYER 434 — THE ESCAPE (LAUNDRY VAN) AND THE SCRAPYARD HIDEOUT

Block above `kestrelRoster()` (ESC, G.escapeFn/escapeGo, hideoutB, stepHideout, drawHideoutYard, G.hatchFn,
drawHideoutCrew).
- **The escape**: on the LAUNDRY job, 9 AM-5 PM, E at any `pl_cart*` in the laundry room -> "pescape"
  panel -> UNDER THE SHEETS. A dock guard (skill 1-5) searches with PGUARD's formula vs your hide skill
  (min 5% risk). Caught: 48 h in the SHU. Out: dropped at a door 2600+ from Kestrel in the jumpsuit (top
  wanted until a locker), `g.pescaped`, `g.crewOut`; the scrapyard's address goes in the note and the book.
  The cell-door walk-back no longer fires once escaped.
- **The scrapyard** (`hideoutB`, cached in g.hideout): the best garage/warehouse 3000+ from both the
  precinct and Kestrel (aiming ~5200 away), skipping anything a distro/den/gang/shop uses. It becomes
  floors 2, entry 1, "THE SCRAPYARD". floorKind: f1 `scrapgarage` (room `sygarage`: bench, shelves, a
  LOCKER, a wreck, tyres, drums, motors, the open hatch), f0 `shelter` (room `shelterroom`: the ladder hole,
  bunk, cot, gun rack, radio, generator, water tank, map table, shelves, sandbags, gas masks, drums).
- **Outside** (`g.hideProps`, drawn outdoors in prison mode): fence lines top and bottom, wrecks, crusher,
  container, crane, cubes, tyres, drums round it. One random BUY_CARS car parked at the door; when you get
  within 1500 the crew's three cars (lowrider, green, orange) park beside it. Pablo, Leroy and Ras stand in
  the garage in street clothes with green names.
- **The hatch** (`G.hatchFn`): E at `sy_hatch_open` (garage) -> down to the shelter at the ladder; E at
  `bs_ladderhole` -> back up. Stairs also connect the floors.
- Verified: escape (95%), heat 3 in the jumpsuit, the hideout found, garage + shelter furnished, hatch both
  ways, the locker change, the yard and the cars outside.
- Not yet: getting arrested sends you back; the crew as usable assets outside (jobs, driving with you);
  the sewer route; the merc bar.
- Debug hook `__ironlion.hide()` puts you in the garage (after an escape).

---

## 0000000000000000000000000000000000000000. LAYER 433 — WALLS FOR WALKERS, THE SHU DAY, CLOTHES, RIVAL MESSAGES, RAMOS ON THE ROAD

- **Walls**: followers, hunting guards and angry men now run `collideCrew` (collideBuildings) after every
  step. Stuck on a wall > 2-2.5 s they hop round (next to you / next to their target). Verified: a
  follower still reaches and hits the man coming at you.
- **The SHU day** (`SHU`, `stepShuDay`, `drawShuDay`): meals at 7:30, 12:00, 17:30 -- a guard walks the
  corridor to your door, the tray comes through the slot (+hp); the fast clock HOLDS while he walks. At
  2 PM, one hour of yard ALONE: walked out to the empty yard for 25 real seconds, clock held, walked back.
  Verified both.
- **Clothes** (`G.changeFn`, `stepConvictClothes`): NOTE `G.lockerFn` already existed (nearLocker, the gun
  locker) -- the change is `G.changeFn`. In prison mode, E at any `locker` / `pd_lockers` / `pr_locker`
  outside the prison toggles `g.pcivvies` (the street plate). In the jumpsuit OUTSIDE the grounds: heat 3,
  "ESCAPED CONVICT", escalatePolice, wantedT held at 90 while you wear it. `wantedAs` is set to your current
  identity so the identity check does not clear it. Verified: locker in Malcolm's place changes you; heat 3
  outside. (There is still no way OUT of Kestrel -- the escape is its own job.)
- **Rival messages** (`RMSG`, `stepRivalMsgs`, `stepDeskPhone`): with rivals on file, every 240 game
  minutes one sends word -- half left with Sally or Beck (MESSAGES / SOMEBODY LEFT YOU A MESSAGE in their
  panel, read via `house:<who>:msg`, logged in the book), half a call to your desk phone that rings the next
  time you are in the station (subtitle). Lines darken with the rival's tier. Verified the messages and
  reading them; the desk-phone path was NOT seen in a real station.
- **Ramos on the road** (`RDRIVE`, `RAMOS_TALK`, `RAMOS_MARK`, `stepDriveTalk`, `drawDriveTalk`): while she
  drives, a line every 16 s from the tier your `g.ramosBond` has reached (+1 per drive that arrives); at
  bonds 3, 7, 12, 18 she says a milestone line once each -- the slow reveal of how she feels. Subtitle
  box at 66% screen height. The subtitle draws (verified); a real drive was NOT run in the harness.
- Debug hooks: `__ironlion.props()`, `__ironlion.goto(propKey)`.

---

## 000000000000000000000000000000000000000. LAYER 432 — THE SHU (THE HOLE IS A PLACE NOW)

- The hub (`pr_roof_hub`, kind "prison") has **3 floors**; floor 2 is **"shu"**: a corridor (`shuhall`), a
  row of `shucell`s each side (bunk + pan), the guard desk (`shudesk`) at the end.
- `stepHole`: when `g.hole` starts you are walked to a random SHU cell (the infirmary's time -> the
  infirmary ward instead, `holePlace`), followers/hunters/cards cleared; the steel door holds you in
  (clamped to the cell); the clock runs x40; when it ends you are walked back to your own cell
  (`holeReturn`). SHU doors (`drawShuDoors`: steel, food slot, handle) are always shut; outside the hole
  nobody walks into a SHU cell (`stepShuBlock`). Verified: placed on floor 3, held, returned to the wing;
  infirmary time lands in prisoninf.
- **BUG FIXED from layer 425**: plan rooms have NO `gy0` (only the furnisher's grid rooms do), so every
  "top row" test on plan rooms was false -- top-row cell doors were drawn on the outer wall and the
  player's own cell could be clamped wrong. New module helper `rowTop(r, b)` (room above the building's
  middle) now used by the cell doors, his cell, the SHU. Verified: doors on both rows now.
- Debug hook `__ironlion.rooms()` lists the current floor's rooms.

---

## 00000000000000000000000000000000000000. LAYER 431 — YOUR PEOPLE WALK WITH YOU AND FIGHT

Block above `kestrelRoster()` (PFOL, folStart, folStop, stepFollowers, drawFollowers).
- A recruit's panel now has WITH ME / STAY HERE; the crew's panel too (Pablo, Leroy, Ras). Up to 4 follow
  (`g.pfol`: copies of the folk objects; the originals are hidden while they walk with you).
- They keep a step behind in a fan, catch up fast from far off, follow you to another floor or building
  1.5 s after you, and drop off at every count, in the hole, or out of prison mode.
- Anyone `angry` within 300 of you: your people go for the nearest; a blow a second, three and he is down
  (relViolence runs -- everyone saw it). E on a follower talks to him.
- Verified: a recruit closed from 526 to 37 in 3 s; a man set angry beside you was put down by him (you
  took 4 hp meanwhile); followed to floor 1.
- They walk straight -- no wall collision yet (same as the hunting guards and angry men).

---

## 0000000000000000000000000000000000000. LAYER 430 — NAMES, TRAITS, DISPOSITION, FEAR, RESPECT, RECRUITING

One block above `kestrelRoster()` (PTRAITS, PREL, rel, relDisp, relCol, relViolence, inmatePanel).
- **g.prel[inmate no]**: traits (1-2 of HOTHEAD, COWARD, GREEDY, PROUD, LOYAL, TALKER, QUIET, FAITHFUL, from
  a string hash of his number), disp -100..100 (starts +30 if he is in your gang, else -10..+10), fear and
  respect 0..100, met. Reset at prison start.
- **E at any plain inmate** (not store/shot caller/crew/guard; a card table in reach wins) -> "inmate" panel:
  INTRODUCE / TALK (talkers +8, quiet +2, else +5), GIVE A PACK (greedy +14; proud and not yet a friend = -4),
  THREATEN (fear up; coward comes round +6, hothead -25 and swings at you, proud -15, others -8),
  RUN WITH ME at 80+ (90 for LOYAL) and only with no gang of your own. The panel shows FRIEND/NEUTRAL/ENEMY,
  the number, fear, respect, and his traits once met.
- **Name over the head once met**: green 40+, blue, red -30 or less; your crew and recruits always green.
- **Putting a man down** (relViolence): everyone on the floor fears you more (cowards double), proud and
  hotheads respect you a little, his gang -15 (LOYAL -25), him -40.
- **Recruits** (g.pmine): disp locked at 100, "WITH YOU"; each one poached adds PREL.poach (10) heat against
  you with every other man of his old gang (g.pheat). They do not follow or fight for you yet.
- Verified: talk+gifts took a FAITHFUL/GREEDY Eterno to 100, recruited, Eternos heat 10; a threat on a
  GREEDY/TALKER put fear 15, disp -8. Not verified: the tag colours on screen (no inmate art locally).

---

## 000000000000000000000000000000000000. LAYER 429 — CARDS AT THE TIER TABLES, BORROWING, THE HIT

One block above `kestrelRoster()` (PC, pcScore, G.cardsFn, pcardsPanel, drawPrisonCards, stepDebt).
- **E at a tier `cardtable`** (free time, not a count, >= 1 pack) sits you with up to three men nearest
  the table. Five-card draw for packs: ante 1 -> bet (CHECK / BET 1 / BET 3 / FOLD) -> the others call,
  fold or raise once (hand strength + each man's bluff) -> you CALL or FOLD -> DRAW (tap cards KEEP/SWAP;
  they keep pairs and made hands) -> second bet -> showdown, winner takes the pot. DEAL AGAIN / GET UP.
- **On the table**: each seat's five cards lie between him and the middle (theirs face down until the
  showdown, folded hands stacked), his bet beside them as ci_cigs packs, the pot piled in the centre;
  your own hand also drawn large on screen. The seated men are drawn from COPIES at the seats (the folk
  list rebuilds as the day moves); the originals are hidden while `g.pc` runs.
- **Borrowing** (shot caller panel): BORROW 10 PACKS, pay 15 within 2 days (`g.pdebt`, days counted by
  `g.pday` when the clock wraps). PAY BACK clears it. Overdue -> "THERE'S A HIT ON YOU": a man of that
  gang on your floor becomes `hitman` (angry, 2 hp a blow) until you pay -- or he puts you in the
  infirmary, which squares the debt. Verified: dealt, bet, drew, showdown (pot 11); hit assigned.
- The harness has no inmate plates or table art locally, so the seated men and the table were not SEEN --
  check them on the live site.

---

## 00000000000000000000000000000000000. LAYER 428 — HIS LIVING ROOM FIXED, GUNS, FIGHTS, THE GUARD SQUAD

- **Malcolm's living room**: two things were eating the set. (1) makeFloor's last filter deletes any prop
  closer than WT to the OUTER wall -- the set now starts at q2.x0/y0 + 16. (2) tidyRoom and the doorway
  pass now skip `ap_*` (hand-placed). Verified: sectional, console + speakers, coffee table, both armchairs,
  Atari, bean bag, plant, lamp all draw.
- **Guns** (`PGUN`): a strike with the zip gun or pistol out shoots the nearest inmate within 260 (tracer
  line). Zip gun: one shot, then it comes apart. Pistol: 6 rounds (g.pammo), then dropped. Verified.
- **Fights** (`PFIGHT`): bare hands take 3 hits to put a man down, and he fights back. Whoever you hit,
  his gang's men within 260 get `angry`: red "!" over them, they walk in and hit you (1 hp / 1.1 s).
  At 0 hp: the infirmary, 8 hours on the fast clock, hp restored. Verified (two Eternos came, hp 10 -> 5).
- **The guard squad** (`prisonAlarm`, `g.phunts`): violence calls 1-3 guards (more for a gun), nearest
  first, each his own search skill, faster the better he is; none on the floor -> they come from the
  stairs. They FOLLOW you: change floor or building and 4 s later they come in behind you. First to
  reach you searches (as layer 427). Verified: three followed to floor 1.
- There is no `playSfx` -- the gunshot call is guarded and silent; wire it to the real sound function.

---

## 0000000000000000000000000000000000. LAYER 427 — POCKETS, DRUGS, WEAPONS, THE GUARD WHO COMES FOR YOU

No new art. All in one block above `kestrelRoster()` (PFX, PWPN, PGUARD, pocketsPanel, stepPrisonFx, drawPrisonFx).
- **POCKETS** button (prison mode only) -> "pockets" panel: everything on you, HIDE SKILL n/5.
- **Using things** (`PFX`), each ~30 s, done with the canvas's CSS filter (cheap) + a tint, lifting in the
  last 3 s: weed = green blur; pills = heavy/dim (+2 hp); hooch = sepia + the screen sways (-stamina);
  heroin = grey and dark 40 s (+6 hp, -60% stamina); a smoke costs one pack, puffs over his head for 30 s,
  +3 hp, -25% stamina. Verified: weed sets the filter.
- **Weapons** (`PWPN`: shank, razor, pencil, zip gun, pistol): PULL OUT puts its icon over his head
  (HEAD_ICON -> wi_*). A strike with one out puts the nearest inmate down (q.down: lying, blood). Crew are
  never hit. Verified.
- **The guard** (`PGUARD`): violence sets a 60 s alarm; the nearest guard walks to you (label "GUARD ·
  SEARCH n", skill 1-5 from where he stands) and searches: find = 0.5 + 0.1 x his skill - 0.08 x your hide
  skill; a DRAWN weapon is found every time. Found -> everything with sev > 0 taken, the hole. Verified: a
  level 3 guard found the drawn shank -> 24 hours.
- The player's hide skill (g.pskill) now starts MAXED (Donny). Guards patting down still use stepPatDown.
- Not yet: guns firing, fights back from inmates, the guard hunting across floors, other guards joining.

---

## 000000000000000000000000000000000. LAYER 426 — THE OVAL TRACK, PLAYER #0001

- **player_426.zip** -> assets/prison/: yd_track_oval (the oval Donny prefers), yt_player_in / yt_player_civ
  (hip-cut, jumpsuit "0001" and the leather jacket + grey hoodie), pt_player_in / pt_player_civ (faces).
- The yard draws **yd_track_oval** first (width min(60% of the yard, fits its height)), then the ring, then
  the quarters. Verified in the running game.
- Prison mode draws the player from **yt_player_in**, or **yt_player_civ** when `g.pcivvies` is set; the old
  yt_pr_player is the fallback. Verified: the jumpsuit plate walks. Nothing sets `g.pcivvies` yet -- that is
  the garage locker change (the game already has a locker; use it), and prison clothes outside = top wanted.
- Malcolm's living room re-laid for its real (deep) shape. **Still not right:** the sectional, the console TV
  and the coffee table are removed after placement -- almost certainly the homes-only tidy/doorway pass.
  Find what strips them (log plan.props for that room before and after tidy) before moving them again.

---

## 00000000000000000000000000000000. LAYER 425 — YOUR CELL, CELL DOORS, THE CREW, HIS SUITE, K-9, THE NEW OFFICERS

Art: **art_425_part1.zip** (home, prison, police, heroes, tex, ui -- 90 files) and **art_425_part2.zip**
(crew, cars, scrap -- 83 files). Unzip both at the repo root. Everything is registered UNDER its lists
(module block "LAYER 425 ART", just above `const PITCH`).

- **His cell** (`g.pcell`): prison mode assigns the last ground-tier cell of the block; the player starts on
  the FLOOR by the bars (not on the bunk); prisonFolk leaves that cell empty. Verified: B block, cell 19.
- **Cell doors** (`CELL_DOOR`, `stepCellDoors`, `drawCellDoors`): at every "cells" phase (the counts and the
  night) a barred door slides across each cell's doorway; it shuts once the player is in his own cell, or
  after `grace` (20 s) a guard walks him back. Shut doors clamp him inside his cell and out of every other
  (prison mode only). Verified at 4:04 PM: doorT 1, doors drawn.
- **The crew** (`CREW`): Pablo Diaz (lowrider car_crew_viejo -- id stays "viejo"), Leroy Banks (green car),
  Ras Leroy (orange car). Prison plates yt_crew_<id>_in, street plates yt_crew_<id>, faces, cars. They live
  in the three cells before his, in or out by the hour; green name over the head; E -> "crew" panel.
  Verified: all three spawn in his block. Charges/sentences are placeholders.
- **Yard**: `yd_track_ring` replaces the four quarters (quarters are the fallback); weights `YARD_WEIGHTS_W` 120.
- **Malcolm's suite**: homeapt is two suites -- his (living/bed/kitchen/bath on wood/rug/tile) + a corridor +
  apt_neighbor. Furnished from ap_* (PROP_ART + SOLID_PROP registered next to PR_PROPS). Verified drawn.
  **Some living-room pieces (sectional, console TV) did not appear** -- the room is taller than wide and the
  tidy pass probably removed overlaps; re-lay `case "apt_living"` against the real room shape.
- **The console**: E at ap_atari -> "console" panel -> RALLY '86 (new Pong, `stepPong`) or the three arcade
  games. E now quits a cab game from ANYWHERE (it only worked inside the arcade). Not clicked through in the harness.
- **K-9** (`K9`, `stepK9`, `drawK9`): radio "K-9 UNIT" (10 juice) or Cpl. Beck -> pd_k9 truck, Beck + the dog
  (dog_rio plate). The dog works the nearest standing distro within 700: three finds a house (floor, walls,
  cutting room), each +5 juice, cash, notebook line. NOT run in the harness yet.
- **Station**: street floor's locker room and bathroom give up their bottom halves -> `sgtoffice` (SGT. MARIA
  CHEN, SWAT: "SWAT, ON ME") and `ltoffice` (LT. ARTHUR DALE, watch commander); CPL. JAMES BECK (K-9) in the
  lobby. The three talk off `COP_TALK` by juice / a lost last case. **Walk-test the new offices.**
- **Showers**: tx_shower floor, bigger heads, drains, stools, wet-floor sign, soap.
- Registered, not placed yet: BUY_CARS (15), SCRAP_KEYS (scrapyard + shelter + roof hatch rf_*), tx_bunker*,
  tx_shack_wood, HEAD_ICON map (wi_* weapon icons over heads). wi_knife was dropped (blade lost in the cut).
- Debug hooks: `__ironlion.G` (live state), `__ironlion.home()` (his living room), `__ironlion.yard()`.

### Asked for, NOT built yet
Usable prison items (weed = green blur 30 s, other drugs, smokes = puffs 30 s + health up / stamina down),
shanks and guns as weapons, violence -> guards hunt and search, guard search skill vs inmate hide skill
(player maxed), prison cards + borrowing, dispositions / name colours for everyone, planting evidence,
rival messages, Ramos's drive talk, the prison-mode bus intro, the player's own prisoner art + street
outfit + garage locker change (prison clothes outside = top wanted level), the scrapyard garage and the
bomb shelter, roof hatches, the sewer under Kestrel as an escape route.

---

## 0000000000000000000000000000000. THIS SESSION — COLD CASES FOR REAL, THE KING GRAVES, THE HOMES

- **The cold-case computer**: a `terminal` in the evidence room (ground floor). E there: COLD CASE FILES --
  COLD.files (4) boxes, each a crime, a year 1968-81, a real place, a victim, three suspects (one guilty)
  and two witnesses, with two pieces already bagged. Take one (`coldTake`): COLD.spawn NEW evidence goes
  out in the world (the old scene, out back of the guilty one's building, another bar or shop) -- walk
  over it. People are at real addresses: at home, MOVED (the file says where), or DEAD (a grave at St
  Brendan's; LOOK CLOSER gives a clue). E on a witness: a statement (evidence). At COLD.need (5) pieces
  Kearney names two suspects; CHECK THE ALIBI on each -- one holds, one breaks; arrest the broken one:
  +200 juice, $6000, and a FRONT PAGE kept in g.papers, readable on the computer (CLIPPINGS). This is
  separate from the main case (g.cold, not g.case). Kearney's old coldCase (which made a main case) is
  renamed coldCaseOld, unused. Verified end to end.
- **The King graves** (FAMILY_GRAVES, CEM_CENTRE): Walter and Ruth King at St Brendan's -- PLACEHOLDER names
  and years, check the Master Canon. E at a stone reads it. Flowers on both.
- **Homes** (`homes()`): the two nearest apartment/house buildings to the station (2+ floors) become
  MALCOLM'S APARTMENT and RAMOS'S PLACE with real addresses; their top floor is "homeapt" (living room
  with the computer, gun lockers, safe, sofa and TV; bedroom; kitchen; bath). Both in the rolodex; "HOME"
  at the top of Ramos's list. Ramos's own car (unmarked) is parked out front of her place.
  (LIVE_KINDS -- HOME_KINDS was already a name in the file.) The record-shop apartment is still to come.

---

## 000000000000000000000000000000. THESE TWO SESSIONS — KESTREL FILLED IN, DEPTH, JOBS, THE ROLODEX

- **laundry_bus_and_3.zip**: the laundry pieces (pl_*), pr_laundry_van (nose up), pr_bus (keyed off its
  road, nose up) and the three files Donny's list still showed (yt_cv_p2_1_13, pt_in_r0_7, pt_inm_7761).
  The van and bus art spell it "KRESTAL" -- the game says Kestrel.
- **Campus**: PRISON_CAMPUS buildings x0.8, PRISON_BOX pulled in again; grass inside the wall with a concrete
  apron; a visitors' LOT outside the gate, filled once you are near (`stepKestrelLot`).
- **Cell blocks**: a SHOWER room down the whole far-left column (24 `pr_shower` heads -- art not yet, drawn
  as boxes and NOT registered so it is not "missing"); common area moved to the tier's left end; every cell
  (19 a floor now) has bed, desk, toilet LEFT and sink RIGHT of the door gap, all clear of the outer wall
  (the shell filter was eating the north cells' beds). The hub's laundry has washers, dryers, carts, rack.
- **The bus** (KESTREL_BUS): at 2:00 PM daily everyone sentenced since yesterday arrives (`q.arrived`);
  until then they are awaiting transport and not in a cell. The white bus parks outside the gate until 4.
- **Laundry detail** (LAUNDRY, `G.laundryFn`, `stepLaundry`): take it in the laundry room; E on A-D blocks'
  tiers to collect, E at a washer (12 s), a dryer (12 s), the folding stacks -> 8 packs. The cart rolls
  ahead of you. Verified end to end.
- **DEPTH** (DEPTH table, drawMarks): landmark roofs lean away from the camera by 0.035 per floor, the walls
  filled beneath, a shadow down-right. `DEPTH.on = false` for flat. City generic blocks are unchanged.
- **Court**: jurors face the witness stand, the gallery faces the bench (was the door).
- **Station lot**: one row of eight stalls along the building, nose in, 72 apart, east of the front door,
  the open lot behind for backing out (NOT re-verified in the harness this session).
- **Ramos**: "THE CALL" (the radio's current g.crime) in his list, and **THE ROLODEX** -- every named
  building, A-Z, eight cards a page (`rolodex()`, pick kinds "rolo"/"rdrive:").
- **PRISON JOBS** (PRISON_JOBS, JOB_ORDER): every roster man has one (on his card); exactly ONE warden's
  assistant (a low-threat man, or the player -- the warden refuses gang men and anyone with skill < 3).
  E by the warden: the job board. Pay at 5 PM; `pat` changes pat-down odds; the commissary clerk gets 30%
  off; the assistant is warned which block is next for a shakedown. Laundry pays per load.

### Asked for, NOT built yet (design notes in chat)
K-9 unit on the radio; planting evidence / paying a witness at trial, and wrongly-jailed men holding a
grudge; rivals' messages via the desk sergeant, Sally and the desk phone; Ramos's drive conversations and
the slow reveal of her feelings; card games at the tier tables.

---

## 00000000000000000000000000000. EARLIER SESSION — A TIGHTER KESTREL, JOINING A GANG, THE SHOP, THE STASH MENU

- **Tighter**: PRISON_BOX pulled in (buildings closer); **no civilians** on the grounds (spawnPed drops any
  inside `inPrisonGrounds`, a 2 s cull walks strays off, and prison mode clears them at the start).
- **The yard** (PRISON_YARD fractions): fenced on all four sides with one gate in the top fence -- and the
  fence is SOLID (its pieces are in the generator's wall list, like the perimeter). The track is four
  quarter pieces round one centre (a loop) with the iron pile inside. **Paths**: PF("walk") concrete
  from every building's door to the hub's and from the gate to the hub. `MARKS_REF` exposes the marks
  to drawPrison.
- **Cell blocks**: the door moved to the middle of the south face under the roof's steps; the plan gives
  that column to a "tierdoor" corridor (23 cells a floor). Every cell: a full-size bunk and a proper
  desk on the BACK wall (away from the tier), pan and sink on the side, concrete floor (tx_concrete).
  The tier has a COMMON AREA: couch facing a TV, two card tables with chairs.
- **Prison mode**: no street jobs (callJob returns; g.job cleared); the objective panel shows
  `prisonObjective()` -- survive, the join steps, the hole, or "you ride with".
- **Joining a gang** (JOIN_STEPS, g.pmission, `prisonGangPick`): E by a shot caller -> "I WANT IN" ->
  (1) bring a blade (shank/pencil/razor/zip gun/gun), (2) carry THE GANG'S PACKAGE (sev 3 -- the hole if
  patted down) to a cell in another named block and hide it there, (3) pay ten packs -> g.pgang.
  Verified end to end: Jade Lotus joined.
- **The store** has STOCK (STORE_STOCK ranges, per store man per day, restocked each morning) and shows
  each item's icon, price and how many are left. **The stash** is a menu now: E at any hiding place lists
  TAKE for what is there and HIDE for each thing you carry, with icons (prison mode). You keep moving
  and acting while carrying; E picks the nearest of store man / shot caller / hiding place.

---

## 0000000000000000000000000000. EARLIER SESSION — UPPER TIER, VACANCIES, SENTENCES, THE LOT, THE GARAGE SIGNS

- **missing_56.zip**: exactly the 56 files on Donny's missing list (Kearney + the r-batch inmates) -- they
  are in ALL_ASSETS.zip too; GitHub's web uploader takes 100 files per upload, which is the likely cause.
- **Upper tier**: every cell block is 2 floors ("cellrow" on both, stairs in the plan); roster cells 25-48
  are the upper tier (shown "U1".."U24"). **The roster fills KESTREL_FILL (72%)** of each block's open
  cells, spread by a fixed shuffle; the other cells are VACANT. Cast members with no cell go to
  g.kestrelReserve. Cell 3 is always the store man's; cell 2 (men) the bodyguard's, left empty.
- **`vacancyMap(blk)`**: the vacancies in order, given to the people Malcolm sent (g.convicts, in order),
  then the war's jailed seats -- the same on both tiers every visit. Empty cells stay empty.
- **Sentences** (PRISON_SENTENCE -- `SENTENCE` was already the court's table): a year is one game day
  (24 real minutes); g.day counts days as the clock wraps; `kestrelReleases()` runs daily: parole at
  half term for anyone below HIGH threat, the full term for HIGH. Convicts carry years, inDay, threat.
  Verified: a 12-year convict released after 12 days, with a note.
- **Alonzo and Kearney's cars have the siren** (GUMBALL.cars).
- **The station lot**: `g.stalls` -- every assigned car in its own labelled stall (painted lines + name at
  the head: the three senior detectives up top, Delgado / Alonzo / Kearney / UNIT 01 below, Malcolm in
  his own). Cruiser 01 used to sit on top of Alonzo's car. `drawLotPaint`.
- **Garage signs** (`drawGarageSigns`, `drawChevronSign`): every car park's ramp has a painted box with
  chevrons outside ("POLICE GARAGE · E" at the station) that pulses when a car is in reach; inside on the
  garage floor the way out is marked "EXIT RAMP · E". Verified in screenshots.

---

## 000000000000000000000000000. EARLIER SESSION — EVERY PRISONER IS SOMEBODY

- **`kestrelRoster()`** (g.kestrel, built once, deterministic -- `khash` off each plate key, so it is the
  same every session without saving): every intake-page inmate gets a unique name (KESTREL_NAMES by race
  and sex; printed names kept; never a shot caller's name), his number, block, CELL, charge, sentence,
  release year and gang (60% of a men's block ride with its gang; women 50% with any of the four).
  Cells start at 4 (shot caller, bodyguard, store man first; 5 in W for the four queens); past 24 a man
  is on the UPPER TIER ("U12") -- which does not exist as a floor yet. 328 people: A 47, B 43, C 52,
  D 42, W 144.
- The cell belongs to him: in or out is decided by the hour (`khash(plate + phase) < inCell`), never at
  random, and nobody generic ever fills an owned cell. The men's MESS HALL at chow holds the actual men
  who are out of their cells for that meal (the women's block eats apart). Verified: same man in the
  same cell at 7:05, 7:10 and 9:05 PM; breakfast full of named men from all four blocks.

---

## 00000000000000000000000000. EARLIER SESSION — THE MISSING-FILES LIST

- The "N ASSETS MISSING" line is tappable ("TAP FOR THE FILE NAMES"): it opens a panel listing every
  missing file by its EXACT path from the repo root, sorted, in a selectable text box, with COPY ALL
  and CLOSE. The loader now records every failed path (`window.__ironlion.missingPaths`), not just the
  first. The open flag is its own React state (`missOpen`) -- in `hud` it was wiped by the per-frame
  HUD refresh and the panel never stayed open. Verified: tapped, the list shows full paths.

---

## 0000000000000000000000000. EARLIER SESSION — ONE ZIP FOR EVERYTHING; THE WARDEN; THE HUB'S PEOPLE

- **ALL_ASSETS.zip**: every file cut in these sessions (1,002) in one tree -- assets/civ, heroes, leaders,
  map, police, prison, ui. Unzip at the repo root and the "ASSETS MISSING" list for this work clears.
  The per-session zips are all inside it.
- **The warden** (PRISON_WARDEN, "Warden Everett Crane", yt_pr_warden) in his office upstairs in the hub.
  prisonFolk now fills the hub too: gate guards, men in the old blocks, the laundry at work time, a
  guard in visiting; upstairs a guard on the post and one in records. Don Matteo's cell is untouched.
  Verified: 9 downstairs, 3 upstairs with the warden.
- Medical: the INFIRMARY already exists (a ward of beds with inmates and a nurse, and the nurse's office).

---

## 000000000000000000000000. EARLIER SESSION — THE WOMEN OFFICERS

- **women_guards.zip** -> assets/prison/yt_gw_0..4 + pt_gw_0..4: five women officers off IMG_4062's top
  row (two Black, Latina, Asian, white), each with the photo under her -- these DO match. GUARD_FACE
  gives each her photo and tone; PR_PEOPLE.guardW is now six (with yt_gd_1_3). Guards in campus
  buildings can be asked for ID (a plain card with the photo, sex by block). Verified on the women's
  block: three women officers on duty, carded one -> her photo, female.
- IMG_4063 and IMG_4064 repeat the same five (plus inmates and officers with no matching photos);
  IMG_4061 was already used. Nothing further taken from them.

---

## 00000000000000000000000. EARLIER SESSION — THE GUARDS

- **guards.zip** -> assets/prison/yt_gd_*.png: nine guard bodies off the three guard sheets' TOP rows
  (IMG_4061 repeats IMG_4060, so it gave nothing new; IMG_4059's Asian woman officer did not cut
  cleanly and is not in). Eight join PR_PEOPLE.guard with their own sizes (GUARD_TALL); the Black woman
  officer (yt_gd_1_3) is PR_PEOPLE.guardW and the only guard on the women's block tiers and post.
- NOT used: the sheets' mugshots (shuffled -- they do not match the bodies, so guards carry no photo),
  the bottom-row figures (front-facing busts, not top-down sprites), and the store man's cell picture
  (a scene, not props). Verified: men's blocks mix old and new guards; the women's block has only her.

---

## 0000000000000000000000. EARLIER SESSION — CONTRABAND ICONS, PROTECTION FOR JAILED LEADERS

- **contraband_icons.zip** -> assets/prison/ci_<item>.png (15, mostly the first sheet; pencil and milk carton
  off the second). New CONTRABAND: pencil (2), weed (1), heroin (3), stamps (0, currency), book (1),
  gun (6 -- 36 h in the hole). PRISON_STORE sells pencil 5, weed 5, heroin 14, stamps 3, book 7 as well.
  Carried items draw as icons under the prison banner; the banner text is just the packs.
- **PROTECTION** (`protectorOf`, `payProtection`, PRISON_PROTECT, in prisonEcon): every jailed war seat is
  watched by a prison gang. If his gang is a patron of one (Kings -> Old Crown, La Perla -> Los Eternos,
  Bracken/Irish/Security -> Iron Covenant, Chinatown -> Jade Lotus) it is his own people, 60 a seat a
  prison turn. Everyone else (the two mob families, the Wolves, the Gomez family, the Deuce) buys it
  from the gang running the block he is housed in (GANG_BLOCK), 320 a seat a turn -- out of the outside
  gang's cash into the prison gang's. Short of the fee = `G.unprotected` counts up (for a hit later).
  His card reads "HIS OWN: <gang>" or "PROTECTED BY <gang>". Verified: Kings paid 60, young mob 320.

---

## 000000000000000000000. EARLIER SESSION — 63 MORE INMATES (THE THIN GROUPS)

- **inmate_pages_4.zip** -> assets/prison/: yt_in_s0..s5_* + pt_in_s* (63), appended to INMATE_CAST (7000+):
  25 Asian women, 22 Black women, and the mixed pages sorted panel by panel -- IMG_4053's left page and
  IMG_4056 each carried men and women of every group (3 each of Black, Mexican, Asian, white men; 2
  white women, 2 Mexican women). IMG_4051's bottom row has mugshots but no bodies, so only its top five
  are in; IMG_4052 gave 8 of 10. Cast is now 334.
- The two contraband sheets (both named Unknown.jpg) were NOT used: not top-down, mixed with people,
  illegible labels. A tighter prompt is in the chat.

---

## 00000000000000000000. EARLIER SESSION — 135 MORE INMATES

- **inmate_pages_3.zip** -> assets/prison/: yt_in_r0..r12_* + pt_in_r* (135), appended to INMATE_CAST
  (numbers 5000+): 37 Mexican women, 13 Asian women, 19 white women, 34 white men, 30 Asian men.
  The unlabeled women's sheet (IMG_4041) is split: top row Mexican, bottom row Asian. IMG_4044 was
  uploaded twice (used once). Four sheets whose panels touch are cut by a fixed grid (GRID in the
  cutter); IMG_4041's wall strip is keyed out by its own colour in the top quarter so the heads stay.
- The cast is now 271 (44 + 92 + 135). Verified: every block's cells are now almost all intake-page
  inmates of the block's race (and women in W), shot callers and store men in their cells.

---

## 0000000000000000000. EARLIER SESSION — 92 MORE INMATES, THE ECONOMY INSIDE, THE STORE MAN, THE SKILL

- **inmate_pages_2.zip** -> assets/prison/: yt_in_q0..q9_* + pt_in_q* (92), appended to INMATE_CAST
  (numbers 3000+). Cutter splits merged magenta strips into columns; IMG_4033 has its mugshots ABOVE.
  IMG_4029 was uploaded twice (used once). Paired and checked on a contact sheet.
- **PRISON_ECON / prisonEcon()** (runs in warIncome): every 20 s each prison gang's patrons send a share of
  their product inside (4-18%, more when flush; the corners count as product even without houses);
  that value comes OFF the patron's cash. Product sells inside at 35% of the street price, capped by
  campus demand. Selling raises the gang's HEAT; heat past 40 brings SHAKEDOWNS (the block's stashes are
  emptied, 30% of stock lost, heat cut). Gangs BUY GUARDS (4000 x n, up to 3): each cuts shakedown odds
  and pat-downs on their people by 20%. Gangs short of product buy from the gang holding most at 1.4x.
  g.pecon[gang] = { stock, cash, heat, guards, sold, shakes, traded }. Verified: all four stocked,
  selling, earning, heat rising.
- **Pat-down skill**: a pat-down now FINDS what you carry 90% of the time, minus 8% per skill level (g.pskill,
  max 5, +1 each time one misses what you had) and 20% per guard your gang (g.pgang) has bought.
- **Cigarettes are packs** (g.pcigs, 20 to start; a stashed carton is 10). **The store man** keeps cell 3 of
  every men's block: E by him in PRISON MODE opens COMMISSARY (PRISON_STORE: shank 12, razor 6, pills 8,
  hooch 4, zip gun 45, bills 10). Verified: bought a shank, 20 -> 8 packs.
- Joining a gang (g.pgang) is not built yet; everything that reads it is ready.

---

## 000000000000000000. EARLIER SESSION — PRISON MODE STARTS, THE STASH, THE HOLE, THE BODYGUARDS

- **bodyguards_player.zip** -> assets/prison/: yt_/pt_ bg_covenant (IMG_4020), bg_eternos + bg_jade (the
  Varga twins, 4021/4022), pr_player (4024), bg_crown (the one with the fro, 4025).
- **PRISON_GUARDS**: each gang's bodyguard stands on the tier outside his shot caller's cell (Walt "Tank"
  Krantz / Tomás Varga / Teo Varga / Moses "Mountain" Greer), threat HIGH, cardable. They do not fight yet.
- **PRISON MODE** (title button under DETECTIVE MODE; `g.prisonStart` -> `startPrisonMode()`): you are
  inmate #0001 (yt_pr_player), in the last cell of a random men's block at the 7:00 count, a carton of
  cigarettes on you, no weapon. Verified from the title: C BLOCK, 7:03, Rafa and Tomás Varga on the tier.
  The city HUD (objectives, Lion buttons) is still showing in this mode -- next.
- **THE STASH** (CONTRABAND, STASH_PROPS, STASH, `G.stashFn` on E inside campus buildings, g.stash,
  g.pinv): every bed, pan, sink, shelf, washer, bench and table hides things; 28% hold another man's
  stash. E takes what is there, or hides your worst contraband there (never your cigarettes -- money).
  **Pat-downs** (PRISON MODE only): a guard within 64 checks you, 45% of the time, 40 s apart. Anything
  with sev > 0 on you is taken; the hole is worst sev x 6 h + 2 h per extra item (shank 18 h, zip gun
  30 h). **The hole** blacks the screen and runs the clock at 40x until served. Verified: searched ten
  hides, found pills in a mattress, got caught with a shank -> 18 hours.
- The top banner shows what you are carrying, or the hours left in the hole.

---

## 00000000000000000. EARLIER SESSION — 44 INMATES OFF THE INTAKE PAGES, THREAT BY UNIFORM

- **inmate_pages.zip** -> assets/prison/: yt_in_pN_K (hip-cut body) + pt_in_pN_K (the mugshot beside it on
  the same quarter), 44 of them from ten sheets (the duplicate IMG_4012 skipped). Cut by magenta-panel
  detection; IMG_4013/4014 by the 2x2 grid. Pairing checked on a contact sheet.
- **INMATE_CAST** [key, race, sex, clothing, no, name, tall]: race houses them (RACE_BLOCK: W->A, B->B,
  L->C, A->D; women -> W); clothing is THREAT (blue 1 LOW, grey 2 MEDIUM, orange 3 HIGH) and prints
  on the prison card in its colour. Each block draws its own race from the pool without repeats before
  the generic plates. Duplicate printed names are dropped for a generated one.
- **The women's shot callers have their own art now** (p9_0..3), threat HIGH; every shot caller's card
  is HIGH. Verified: 7 cast inmates in each men's block, 16 in the women's, the card on M. Garcia.
- Blue, grey and orange stay mixed on purpose -- the uniform is the threat level.

---

## 0000000000000000. EARLIER SESSION — KEARNEY'S ART, THE WOMEN'S BLOCK, ORANGE FOR THE CONVICTED

- **kearney_women.zip**: yt_kearney / pt_kearney / pd_car_kearney (Ford LTD, len 118 w 52), and the
  women's page: yt_wm_1..4 + pt_wm_1..4 (front mugshots) in assets/prison/.
- **The women's block** (PR_PEOPLE.women, PRISON_QUEENS): all four gangs are in it, each with a woman
  shot caller in cells 1-4 -- Loretta "Mother" Cole (Old Crown), Graciela "La Madrina" Ruiz (Los Eternos),
  Darlene Pruitt (Iron Covenant), Mei-Ling "Auntie" Chan (Jade Lotus) -- wearing the women's plates until
  their own art exists. Every inmate now carries `cast` (sex by block, tone by block) so cards match.
  Verified: 23 in the block at count, the four queens named, every card female.
- **Orange jumpsuits** (`jumpsuit(key)` -> cached canvas "js_<key>"): clothes recoloured orange at their own
  brightness; skin (warm, G > 0.45 R), hair and outlines kept. Checked on four plates.
- **Who is in Kestrel** (`sendToKestrel`, `g.convicts`, `prisonRoster`): a right name or a guilty verdict
  sends the perp to the block his crew's gang (GANG_BLOCK) or his tone (TONE_BLOCK) puts him in -- women
  to W -- and every war seat with state "prison" sits in his gang's block. Both drawn in the jumpsuit,
  in the cells after the shot caller. Verified: a jailed Kings captain in B block in orange.
- Prison start mode: confirmed as a SEPARATE title-screen option (not built).

---

## 000000000000000. EARLIER SESSION — THE GANGS INSIDE, THE CLOCK, PRISON IDS, KEARNEY, RAMOS'S ADDRESSES

- **inmates_card.zip**: yt_inm_/pt_inm_ 4521 7761 9033 1298 (assets/prison/) and assets/ui/id_card_prison.png.
- **PRISON_GANGS**: THE OLD CROWN (B block, Kings' first leadership, shot caller Clarence "Deacon" Cole --
  Andre's uncle, 4521), LOS ETERNOS (C, La Perla, Rafael "Rafa" Ortega speaks for El Viejo, 7761, Spanish),
  THE IRON COVENANT (A, purist, backed by Bracken + Irish + sec as the corrupt-officials money, Dale
  "Preacher" Hutchins, 9033), THE JADE LOTUS (D, the Fongs, Danny Wu, 1298, Cantonese). Each shot caller
  keeps cell 1 of his block. Gang men speak their own language in a bubble when you walk up (PRISON_TALK);
  shot callers answer in English. `patrons` is there for prisonGangPower() -- NOT written yet.
- **The clock**: g.clock, minutes, 1 game minute per real second, starts 7:00 AM. PRISON_DAY: head counts
  7:00 / 4:00 / 9:00, breakfast, lunch, dinner, work/free, rec/visiting, lights out. Shown at the top of
  the screen in and around the prison. The campus population follows the phase (verified: B block 24 at
  the 7:05 count, 4 at breakfast; the shot caller stays in his cell).
- **Prison ID card**: carding an inmate (they are in nearCiv's pool inside the campus) opens Kestrel's card
  (drawPrisonCard): mugshot, name, number, block, cell, charge, sentence, release, affiliation. Verified
  on Deacon Cole.
- **Det. Kearney**, COLD CASES, SQUAD4[5], the second gang-desk office, car pd_car_kearney beside
  Alonzo's (art not in). `coldCase()`: a normal case, aged -- a year 1971-81, all evidence bagged and
  back from the lab, victim and witnesses moved to real addresses listed in the file. She owes a war
  gang (g.kearney.owes) and never pulls a file that leads to its crew. Verified: 1981 assault, six lab
  results in, victim and two witnesses at real addresses.
- **Ramos drives to every address a case has given you**: every stop you have been pointed at and where
  he hangs, out front of the door.
- **NOT BUILT (designed in chat)**: the prison-start game mode, joining a gang, prison jobs, visiting room,
  prisonGangPower and hardened releases.

---

## 00000000000000. EARLIER SESSION — KESTREL STATE REBUILT AS A CAMPUS; ALONZO'S NEW CAR

- **prison_campus_assets.zip** (replaces prison_assets.zip) -> assets/prison/ (roofs, yard, props, people)
  and assets/police/pd_car_alonzo.png. Pink fringe stripped off every prison edge.
- **The campus** (`PRISON_BOX`, `PRISON_CAMPUS`): ten real buildings as MARKS (roof plate on a real
  block -- the rooftop trick), laid out by fractions of the walled box: mess hall, the hub (kind
  "prison", 2 floors -- the old cellblock/wardenwing plans, so w5, the gate and Don Matteo's cell are
  untouched), A/B/C/D blocks and the women's block (kind "prisonwing" -> plan "cellrow": a cell per
  column both sides of the tier, closets, showers, a guard post; each cell bed, desk, pan, sink),
  infirmary ("pinf": ward + nurse), library ("plib"), chapel ("pchapel"). Blocks are segregated
  (PRISON_WING_TONE: A white, B Black, C Latino, D Asian/other, W women) -- the tone table is there,
  the inmate plates do not yet vary by it. Verified: 10 buildings, 24 cells a wing, 24 people in a
  wing on entry (inmates in cells, guards on the tier).
- **The wall** is generated per cell (each cell keeps the pieces inside it, so collision finds them),
  gate gap in the north wall. The old single building is gone. `drawPrison` only paints ground now:
  dirt, concrete, the yard (court, track, weights, stands, tables, handball wall, shack, phone, fence),
  six towers, the gate plate, floodlights and searchlights.
- **Campus population** (`prisonFolk`, `drawPrisonFolk`, PRISON_POP) -- built per building/floor on
  entry. The hub keeps its old folk.
- **Alonzo's car**: the new plate (wheel on the left), Monte Carlo script, SS and bowtie painted out;
  `lowrider: 1` -- parked it sits up and hops now and then; driven, the HYDRO button works.
- **Capacity**: the plan grid caps at 14 columns, so 24 cells a wing, 120 on the campus. The 340
  in the design needs a second tier (upstairs floor) per wing -- next.

---

## 0000000000000. EARLIER SESSION — ALONZO'S ART, ALONZO FOR SALE, THE PRISON SHEET CUT

- **Alonzo's art** (alonzo_assets.zip): pt_alonzo (circle, transparent outside), yt_alonzo (hip-cut,
  tall 1.26 by shoulder width), pd_car_alonzo (black Monte Carlo, nose up, SS badge painted out).
- **ALONZO IS FOR SALE** (`ALONZO_PAY`, `alonzoMarket`, `g.alonzo = { boss, rate, earned, grudge, bidT }`).
  One war gang (never the Deuce) has him on the payroll and pays him `rate` of every dollar its dens
  make, straight out of `G.cash` (in warIncome). Every `every` (120 s) the gangs bid: base + grudge x
  0.025 + cash/20000 x 0.03, clamped 6-24%; a new gang takes him only by beating the rate by 12%.
  Every time he gives a gang up (a stash, an underboss) its grudge rises, so the gangs he hurts bid
  for him. He NEVER reveals his employer: its stashes are skipped, and on its crew cases he stonewalls
  -- the only tell. Nothing about this is shown to the player yet. Verified: Kings bought him at 9.1%,
  he gave up three other gangs' stashes and never the Kings', and a burned, cash-rich gang took him.
- **Prison sheet cut** (prison_assets.zip -> assets/prison/, 47 files, NOT wired yet): 9 buildings
  (hub, cellwing, cafeteria, chapel, library, infirmary, tower, gate, wall), 11 room vignettes (the
  gym one is the yard Donny does not want), 12 props, 15 people hip-cut (4 guards, 9 inmates, nurse,
  warden). The buildings are drawn front-facing 3/4, not roofs -- see chat.

---

## 000000000000. EARLIER SESSION — HYDRAULICS, DET. ALONZO

- **Hydraulics** (`HYDRO`, `stepHydro`, `hydroLift`, `G.hydroFn`, HYDRO button / H key). LP_RIDES carry
  `lowrider: 1`. drawBody (all vehicles pass through it; the old body is `drawBodyRaw`) draws a lowrider
  bigger and shifted up by its lift while the shadow stays on the road. Driving one: tap = lift;
  lifted and stopped = hop; lifted and rolling = slam. AI lowriders lift at a stop, slam when rolling,
  and hop now and then. Verified: lift eases in, hop peaks ~0.17 scale.
- **Det. Alonzo**, VICE / NARCOTICS, SQUAD4[4], in the first new B1 office (`pdoffice` 0), car
  `pd_car_alonzo` parked beside Delgado's. `alonzoHelp`: on a war gang's crew case he names the
  underboss and where he sits (seat known); otherwise he puts the nearest unfound distro on the map
  by name and address. 4-minute cooldown. Verified: stands at his desk, gave a distro, then cooldown.
  **Art not in yet**: assets/heroes/yt_alonzo.png, pt_alonzo.png, assets/police/pd_car_alonzo.png
  (prompts in chat). The second gang-desk chair (pdoffice 1) is empty.

---

## 00000000000. EARLIER SESSION — SCENES ON THE GROUND, NOBODY BLOCKS A DOOR, SALLY RUNS NAMES

- **Scenes on roofs.** The bank robbery's scene was the bank door + 70 SOUTH -- inside the building for
  any bank facing north/east. Bank robberies are now INSIDE the bank (biggest room), falling back to
  out front along the door's own facing. `streetSpot` also checks `groundOK` (no deck, no ramp, and
  the real collision would not move a man standing there). Measured: 16/16 outdoor scenes standable.
- **Stuck behind NPCs in doorways.** `shove(q, r)` in sceneSolid: walking into a detective, a Deuce
  regular or anyone on the case moves HIM 85% of the overlap (walls keep him in) and you 15%.
- **Bar four-tops** 76x72 in bar rooms (were 52x32); bar-case tables 72x70, fewer to a row.
- **Sally: RUN <NAME>** for each person on the current case Malcolm has carded, once each (`sallySheet`):
  the perp's sheet fits the job and names where he drinks (40% come back clean), decoys have the wrong
  kind of record, citizens are citizens. Goes into the case lines as SHEET.
- **Sarge's desk:** `pd_counter` taken back OFF ROTATE_180 (desk as drawn; sergeant stays behind it).
- **B1:** a final pass after the furnisher + tidy removes the middle cabinet in each of the three
  detectives' offices (back-wall ones kept) and hangs ONE mug board on the task-force room's bottom
  wall left of the doorway (a duplicate stood in the doorway). Verified by listing the props.

### Designed, not built: the prison (see chat for the plan and the asset prompt).

---

## 0000000000. EARLIER SESSION — THE FOUR DETECTIVES RE-CUT

- yt_okafor / yt_morrow / yt_hayashi / yt_delgado re-cut from Donny's detective sheet
  (detectives_recut.zip -> assets/heroes/). Keyed off the purple gradient by flood from the cell edge,
  cut at the hip line with hands kept; Okafor's folder and Hayashi's case are trimmed at the hand line.
  **Delgado's whole face is on the plate now** -- the old plate clipped his nose.
- Each SQUAD4 entry carries its own `tall` (Okafor 0.84, Morrow 0.9, Hayashi 0.96, Delgado 0.81),
  solved off a 29-unit shoulder span, a touch under the leaders' 33. Checked on B1: they now stand
  smaller than the player figure.

---

## 000000000. EARLIER SESSION — B1: THE TANK AND TWO OFFICES

- The three one-man cells under the detectives' offices are now two offices (k "pdoffice", a desk
  each, placed) and ONE big holding cell on the right half (k "cell" with `holding: 1` -- holdingSpot
  and arrests still find it; the furnisher gives it a bench along the back and a pan, no bunks).
  Verified in the running game: rooms, the tank's bench + toilet, a desk in each office.
- The second task-force desk beside Sally's dispatch desk is removed.
- Delgado alone at `tall` 0.64 (SQUAD4 entry; the others stay at SQUAD_TALL 0.76). **His nose being
  clipped is in the plate itself** (assets/heroes/yt_delgado.png) and needs the file to re-cut.

---

## 00000000. EARLIER SESSION — POLICE NEVER HUNT A DETECTIVE; 128 MORE CIVILIANS

- **BUG: a tester was shot by the police in detective mode.** Every police behaviour keys off `g.heat`
  and nine paths raise it. `witnessed` and `escalatePolice` now return at once in detective mode, and
  the step holds heat, wantedT, wantedAs, copFrom, chaseT at zero and calls off any patrol chase
  while `g.detMode`. Verified: a witnessed gunshot -> heat 0 in detective mode, 3 as the Lion; heat
  forced to 3 -> 0 by the next frames.
- **Civilian page 2** (civ_page2.zip): the 16 x 8 sheet, 128 bodies, `yt_cv_p2_<row>_<col>`, hip-cut,
  x2 nearest, sized by shoulder width. **Its ID photos are NOT used**: on this sheet (and on the 13-wide
  sheet) the generator shuffled the photos -- a body in a suit over a punk's face. These carry no
  photo; the card takes one from the face pages by sex and tone. Sex by row as requested (rows 1-3 men,
  4-6 women), rows 7-8 labelled by eye; tone measured off the figure (approximate).
  `CIV_CAST_SHARE` 0.7: measured 56 of 104 street peds from the cast, 51 of them page 2.
- The 13-wide sheet was not used: its bottom rows have no usable photographs and it repeats page 1.

---

## 0000000. EARLIER SESSION — THE NEW CIVILIAN CAST, PAGE 1

- **CIV_CAST** (module level, registered under the list): page 1 of 16 -- twelve white men, each a hip-cut
  plate `assets/civ/yt_cv_<k>.png` and his own ID photo `assets/civ/pt_cv_<k>.png` (civ_page1.zip).
  `spawnPed` gives `CIV_CAST_SHARE` (40%) of ordinary street peds a cast member once his plate has
  loaded (measured: 34 of 104 on a street). The ped carries `p.cast`; `identOf` takes sex and tone from
  it and stores `castFace`; `faceOf` returns that photo before any sheet lookup; `bookAdd` keeps it, so
  the notebook shows the same face.
- Cut: hands kept, legs cleared from the hem, sized by shoulder width (tall ~1.34-1.46: this page is
  drawn more front-on than the leadership sheets, so the plates run tall).
- Known limit of this page's angle: faces are front-on, so a man walking north shows his face
  upside down. Later pages asked for with heads tilted down (crown and shoulders), like the leaders.

---

## 000000. EARLIER SESSION — LANES, BLINKERS, OLD TOWN'S CARS

- **Traffic stays in its lane.** It aimed straight at the next junction's lane point, so after every
  turn it drove a long diagonal down the middle of the road. It now steers at a point
  `TRAFFIC_LANE.look` (90) ahead ON its own lane line. Measured over 1,758 samples away from
  junctions: median 0 units off the lane line, 90th percentile 3.
- **Blinkers.** A turn is planned `TRAFFIC_LANE.plan` (300) before the corner (`planTurn`, which dry-runs
  `chooseTurn` and stores `v.plan` + `v.sig`); `chooseTurn` applies the plan at the corner and the
  blinker runs 1.4 s more through the turn. Amber front and rear corner on the turning side.
- **Ramos and dispatch drive on the right lane.** `roadRoute` now offsets every leg of the old
  centreline route (`roadRouteC`) onto its lane; corners are where the two lanes cross.
- **Old Town's own police:** beat cars within `OLDTOWN_PD.r` of the circle use the older `cruiser`
  plate and carry no unit number. Their station is not built yet (prompt given in chat).

---

## 00000. EARLIER SESSION — CREWS, RICO, REAL ADDRESSES

### Built (run in the headless browser: 14 generated cases, a 3-man crew chain end to end, RICO)
- **Every building has an address** (`addressOf`, module level): the street the door opens onto and
  how far along the block, odd N/W, even S/E, 100 to a block ("1142 Arden Ave"). `placeGroup` /
  `placeName` / `placeLabel` name a building from what it REALLY is (bars from BAR_NAMES, shops from
  SHOP_NAMES, homes "the walk-up at ...") -- never from what a tip wanted.
- **Leads go to real places** (`realPlace(group, from, r0, r1, avoid)`): the trail's stops, where the man
  hangs, and the next man in a crew are buildings with an indoor standing point, a door and a back.
  The person you want is INSIDE (q.inB/q.inF), or 30% OUT BACK behind the building. Stop evidence is
  inside or out back by the bins. The lead kind follows the building (a bar lead is always a bar).
- **Per-person gating** (`caseHere(q)`): nearCiv, nearTalk, sceneBodies, the collision pass, evidence
  pickup and drawTrailEvidence all ask where each person/piece is, not where the scene is. Verified:
  carded and questioned a perp standing in an apartment lobby.
- **More evidence:** glass, bottle, dropgun, toolmarks, paint, lock (EVIDENCE, EV_ICON, EV_TOPIC).
- **CREW JOBS** in CASE_CRIMES: store_robbery (2, inside a shop), armored_car (3), bank_robbery (4, at a
  bank). Street crimes stay one man. `C.crew = { n, idx, names, gang, label }`; half are a war gang's.
  Closing a member (right name, or GUILTY) calls `crewAdvance`: the next man's case starts from where
  the last one was ("X gave him up: <address>"), witnesses there, no victim. The last one closes the
  crew: pay + juice; if it is a gang's crew it is **RICO** -- the underboss (seat 1) goes to Kestrel,
  gang cash -12000, every corner +20 heat. Verified KINGS: Book Gaines free -> prison.
- **Station:** office filing cabinets moved to the front wall; any cabinet/shelf in the hall or corridor
  is stripped; snack machine and fridge on the left of the back wall. (`pd_counter` has been in
  ROTATE_180 since last session -- confirm in game before flipping again.)

### Next, designed, not built
- Malcolm's apartment: the whole top floor of a three-storey record shop (art prompt given in chat).
- Working shops: stock, prices, cashiers, a till that can be robbed -- one system all shop kinds share.

---

## 0000. EARLIER SESSION — BASES, RACES, THE MAP, THE TOW TRUCK

### Built (all run in the headless browser against the real build)
- **Music had two deciders.** `musicUpdate` ran every frame and played its own pick (drive/chase/title)
  over the 1.5 s chooser's det / zone / job track, and wrote `MUS.want` every frame, which reset the
  chooser's hold so district tracks could never commit. It now only plays the title; the chooser owns
  everything after. (No audio in the headless run -- listen once.)
- **LEADERSHIP ON SITES** (`LEADER_SITE`, `stepLeaderSites`, `g.ldSites[gang] = [base, hideout, hideout]`).
  Boss: the biggest building on his HQ block (LEADERS[].where), 10 men. Underboss and captain: a
  hideout each on a block the crew owns in the war, 7 men each. Levels: men 4 (61 hp), seats 5
  (233 hp), boss 6 (270 hp); men fire via `S.fight` (6 shooters, 4.4 dmg, faster). Sites use the tower
  shape, so combatTargets / guardSites / drawDistros / siteFight take them. A seat taken down goes
  to the hospital (`WAR_HOSP*2`) and comes back. Both seats under a boss down -> he moves to a
  bar/shop/cafe on his turf (verified: Andre Cole, house -> fastfood). In DETECTIVE MODE a site only
  goes hot when somebody is hurt, so you can walk in and talk (E works indoors now); as the Lion they
  shoot on sight. The old street walkers (`leaderCrew`, `stepLeaders`) are retired, code left in.
  **Don Matteo's base is in Kestrel prison** because that is his LEADERS spot -- check that is wanted.
- **STREET RACES:** no scanner alert. In detective mode a race is state `street`: the three run the
  course for `RACE_BUST.life` 240 s. Two hard rams (0.7 s cooldown per contact) stop a car; the driver
  runs (55%) or stands. E on foot cuffs him: notebook line, arrest juice, `g.racePris`.
  **NOT BUILT: the racing trial.** `g.racePris` carries `court: 0.9`; nothing reads it yet.
- **THE MAP IS DRAWN FROM THE WORLD** (`mapBase()`, cached canvas): zone colour, waterDepth, every street
  at its width, every building footprint, expressway + ramps. The painted atlas is no longer used.
  On top: every war turf washed in its owner's colour with borders and a label per crew; icons for
  the boss bases, known hideouts, a moved boss, the station, the court, found distros, a race, the
  case and you. Icons are `MAP_ICONS` at assets/map/ (map_tow_assets.zip); shapes if missing.
- **Motor pool:** the station lot stops a car ~140 off the wall and the ramp reach was 130 -- widened
  to 120x190. The E button reads GARAGE when a car-park ramp is in reach. Verified into B2.
- **Notebook:** text x1.3; the ⤢ tab (the only new control) makes it near full-screen at x1.75.
- **Desk:** `pd_counter` is in ROTATE_180 (front to the door); Sgt. Lee stands BEHIND it facing the
  door. **Sizes:** `SQUAD_TALL` 0.76, Miller (CSI), the CSU tech and the sergeant 0.8.
- **Tow truck:** radio MOTOR POOL (6 juice) sends Kowalski in `pd_tow` (cut nose-up, 150x52); when he
  reaches your car (or the car you're beside) every vehicle is fuelled and repaired, then he leaves.
  Verified: fuel 5 -> 100, damage 0.8 -> 0.

---

## 000. EARLIER SESSION — THE LEADERSHIP WALKS, THE RAMPS OPEN

### Built
- **All 27 seats have bodies.** Nine sheets from Donny, cut to `assets/leaders/yt_ld_<crew>_<boss|under|capt>.png`
  (`leaders_assets.zip`). Cut at the line of the HANDS with the legs cleared out from the hem down, so
  `drawYouth` draws the walking legs; long coats (Foss, Castellano, Fr. Doyle) keep the coat and end at
  the hands. Vargas's braid is trimmed at the hem; Novak keeps his whole briefcase (taller plate).
  Kings: Cole / Book Gaines / Pryor. Wolves: Halleran / Wire Malloy / June Strand. Young mob: Rizzo /
  Foss / Amato. Old mob: Don Matteo (prison blues) / Novak / Castellano. Chinatown: Fong / Chen / Park.
  Irish: Brennan / Fr. Doyle / Kane. Barrio: Moreno / Quintana / Vargas. Bracken: Curtis / Tillman /
  Ellis. Security: Hollis / Maj. Keller / Voss.
- **`LEADER_ART`** (module level, registered UNDER the list) — per plate `tall`, solved off SHOULDER
  WIDTH, not plate height: the Kings, Wolves and young-mob sheets are drawn more overhead and at parity
  by height the Wolves were half again as broad as everyone. `LEADER_SCALE` 1.3 on top, measured in the
  running game beside the street crews.
- **They walk.** `leaderCrew(k)` builds three walkers per crew in `g.ldCrew` at `LEADER_POSE` round the
  leader's spot (pushed out of any building onto the pavement — that becomes home). `stepLeaders`
  (only within 1600 of the player) wanders each within 70, rests 2–6 s, stops at walls, and turns to
  face a man on foot inside 170. Measured: every seat of all nine crews moved 17–57 units in 6 s.
- **The war decides who is standing there.** A seat in hospital or Kestrel State (`g.gwar`) is not
  drawn; talking goes to whoever runs the crew now (boss, or the next seat down). Names show only over
  seats Malcolm knows; the boss always. The Deuce and Gomez are unchanged (own systems).
- **Detectives down a size.** `SQUAD_TALL` 0.88 on Okafor, Morrow, Hayashi, Delgado — rides with a hired
  detective too. **Delgado's face possibly clipped: not checked** — the plate was not in the session.
- **THE RAMPS NEVER OPENED THE PARAPET.** `rampList` set `r.vert` from the ramp's own slope; a diamond ramp
  runs 430 out and 338 along, so every ramp off a N-S leg read as E-W and vice versa. The parapet draw,
  its collision (`barriers`) and the amber gap marks all filter on `vert` — so all 96 ramp mouths had a
  solid parapet drawn straight across them, and the car drove through a wall (the ramp itself switches
  collision off, which is the only reason it was drivable). `vert`/`L` now come from the LEG, and the
  gap is where the lane's centreline crosses the deck edge. Drove 8 ramps both ways in the running
  game: all up to the deck and down to the street, none stuck; old vs new screenshots at two mouths.

### Still open from this
- Ramp feet land 18 units past the pavement, in the lot edge, not on the carriageway — drivable, but a
  car comes down onto kerb/pavement before the road.
- Leaders are scenery with a talk panel: no portraits (`pt_`), not combat targets, no armless variants.

---

## 00. PREVIOUS SESSION — THE GYM, DEUCE'S WILD, SKY ON THE STREET

### What was actually wrong
- **The gym had never loaded a single prop.** The 22 `gy_` keys were referenced by `GYM_FIT` and
  registered nowhere. The old section 3 said "cut, registered, unplaced" — it was not registered.
- **The gym overlay was drawn off the cell CORNER, not the building.** The mark sits at cell
  centre + ox/oy, so the furniture was ~120 east / ~210 south of the walls, under the roof plate,
  with invisible `gymClamp` boxes on the pavement.
- **Every mark with no `kind` is a `store`.** The gym was a shop inside. So was Deuce's Wild.
- **Deuce's Wild's front door was sealed.** mkB always puts the door south; the nightclub plan puts
  its vestibule north. A south door opened into the bar room, where the generic bar case stands a
  solid bar 14 units under the doorway. Nobody could get in.
- **Last session's walk test was too kind.** It tested walls and `hard` boxes only, not ordinary
  SOLID_PROP furniture — which is how it passed a sealed door. The test now uses the game's own
  rules: skip under 26, shrink 6 per side, radius 13.

### Built
- **Gym interior.** `GYM_FIT` / `GYM_SOLID` / `GYM_RING` / `GYM_STAIR` are module level; kind
  `gym` → floor `gymfloor` → props through the normal pipeline. Door centred on the ring steps
  (bench moved -0.05 → -0.12). Stair moved west of the ring. Collision is invisible `gy_block`
  props with `hard: 1` — exact size, never skipped or shrunk. Street overlay and `gymClamp` deleted.
- **`texTile`** on a room sets its tile size; the gym floor keeps its w/3 tile instead of marble scale.
- **Marks take `kind`, `door` (pos) and `doorSide`.** Gym: `gym`, 0.5. Club: `nightclub`, 0.5, north.
  Not `club` — that is the Gilded Crown's identity and code looks it up by kind.
- **Deuce's Wild furnished off its own sheet** (`dw_` keys, `DW_LAYOUT` in makeFloor, gated on
  `b.capPlate === "ct_club"` so no other nightclub changes). Payphone, door desk and queue ropes in
  the vestibule; four booth sets, four bistro tables and two stool tables round the dance floor;
  cigarette machine, bar and crates in the bar; two curved booths; the back room keeps its safe.
  Solid: booths, cig machine, payphone, door desk. Walked end to end — all five rooms reachable.
- **Mirror ball** is drawn in `drawClub`, OVER the crowd (it hangs), with light flecks on the floor.
  Inside only. It is not a floor prop on purpose.
- **Club crowd** spawns on the dance floor, and no longer draws over other buildings or floor 1.
- **SKY ADDICTS.** Seven plates (`sky_`), ordinary peds with `yt` set, so they walk, fall and are
  combat targets for free. `skyAddictAt()` in `spawnPed` reads the live meter: Deuce turf gets
  8% + 42%×Sky of new peds; zones the ring has taken 30%×Sky; nowhere else. They shuffle at 22–34
  instead of 54–84. Push Sky down and the corners thin out as they walk off and are not replaced.
- **`gang_kings`** plays on the Kings HQ top floor.
- HUD: GYM / CLUB FLOOR floor names; DEUCE'S WILD / NORTH END GYM venue names.
- **Addicts talk.** `SKY_LINES` (module level) — `mutter` to nobody while they walk, `ask` when you
  are within 95 on foot (9–15s cooldown each), `deep` once Sky passes the second ring step (these
  talk about DOWN — the setup for the sewer camps), `flinch` on gunfire, and two `own` lines per
  face. Green-washed bubble. Only computed within 900 of the player. Answers a civilian with a
  mutter instead of a civilian line.
- **Fifteen addict faces**, not seven — the second sheet added eight, two `own` lines each. Equal
  weight in the pick.
- **SEWER CAMPS.** `SEWER_CAMP` (module level) is the layout; `campAt(i,j,arm)` builds one per
  seeded tunnel arm (30%, ~38 across the network) and caches it in `g.camps`, so the same people
  are there when you come back. Every piece is `[key, u, v, w]` — u along the tunnel, v out from
  the centreline — so one list lays a camp against either wall of a vertical or horizontal arm.
  Placement is clamped to the walkway band (34–96 off the centreline): **verified over all 38,
  every piece and person, zero strays.** `drawCamps` runs AFTER the dark gradient, so a fire is
  visible down a tunnel you cannot otherwise see; brightness is max(fire reach, your own reach).
  Seats fill with the meter: 1 at Sky 0, 4 at 100. They use `skyChatter`, so the deep lines land
  where they were pointing. `__ironlion.camp()` drops you at the nearest one.
- **VANCE TOWER IS A TOWER.** It was a mark with no `kind`: seven `store` floors, and `TOWER` was
  data nothing read. Now kind `vance`, 8 floors, `entry: 1` — index 0 is the car park, 1 lobby,
  2 pool deck, 3–5 flats, 6–7 the twins (mansion layout). Floor finishes come off `TOWER.floors`.
  Front door north; the ramp is a 128-wide gap in the south wall of the car park only.
- **The garage ramp never worked.** `nearTowerRamp` returned `{...b, entry: -1}` — a copy of the
  building (so no identity check could ever match) and floor -1 (not an index, no plan). And any
  vehicle indoors outside the den was thrown back into the street the same frame. `garageHere()`
  now covers den bay + any `carpark` floor 0 at all four sites; the ramp hands back `_b`/`_floor`.
- **Car park:** six painted stalls; the twins' SUVs and Rochelle's coupe are solid props.
  `rochelleIn()` — after dark (`night > 0.45`) — decides whether her car is there; when she is
  out the stall says RESERVED and is empty for collision too. Replace that one function when she
  has a real schedule.
- **THE LIFT.** Any building with `b.lift` gets an `elevator` prop on EVERY floor, placed by trying
  a list of wall spots against that floor's real walls, stair, doorways and stalls; furniture in
  its way is moved out. Vance Tower and the Kings HQ tower both have one. E at the doors opens a
  floor panel (top floor first, current floor lit, locked floors shown); picking a floor puts you
  in front of the doors on that floor. `TOWER.floors[n].lock` already greys a floor out.
  **Walk-tested all 15 floors of both towers:** door, stairs and lift reachable on every one; the
  car park reaches the street through the ramp.
- **Doors follow the entry floor.** The street doorway was cut into index 0 by a hardcoded
  `f === 0`, so the FIS field office had its door in the holding cells and a sealed lobby. Wall
  cut, door mat and walk-out test all read `b.entry` now. Verified on the field office.
- **Stairs are drawn, not plated** — `drawFlight()`: treads that brighten climbing and sink into
  black descending, risers, stringers, handrail, direction chevron. Interior stairwells and all
  four stair towers at every El station use it.
- **Chopper "shake" was the camera being dragged.** `stepFly` sets the camera over her, then the
  follow camera lerped it 7% back toward the man on the ground every frame. Flying now owns the
  camera, zeroes street shake, and holds a steady zoom.
- **NEON FLATS HAS AN IDENTITY.** `zoneOf` still calls these cells `city` — the district was an
  office, a bank, a hospital and four empty lots. Six houses on 7,14 / 7,15 / 6,15 and Rochelle's
  on SAFEHOUSE (7,13, the club's lot) are MARKS with kind `nfhouse`, 2 floors, `entry: 1`.
  **Bedrooms are in the basement** (floor 0 uses the upstairs plan; floor 1 is living, kitchen,
  dining, bath). `face` turns each door to the nearest street; `settleDoor()` then moves it onto
  the middle of a room so it never lands on an interior wall.
  Interiors match the roofs: pastel walls per house (`NF.hue`), a neon cove line down every wall,
  brighter downstairs; terrazzo up, carpet down. Rochelle's is lux furniture, charcoal walls, one
  violet line, marble downstairs, and no sign outside.
  **Walked all 14 floors** of the seven houses with the real collision rules: door, stairs, every
  room reachable. Placement verified: in lot, no overlaps, doors on streets.
- **Neon on the street** (`drawNeonFlats`, after the roofs): ring lamps down every pavement, an L
  on each lot corner, kerb tubes, puddles on the road, bollards at every door, a sign over each
  house door, cocktail + dice + an arrow at the club. Halos scale with night and flicker out of step.
  Rendered in a headless browser from the real code before shipping.
- **Blacktop** across the Flats and its boundary streets — `tx_blacktop`, one patterned fill
  before the blocks, 440-unit tile, world-anchored.
- **Three city-wide fixes found on the way:** `lx_rug` was SOLID and cut every luxury hall in two
  (Arden too); the tidy pass could push furniture into the FRONT door, because only interior
  doorways were cleared; and the doorway clearance was 22 deep against a 26-wide man, so a piano
  19 units off a doorway sealed the room. All three fixed; towers, club and gym re-tested clean.
- **THE WAR REACHES THE CASELOAD.** When a crew takes a corner off somebody, that killing is
  queued (`W.pending`, max 4) and the NEXT case dispatch hands Malcolm is that body, on that
  corner, with Ramos naming both crews; convicting it costs the crew $6k and heat on every turf.
- **THEY HIT BACK.** `grudge()` builds on a bust or a conviction and `stepGrudge` spends it on the
  CASE, not the detective: a witness withdraws (his `know` is emptied, mood afraid), a corner that
  was going to talk goes quiet, or his car is opened up in the street — each read out by Sally.
- **A CREW CAN BE FINISHED.** A guilty verdict against a man who holds one of a crew's three seats
  sends that seat to Kestrel State (`state: "prison"`, written to the notebook). All three inside
  and the crew collapses: every turf opened, crews and dens cleared, cash zeroed, "KINGS IS
  FINISHED" on the banner and double rival juice. Verified end to end.
  **Watch the anchor:** the seat block first landed in the *name-him* close path (where `guilty`
  does not exist) because `C.stage = "done"` appears in more than one ending. It lives in
  `trialVerdict` now. Also guarded all three `g.book.cases` writes — `g.book` is not always built.
- **TRAFFIC LIGHTS.** One clock for the city (`LIGHTS` / `lightPhase`): north-south green, amber,
  east-west green, amber. A car reads the phase for its own axis, finds the stop line at the next
  junction (`idx * PITCH - dir * (halfW + 26)`) and brakes into it; on amber it only stops if
  there is room. `drawLights` puts a head on each of the four approaches with red/amber/green
  lamps and a glow on the live one. Measured at a downtown junction: up to four cars holding on
  red, moving on green.
- **TRAFFIC WAS A GHOST.** Traffic never tested buildings — a swerve, a shunt or a turn could put
  a car through a wall. Every non-bus, non-parked car now runs `collideBuildings(v, 20, true)`.
  Measured: 0 of 95 cars inside a building.
- **PILE-UPS CLEAR THEMSELVES.** A car stopped under 12 units/s for 10 s that is NOT at a light is
  recycled if it is out of sight (900+ away) or shoved back into motion if it is not. The wild
  swerve from a hard bump was also cut to a third — it was driving cars off the road.
- **RAMPS ARE CLEAR OF THE STREET.** The foot was `halfW + 6`, which sits on the pavement and bled
  the apron into the cross street; it is `halfW + SW + 18` now. All 96 ramps land at least 82 units
  beyond the kerb.
- **THE BOARD** (`pd_warboard` in the task force room, BOARD button): every crew with turfs,
  houses and heat, the seats Malcolm has learned in blue and the ones in a bed or a cell in red,
  plus which corners will talk and which houses are wide open. The war had no window into it.
- **AUTHORED SEATS.** Every crew's three names are written now (`WAR_GANGS[].names`) — Cole/Gaines/
  Pryor, Halleran/Malloy/Strand, Rizzo/Foss/Amato, Vescari/Novak/Castellano, Fong/Chen/Park,
  Brennan/Doyle/Kane, Moreno/Quintana/Vargas, Bracken/Tillman/Bracken, Hollis/Keller/Voss,
  and Gomez/Vaskov/Gomez. `warName` only fills a gap now.
- **COP PLATES.** `cop_<m|f>_<mask|pale|tan|brown|dark>` drawn by `drawCopPlate` off the officer's
  roster race and sex (mask is the uncoloured base for future tinting). Roster rest is **5 minutes**
  (`COP_REST`), and with 448 names the force cannot be emptied.
- **CSU GIVES A NUMBER.** The tech reads out the victim's actual height and compares it to the
  perp's card in inches (`hgtIn`), so "taller by a good three inches" can be checked against a man.
- **Malcolm can shoot while she drives:** `strike()` allows a shot when `g.auto` is running and he
  is armed, and TGT/FIRE appear in the driving controls.
- **The manor** was replaced with the walled version, its cars and gates painted out with sampled
  cobbles, resized to 470x330, and **THE GOMEZ MANOR** is a fast-travel stop on his terminal.
  **Watch the load order again:** registering `COP_PLATES` art above its declaration killed the
  whole game at boot — the same trap as `CT_KEYS`. Registration goes UNDER the list.
- **THE ROSTER.** `COP_POOL` weights a real department (white 46, black 24, latino 22, asian 8) with
  first and last names per group; `copName()` draws an unused one and `copDown()` hands it back and
  rests it for `COP_REST` (30 min) when that officer is killed or hurt, with Sally reading it out.
  Names hang over the station's uniforms, the officer holding a scene and anyone riding with
  Malcolm (who now carry 8 hp and are dropped from the squad when they go down).
  **Art still to come:** uncoloured cop bases to tint per group (prompt given).
- **Break room:** the GENERIC furnisher was adding a freezer, cooker and locker on top of the
  station's own units — that was the white unit on the left. They are stripped from that room and
  the snack machine and fridge sit in opposite top corners. **Desk Sgt. Lee** stands behind his
  counter facing the door (he was in front of it, facing away).
- **Music:** a track is looked for in `assets/`, then `assets/music/`, then `assets/audio/`.
- **THE GANG WAR IS `g.gwar`, NOT `g.war`.** `g.war` was already the Lion's storyline flag AND is
  written by `collectSave` — the simulation was sitting in that slot, so a save would have shipped
  the whole board into a number field and a load would have turned the war into `0`. Renamed
  throughout before it ever bit.
- **THE SAVE NOW CARRIES THE DETECTIVE.** `collectSave`/`applySave` also hold juice, rivals, the
  notebook's notes and closed cases, the captain's praise, the car's armour and boost, and the war
  — turfs, crews (ranks only), dens, heat, snitch/bust flags, every gang's cash, upgrades and
  seats with what is known. The war is rebuilt by `warInit()` and the saved numbers laid over it,
  so live references (the man on the corner) are never serialized. Verified across a real page
  reload: juice, cash, turn 120, four Kings turfs, 53 dens, the note, the rival and a known seat
  all came back. DETECTIVE MODE already calls `G.loadFn()`, so it picks the save up on entry.
- **Fixed:** Ramos's ANY IDEAS text was cleared as the panel was built, so the next redraw wiped it
  — it stays until he answers; **cards indoors** (`nearCiv` refused while `g.inside`, so an indoor
  scene could not be worked); **where she parks** — the scene drive target is the door plus 140
  for an indoor scene, and she stops `DET.park` (150) short of any address instead of on top of it.
- **THE GOMEZ FAMILY, OLD TOWN.** `ct_gomez` (the walled house with its courtyard and fountain)
  stands on the circle as mark `ot_gomez`, kind `gomezhouse` -> floor `gzhouse`: hall inside the
  door, parlour off it, Hector's office at the back, on the court's wood. `GOMEZ` seats five in
  their rooms — **Hector** (older brother), **Vaskov** (underboss), **Arty** (younger brother),
  **Theo** and **Leo** (Arty's sons) — with four crew (`GOMEZ_CREW`, yt_gm1-4) standing about, each
  with portrait and plate. Talking: ASK ABOUT THE FAMILY, PRESS HIM (25% he lets a hidden seat slip,
  which goes in the notebook), SAY A NAME YOU'VE GOT.
  **In the war** their seats are the real names, and their two traits are live: `quiet: 2` (heat
  rises slowest on their ground) and `patient` (they only attack when already pushed — measured
  over 200 turns: 4 turfs, heat 15 against other crews' hundreds, 2 attacks).
- **THE PRODUCT.** `dr_stone/leaf/diamond` and `_bag` variants in assets/drugs. A wide-open house
  now shows the bag of what it sells hovering over its turf with a "<DRUG> HOUSE" label
  (`drawBustMarks`), the bust payout scales with what was seized (`WAR.income` x level), and the
  seizure goes in the notebook: "BUST: <street> -- STONE, LEAF off KINGS, $400 off the street."
- **THE WAR REACHES MALCOLM.** Each gang has three seats (`WAR_SEATS`): the BOSS is the name the
  city already knows (from `LEADERS` — Andre Cole, Torque Halleran, Don Matteo, Sal Rizzo, Mrs Lily
  Fong, Declan Brennan, Estela Moreno, Del Hollis, Curtis Bracken), the UNDERBOSS and CAPTAIN are
  generated by `warName` and hidden until somebody gives them up. A hit can put a seat in the
  county hospital for `WAR_HOSP` turns, and a gang with two seats away attacks far less.
  **The snitch** stands on his corner (`nearSnitch` / SNITCH button) and names a seat, which goes
  in the notebook for good. **The bust**: a wide-open house can be hit with SWAT for
  `JUICE.cost.swat` — it takes the dens, the crews and $4k off the gang, pays cash and juice, and
  60% of the time turns up another name.
- **THE NOTEBOOK HAS PAGES NOW.** Written pages are built into a stack — the case in sevens, then
  WHAT HE'S BEEN TOLD (snitch notes, `bookNote`) — and the ‹ › arrows walk all of it before the
  name pages. A long case used to spill off the bottom of one page and the oldest lines were lost.
- **Villain jobs no longer fire in detective mode** (`startMission` returns early): they were
  taking over the screen and moving the player mid-case.
- **THE WAR (background RTS, core running).** The city is cut into TURFS of 4x4 blocks
  (`WAR.side`, 8x8 board on N=30); ten factions (`WAR_GANGS`, Gomez holding Old Town) start with
  three turfs each. Every `WAR.turnEvery` (22 s) the dice set the order and each gang takes ONE
  action: claim open ground, recruit a thin turf, ATTACK (four flavours in `WAR_ATTACKS` — hit the
  crew, bomb a den, car bomb, sweep the block), open a DEN, PLOT (intel, better odds), DEFEND,
  UPGRADE (crews / ranks / quiet) or sit. Crews are rank 1–4 (`warRank`, a four is rare). Dens pay
  per second by drug (leaf 20, stone 30, diamond 45, sky 100 × level), turfs pay `WAR.street`
  either way, crews cost upkeep, and nobody borrows. Heat rises with selling and attacks: past
  `heat.snitch` somebody on that turf will talk, past `heat.bust` a house is wide open — and if
  Malcolm doesn't go, **the police raid it themselves** after `raidAfter` turns. Taking a turf
  takes any distro standing on it. A wiped faction returns after `comeback` turns on its old
  ground. `__ironlion.war()` dumps the board.
  **Balance history:** unchecked DEFEND ran everyone $50k into the red; then one crew snowballed to
  $5.4M while the rest had no income (fixed by street income, a cash floor and police raids); then
  three factions were wiped permanently (fixed by comebacks). Verified to turn 1000: all ten alive,
  turf and distros changing hands, no errors.
  **Not yet built:** the Malcolm-facing ends — the snitch to talk to, the SWAT bust, and hidden
  hierarchies to investigate.
- **THE SCENE, PROPERLY DRESSED.** Three witnesses who saw something and 3–8 onlookers who saw
  nothing, all placed on a ring OUTSIDE the tape (`CASE.tapeW/tapeN/tapeS` drives both the cordon
  and where people may stand); only the officer and the tech are inside it, and the tech now works
  at the markers instead of in among the witnesses. **The tech talks**: cause and time of death on
  a body, or the point of entry on a break-in — once, into the notebook, worth juice.
- **SALLY IS THE RADIO, RAMOS IS THE CASE.** `radioSay()` queues what the station finishes (lab
  results, the morgue's ID) and `stepDispatch` only reaches him `atTheRadio()` — in a car or within
  150 of his own. Her own lines are station business: holding, court, calls over the wire. The
  case thinking stayed with Ramos (ANY IDEAS?).
- **INDOOR SCENES.** A break-in, a burglary ring or a bank job happens INSIDE: `startCase` finds a
  house/walkup/apartment (or the bank) near the chosen spot and puts the scene in a room of it
  (`C.inB`, `C.inF`). Everything that draws or steps the scene — tape, markers, bodies, talking,
  pickups, `atScene` — follows it indoors; the CSU van parks at that building's door.
  **Watch for:** `const atScene` was declared BELOW its first use in `stepCase` and threw every
  frame until it moved up.
- **OLD TOWN, dressed.** Five landmarks (church, market hall, Red Lion, pawnbrokers, old civic
  building) and eight tenement plates placed as marks across the quarter, cobbles (`tx_cobbles`)
  under the whole district at 128 units a tile, the memorial on the green (`ct_ot_monument`), and
  street furniture round the circle (lamps at the kerb, benches on the green, bollards, a fountain,
  pigeons). **The circle moved from the (3,1) crossroads to (3,2)**: `FWY_H` runs the North Spur
  east-west along row 1, so the elevated deck flew straight over the roundabout and hid it.
- **CAPT. MULCAHY** replaces the generic captain: his own plate and portrait, in his office on the
  street floor. REPORTING IN reads your record back at you (closed, cold, and the rival who beat
  you) and pays 10 juice the first time you are ahead; WHERE I'M AT tells you the next thing —
  including "you've got a man in my holding cell who hasn't been advised".
- **Music:** a track now falls back to `assets/music/<name>.mp3` if `assets/<name>.mp3` is not
  there, so det.mp3 plays from either place.
- **OLD TOWN (the skeleton).** The `northend` zone (cells 0–5 x 0–2) is Old Town now, and its
  centre is a **roundabout on the crossroads at SX(3), SX(1)**: `OLDTOWN` = rOut 600, island 330,
  two circulating lanes. Cell generation drops any building whose box comes within rOut+30 of the
  centre, `drawRoundabout` lays carriageway, kerbs, a dashed lane line, the green and a monument
  (`ct_ot_monument` when the art lands, a drawn obelisk until then), and **traffic circulates**:
  a car that enters the disc takes a lane, goes anticlockwise, and is put back on whichever street
  it wanted at the exit (straight on, either turn, or back the way it came). Verified in the game:
  four cars circling on both lanes, none on the island, no buildings inside the circle.
  Still to come: Old Town's own roof plates, cobbles and landmarks (prompts given).
- **JUICE** (never call them points): earned by the work — evidence 2, a statement 2, evidence in 3
  each, rights 2, an arrest 10, a confession 25, a conviction 40, a rival 60, a raid 15, brass 1 —
  and spent on the department: a detective riding along 25, SWAT 30, cars 6/12/18, EMS/fire 5,
  a rush at the lab 10, a car off the pool 12, armour 20, a boost 15. Shown under the title.
- **THE HOUSE.** `STAFF`: **Sally O'Connell** at the dispatch desk on B1 (facing it), **Sgt. Hawk**
  in the evidence room (hand bags in here instead of to the beat cop, or ask what is where),
  **Det. Miller** in the CSI room on B1 (reads what each piece will tell you; RUSH ONE for 10
  juice), **Ofc. Kowalski** in the B2 garage (patch the car up, fill every tank, armour — halves
  `g.car.tough` — a boost through the existing `boost` term, and a car off the pool; the radio
  carries the car and the top-off too). **Sally's calls**: `stepDispatch` puts her portrait on the
  screen every 100–220 s with a tip, a job or something she should keep to herself, and Ramos has
  something to say about it.
- **THE STATION REBUILT.** B1 is task force + dispatch desk, four offices along the top, three
  cells, and along the bottom — opposite the rest — **Delgado's office, Ramos's office and the CSI
  room**. No filing cabinets in the hall, the front desk pulled back off the door, stairs against
  the west wall (208 from the door, not in front of it), and the lift off the captain's wall (the
  default candidate order put it inside his office; `b.pd` tries the hall's west wall first).
  Detectives can be hired to ride along for juice and are drawn from their own plates.
  **Delgado was re-cut** — his old plate kept its legs, so drawYouth painted a second pair under it.
- **Fixed: after Ramos drove, he could not get into ANY car.** Blocking the Lion's car in detective
  mode blocked the slot, and the car he drives lives in that slot — now only blocked while it still
  wears the Lion's own skin.
- **RIVALS.** A guilty man acquitted at trial goes on file (`g.rivals`, `makeRival`): same card,
  same idSeed, same face. `ESCALATE` then `BIG_CRIMES`: assault → serial assault → serial killing;
  mugging/hold-up → armed robbery → bank job; break-in → burglary ring → armed robbery. 60% of new
  cases are a rival's (`RIVAL.chance`), and his are bigger: 5 evidence, 3 lookalikes, 2–3 stops,
  prints always on file, a bank job's scene at a real BANK_CELLS bank, and pay ×1.6–2.8. Convict
  him (verdict or confession) and he comes off the board — "RIVAL DOWN".
  Verified end to end: a lost trial put Carroll on file at serial assault, her next case arrived as
  SERIAL ASSAULT with 8 pieces, and convicting her paid $714 and cleared her.
- **A FULL CASE WAS PLAYED, CLUE TO CONVICTION,** and it found three real faults:
  **(1)** a lead who took three strikes was silent FOR EVER, which could strand a case with no way
  down the trail — they cool off after 90 s now (calmer, and a notch less hostile), the panel says
  how long, and Ramos's tip points at Delgado meanwhile;
  **(2)** the $20 approach was offered with no money in his pocket and did nothing when tapped —
  an endless no-op on a lead you could only buy; it is hidden unless he can pay;
  **(3)** a rival's prints came back "never been booked".
  Also: trail stops may no longer share a street name with each other, the scene or the hangout.
- **THE RIGHTS.** An arrest sets `C.arrest.rights = false` and the objective becomes READ HIM HIS
  RIGHTS. **RIGHTS** at the cell reads `MIRANDA` a line at a time. **No interview until they are
  read** (`startInterro` refuses, Ramos says so), and at trial an unadvised defendant costs 15 on
  the jury and adds a `rights` attack the defence can run — standing firm on it costs you anyway
  ("You can't answer that one, and the jury watches you not answer it"). Verified on one fixed
  cast: 33 with rights read, 18 without.
- **EXHIBITS ON THE TABLE.** `g.trialRun.shown` collects what has been presented, and the court's
  evidence table carries a card per exhibit along its FRONT edge with the item's own art
  (`EV_ICON`, one map now, shared with the scene markers) and an EXHIBITS · n label. Dropping the
  icons on the table itself read as nothing — that art already has bags painted on it.
- **THE COURT.** THE COURTHOUSE (14,5) is a real building now: `kind: "courthouse"`, one storey,
  south door, `courtroom` floor on `tx_court_wood`, 20 fittings laid out as a courtroom (bench and
  flags north, witness box beside it, stenographer, jury east, evidence table and easel west, two
  counsel tables, the rail with its gate, pews to the door). `courtSpots` reads the placed props
  for where people stand; `courtPeople` (jurors, gallery, bailiff) and `courtCast` (judge,
  prosecutor, and in a trial the DA, the defendant and his lawyer).
  **Getting there:** at the cell, QUESTION or **TRIAL**; a perp who lawyers up in the interview is
  sent to trial rather than walking. **On the stand** (STAND at the witness box): six questions,
  the People leading and the defence attacking, each on a clock (timeout = "I don't recall", −10).
  Exhibit that matches the topic scores `worth(e) * 0.7`, wrong exhibit −8 (×the defence's missX on
  cross), STAND FIRM +7 on a procedure attack, +2 where you hold nothing, −3 where you did.
  Guilty at 60. `JUDGES` / `AAGS` / `DEFENSE` each bend the maths (O'Connell discounts weak
  evidence, Banks favours witnesses, Voss starts you 15 down; Ellison boosts forensics, Ruiz boosts
  cross; Sterling costs the jury 12 and doubles down on cross, Rossi cuts the clock to 10 s).
  **Only money gets Sterling** (`richDefendant`: a crew's man, or 12% of citizens).
  **Fixed:** the court art registered BEFORE `CT_KEYS` existed — that threw on load, so the whole
  game was dead until it moved below the lists; the trail's lead items had no `EV_TOPIC`, so the
  defence asked about `undefined`; and at full worth one strong exhibit pinned the jury at 100 by
  the second question. Balance now: answering every question right convicts 7 of 8.
- **THE GUMBALL.** `GUMBALL.cars` — Malcolm's, the four detectives' and the plain unmarked — carry
  a magnetic dome on the roof (drawn in the unit-number pass): dark red parked, and when he taps
  **SIREN** in one, a pulsing red dome, a turning beam and a red wash on the road, the existing
  two-tone `sirenVoice`, and traffic within 480 ahead in his lane drops to 40 to let him through.
  It switches off when he leaves the car. **`vehModel(v)` = `v.m || v.skin`** — the car he is
  driving is the Grand National's body wearing the other car's `skin`, so anything that asks "what
  car is this" of his vehicle must read the skin.
  **Fixed while doing it:** in detective mode E put Malcolm in the LION'S car (`mountNearest`'s
  `carOK`/`motoOK` now skip the Lion's car and bike when `detMode`); taking his own car no longer
  counts as a theft, and `g.detCar` follows him into the driven body so the trunk and radio find it;
  and RADIO / SIREN / RAMOS were only in the on-foot button set — they are in the driving set now.
- **NEXT: THE COURT SYSTEM** — testimony minigame for the bigger cases; three judges, three
  prosecutors and a DA (prompts given).
- **THE SQUAD ROOM** (`SQUAD4`): Okafor (homicide, green car, office 0), Morrow (vice, black car,
  office 1), Hayashi (forensics, blue car, office 2), Delgado (robbery, brown car, task force room),
  on B1 with portraits (`pt_*`, square-cropped with their round frame) and hip-cut sprites (`yt_*`).
  Cars cut off asphalt with GrabCut and filled to their convex hull (a black jacket on the black
  car's roof cut a hole otherwise), turned nose-up. **The lot now:** their four cars, one cruiser
  (01), Malcolm's car; the rest of the fleet is in B2. Talk to one → portrait panel; **HELP ME WITH
  THIS ONE**, once each a case (`C.helped`): Okafor −200 s off a John Doe's ID or one fact about the
  perp; Morrow lifts every witness and trail person a notch toward cooperative and clears their
  strikes; Hayashi cuts pending lab clocks to 35%; Delgado `revealNext`. Verified each in the game.
- **CASES ARE A TRAIL.** `C.stops`: one to three places between the scene and the man
  (`LEAD_KIND`: bar ← matchbook, address ← torn phone-book page, pawnshop ← pawn ticket), each with
  a `lead` person who knows `next`, and half with evidence on the ground. The scene's lead item
  matches stop 0. `revealNext(C)` is the one way down the trail — the lead item, the stop person,
  fake bills at the lab, the coroner's ID, the beat cop — and after the last stop it sets `C.lead`
  (the hangout). A stop person has nothing to say until the trail has reached them. The objective,
  Ramos's driving and the **blue arrow** (`drawCaseArrow`) all follow the current stop.
  Measured: 17/13/10 of 40 cases have 1/2/3 stops.
- **RAMOS: ANY IDEAS?** `ramosTip(C)` — the first undone thing, in the order a detective does them.
- **BRASS.** `fireBullet` drops a casing (`g.casings`, 160 cap, 5 min, per building and floor).
  In detective mode walking over a stranger's casing during a case bags ballistics; police brass
  is not evidence.
- **The objectives panel folds** — the ▾ HIDE / ▸ SHOW OBJECTIVES tab under the title.
- **The station's people:** five uniforms and the CAPTAIN on the street floor, one on B1
  (`D.staff`). RECRUIT takes up to two (`g.squad`): they follow, ride along, shoot hostiles;
  DISMISS sends one back to his post.
- **Cop cars:** `wreckReaction` returns early for any police car — no civilian bailing out of a
  cruiser, and in detective mode no heat for bumping one. **Civilians hit hard** now: 15% keep going,
  15% freeze in the lane (`unfreeze`), 25% floor it and swerve (`wild`), 17% get out swinging (a
  `fight` bailer who punches Malcolm and is in combatTargets and hostiles), the rest run.
  Measured over 100 bumps: 33 run / 19 floor it / 18 keep going / 16 fight / 14 freeze.
- **LATER, AS DONNY PLANS IT:** a court system with a testimony minigame for the bigger cases;
  multi-act cases (a serial killer, a serial assaulter); Malcolm buying a dog.
- **THE INTERVIEW ROOM (detective mode).** Naming someone to Ramos is an ARREST: `C.arrest`, the
  person taken off the street and drawn in the first B1 cell, `C.stage = "custody"`. **The stage
  check that moves a case to "name" must only fire from "open"** — it ran every frame and pulled a
  custody case straight back. QUESTION at the cell starts `g.interro`: the bar starts at the sum of
  held evidence (15 each, 30 for DNA or prints on file, cap 70; an innocent starts near 5) and
  drains 3.5/s. He makes claims keyed to a topic (there / seen / weapon / clothes / car / money);
  evidence of the same topic adds its weight, anything else −10, and everything is −10 against an
  innocent; PRESS/GO EASY swing by his attitude. 100 = confession, pay; 0 = he walks (and Malcolm is
  told who it was). Verified both ways in the running game.
- **THE DAILY GRIND.** Three coffee shops (9,11 beside the station, 12,9, 5,6) — marks with `id`
  (three share one plate, so the building key is `mark_<id>`), a plate with both lots, `clear`.
  `dgfloor`: yellow tile (`tx_dg_floor`), 19 fittings placed walk-out, **no stair** (every plan got
  one in the middle, even a single storey). `dgPeople(b)`: two staff (`yt_dg_*`), four customers,
  two cops on a break, depth-sorted and solid, with lines.
- **MALCOLM'S TERMINAL** (`pd_computer`, his office on B1 — four offices there now, his has a
  nameplate and he starts in it): FAST TRAVEL (station, morgue, each Daily Grind, the scene and the
  hangout during a case) and CASE FILES (the open case and the last eight, each readable).
- **Scenes:** chalk outlines (`cs_chalk_1..5`); a closed scene stays taped for 90 s with its van;
  witnesses, officer and tech are solid and drawn in the depth-sorted pass (they were painted over
  Malcolm). **Wall art** (`wallArt`) hangs across the room's top wall and is drawn after the walls.
  **The lot:** the front fence is paved over; the west fence is solid (`b.fences`).
  **Cars:** Malcolm's 0.22, cruisers 0.30, SWAT van 0.16 in CARTOUGH. **Music:** `det` →
  `assets/det.mp3`, plays throughout detective mode (the boss track still overrides it).
- **SWAT, LT. CARVER, THE BERETTA, MALCOLM'S CAR.** The SWAT van (`pd_swatvan`), fire engine
  (`pd_fire`) and Malcolm's black car (`pd_malcolm_car`) are `PD_CARS2`, cut and turned nose-up.
  SWAT is Carver (`yt_carver`) plus three of eight `yt_swat_*`, all through drawYouth (hip-cut,
  painted legs, rifle shown while firing). Within 90 of Carver: **CARVER** → ON ME, RAID <target>,
  SNIPER ON A ROOF, SET A PERIMETER, STAND DOWN. Raid target = nearest distro with a building
  within 2200, else the nearest door; the team stacks on the door, fights whoever is outside, then
  breaches (one man inside down every 0.9 s) and takes the distro OFF THE BOARD — no heat, it is
  the department. Sniper: one man on the nearest roof, drawn with the roofs (`drawSnipers` after
  the neon), reach 820, damage 6. Perimeter: a 260 ring held where it was set.
  **The Beretta** is its own weapon, `beretta` (WPN_STAT, WPN_SCALE, WPN_AMMO 12), carried by
  Malcolm and Ramos and the trunk's first slot. Its plate is `wp_beretta` (muzzle left). **Fixed:**
  a weapon not on the atlas used to draw the WHOLE ATLAS in the hand — standalone plates now draw
  on their own, and the HUD shows the plate when there is no side-on icon.
  **Ramos's walk:** drawYouth wants a plain HEADING in `bang`; she had a rotation meant for another
  sprite, so every time she stopped she turned the wrong way. And she started and stopped on one
  distance line on alternate frames. Now: walk past follow+28, stop inside follow, speed eased,
  facing her movement or, standing, the way he faces. Verified: no flips, no drift.
  The badge (`ui_badge`) is on the DETECTIVE MODE button and the radio panel.
- **MALCOLM'S KIT (detective mode).** `DET` holds the numbers.
  **Ramos** (`g.partner`): follows at 64, closes faster when far, snaps to him through doors and
  stairs, gets in any car he takes within 420 and out beside it, and shoots `hostiles()` (hostile
  crews, alerted guards on his side of the wall, thugs) with a service pistol. Friendly fire is
  `fireBullet(..., byPlayer = true)` so it hits their people and never him. She is not killable.
  Report to her anywhere now — `contactSpot` is wherever she is. **She drives:** RAMOS in the car →
  THE SCENE / the hangout / THE STATION / THE MORGUE; `roadRoute` is two turns along street lines
  (cell boundaries) to the corner nearest the target. While she drives, `collideCircle` is skipped
  (a stopped car in the lane held the car in place for good) and the car's own velocity is zeroed
  (it was being moved twice — double speed); she drives at 300 and the speedometer reads `g.autoSpd`.
  **Trunk:** within 70 of the unmarked car's rear — service pistol, shotgun, rifle.
  **Radio** (in a car or at his): 1/2/3 cars of two officers, SWAT (armoured van, four, harder
  hitting), EMS (heals him on arrival), FIRE (knocks down burning buildings within 700), STAND
  DOWN. Units drive the road route to him, get out, hold a ring round him for 150 s and shoot
  hostiles; cars are numbered R1–R9. **No fire-engine art** — drawn red with a ladder; SWAT are
  cop sprites with a dark helmet until there is SWAT art.
  **No ID on the victim:** 35% of cases where somebody got hurt. The body goes to the morgue, and
  the coroner's clock (480 s) runs; DNA −180, prints −90, each witness statement −45, walking up to
  the coroner once −150. When it lands: the name, age and address, and a lead to the hangout.
  Verified in the running game end to end, every piece.
- **THE MORGUE, under the hospital.** The hospital is 5 floors with `entry: 1` now — index 0 is
  `morgue`, reception moved up to 1 (floorKind shifted; nothing else keyed on hospital floor
  numbers). Rooms: cold room (west, both drawer walls, a gurney), autopsy (the hub, both tables,
  lamps, sinks, scales, tray, cart, a covered gurney), the coroner's office and `mgrecords` (both
  X-ray boxes) along the south. **Not "records"** — that name is an existing room case that fills
  with filing cabinets. The south strip is 45% of the depth: at a third it was 76 deep and the
  desk had nowhere to go. All 18 pieces placed, every room reachable. The coroner stands by the
  table (`coronerAt`, `drawCoroner`) and says a line when you come near.
  **No lift in the hospital:** one was added and landed unreachable on all four upper floors, so
  a ride could strand you; the stairs reach every floor.
  **Pre-existing, not fixed:** on the hospital's upper floors the reception desk, the ER, the store
  room and two ward bays are sealed off — identical before this change.
- **IN DETECTIVE MODE YOU ARE MALCOLM.** `g.detMode`: the player is drawn off `yt_malcolm` through
  drawYouth (same legs and arm swing as everyone), starting on Malcolm's own spot; the Malcolm NPC
  is not drawn. **Ramos is your contact** — `contactSpot()` is her desk on B1, or the scene while a
  case is open (she is out there) — and the panel carries her name, portrait and lines ("Dispatch
  has one for us, Malcolm."). The objective says BACK TO RAMOS. The Lion's buttons (LION,
  MASK/SUIT, HOOK/JUMP, ROAR) are hidden; **their keyboard keys are not blocked yet.**
  Outside Detective Mode nothing changed — Malcolm still stands in the task force room.
  Verified: clicked the real button, Ramos's panel, the hidden buttons, a full case closed by
  naming him to Ramos at the scene; the normal-mode case still closes with Malcolm.
- **DETECTIVE MODE on the start screen.** Under BEGIN/CONTINUE. Loads a save like BEGIN, skips
  the den, sets `g.detStart`; `stepCase` then puts you in plain clothes (`g.plain`) beside Malcolm
  on B1 with his case offer open. The camera and `g.insideT` are set there too — Malcolm's panel
  pauses the game, so neither would ever catch up on its own. Verified by clicking the real button.
- **B2 IS YOUR GARAGE PAINTING** (`pd_b2`). Drawn after the room floors and BEFORE the props
  (after them, it buried the parked cars). `PD_B2.solid` — pillars, tool chest, tyres, pump,
  cabinet, the painted car, lift posts, workbench — become invisible `gy_block` solids; the stair
  sits on the art's stairs; the fleet parks in the art's empty bays. **The ramp has two
  positions now:** `rampPos` (0.83, where the canopy is outside) triggers it, `rampIn` (0.504, where
  the art draws it) is where the car comes down and the B2 wall gap is.
- **Pieces lifted off your two station scenes with GrabCut** (`PD_KEYS2`): vending, snack
  machine, two fridges, round table set, captain's desk, trophy case, flag, podium, chalkboard,
  briefing chair rows, a single chair, filing cabinet, long bench, the evidence window. They
  furnish the street floor now. The captain's desk has to be placed FIRST, top middle — the lift
  takes the east wall and it found no room after the flag and trophy case.
- **The station's people** (cut at the belt, `yt_sergeant`, `yt_csu`, `yt_coroner`): the sergeant
  behind the front counter, the CSU tech beside the van at every scene. **The coroner is
  registered, not placed** — waiting on the morgue.
- **THE STATION (`ct_precinct`, 8,11).** A MARK with a new field, `plate`: where the building sits
  inside the art. `b.plateRect` is the whole plate in the world; `drawMarkGround` draws it with the
  ground (the lot is walked and parked on) and `drawMarks` draws it again clipped to the building,
  as the roof. `clear` clears the whole plate rect, so the generated precinct is gone.
  3 floors, entry 2: **B2 `pd_garage`** (fleet props, ramp chevrons, the ramp a gap in the south
  wall at `rampPos` 0.83 under the canopy — `nearTowerRamp` now serves ANY `carpark` building off
  `rampSide/rampPos`), **B1 `pd_lower`** (task force room, two offices, four cells — Malcolm and
  Ramos live here now), **street `pd_main`** (lobby with the counter, briefing, evidence, captain,
  break room, lockers, bathroom). Lift on every floor. Furnished by a place-and-walk-outward helper.
  The street door is the south face's west end; the two stalls in front of it stay EMPTY — a
  cruiser there sealed the entrance. Walk test: all three floors, every room, door/stairs/lift/ramp.
  The break room had to go from 0.45–0.60 to 0.40–0.62 wide: at 77 units with a table in it,
  it sealed the evidence room, the captain and the lift.
- **Numbered police.** Five cruisers (01–05) and the unmarked car park in the plate's stalls
  (placed off the plate's own pixel coordinates). **Parishes:** each district (`zoneOf`) gets a
  number the first time a car is assigned there; `spawnTraffic` turns 22% of new traffic in a
  parish into its beat car while it has fewer than five out (`g.beats`), unit = parish + slot
  ("34"). Responding cars take the next free number where they arrive. Numbers on the roofs,
  turned with the car. Verified: parishes numbered, never more than five out.
- **Notebook on the right, controls on its top edge** — ‹ › CLOSE. No tap sheet over anything:
  a book-sized one still sat over the button row. Verified with real taps: every HUD button is the
  top element while the book is open; both arrows and CLOSE work. Text moved below the binding.
- **Scenes use the kit:** your tape round the four sides, a numbered tent beside each piece drawn
  as what it is (casings, blood, glass, hanky, tread, shoe prints, matchbook, bills), the weapon
  left where it fell, and a CSU van at the kerb that leaves when the case closes.
  Malcolm's portrait is in his dialogue (`assets/heroes/pt_malcolm.png`).
- **The morgue sets are cut and registered but not placed** — the coroner needs a home.
- **THE NOTEBOOK FROZE THE GAME.** The page-turn sheet covered the whole screen, BOOK button
  included, and a tap in the middle did nothing — open the book and nothing answered. The middle
  third now shuts it. Verified with real taps: open, middle closes, BOOK works again.
- **DETECTIVE MODE, v2 — cases break down into EVIDENCE, WITNESSES and THE BEAT.**
  `EVIDENCE` types with lab clocks in seconds: DNA 600, prints 300, fake bills 90, ballistics 50,
  fibres 35, tyres 30; shoe print and matchbook read on the spot. Each crime (`CASE_CRIMES` —
  named so because the component already has a `CRIMES`) has its own pool; a scene gets 4, always
  one that points somewhere. Walk over a tent: BAGGED, and Ramos (out at the scene while a case is
  open, speech bubble + notebook line) gives her read. Hand the bags to the BEAT COP (TALK →
  TAKE THESE IN): they go to `C.lab` and develop on their own clocks; results land in the notebook.
  Prints are on file 55% of the time; DNA always names him, slowly.
  **People have traits** (`rollTraits`): mood, attitude, influence (Sky — likelier where
  `skyPresence` is high — or drink) and a look (rough/professional, purple-stained fingers, scars,
  a split lip on the victim, blood/scratches/bruised knuckles on a violent perp). `willing()` =
  attitude base + mood + influence − 10/strike, and each APPROACH (go easy, press, $20, badge)
  shifts it by mood and attitude. Success spends one of the facts they know (read off the perp's
  card); failure is a strike and can make them worse (pressing the distraught, badging the evasive).
  Three strikes and they are done. Drunk or high witnesses give a wrong fact 45% of the time and
  Ramos flags it. The beat cop always talks: time, direction, and what the beat knows (the
  hangout street). Suspects: decoys have alibis that hold, the perp's do not.
  The hangout is always ≥1350 away and never on the scene's own corner (30/30 checked).
  Verified in the running game end to end: 4 bagged, cop statement and hand-in, 3 interviews,
  lab results, alibis, named, CASE CLOSED.
- **THE UNREPRODUCED GRADIENT CRASH IS FIXED** — caught at last. `drawHeadlights` builds a radial
  gradient per traffic car, and createRadialGradient THROWS on a non-finite number, so one car
  with a NaN position for a single frame took the whole frame. It runs before the NaN sentinel
  scrubs traffic, so the sentinel could never save it. Non-finite cars are skipped now. Six clean
  runs of the test that used to show it about one run in ten.
- **363 FACES ON 13 PAGES.** Six civilian pages and six gang pages joined `id_faces_1`, all in
  assets/id/. **Sex was labelled by eye; TONE WAS MEASURED** — the lit side of each cheek, skin
  pixels only, banded light/mid/deep — which is why the cards agree with the bodies in the street.
  Each cell of each sheet was re-cut to drop its own sheet border, or a teal or magenta stripe
  ends up on the licence photo. `"-"` marks an empty cell and is never handed out.
  Pages carry `gang: true/false` and `facesFor(sex, tone, gang)` keeps crew mugshots off ordinary
  licences; `identOf` sets `gang` from `p.gang || p.distroGuard || p.crew`.
  Verified in the running game: 106/106 pedestrians got an exact sex+tone match, 45 distinct
  faces, none from a gang page. Pool depth: m light 179, f light 64, m deep 67, f deep 16,
  m mid 24, f mid 13 — **mid-tone women are still thin.**
- **Malcolm and Ramos** are cut at the hip (`yt_malcolm`, `yt_ramos`, assets/heroes/), so drawYouth
  gives them legs and a swinging arm. Registered and loading; **nothing places them in the world
  yet** — that is the first job of detective mode.
- **THE NOTEBOOK.** `g.book.people` — every card you have looked at, newest first, capped at 60,
  never the same number twice, with name, sex/age/height, ID number, address and WHERE and WHEN
  you stopped him (`crossStreet`, after-dark flag). BOOK button on foot; 5 to a page, tap the left
  or right third to turn. `drawNotebook()` draws on the canvas over everything; `id_notebook` is
  a plate if it exists, a ruled page if not. **`g.book.cases` is there and empty — that is where
  detective mode writes.**
- **Faces are a MANIFEST, not a file name per sex/tone.** `ID_SHEETS[].who` lists what each cell
  of a page is ("m deep", "f light"), read across then down, so a mixed page works and a new page
  is one file plus one line. `faceOf()` picks a face that IS that sex and tone, widens to same-sex
  any-tone, then gives up to the silhouette. Verified: 60/60 identities got an exact match.
  Sheet 1 (`id_faces_1`, 6×4) is thin in places — 1 f-mid, 2 m-mid — so more pages are wanted.
  The card takes its shape from `id_card_blank`'s own aspect.
- **titleCam again, properly this time.** The earlier guard stopped NaN but not a NEGATIVE clock:
  `Math.floor(t) % 6` can be -1 and legs[-1] is the same frame error. Clamped at 0 and the index
  wrapped both ways. Three clean runs.
- **IDs.** `identOf(p)` builds a card once per pedestrian off one seed and keeps it on him: name
  (`ID_NAMES`, ordinary people — the gang pools are reserved), DOB and age, sex, height, an address
  on a real AVE_NAMES street, a number, and a face index. **`sex` and `tone` come from the body
  where the game knows it:** the procedural crowd is recoloured from CIV_SKIN so its skin is
  recorded on the pool entry (`skin`), and `civ_art_b` is the dress page (`sex: "f"`); otherwise
  they roll. Verified in the running game: tone matched the painted body 105/105, and the same man
  gives the same card twice.
  Faces come off pages by sex × tone (`ID_PAGES`, 6×4 = 24 a page, assets/id/id_face_<sex>_<tone>.png)
  with `id_card_blank` behind them. **No art needed to work:** the card draws itself and the photo
  falls back to a silhouette in his own skin tone.
  Verb: walk within 74 of somebody on foot and the **ID** button appears — he says "ALL RIGHT,
  ALL RIGHT." and the card comes up over everything; tap again to hand it back.
  `nearCiv()` and `identOf()` are what a case will use to name a face.
- **The twins' plates are art-only.** `dc_julian` (maroon) and `dc_damian` (green) were already
  registered from assets/deuce/ and read by `TOWER_WHO`, so new cuts need no code. Verified in the
  running game: both load, Julian draws on floor 6 with his name and bar.
  **Julian's plate is drawn FACE-ON, Damian's from above.** Side by side on a floor the twins do
  not match; a top-down Julian would.
- **STRAYS.** `ANIM` + `spawnAnimal` / `stepAnimals` / `drawAnimals` / `spookAnimals`. Up to 7 at
  once, spawned on a pavement 620–1500 off, culled at 2600; never indoors, in the sewer or on a
  roof. sit → amble → sit, and they run from you on foot, from any moving vehicle, and from
  gunfire (`scatter` calls `spookAnimals` at 1.2× its radius). Cats go sooner, faster and further.
  **NOT combat targets, deliberately.** Plates `an_dog_1..12` / `an_cat_1..12` in **assets/animals/**
  — registered, and until the files land each one draws as a drawn dog or cat (body, head, tail,
  four paws that move), so this ships before the art. If the cuts are named differently, the only
  change is `ANIM.dog.pre` / `ANIM.cat.pre`.
  Verified in the running game: 7 strays, sitting/ambling/running; walking up to a dog took it
  from 60 away to 209; a shot put 4 more to flight.
- **The station's stair mouths already existed** (`stairFeet`, `autoStairs` — the handoff item was
  stale). What was wrong: `nearPlatform()` named the station from 150 of the PLATFORM CENTRE,
  which is under the deck in the middle of the road. It reads the stair feet at 74 now and the
  HUD says "<NAME> · STAIRS". Verified: named at a staircase, silent under the deck.
- **TWO MORE DEUCE REGULARS AND A SECURITY PAIR.** `hx_deuce_6` (gold shirt) and `hx_deuce_7`
  (black crew, glasses) join HENCH_POOL.deuce — seven now, `PLATE_GANGS.deuce.n = 7`, so they
  come through drawYouth with legs like the rest. The hooded pair is `PLATE_GANGS.deuce.sec`
  (`hx_deuce_g1/g2`), NOT in the pool: `m.distroGuard` picks from `sec`, so the men on distro
  rings and the tower's floors are security and the street is regulars. All four cut at the hip,
  in assets/villains/. Verified in the running game: all four load; 60 street draws used all
  seven plates, 60 guard draws used only the two.
- **VANCE TOWER MOVED ONTO ITS LOT, FRONT DOOR ON THE FRONT.** At ox/oy -0.26 it overhung the
  pavement and road by 204 west and 132 north. Now ox 0.024 / oy 0.1453: the south half of the
  block, 40 in from the kerb. The plate draws its entry steps and helipad on the SOUTH edge, so the
  door is south (doorSide 2); `TOWER.back` is north and `nearTowerRamp` reads it, so the car park
  ramp is a gap in the north wall with the stalls moved to the south wall and the chevrons flipped.
  New mark flags: `clear` removes generated buildings under the footprint (the office on 8,9 —
  any distro inside one is re-sited), `lawn` turns the lot to grass with a kerb hedge, trees kept
  off the paths, a front walk and a drive (`c.lawn`, `c.lawnPaths`). Verified in the running game:
  in lot, office gone, walked in the south door to the lobby, drove in from the north to floor 0;
  all 15 tower floors walk clean.
- **Title camera NaN on Continue** — a loaded save has no `titleT`; one more title frame read
  legs[NaN]. Clock now starts from 0 when not a number.
- **FRAME ERROR `p.tgt[0]` — the carjacked driver.** Stealing a MOVING car puts its driver on the
  pavement, and he was half a pedestrian: no bi/bj/ck, no off, no spd, no tgt. When his panic
  ended, or a smoke bomb set him walking, the ped loop read p.tgt[0] off nothing every frame.
  The Flats' traffic made driven-away cars common, so it surfaced now. Fixed at the source (the
  driver is built whole), in `retarget` (fills any missing route from where the ped stands) and
  in the ped loop (a walker with no target is given one instead of throwing). Reproduced in the
  running game before the fix — 74 and 150 frame errors — and zero after.
  **Rule: a ped pushed anywhere must have tgt, off, bi, bj, ck, spd.** The loop now survives
  one that does not, but the spawn site is still wrong if it relies on that.
- **THE VANCES CANNOT BE TAKEN DOWN — for now, by decision.** `TOWER_WHO.julian/damian.untouchable`
  with `floor: 6`. Clamped with a getter/setter on the boss object's `hp`, so every one of the
  damage sites that subtract from .hp directly is covered, not just bullets. First time one hits
  the floor: "NOT TONIGHT". Tiny is still beatable and still drops the card. Verified: 500 damage
  leaves Julian at 6, never `bossDown`.
- **THE TOWER IS DECORATED.** Lobby: velvet ropes at the desk, the dark sectional and table, neon
  palm and dice on the walls. Pool deck: two bistro tables, a neon wave. The twins' floors: their
  room's sofa and table swapped to the dark set, then a sectional, TV, dining set and bistro table
  in the big room and a bed and dresser in the study, each walked out from its spot until it is
  clear of walls, furniture, stairs and doorways. Lobby, pool and both Vance floors have charcoal
  walls with a Deuce-green neon line. Floors 3–5 and the car park unchanged.
  The dark `nfd_` set is REGISTERED now (assets/nflats/, shipped in flats_cars_furniture.zip).
  All 15 tower floors still walk clean.
- **THE PICKUP DROVE BACKWARDS BECAUSE OF THE FIX FOR IT.** It was in ROTATE_180 on a centroid
  measurement that read the open black BED as a cabin. The embedded plate is nose-up. Removed; the
  loaded image, drawn beside the taxi in the running game, now faces the same way (it did not before).
  The other ROTATE_180 entries were measured the same way and are unverified by eye.
- **GUARDED PLACES FIGHT BACK.** `siteFight(S, dt)` runs every distro and every occupied tower
  floor. A site goes alert when one of its men sees you (`SITE_FIGHT.spot` 250 on the street,
  `spotIn` 330 in a room) or any of them is hurt; the whole site knows. Men on your side of the
  wall face you, close to 180, give ground inside 110, and the nearest 4 fire real rounds through
  `fireBullet` (so cars are cover and LION time works). They forget you 22 s out of sight.
  **Your rounds never hit distro guards** — updateBullets had crews, police, peds and the boss,
  not them; they could only be hurt by hand. They are on it now, bosses too, plane-filtered.
  Verified in the running game: door men spotted, advanced ~60 and fired; a player round took a
  guard 20.8 → 16.8; the inner ring fired indoors while the street ring held.
- **THE TOWER IS OCCUPIED.** `TOWER_WHO`: Tiny on floor 4 (40 hp, 5 men), Julian on 6 and Damian
  on 7 (48 hp, 6 men each), built the first time you step onto the floor and kept after
  (`g.towerSites`). Boss = plate from the Deuce cuts, name and health bar over him.
  **The twins' floors are locked** (`TOWER.floors[6,7].lock = true`) and `floorLocked()` gates the
  lift AND the stairs until **Tiny is down** (`g.vanceKey`, "he was carrying the card"). A twin
  going down alerts the other twin's floor. Verified end to end in the running game.
- **ONE BUILDING IN FIVE COULD NOT BE ENTERED.** Door position is rolled before the rooms exist,
  so a third of the city's doors landed where a room wall meets the outside wall. The shell had
  its gap and a stub of room wall stood across it: the game flagged you inside while you stood
  on the threshold, outside the walls, with the interior showing. makeFloor now cuts the lane
  through the entry door clear of ROOM walls (60 wide, WT+36 deep); the shell is never touched.
  Blocked doors across the city: 467 → 11. Walk-in test in the RUNNING game (headless Chrome,
  real React build): 5 of 68 sampled buildings stuck before, 0 after; all 36 buildings in and
  around Neon Flats enter, including the 6,14 bank that started this.
  **Test note: N = 30.** Cells at 30+ are outside the map; a harness that samples them reports
  false failures.
- **The step through a door is straight in and straight out**, not toward the building's middle,
  which for a corner door was mostly sideways into the jamb.
- **Bathrooms keep their fixtures.** The doorway pass deleted toilets and sinks on the door's wall.
  They are now shoved clear and slid along the wall to a free spot (clear of walls, furniture and
  the doorway), deleted only if none exists. City-wide, toilet AND sink: 38% → 76% of bathrooms;
  overlapping fixture pairs unchanged at 22.
- **DISTROS ARE INDOORS.** They stood at the dead centre of a lot, so any building there put the
  Chemist and the rest on its roof. `distroSite()`: the biggest ordinary building on the lot (not
  police, hospital, city hall, courthouse, bank, FIS, silo, barn), its biggest room on the entry
  floor, at a spot clear of walls, solid furniture and stairs; open ground if nothing fits.
  `distroGuards()`: inner ring (up to 6, `indoor: 1`) in the room with him, the outer rings in an
  arc on the street in front of the door. Drawn and hittable only where you are — the man and
  the inner ring from inside that floor, the door men from the street. His name shows over the
  door once found. The Wrench's move reuses both functions.
  Verified in the running game: every distro inside a building or in open ground, no guard on a
  roof, no errors.
- **The Flats' own traffic.** `NFC_M`, twelve sports cars (cut nose-left, turned nose-up at cut
  time — not in ROTATE_CW). `spawnTraffic` swaps 55% of cars that APPEAR within 2.5 cells of the
  district for one of them, 18% quicker. Width per car from its plate.
- **The Flats' own furniture.** Two pastel sets (`nfa_`, `nfb_`) alternate house to house. Room
  cases still place standard keys; `NF_FURN` swaps them after furnishing and before tidy, re-cuts
  each footprint to its plate, anchored to its wall. `NF_STD` maps every swapped key back to the
  standard one so tidy and doorway rules treat it identically — without that, the unfamiliar keys
  were deleted. Bath fixtures keep the standard box. **Verified: every piece the standard set
  keeps, the Flats set keeps (81 vs 78), all 14 floors walkable.** Rochelle's is untouched.
  The dark `nfd_` set is cut and in the zip, deliberately unregistered.
- **Beds are shoved out of doorways, not deleted** — a small bedroom with its door near the bed
  lost the bed. City-wide.
- **Sky gossip.** `skyPresence(x, y)`: the Flats +30% always, Deuce turf 12% + 34%×Sky, taken ring
  ground 26%×Sky, +10% per addict within 480 (cap 35%), +28% within 1100 of the Deuce distro;
  cap 85%. It is both how much more often civilians there talk (up to ~2×) and the chance a line
  is about Sky. `SKY_GOSSIP.near` when an addict is within 150, `heavy` above 55%. The listener
  usually answers in kind. Measured: Flats 42/59/76% at Sky 0/50/100; Kings ground 0% until
  addicts show up on a corner.
- **Station platforms are steel deck plate.** `tx_deckplate` was cut and registered and nothing
  ever drew it; the platforms were a grey wash. Now a clipped pattern at a fixed 44-unit tile,
  anchored to the platform corner so the tread does not crawl with the camera. Missing file falls
  back to the old wash.

### Rules that earned their place
- **Plates are sized by HEIGHT.** Anything painted below the hip — the old man's carrier bag — makes
  the whole figure smaller. It was cut.
- **A reachability test must use the same collision rules as the game**, or it passes sealed rooms.
- **Render the plan before placing furniture.** A 2× top-down image of rooms, walls, props and the
  walkable flood found the sealed door in one look.
- **Check declaration order** again: `GYM_KEYS` was first written 3,000 lines below the loader
  registration that reads it. Caught before shipping.

### Assets this session (`sky_addicts_assets.zip`, unzip at repo root)
| folder | keys |
|---|---|
| `assets/sky/` | sky_man_coat, sky_girl_ward, sky_old_coat, sky_hood_a, sky_hood_b, sky_coat_a, sky_coat_b |
| `assets/deuce/` | dw_booth, dw_booth_set, dw_bistro, dw_stooltable, dw_rope, dw_rope_b, dw_cigmachine, dw_payphone, dw_crate_a, dw_crate_b, dw_desk_door, dw_mirrorball |

The 22 gym plates must be at `assets/gym/<key>.png` under the names in `GYM_FIT`.

---

## 0. THE PATTERN THAT CAUSED MOST OF THIS SESSION'S BUGS

The previous two shapes both came back. A third joined them, and it was the worst one.

**SHAPE A — something exists but is on nobody's list.** Still the most common failure here.

| thing | list that did not know about it |
|---|---|
| the player's own bullets | `policeUnits()` and `federals()` were in the **NPC** branch, not `byPlayer` |
| Elegy | `combatTargets()` — she could not be hurt at all |
| distro guards | `combatTargets()` |
| the club crowd | `combatTargets()` |
| the Deuce | `GANGTOP` — no sheet, so `drawGangTop` returned false and they were INVISIBLE |
| `hh_sec_van` | nothing ever spawned it; a model in a table is not a car in the world |
| La Voz, Elias | `VIL_CARS` — neither had a car, so their scenes fell to the generic fallback |

**SHAPE B — a thing that exists but was never drawn or placed.** `hh_sec_van`, the six `vh_` rogue
cars, `dt_sky`, every tile in `assets/tex/`, 51 deco pieces, 17 club props: all cut, all
registered, none reachable. **Registered is not placed. Placed is not drawn. Drawn is not
reachable.** Check which of the three you actually did.

**SHAPE C — the guard that tested the wrong thing.** The Lion fell back to a brown box because
the gate read `imgs.current[k]` for truthiness. The loader puts an Image object there the moment
it starts fetching, so a 404 leaves a **real object that is 0 wide**. **Test `.width`, never the
object.** Same class as the `dryOut` break: a safety net written the wrong way round does the
opposite of its stated purpose.

### Rules that earned their place

- **Measure before you size.** A generated building is 260–400 units across, about a quarter of
  a cell. Plates drawn at 1 cell came out four times the size of the city. `MARKS` is fractions
  of a cell now.
- **A fallback that reverts to the old value silently kills every fix above it.** `heroTall`
  fell back to the original hardcoded numbers, so two rounds of tuning were dead code and the
  same three sprites stayed wrong. A reference measurement is not runtime state — hardcode it.
- **`g.fx` is lazy.** Every site writes `g.fx = g.fx || []` first. One that did not threw inside
  `drawJobBoss`, and a throw there takes the rest of the frame: the rogue's AI, his car, his
  crew. One missing guard read as four separate bugs.
- **Key by hue, not by modal colour.** Four building plates came back with the background intact
  and the roof missing, because the roof was larger than the visible magenta and outvoted it.
- **Check declaration order.** A registration loop reading `DISTRO` ran before `DISTRO` was
  declared — a TDZ throw at boot, not an `undefined`.
- Watch the number instead of hooking the sites. Fourteen lines take health off the player;
  regeneration and the guard soak both work by **watching hp drop between frames**, so anything
  added later is covered on the day it is written.

---

## 1. WHAT WAS BUILT

### The plate rule (write this on the wall)
**Every character plate is cropped at the hip and nothing below it is painted on.** `drawYouth`
draws legs procedurally and swings the striking arm over the top. Painted legs double up — Rio
and Sho each lost 53px to this. Painted arms are fine at rest and wrong the moment he fires,
which is what `yt_lion_hero_bare` exists for. **Any plate that will hold a weapon wants an
armless variant.**

### Heroes
- Six plates each re-cut: Lion, Rio, Kenny, Sho, Eclipse, mentor. `HERO_ART` is one folder,
  spread last, so re-cutting the roster is one place instead of three.
- **Sizing is solved off SHOULDER SPAN, not height.** `HERO_SPAN` says how wide each man reads
  relative to the Lion; `heroTall` solves the tall backwards from the plate aspect. `HERO_REF`
  is hardcoded 224/159. `HERO_FIT` is per-plate correction and is currently empty.
- The Lion draws from a plate everywhere now — ground, bench, bike. He was hardcoded out of all
  three. `lion_act` is still the strike/grapple fallback behind `drawDariusTop` — see file size.
- `TOUGH = 2.5` divides all fourteen damage sites. `REGEN` heals 6.5/s after 3s untouched.
- `GUARD` — one button, five answers. BRACE / BLOCK / PARRY / ROLL / VEIL, all sharing one
  damage-soak so a defensive move is a number, not five interceptions.
- `DOWN_KIT` / `downHero()` — KO or arrest benches a hero on a clock and you continue as the
  next man, out front of the den. Roster empty → the closest to ready comes back at 100.
- `SENTENCE` — arrest time is base 90 + 55 per heat level, ×0.6 if anyone holds the Clerk.

### Centella, Rio's shepherd
Bite / howl / heal, a drawn leash, **cannot be targeted** (deliberate — the one place the
omission is the design). HOOK unclips her; TOW clips her back on. `TOW` also opens a destination
picker: tap to cycle, stop tapping for 1.5s to confirm, and she tows him there on the board.

### The Icicle, Elegy, and the rogues
- `zero` became `icicle` — Clarissa Vance, `she: true`, crew 5, wing `ice`, seat in the mountain
  zone. Cryo beam is stun-led and runs through `combatTargets()`.
- **Elegy** (Perdita Kell) stands at Monstruo's scenes, speaks once, gas / whip / pistol. Gas
  does no damage — it takes the screen off you for a beat. She can be put down; when she is, he
  stops and looks at her.
- **The Voz Girls** — La Voz's own wing, half dressed as him and half as her.
- Rogue crews keep their guns out now (`drawnT` only ran for a second after firing).
- Rogue getaway cars appear at last: **the cull was deleting them.** Any `dead` vehicle more
  than 1400 away for 50s was spliced, and the car is parked the moment the job is announced.
  `rogueRide` is exempt, the same way `crewCar` already was.

### The Deuce, Sky, and the distros
- Faction wired: colour, label, leaders, turf (downtown + Neon Flats), `PLATE_GANGS` art.
- **`SKY`** — one meter. Climbs unattended, falls only where you stand with heat on you, doubles
  at night. `DEUCE_RING` closes skate park → terminal → projects at 35/65/90 and never reopens.
  Andre Cole has three lines for it. **Now visible on the street as addicts — section 00.**
- **Six distros**, one per gang, placed on their own turf with three rings of guards. All six
  effects live via `GANG_STAT` + `DISTRO_STAT` + `gstat()`. Rivals raid every 95s and the gang
  holding `ears` raids first.
- Vance Tower (7 floors, `TOWER` plan, `lock` written and false), Deuce's Wild with a crowd and
  shifting purple/gold light, Rochelle's safehouse in the Flats.

### The city
- Three new districts: **NORTH END** (0–5, 0–2), **CIVIC** (12–16, 4–7), **STADIUM** (22–26,
  3–7, super). Plus `neonflats`, `county`, `kestrel`.
- **`MARKS` + `placeMarks()` — the placement pass.** A mark becomes a real building via `mkB()`
  pushed onto the cell's own `blds`, so it gets a door, an interior, collision, a stair and a
  roof for free. Marks now also take `kind`, `door` and `doorSide`.
- Stadium drawn at zone scale with the dome fading as you walk under it and the field clamped.
- Gym floor: now a real interior (section 00).
- Vance garage: drive at the rear face and park inside, same ramp pattern as the den.
- Observer chopper — `__ironlion.fly()`, or E on the pad beside the den.
- Weather: rolled, not toggled. Light / med / storm with lightning that shakes the screen.
- Doorways: `DOORW` 34 → 48, and the nub threshold 2 → 7. A 2px stub is invisible and still
  collides, which is what was catching everyone in bank doors.
- `TRAVEL` has nine direct destinations with an `always` flag that bypasses discovery.
- **NaN sentinel** — last known good position, traffic scrubbed, both logged to console.

---

## 2. STILL OPEN

- **Interiors: two done, the pattern is set.** Gym and Deuce's Wild are furnished (section 00).
  Still unplaced: 51 `fx_` deco, 17 `cl_` club props (numbered — need eyes on the art to name
  them), 10 tiles. Copy either: a layout list of fractions + a makeFloor block + render the plan
  + walk test with the real collision rules.
- **Twelve marks still default to `store`:** walkup ×2, store, courthouse, offices, chronicle,
  policehq, gates, tower_cap, barber, laundro, church, works. Each needs a `kind` on its mark.
  Check what a kind already means before reusing it (`club`, `precinct` carry identity).
- **The generic nightclub bar is broken in any shallow room** — the solid bar stands under the
  doorway. Deuce's Wild routes around it; Ember Flats' clubs still have it.
- **Mark roofs:** `capPlate` is set and never read, so a mark also gets its kind's generic roof
  class under the plate (the club now gets `gen_bar`). Harmless while the plate covers it.
- **Passcode.** The lift exists and honours `lock`; nothing sets a lock or asks for a code yet.
  The twins' floors (index 6, 7) are the ones to flip.
- **Nobody lives in the tower yet.** `who: "tiny" / "julian" / "damian"` on TOWER floors are still
  unread — the floors exist to put them on.
- **11 doors are still crossed by a room wall** after the lane cut — too few to chase blind; the
  door scan in this session's notes lists them if they ever matter.
- **`g.vanceKey` and `g.towerSites` are not saved.** A reload re-occupies the tower.
- **Guards do not chase you through a door** — the street ring waits outside while you are in.
- **The blacktop tile has pink/cyan reflections baked in**, so they repeat every 440 units. Fine
  at speed; a clean tile + drawn reflections would be better.
- **Detective mode** needs `CASE` — a crime that outlives its scene. `yt_malcolm`, `yt_ramos`,
  `hh_det` are cut and idle.
- **The prison** needs `BID`, and before any code, the verb: what you DO in there that is not
  shooting.
- **Elegy's asylum and the Monstruo breakout.** She has `hp: 34` and a KO state with nowhere
  to go.
- **Fear and berserk on ROAR** — needs the crew AI to read a new state. Setting the fields
  without that writes two things nothing reads.
- **Can the Kings take turf back?** `DEUCE_RING` is a count, not a per-zone owner. Reversal
  means a different data shape. Decide before building.
- **Camps are scenery with people in them.** Next verbs: they are not in `combatTargets()` yet
  (deliberate — decide what hitting a camp MEANS first); a camp could be a place to buy, to ask,
  or the thing a Kings raid burns. `g.camps` is a Map, so a camp can carry state.
- **Sky addicts talk but do nothing else** on the street. Obvious next verbs: they approach the player and ask,
  they flock to a distro when it is restocked, they are what a Kings raid clears off a corner.
- **Street routing around the stadium.** `ZONES.stadium` is `super: true`, which should cut
  internal streets. If a road still crosses it, the generator is not reading that flag.
- **The station** — `tx_el_station` cut, `EL_STOPS` still points with no stair mouth. One
  coordinate per stop and `nearPlatform()` tests THAT at ~70 instead of the platform at 150.
- **24 street animals** (`an_dog_*`, `an_cat_*`) — no system.
- **File size — 3.09 MB.** Past the ~2.4 MB where Safari has refused before. **Blobs are not the
  main problem:** 155 embedded blobs total 1.40 MB and `lion_act`, the largest, is 82 KB — and it
  is still live as the strike/grapple fallback. The code itself is ~1.7 MB. Moving blobs out
  cannot get under 2.4 on its own.

---

## 3. REPO / ASSETS

Repo is **`Black_Lion`**, served at adonisdross.github.io. `cuts/`, `cuts2/` and `assets/` sit
at the **root** beside `game.jsx`.

| folder | count | what |
|---|---|---|
| `villains/` | 94 | rogues, hench pools, distros, vehicles, weapons, Sky |
| `deuce/` | 73 | the twins, Rochelle, Tiny, their cars, 51 deco pieces, 12 `dw_` club pieces |
| `gym/` | 22 | ring, bags, iron, lockers, wall pieces — registered as of this session |
| `heroes/` | 18 | roster civ + hero plates, the dog, the chopper |
| `club/` | 17 | bar, DJ booth, speakers, mirror ball, seating |
| `city/` | 16 | North End, Civic, stadium, tower cap, club |
| `tex/` | 12 | rail, station, interior floors, dance floor, car park, blacktop |
| `sky/` | 15 | the addicts, hip-cropped |
| `sewer/` | 17 | camp kit: barrels, shelters, bedding, lights |
| `nflats/` | 78 | house roofs, Rochelle's, neon, 12 cars, three furniture sets |
| `roofs/` | 7 | four walk-up, three row |
| `audio/` | 1 | `gang_kings.mp3` — plays at Kings HQ |

**Registering a key makes the loader go and look for it.** Nothing here is registered ahead of
its art except `vil_icicle_civ`, which is deliberately `null` until Clarissa out of the suit
exists.

---

## 4. DEBUG HOOKS (all temporary, all safe to delete)

```
__ironlion.fly()          observer chopper up / down; fly(i,j) over a cell
__ironlion.go("gym")      fast travel on foot; go("stadium",1) arrives by air
__ironlion.pad()          where the chopper pad is and how far off you are
__ironlion.where()        every distro, whose it is, what cell
__ironlion.gangs()        every gang's live stats and what they hold
__ironlion.distro(g,k)    force a distro;  reseed() re-rolls the board
__ironlion.sky(n)         set the Sky meter (sky(90) fills the Flats and the camps);  ring() reads closures
__ironlion.camp()         drop into the nearest sewer camp
__ironlion.rain("storm")  force weather
__ironlion.down()/up()    bench the current hero / clear all cooldowns
__ironlion.tow()          open the dog's destination list
```