# Deep Research: Warcraft III & Age of Empires III AAA Modeling, Environment, Autonomous Life, Audio & Live Weather

## 1. Visual Philosophy & Silhouette Engineering

### 1.1 Warcraft III (Samwise Didier / Blizzard Entertainment)
- **Heroic Proportions & Top-Down Readability**: Early realistic builds failed because units read as tiny muddled specks from RTS camera height. Blizzard shifted to bold, chunky silhouettes: oversized pauldrons (shoulders), exaggerated weapons/shields/staves, distinct headgear (plumes, hoods, horns, halos, crowns), and high-contrast team-color surfaces.
- **Silhouette First**: Every unit and hero class must be identifiable at a glance by outline alone:
  - **Knight / Marshal / Paladin**: Heavy plate pauldrons, kite/tower shield with heraldic cross, broadsword or warhammer, flowing team-colored cape, horned/plumed greathelm.
  - **Archmage / Enchanter / Spellbreaker**: Tall arcane staff topped with levitating crystal/ring, billowing scholar robes, pointed hat or arcane crest, glowing spell tome or glaive.
  - **Ranger / Scout**: Hooded cloak, recurve longbow drawn across chest, quiver on back, feathered mantle, agile stance.
  - **Far Seer / Cleric / Bard**: Totemic/holy staff or lute, prayer beads/runes orbiting torso, glowing hands, ceremonial mantle.
  - **Runesmith / Inquisitor / Shadowblade**: Forge hammer + anvil buckler / twin daggers + stealth cowl / inquisitor war-cross.
  - **Peasant / Worker**: Tunic, leather apron, mining pickaxe / woodcutter axe, carrying gold sack or timber bundle when hauling.
  - **Minion (Footman / Skeleton / Treant / Construct)**: Compact shield-and-spear or arcane construct silhouette with distinct crest.
- **Hero Glow & Auras**: In Warcraft III, Heroes are immediately distinguished from regular units by:
  1. A soft radial team-colored **Hero Glow** beneath their feet.
  2. Concentric rotating geometric **Aura Runes** (Devotion Aura cross-ring, Brilliance Aura arcane hexagram, Command Aura war-star, Trueshot Aura wind-ring) when active/high-level.
  3. Floating **Level Star / XP Crest** and animated weapon glint.

### 1.2 Age of Empires III (Ensemble Studios / BANG! Engine SM3.0)
- **Warm Sunlight, Rich Materials & Architectural Detail**: Timber-framed masonry, terracotta/slateroof shingles, dormer windows, chimneys with rising smoke plumes, rotating waterwheels/windmills, market awnings in vibrant stripes, hanging lanterns, barrels, crates, and cobblestone/packed-earth plazas around structures.
- **Connected Settlement Feel**: Buildings are not isolated icons on green squares; dirt/cobblestone roads connect the Town Center (Town Hall) to surrounding production buildings, Trading Posts (Marketplace), and Forts/Towers.

---

## 2. Structures (All 11 Buildings Modeled in Detail)

| Building ID | WC3 / AoE3 Archetype | Architectural & Animated Elements |
|---|---|---|
| `town-hall` | Keep / Town Center | Multi-tiered stone keep with timber wings, blue/gold pitched roof, twin crenellated towers, grand arched gate, 2 wind-flapping banners, courtyard cobblestone plaza, lantern glow. |
| `barracks` | Human Barracks / Military Academy | Fortified stone garrison, arched sally port, weapon rack with spears/shields outside, training dummy in yard, twin braziers with flickering fire, red/gold war banner. |
| `tavern` | Neutral Tavern / Inn | Half-timbered two-story inn, warm thatched/shingled roof, hanging wooden ale-mug signboard swinging in the wind, barrels outside, chimney puffing warm smoke, warm glowing windows. |
| `library` | Arcane Sanctum / University | Octagonal mage tower + skylight dome, floating rotating arcane rings above roof, stained-glass lancet windows glowing cyan/gold, levitating obelisks flanking entrance. |
| `watchtower` | Guard/Cannon Tower + Outpost | Tall stone spire with wooden machicolations, rotating lookout beacon/spyglass torch at top, crenellated parapet, fluttering pennant at peak (extended sight radius). |
| `runeforge` | Blacksmith / Foundry | Heavy stone smithy, glowing open furnace hearth (pulsing orange/red), outdoor anvil + water quench barrel, chimney belching dark forge smoke + rising orange embers/sparks. |
| `vault` | Arcane Vault / Bank | Domed treasury with reinforced iron-bound vault door, golden pediment, rotatingfloating relic crystal on pedestal, guarded columns. |
| `portal` | Dark Portal / Waygate | Twin carved runic stone obelisks with architrave, swirling purple/cyan dimensional vortex inside, orbiting void particles and lightning arcs. |
| `marketplace` | Trading Post / Market | Colorful striped cloth market stalls (red/white & gold/blue awnings rippling in wind), stacked crates, grain sacks, merchant cart, swinging scale emblem. |
| `altar` | Altar of Kings / Cathedral Shrine | Stepped marble dais, winged angelic/heroic statue in center, four corner columns, twin sacred braziers burning with cyan/gold soul-flame. |
| `trophy-hall` | Hall of Heroes / War Monument | Classical colonnade pantheon with golden pediment, crossed golden swords & shield crest above entrance, victory torches, banner streamers. |

---

## 3. Autonomous Unit/Hero Life ("Living World" AI & Animation States)

In Warcraft III (`Stand - 1`, `Stand - 2`, `Stand - 3`, `Stand Ready`, `Stand Work`, `Stand Victory`, `Spell`, `Walk`) and Age of Empires III (`Idle`, `Bored`, `weapon_talk`, `cheer`, villager tasks):
- **Breathing & Weight Shift (`Stand - 1`)**: Continuous subtle torso rise/fall and weapon/shield counter-sway.
- **Bored / Fidget Cycles (`Stand - 2`, `Stand - 3`)**: Deterministic-yet-varied autonomous sub-actions every few seconds per unit:
  - **Head Turn / Look Around**: Unit glances left/right scanning the battlefield.
  - **Weapon Flourish / Practice Swing**: Knights/Marshals raise sword or tap shield; Rangers inspect bowstring; Mages twirl staff and emit a tiny arcane sparkle.
  - **Social Chatter / Nod**: When two idle units are within 2.5 tiles of each other, they periodically face each other, gesture, or nod (AoE3 Home City citizen / settler interaction).
  - **Patrol / Guard Micro-Pace**: Idle military heroes occasionally take 2-3 slow guard steps around their post and return.
- **Locomotion (`Walk`)**:
  - Multi-limbed stride cycle (alternating legs/boots, swinging opposite arm, bobbing torso/head).
  - **Footstep Dust Puffs**: Walking units kick up tiny fading dust clouds behind their heels (or water splashes if crossing shallow water, or mud splashes in rain).
  - **Cloth & Cape Physics**: Hero capes, plumes, and banners trail behind movement vector + oscillate with the live wind vector.
- **Active Work / Combat / Casting (`Stand Work` / `Attack` / `Spell`)**:
  - Running/working heroes swing weapons or channel glowing spell runes with rising arcane particles.
  - Workers visibly swing pickaxes/axes at destination nodes and carry a gold sack (gold glint) or wood bundle back to the Keep.

---

## 4. Environment, Terrain, Water & Wind Physics

### 4.1 Unified Wind Field (Driven by Real Local Forecast)
- Wind has real `speed_kmh`, `gust_kmh`, and `direction_deg` (meteorological direction -> world wind vector `(wx, wy)` + time-varying gust turbulence `gust(t)`).
- **What reacts to the wind vector**:
  1. **Trees & Foliage**: Multi-layered tree canopies (ground shadow + trunk + 3 foliage crown clusters) sway in the wind direction with per-tree phase offset; stronger gusts shed **falling/drifting leaves** carried along the wind vector.
  2. **Grass Blades & Reeds**: Procedural grass tufts on meadow tiles and cattails/reeds along water shorelines bend with wind waves passing across the field.
  3. **Water Waves & Whitecaps**: River/lake water tiles animate wave crests and specular sun/moon glints moving along the wind vector; shorelines render rhythmic lapping foam rings.
  4. **Cloth, Flags, Banners & Capes**: Building roof pennants, marketplace awnings, tavern signboards, and hero capes wave in the wind direction with frequency proportional to `wind_speed + gust`.
  5. **Smoke Plumes & Embers**: Tavern/Runeforge chimney smoke and brazier flames lean and drift downwind.
  6. **Clouds & Weather Particles**: Cloud shadows drifting across the terrain, rain streaks slanting at the wind angle, snow flakes swirling in wind eddies, or rolling mist banks.

### 4.2 Terrain Richness (WC3 World Editor + AoE3 Maps)
- **Natural Water Bodies**: Deterministic river/lake channels along region borders and low-elevation basins, with deep water, shallow water, sandy/rocky banks, and wooden bridges where roads cross water.
- **Road Network**: Packed-earth and cobblestone roads linking the `root` Keep capital to every region capital and building plot.
- **Forest Clusters & Doodads**: Dense tree clusters near map edges and region borders, boulders, wildflowers, mushrooms, campfires at neutral camps, and gold mine rock veins with sparkling ore.
- **Living Critters**: Wandering sheep/deer grazing on grass, frogs/ducks near water, birds flying with wind, and fireflies glowing at dusk/night.

---

## 5. Sound Design (Procedural WebAudio Engine)

- **Continuous Ambient Soundscape** (toggleable with `snd`, scaled by volume & weather):
  - **Wind Loop**: Pink/white noise through a resonant bandpass filter whose cutoff frequency and gain modulate with real wind speed and gusts.
  - **Rain / Storm Loop**: Filtered droplet noise + patter when real weather has rain/drizzle/showers, plus distant low-pass **thunder rumbles** when weather is thunderstorm (or stormy gusts).
  - **Day / Night Nature**: Subtle bird chirps (high sine FM chirps) during day/clear weather; cricket/cicada chorus + owl hoot at night.
  - **Forge / Campfire Crackle**: Subtle warm crackle and anvil chime when camera is near active buildings.
- **RTS Interaction SFX** (WC3/AoE3 inspired):
  - **Unit Select**: Heroic brass/chime chord by class archetype (metallic shield clink for martial, arcane harp shimmer for caster, bowstring pluck for ranger, drum/horn for commander).
  - **Move / Attack Order**: Crisp war-drum / boot-march thud + horn ack.
  - **Building Click**: Distinct sound per structure (`town-hall` bell chime, `runeforge` anvil hammer clang, `barracks` sword draw, `library` page/crystal hum, `tavern` mug/lute chord, `portal` void hum, `marketplace` coin jingle, `altar` choir chord, `watchtower` horn/bell).
  - **Resource / Quest Complete**: WC3-style triumphant fanfare arpeggio.

---

## 6. Real-Time Local Weather System

- **Location & Forecast Pipeline (`rtsd.py` + `world.py`)**:
  - Auto-detects user coordinates via IP geolocation (`https://get.geojs.io/v1/ip/geo.json` with fallback to `https://ipwho.is/` and `http://ip-api.com/json/`) with `User-Agent: rtsd/3.8`.
  - Queries **Open-Meteo** (`https://api.open-meteo.com/v1/forecast`) for current + hourly forecast (`temperature_2m`, `relative_humidity_2m`, `is_day`, `precipitation`, `rain`, `showers`, `snowfall`, `weather_code`, `cloud_cover`, `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`).
  - Cached for 10 minutes (`600s`) in memory + persisted to `.devin/rts/weather.json` so offline/tests never block or fail.
  - Exposed at `GET /weather` (and `POST /weather` override for testing/cycling weather presets: `live`, `clear`, `overcast`, `rain`, `storm`, `snow`, `fog`, `windy`) and included in `/snapshot` (`snap.weather`).
  - Header HUD badge (`#wxBtn`) shows real city + condition + temperature + wind (e.g. `Curitiba 13.2°C Overcast 11km/h ENE`), and clicking it cycles live forecast vs previewing weather states or opens forecast details!
