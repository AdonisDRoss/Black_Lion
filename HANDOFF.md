# LAYER 660: one body, cop legs cut and walking

## What changed in game.jsx
- Character creator: one build. Step 2 says ONE BUILD FOR NOW. The body picker is gone, and the default body is `big`.
- `big` body: runner_body_big_nohead.png in assets/runner/body/. The head is placed from its anchor (HEAD_CY big 0.0885, HEAD_WF big 0.4898). Its legs and arms are in the art, so the code legs are skipped for it. It stands still for now, with no walk cycle.
- Cop (cop_gas): the legs are cut from the uncut bust and drawn under the coat. At rest they add back to the uncut art exactly. While he walks, one leg shrinks and the other grows about the hip (COP_LEG_AMP 0.2). The code-drawn trousers are not drawn for him.
- Cop arms: left drawn in code. The arm cut reassembles exactly at rest, but when the arms swing, the body art shows patches, so I did not wire them.
- Air cop: unchanged (uncut art).
- Fallback fix: a body with no arm entry no longer draws the grey disc over itself.

## Files in this pack
- game.jsx (LAYER 660, the source of truth)
- assets/runner/cops/gas_leg_L.png, gas_leg_R.png (224 x 159, full canvas, legs only)
- assets/runner/body/runner_body_big_nohead.png and its .anchor.json
- cop_leg_anchors.json (hip pivots, leg_amp, arm pivots)
- screenshots/creator_one_build.png, cop_legs_zoom.png, cop_cut_frames.png, big_body_zoom.png

## Test
- The test build loads with no page errors. The 404s are non-runner art that the test folder doesn't have, and they were there before this layer.
- The cop legs move, but at phone scale the step is only a few pixels. COP_LEG_AMP can be raised (0.35 would be clearly visible) if you want it bigger.

## Not done
- The drifter has walk_a and walk_b, but only walk_a is loaded. He does not walk yet.
- The sewer's druggies, market traders and breather people are not made yet.
- The big body's legs are not cut, so it does not walk yet.
