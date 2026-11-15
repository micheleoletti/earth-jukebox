# Free orchestral / cinematic libraries (as of 2026-11-14)

## TL;DR
1. LABS is NOT the baseline. It is a texture/colour plugin (now folded into Splice INSTRUMENT, Oct 2025). The free orchestral foundation is **Spitfire Symphony Orchestra Discover** (Nov 2025, AIR Lyndhurst, 44 instr, Kontakt Player, 5.7 GB) or **BBC SO Discover** (240 MB), with **OT Berlin Free Orchestra** (Mar 2025, SINE) as an alternative.
2. Stack: drone = LABS Frozen Strings / Trumpet Fields + low SSO strings; ostinato = SSO Discover strings shorts; taiko = Strezov Thunder X3M Taiko Freebie (Kontakt Player); brass stabs + horns = SSO Discover brass + Sonokinetic Tutti Free / VSL Big Bang Orchestra tutti hits; choir = LABS Choir or MuseSounds Core choir (MuseScore only, export WAV).
3. Licences (Spitfire, OT, Sonuscore, Muse) all allow finished music in any media, royalty free. All ban redistributing samples as samples.
4. Single-note dry one-shots in a browser sampler = grey-to-red zone (Spitfire support names "playing a single note" as the risk; OT bans distributing "individual samples"; Sonuscore bans "isolating" and "embedding into ... sample playback system"). Ship composed, mixed, multi-instrument musical phrases/hits (layered + reverb, 1+ bar), not clean per-note samples.
5. Host: Mac + any AU/VST3 DAW (GarageBand/Logic/Reaper). Needs Native Access + Kontakt Player (free), Spitfire App, SINE, Splice account. All need a free account.

## Comparison (ranked for Zimmer-style use)

| # | Library | Coverage (drone / ostinato / taiko / brass stabs / horns / choir) | Quality rep | Host / size / signup |
|---|---|---|---|---|
| 1 | Spitfire Symphony Orchestra Discover (Nov 2025) | strings (sections, a16), brass incl. solo horn, trombone, tuba, ww, orch perc. No taiko, no choir | Spitfire's "largest free library", AIR Lyndhurst (the room Zimmer/RCP use). Launch coverage only, no in-depth review found yet | Kontakt Player 7.5.2+, VST3/AU/AAX/standalone, macOS 11+, 5.68 GB, Spitfire App + account (BPB says newsletter gate) |
| 2 | BBC Symphony Orchestra Discover (2020, free since 2022) | strings, brass (horns), ww, timpani + untuned perc. No taiko/choir. 1 mix, 34 instr | 1M+ downloads; SOS reviewed favourably; drier/more "concert" than AIR | Own Spitfire plugin AU/VST3/AAX, ~240 MB, free account |
| 3 | OT Berlin Free Orchestra (Mar 2025) | 34 instr, 67 artic, strings/ww/brass/perc, 2 RR, 2 dyn layers. No choir/taiko | BPB: "a little shocked" it's free; Berlin series = Teldex sound | SINE Player AU/VST3, OT account |
| 4 | Spitfire LABS / Splice INSTRUMENT | Strings, Frozen Strings, Scary Strings, Choir, Percussion, Trumpet Fields (droning brass), Foghorn. Single-patch, few artics | Great for colour/pads; not a playable orchestra. LABS+ symphonic packs are PAID (sub) | Splice INSTRUMENT or legacy LABS AU/VST3/AAX, Splice account, reportedly online to load |
| 5 | MuseSounds Core + Muse Percussion (MuseHub) | full orch, 40-voice choir, taiko sections | Strong notation playback; reviewers love percussion | MuseScore Studio ONLY: "not compatible with DAWs, plugins". Export WAV per part |
| 6 | Strezov THUNDER X3M Taiko Freebie | low solo taiko + rimshots | Strezov = top-tier epic taiko vendor | Kontakt Player 7.0.11+, ~600 MB, Native Access |
| 7 | Sonokinetic Tutti Free | aleatoric: stabs, crescendi, glissandi, textures | good for hits/risers | Kontakt Player 7.7.2+, 445 MB, account |
| 8 | VSL Big Bang Orchestra (free core) | tutti hits, swells, marcatos; taiko only in PAID packs | VSL Synchron quality | Synchron Player, Vienna Assistant, iLok/free account, 1.4 GB |
| 9 | ProjectSAM The Free Orchestra 1+2 | Luminous Choir, staccato strings, brass clusters, Bold Legato Brass | "epic" ProjectSAM sound | Kontakt Player 6.5.3+, ProjectSAM + NI accounts |
| 10 | Sonuscore Orchestra Elements / The Score Elements (4 Nov 2026) | strings, brass, ww, perc, choir ensemble engine | solid; Score Elements too new for reviews | Kontakt Player (Score Elements needs 8.13.1+, macOS 14+), Native Access |
| - | Komplete Start | just the host bundle (Kontakt Player); orchestral content thin | n/a | Native Access |
| - | Pianobook / Decent Sampler, VSCO2 CE (CC0), Sonatina | indie/CC; weaker for epic | VSCO2 CE is CC0 = licence-safe fallback for one-shots | Decent Sampler / SFZ |

Not verified: any VI-Control/Reddit head-to-head of SSO Discover vs Berlin Free vs BBCSO Discover (none retrieved). Quality ranking above = recording venue + vendor reputation + review coverage.

## Licence quotes

**Spitfire (LABS, BBCSO Discover, SSO Discover)**, EULA https://www.spitfireaudio.com/pages/spitfire-audio-end-user-license-agreement
- Cl. 5: "use the purchased Sound File(s) only within your own newly-created sound recording(s) and/or performances"
- Cl. 5: "except where you have combined them with other sounds within one or more musical composition(s)"
- Cl. 5: "reselling or distributing those loops and sounds other than in a musical composition is strictly prohibited."
- Cl. 5: bans use "as sounds, multi-sounds, samples, multi-samples ... in a sampler"
- Cl. 9: "only your own original musical compositions and productions."

Support FAQ https://support.spitfireaudio.com/en/articles/11815239
- "Yes, you can use our libraries on commercial recordings you release." Applies to free licences (LABS, Discover), "includes looped content".
- "it is not permitted to use the sounds to create another sample library, or something that can be construed as such."
- Game/interactive OK as incidental music if sounds "can't be recorded or exported" (paraphrase). Browser audio files are always fetchable, so lean on "musical composition" framing.
- Spitfire staff (via Freesound forum, secondhand) https://freesound.org/forum/legal-help-and-attribution-questions/43195/97780 : loops fine unless "you're not playing a single note, where someone may take this and use it to create a new sample library."
- LABS now inside Splice INSTRUMENT; Splice terms https://splice.com/terms may also apply to content pulled via INSTRUMENT. Not checked clause by clause.

**Orchestral Tools (Berlin Free Orchestra, SINEfactory)**, GTC §8.2 https://orchestraltools.com/legal/terms
- may use "for the composition of music and audio productions"
- "Individual samples, sound sets or audio loops may not be distributed, except in the context of work results."
- "may not be repackaged in whole or in part as audio samples, sound libraries or sound effects."
- EULA §4 https://www.orchestraltools.com/legal/license-agreement : no TDM / AI training.
- Licensing FAQ https://orchestraltools.helpscoutdocs.com/article/165-licensing-faq : "ALL media productions can use purchased collections in accordance with the Terms of Service."

**Sonuscore**, https://www.sonuscore.com/terms-condition/
- §4: "You may use the Content in your own finished productions without additional license fees."
- §5: no "re-selling, trading, sharing, resampling, mixing, processing, isolating, or embedding into software or hardware of any kind" ... "or any form of musical sample or sound effect sample playback system or device". Strictest; avoid Sonuscore for anything resembling one-shots. (NI-partner titles fall under NI's licence instead.)

**MuseSounds**, EULA text as quoted on https://musescore.org/en/node/344132 (musehub.com/eula returned 403):
- "You may not use these sounds for any commercial or non-commercial purpose except where you have combined them with other sounds within one or more musical composition(s) and/or recording(s)."

**ProjectSAM**, EULA (Crypton mirror) https://ec.crypton.co.jp/download/pdf/eula_sam_dl.pdf : COMMERCIAL USE "in music production, public performance, broadcast or similar use"; ProjectSAM keeps ownership of the recorded sounds.

**Strezov, VSL, Sonokinetic**: product pages link generic T&Cs; not read clause by clause. Assume same pattern (music yes, samples no). Check before submission.

## One-shot verdict
- Bounced stems/loops/beds: clearly fine everywhere.
- "Taiko hit" / "brass stab" as one-shots: make them **composed musical events**: e.g. 2-3 layered taiko + timpani + low brass + reverb tail, processed, 1-4 beats long, at fixed pitch/key. That is "combined with other sounds" in a composition, not a playable sample set.
- Do NOT ship: per-note chromatic/velocity-layered dry samples, a mapped keyboard, or anything a user could rebuild as an instrument. That is what Spitfire Cl. 5, OT §8.2 and Sonuscore §5 target.
- Need truly clean per-note samples? Use CC0 VSCO2 CE (https://versilian-studios.com/vsco-community/), not commercial freebies.
- Credit every library + vendor in the hackathon resource list.

## Sources
- Spitfire EULA: https://www.spitfireaudio.com/pages/spitfire-audio-end-user-license-agreement
- Spitfire royalty-free FAQ: https://support.spitfireaudio.com/en/articles/11815239
- Spitfire single-note comment (forum): https://freesound.org/forum/legal-help-and-attribution-questions/43195/97780
- SSO Discover product: https://www.spitfireaudio.com/products/spitfire-symphony-orchestra-discover
- SSO Discover launch (SOS, 12 Nov 2025): https://www.soundonsound.com/node/4934367
- SSO Discover (BPB): https://bedroomproducersblog.com/2025/11/11/spitfire-symphony-orchestra-discover/
- BBCSO Discover review (SOS): https://www.soundonsound.com/reviews/spitfire-audio-bbc-symphony-orchestra-discover
- BBCSO Discover free (BPB 2022): https://bedroomproducersblog.com/2022/07/22/bbc-symphony-orchestra-free/
- LABS to Splice INSTRUMENT (KVR): https://www.kvraudio.com/news/spitfire-audio-labs-evolves---introducing-splice-instrument-free-vst3-au-and-aax-64929
- Splice INSTRUMENT: https://splice.com/instrument/labs-instrument
- BPB free orchestral roundup: https://bedroomproducersblog.com/free-vst-plugins/orchestral/
- OT Berlin Free Orchestra: https://www.orchestraltools.com/berlin-free-orchestra , https://bedroomproducersblog.com/2025/03/20/orchestral-tools-berlin-orchestra/
- OT GTC: https://orchestraltools.com/legal/terms ; OT EULA: https://www.orchestraltools.com/legal/license-agreement
- MuseSounds DAW limitation: https://support.musehub.com/en/articles/15070615-what-are-musesounds
- MuseSounds Core: https://www.musehub.com/bundle/musesounds-core ; Muse Percussion: https://www.musehub.com/muse-sounds/muse-percussion
- Sonuscore terms: https://www.sonuscore.com/terms-condition/ ; Score Elements: https://sonicstate.com/news/2026/11/04/sonuscore-releases-the-score-elements/
- Strezov Taiko Freebie: https://www.strezov-sampling.com/products/view/THUNDER%20X3M%20Taiko%20Freebie.html
- NI free Kontakt list: https://www.native-instruments.com/blogs/blog/best-free-kontakt-instruments
- ProjectSAM Free Orchestra 2: https://projectsam.com/libraries/the-free-orchestra-2
- Sonokinetic Tutti: https://www.sonokinetic.net/products/classical/tutti/
- VSL Big Bang Orchestra: https://www.vsl.co.at/instruments/bbo/bbo
