# Layer 720: the face picker, new men and women from the sheets (no old people, no gray hair)

Upload order: everything in assets/ first (including the new assets/picker/ folder, 105 images), then game.jsx last.

## What changed in 720
- **Men: 64.** 59 new faces cropped from the six sheets (assets/picker/m_*.png), plus five named characters at the bottom: Ray (crew), Alonzo, Sparky, Malcolm and Deon King (the QB, shown as DEON). The old male faces (assets/faces f_B42 to f_S104) and the runner male portraits (male_01 to male_10) are no longer listed. Their files are still in the game, just not on the picker.
- **Women: 64.** 10 runner portraits, Ann 03, Ann 07, Denise King, D, four school students (stu_ch_16, 21, 23, 28), and 46 new faces from the sheets (assets/picker/f_*.png).
- **Removed.** Malcolm from the women, the four cop busts, the school mom. Old and gray-haired named men: Crew Viejo, Hector and Okafor.
- Build tag reads LAYER 720.

## Checks run
- Game bundles with esbuild, no errors. Undefined-name scan: only playSfx and boomAt, both typeof-guarded.
- Men's page 64, women's page 64. No duplicate keys in either list.
- Every new picker key maps to a file in assets/picker.

## Open
- The age and gray-hair calls were made by eye on the sheets. Two middle-aged men with glasses and mustaches (picker keys m_B09 and m_E22) are the closest calls. Swap them if they read as gray.
- Not yet run in the game in a browser.
- Carried over: D's portrait is labeled 27 (D is 31); teammate car, car entry, police car backwards, a keyboard key for sneaking.
