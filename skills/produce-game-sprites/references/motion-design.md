# Motion design for game sprites

Read body structure before applying animation rules. Biped, quadruped, serpent, winged and floating actors need different phase plans.

| Action | Pose plan | Gameplay checks |
|---|---|---|
| Idle | Stable rest → breathing/weight shift → rest | No creeping root or accidental weapon change |
| Walk | Contact A → down → passing → up → contact B → matching phases | Alternating legs, readable cadence; compare to world movement speed |
| Run | Contact → compression → push-off → flight → opposing contact | Different stride/weight from walk, no whole-image sliding substitute |
| Melee | Anticipation → acceleration → impact → follow-through → recovery | Grip and reach coherent; damage event at impact |
| Cast | Gather → release → settle | Spell origin and event align; VFX separate if practical |
| Hit | Impact → recoil → recover | Brief readable interruption; no walk-like looping |
| Death | Loss of support → fall → settle/terminal | Terminal pose held; no automatic resurrection loop |
| Jump/dodge | Preparation → launch → travel → land/recover | Declare root movement and collision timing |

Treat these as design guides, not universal fixed frame counts. Match the actual game's responsiveness. Long attack wind-up is a combat choice, not a free quality improvement.

For in-place locomotion, the planted foot often travels backward inside its cell while the world root advances. Check contact in world space when root trajectories exist. Do not demand a frozen on-screen foot in all walk frames. Do not infer hidden joints as observed landmarks.

Lock action-ready initial poses and motion space. Swinging weapons need space in the swing direction; jump needs headroom; retreat needs room behind. Increase canvas without resampling the subject and translate the declared origin by the same padding offset. Key poses must share the same canvas and anchor convention.

Separate in-place clips from root-motion clips. The engine must not apply both authored translation and full movement-speed translation unintentionally. Mirror asymmetrical weapon grips only when the intended design really swaps hands.

Review loop endpoint rhythm without forcing exact-copy endpoints. A hold frame can legitimately repeat; identical images for every frame of a supposed articulated attack cannot demonstrate that action. Add event times to timeline metadata; artwork alone does not define damage or collision boxes.


## Landmarks, sockets and depth

Use lightweight motion landmarks to expose continuity problems; do not force every sprite into a skeleton model. Head/pelvis/feet are useful for locomotion; grip/weapon tip are useful for attacks. A large adjacent step is a review prompt, not proof of an error.

Runtime attachment sockets should follow the visible art. During attacks, inspect hand_main → weapon_base → weapon_tip together with the impact event and hitbox. During casting, inspect cast_origin and VFX separation.

For top-down 3/4 motion, depth changes are part of the pose. Front/back arm order, foreshortened legs, cape/hair and weapon traversal may differ per facing; do not reuse a single layer order blindly across north/south/east/west.
