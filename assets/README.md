# Skate park & arcade assets — cut from the LAYER 311 uploads

Magenta keyed, alpha eroded 1px, despilled, trimmed to content. Residual magenta on every
file measured at **0 pixels**. Names match the `case` labels in `drawSkateObs()`.

## skate/ — drop-in for `drawSkateObs`

| file | replaces `case` | note |
|---|---|---|
| `sk_halfpipe.png` | `halfpipe` | reads correctly from above |
| `sk_bowl.png` | `bowl` | round, correct |
| `sk_bowl_square.png` | — | **see below** |
| `sk_funbox.png` | `funbox` | correct |
| `sk_kicker.png` | `kicker` | correct |
| `sk_bin.png` | `bin` | correct |
| `sk_pool.png` | — | the drained pool. Best piece in the batch. |
| `sk_quarter.png` | `quarter` | **elevation, not top-down** |
| `sk_rail.png` | `rail` | **elevation** — legs are visible |
| `sk_bench.png` | `bench` | **elevation** |
| `sk_fence.png` | `fence` | **elevation**, and the mesh is transparent |
| `sk_pile.png` | `pile` | **elevation** — has a brick wall behind it |

`sk_bowl_square.png` came out of the arcade sheet, in the cell where the prompt asked for a
change machine. It is not a change machine — it is a second, square-cornered skate bowl, so
it is filed here rather than under the name that was requested. There is still no change
machine anywhere in the batch.

The five marked **elevation** will lie flat and read wrong beside the top-down pieces. They
are cut and named so they are ready the moment they are redrawn; the procedural `case` in
`drawSkateObs` still runs until you swap them.

`sk_pool.png` has a skateboard baked onto the coping. It will sit there permanently.

## arcade/ — for the arcade and the band venue

`ar_upright`, `ar_cocktail`, `ar_pinball`, `ar_stage`, `ar_drums`, `ar_amp`, `ar_mic`, `ar_pa`.
`ar_cocktail` and `ar_drums` are true top-down. The rest are elevation, which is the same
convention the game's existing furniture plates already use, so they should sit fine.

## reference/

`deck_01..08` — the eight board designs, at the size they arrived: about **126×47**. Too small
to use. Re-render these at working size.

The arcade room shots on that sheet are mood images, not assets, and are not included.

## _needs_redraw/

The twelve kid cells, sliced and named. Measured against the three tests in
`YOUTH_DISTRICT_PROMPT.md`:

- **no face patch on any of the four.** Skin at the top of the head is 45px on the skater
  against 395px at the bottom, and the bottom skin is two separated blobs left and right —
  those are the hands at hip level, not a face. Test 4.
- **widest point sits at 63–75% down, never at the middle.** The hands-and-hips band is wider
  than the shoulders. Test 3.
- both arms to hip level passes — that is what the hands are.

Camera and build variation are fine. One more round fixing the head should do it.
