# storytold org repo triage (ISSUE_03 step 0)

Verified enumeration 2026-11-17 via `gh api orgs/storytold/repos`. Org now
lists **82 public repos** (recon doc said 44; the org grew and new craft
apps shipped). Fields: name, primary language, license, stars, last push.

## Craft suite - consumable engines (Rust, Apache-2.0 unless noted)

Clean-room Adobe/Office analogs; typed command registries via CLI/JSON/MCP.

| Repo | Stars | Analog |
|---|---|---|
| photocraft | 80048 | Photoshop (layers/masks/adjustments, real PSD) |
| artcraft | 41365 | intentional crafting IDE (2D/3D compositing, posing) |
| craft-anything | 35573 | "understand how any software works" meta-app |
| pdfcraft | 21000 | Acrobat |
| filmcraft | 18478 | Premiere (nonlinear video edit) |
| wordcraft | 18191 | Word |
| lightcraft | 16106 | Lightroom (non-destructive photo) |
| vectorcraft | 11840 | Illustrator |
| effectcraft | 8913 | After Effects (motion graphics/compositing) |
| cadcraft | 8208 | AutoCAD |
| gridcraft | 7618 | Excel |
| designcraft | 5312 | InDesign (page layout) |
| figcraft | 5089 | Figma (interface design/prototyping) |
| deckcraft | 4844 | PowerPoint |
| soundcraft | 4423 | DAW (ProTools analog) |
| artcraftx | 1131 | ArtCraft variant |
| texturecraft | 682 | 3D texture painting |
| anicraft | 455 | 2D animation editor |
| materialcraft | 406 | node-based material designer |
| autocraft | 33 | TS (not Rust) |

New vs recon: designcraft, figcraft, effectcraft, materialcraft,
texturecraft, anicraft, craft-anything, artcraftx. The suite expanded
past the original 12.

## Shared craft infrastructure (Apache-2.0 unless noted)

| Repo | Purpose |
|---|---|
| craft-libs | shared Rust crates monorepo (promotable libs) |
| craft-launcher | app launcher (5.4k stars) |
| craft-ai-integrations | AI layer: providers, keys, connections |
| craft-extensions | shared themes/plugins/resources |
| craft-fonts | bundled fonts |
| craft-i18n | TSV translations |
| artcraft-services | backend/web frontend. License NOASSERTION, verify before consuming |
| craft-skills | shared agentic-dev skill corpus |
| craft-wiki | docs wiki |
| craft-contrib | contributions meta |
| craft-pr-review-tool | PR tooling |
| craft-repo-status-app | CI/PR status viewer |
| craft-launcher-assets | runtime-downloaded pictures |
| egui / wgpu / winit / harfbuzz | upstream forks; check divergence before using |

## Corpus / test data (Apache-2.0)

cadcraft-corpus, photocraft-corpus, effectcraft-corpus. Labeled test
media, useful as eval fixtures without cloning app repos.

## Capture / 3D / mocap (mixed licenses)

| Repo | License | Note |
|---|---|---|
| spark | MIT | THREE.js Gaussian Splatting renderer; PLY/SPZ/SPLAT/KSPLAT/SOG |
| LiveScan3D | MIT | real-time 3D reconstruction (2021, stale) |
| bevy-mocap | none | Bevy exploration |
| cloudcam + CloudCamPlugin | none | pointcloud pipeline to UE |
| k4a-sys-temp | MIT | patched Azure Kinect sys crate (linux build) |
| xsens-packet-send | none | mocap packet relay (2022) |
| motion-capture-data | none | session data |
| point-generator | none | DEPRECATED |
| hanashi-graphics-demo | none | fyrox wasm demo (2023) |

## Audio ML (mostly unlicensed; verify before use)

storyteller-ml (Tacotron), realtime-voice-conversion, vits-finetuning
(MIT), fakeyou-recast, discord-vocodes, voder-proxy.

## Legacy UE plugins / game projects

ActorSpawningPlugin, EventCenterPlugin, RuntimeAudioImporter (MIT),
RuntimeFilesDownloader (MIT), UE4-OSC (MIT), UnrealZeroMQ, AnimationTest,
StreamTwo, HyperJail, Azure-Kinect-Sample-for-Unity. All 2020-2023,
stale, not consumable for craft-bridge.

## Infra / misc

cloud-worker, discord-github-ticket-relay (MIT), font-preview-service,
github-media, html_test, indd-utils (INDD->IDML, Apache-2.0),
irsa-manager (MIT), placeholder-artcraft, redirect-vocodes,
terraform-aws-observability-accelerator, torchscript-models, winprint.rs
(BSD-3), storyteller-bevy.

## Step-0 conclusions for ISSUE_03

1. **Consume-first set for craft-bridge**: photocraft, filmcraft,
   vectorcraft, lightcraft, effectcraft (motion graphics, direct overlap
   with the animation-direction pipeline), gridcraft, deckcraft. All
   Apache-2.0, all pushed within 24h of enumeration (org is hyperactive).
2. **Verify-license set**: artcraft-services, harfbuzz, audio-ML repos
   carry NOASSERTION or no license.
3. **Skip**: legacy UE plugins, deprecated point-generator, upstream
   forks (egui/wgpu/winit exist for their own builds, not for us).
4. Next step per issue: shallow-clone craft suite + craft-libs, verify
   command registries and MCP entry points against source (recon claims
   650+/500+ cmds, unverified).
