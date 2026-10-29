# Layer 707: the jobs, the flashes and the MISSIONS tab

Upload: game.jsx (replace). No new assets this layer; the gold ! badge, the flashes and the log are drawn in code.
Build tag should read LAYER 707.

## What is in it
- After the lethal chip is in, four people on the street wear a gold ! over their head (one more every 4 seconds until four are out).
- A (on foot) next to one: their offer, then TAKE THE JOB or NOT NOW.
- 16 jobs: 8 missions (deliver a package, fence a part, hold a stash, tail a target, find the missing kid, run a message, scout the night, breather run) and 8 crimes (lift a parcel, pick a pocket, shoplift, break into a car, strip a car, shakedown, burgle a shuttered shop, rob the fence). Each one pays into the pocket on completion.
- Each job is a short run of steps. The arrow, the blue minimap star and a dashed gold ring mark the current spot. The HUD shows JOB: <step>.
- Flashes across the screen: MISSION STARTED (with the job's name), MISSION COMPLETE with +$ pay, MISSION FAILED in red with the reason (BLOWN: <step> or TOO LATE).
- Pause menu: new MISSIONS tab (LB/RB, or click). The list shows each job and its status. Select one to read the offer, the talk and the objectives (ticked as they are done). On the pad: D-pad to a row, A to open it.

## Test steps
1. Buy the chip from the doctor ($10). Within about 12 seconds, four gold ! badges should show on the street.
2. Walk up to one and press A. Read the offer. Choose TAKE THE JOB. MISSION STARTED flashes.
3. Follow the arrow and the blue star to the spot. Check the dashed ring is on it and the HUD line matches.
4. Finish a mission: MISSION COMPLETE with the pay. Check the pocket went up.
5. Finish a crime: stand on its spot and press A. A blown job shows MISSION FAILED and pays nothing.
6. RUN A MESSAGE is timed: 90 seconds from picking up the note. Let it run out to see TOO LATE.
7. Pause, open MISSIONS. Check the offer, the talk and the objectives are all there for the job you just did.

## Not yet
- Night objectives (the pot ones) are not in this layer.
- One job at a time.
- Hunter nets, the C.A.N. tower start on the roof, and the roof art are not in this layer.
- Not browser-tested yet. The job logic was tested headless (all 16 jobs start to finish, a blown crime, a timed failure). Check the gold ! height over the heads and the flash placement on screen.
