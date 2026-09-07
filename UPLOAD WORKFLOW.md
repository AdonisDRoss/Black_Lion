# HOW TO UPLOAD A ZIP TO `adonisdross.github.io`

You are on iPhone, so this is the phone route. Do it in this order — **game.jsx last, always.**

## From the phone, in Safari (no apps needed)

1. **Unzip first.** Tap the zip in Files → it expands into a folder beside it.
2. Go to `github.com/AdonisDRoss/adonisdross.github.io` and sign in.
3. **Assets before code.** Open the `raven-hook/assets/` folder → **Add file → Upload files**.
   Tap **Choose files**, then **Browse** in the picker, and select the PNGs from the unzipped
   folder. Upload one asset folder at a time — Safari's picker gets unreliable past ~40 files.
4. Commit. Repeat per folder (`bank`, `food`, `bar`, `cafe`, `gun`, `lux`, `motel`, `sov`,
   `sewer`, `shop`, `race`).
5. **`game.jsx` last.** Open `raven-hook/` → the existing `game.jsx` → pencil icon is no good
   for a 2.5 MB file, so use **Add file → Upload files** and drop the new `game.jsx` in the
   same folder. GitHub replaces it and keeps the history.
6. Wait ~60 seconds for Pages to rebuild, then hard-reload the game.

## Confirming it actually took

**Read `BUILD_TAG` on screen.** This build says **`LAYER 381 — HER TOOLS`**. If it still says
an older layer, the upload did not land or Pages has not rebuilt — do not start debugging the
game until that string is right.

## Why assets first

If `game.jsx` goes up before the art, every new key 404s for a minute. Nothing breaks —
missing sprites fall back to colour blocks by design — but you will think a system is broken
when it is only early.

## If a file is too big

GitHub's web uploader refuses over 25 MB per file. Nothing here is close; `game.jsx` is the
largest single file at 2.5 MB.
