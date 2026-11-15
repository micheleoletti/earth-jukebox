# Music engine: vision (Myky, 2026-11-14)

## North star
NatGeo / MasterClass visual polish + Hans Zimmer audio fidelity, on an explorable 3D Earth that stays dynamic to real data.
Looks good and feels good beats a clever, faithful data mapping that sounds bad.

## Model: Serious Sam style intensity layering
Reference: Serious Sam's adaptive music. Each map has music in phases (chill, fighting, more violent fighting), crossfaded on one shared tempo. (Exact Serious Sam implementation not verified; this is the intended feel.)

- **One shared tempo** for every layer, so any layer can fade in and stay in sync.
- **Intensity** = one spectrum, driven by a set of data parameters.
- Music moves along the spectrum by fading pre-composed layers in and out.

## The intensity spectrum

| Intensity | What plays |
|---|---|
| Low | Bass, no percussion. Relaxing, almost meditative drone / ambient soundscape |
| Mid | Ostinato strings start, first light percussion |
| High | Taiko drums, brass stabs, full ostinato strings |
| Peak | Everything, most violent version |

Low end = calm planet. High end = stressed / active planet (storms, pollution episodes, heat).

## Open
- Which data parameters feed intensity, and how they combine (one "planet stress" index?).
- How many intensity steps / stems.
- Who composes the stems and with which libraries (Q1b).
- How zoom interacts with intensity (zoom = which regions feed the index? or which layers are audible?).

Research behind this: `research/realtime-vs-stems.md`, `research/harmony-and-mix.md`, `research/instruments.md`.
