# HeyClicky - Research Report

## 1. WHAT IT IS

**HeyClicky** (formerly "Clicky") is a **consumer macOS AI companion app** - not hardware, not a browser extension. Category: voice-first AI assistant + agent spawner with screen awareness and an on-screen persona.

Site's own words (heyclicky.com):
- "an ai buddy that lives on your mac"
- "press the hotkey and it sees what you see, so you can ask it anything out loud and it'll walk you through whatever you're working on, or say 'heyclicky agent' and it'll go do the task for you."
- FAQ: "which apps does it work with? - anything on your screen. if you can see it, heyclicky can see it. no plugins or integrations needed."
- Privacy: "we only see your screen when you press the hotkey, and screenshots are never stored. we do keep basic text summaries so heyclicky has context."

**Two modes:** "Talk" (hotkey -> screenshot + voice -> spoken answer, with a blue "buddy" cursor that flies to and points at UI elements, plus on-screen drawing) and "Agent" ("heyclicky agent" -> background agent doing tasks: research, file cleanup, Notion/Gmail/Calendar/Reminders actions, "build Mac apps locally").

**Pricing:** Free (25 talk + 25 agent msgs/mo), Pro $20/mo (unlimited talk/dictation, 150 agent msgs), Max $100/mo (1,000 agent msgs), 20% annual. macOS 14.2+ only; Windows waitlist.

## 2. TECHNOLOGY

The **open-source predecessor** (`farzaa/clicky`, MIT, ~7.3k stars) is fully documented; current product is closed-source but shares lineage.

Verified architecture (repo AGENTS.md + DeepWiki + Isaac Flath teardown):
- **Native Swift/SwiftUI+AppKit** menu-bar app (LSUIElement=true), two NSPanels: control panel + **full-screen transparent click-through overlay** (ignoresMouseEvents=true, .screenSaver level, .canJoinAllSpaces, one per display).
- **The "buddy" is a fake cursor** - a blue triangle drawn inside its own overlay window. It never moves the real cursor; clicks pass through. Flight = bezier-arc animation.
- **Screen**: ScreenCaptureKit (SCShareableContent), hotkey-gated screenshots, multi-monitor.
- **Grounding**: ElementLocationDetector.swift calls **Claude Computer Use API purely as coordinate oracle** - picks Anthropic-recommended resolution closest to display aspect ratio (1280x800 for 16:10) to avoid distortion, remaps top-left->bottom-left origin. Model embeds `[POINT:x,y:label:screenN]` tags parsed by regex.
- **Voice**: push-to-talk (Ctrl+Option) via AVAudioEngine -> AssemblyAI u3-rt-pro streaming WS (OpenAI/Apple fallbacks) -> Claude SSE -> ElevenLabs eleven_flash_v2_5 TTS. Newer builds use GPT-Realtime 2.0 (triple-CTRL, experimental). Other providers per privacy policy: Deepgram, Cerebras.
- **Hotkey**: listen-only CGEvent tap - observes, doesn't consume.
- **Proxy**: Cloudflare Worker holds API keys (/chat,/tts,/transcribe-token); PostHog analytics; Sparkle auto-update via clicky-releases appcast.
- **Permissions**: Accessibility (hotkey + window ops + formerly AX reads), Screen Recording, Microphone, Screen Content.

**Agent mode (closed source - inferred):** connectors Gmail/Calendar/Drive/Notion; native-app actions via AppleScript/EventKit-style channels (Reminders demo); local file/shell actions; "Clicky can now click" shipped v1.0.12 - mechanism undisclosed. Changelog: proactive tracking + "all accessibility-data collection" REMOVED in v1.0.46 after pushback. Reviewers report GUI actions flaky (failed in Blender/game engine; guides instead).

## 3. COMPANY / SIGNALS

- **Founder:** Farza Majeed, SF - ex-founder buildspace (YC+a16z, shut down); ex-CTO Kanga, Visor.gg. Team ~1-10.
- **YC Spring 2026**; f.inc portfolio (founded 2025); **~$12M raised** (per interview transcript).
- **Launch:** Product Hunt Apr 11 2026 - 135 upvotes, #6 of day; Launch YC; viral demo ~3M views (Greg Brockman praise); ~15M cumulative views; ~7.3k stars; 1.2M messages by ~20 weeks.
- **Coverage:** TBPN interview, Isaac Flath teardown, MakerStack 7.6/10, therundown privacy review, ChatableApps 4.5/5, newsletters. Changelog to v1.0.51 (Sep 2026).

## 4. APPLICABILITY -> directed input without hijacking

| HeyClicky mechanism | Solves | Borrowable |
|---|---|---|
| Click-through overlay + **virtual second cursor** | "Mouse without focus" for VISUALIZATION - pointing/highlighting w/o touching real cursor | YES - NSWindow/NSPanel (or Win32 layered window) input pass-through + app-owned cursor sprite = zero interference |
| Computer-Use-as-coordinate-oracle + aspect matching + `[POINT:x,y]` tags | grounding "that button" -> pixel coords | YES - protocol + resize trick transfer verbatim |
| Listen-only event tap | global hotkey w/o swallowing keys | YES - CGEventTapCreate(listenOnly) / Windows LL hook |
| Connectors + AppleScript/EventKit/file/CLI actions | acting on apps WITHOUT HID injection - the real answer to input-scoping | YES - agent demos are all API/native-channel, not pixel-clicking |
| "Clicky can now click" (v1.0.12) | actual GUI actuation - mechanism UNDISCLOSED | WARNING - if CGEvent/SendInput it steals cursor; if AX AXPress it doesn't. Accessibility perm held so AX plausible, but unverified |

**Bottom line:** HeyClicky's documented innovation is NOT directed input - it's the opposite: a persona layer that *avoids* touching user input. Borrowable: (a) overlay virtual cursor, (b) tag-based grounding, (c) implicit architecture preferring app-native channels (AX actions, AppleScript, app APIs, shell) over synthetic HID. Its actual "click" path is closed-source and, per reviews, the weakest part.

## 5. VERDICT

**VERIFIED (primary):** open-source architecture in full - overlay fake cursor, ScreenCaptureKit, Computer-Use grounding, AssemblyAI->Claude->ElevenLabs, listen-only tap, Cloudflare proxy, permissions, Sparkle. Product: macOS-only, pricing, YC S26, founder, PH launch, virality. "Clicky can now click" shipped v1.0.12. Proactive+AX collection shipped then removed v1.0.46.

**INFERRED (strong, unconfirmed):** agent-mode actions predominantly app-native/API channels (connectors, AppleScript/EventKit, file/shell) - consistent with demos + flaky-GUI reviews. Agents likely orchestrate coding-agent-style loop + cloud connectors.

**UNVERIFIED:** exact clicking mechanism (CGEvent vs AX AXPress vs hybrid); whether clicking hijacks cursor/focus; any true per-app input-scoping; rumored "Fable 5" model mention.

**Site itself is thin marketing** - substance lives in open-source repo + Isaac Flath teardown. Transferable insight: persona cursor decoupled from OS cursor; real action through app-native channels - the non-hijacking direction F3 wants.

## 6. SOURCES (50)

1. heyclicky.com - homepage; product/pricing/FAQ - official
2. heyclicky.com/about - ship timeline - official
3. heyclicky.com/changelog - Clickys, proactive-removal, security audit, v1.0.51 - official
4. heyclicky.com/privacy-policy - providers, PostHog - official
5. github.com/farzaa/clicky - MIT open source, architecture - primary code
6. .../AGENTS.md - models, CGEvent tap, POINT tags, Worker routes - primary
7. .../ElementLocationDetector.swift - coordinate detection, aspect matching - primary
8. deepwiki.com/farzaa/clicky - system overview - tech doc
9. deepwiki 2.3.1 - overlay window flags, coordinate mapping - tech doc
10. deepwiki 2.6 - four macOS permissions - tech doc
11. deepwiki 4 - Sparkle/notarize pipeline - tech doc
12. github.com/farzaa/clicky-releases - appcast feed - primary
13. isaacflath.com/writing/how-clicky-works - independent teardown; overlay rationale - blog
14. ycombinator.com/companies/heyclicky - batch, location - official
15. ycombinator.com/launches/QNN - Launch YC text - official
16. hunted.space/dashboard/clicky-2 - PH stats, hunter, date - tracker
17. tbpndigest.com story - 8-week build, 4 models, Claude 4 default, 25c/action, 15+ connectors - press
18. podtail.nl TBPN episode - "executes user commands on computers" - podcast
19. freespoke.com TBPN listing - corroboration - index
20. youtube.com/watch?v=Z98ZuXR7kDM - founder interview - video
21. you-tldr.com transcript - "$12M raised" - transcript
22. farza.com - founder bio (buildspace, a16z/YC) - personal
23. linkedin.com/in/farza-majeed-76685612a - role, company size - profile
24. LinkedIn "Introducing Clicky Agents" - agent demos (Reminders, desktop, Mac apps) - founder post
25. LinkedIn "Built some new stuff... v1.0.12" - "Clicky can now click", Gmail/Cal/Drive - founder post
26. LinkedIn screen-aware dictation post - Claude Code/Gmail dictation - post
27. LinkedIn YC congratulation post - launch signal - social
28. techtwitter.com/profiles/farzatv - tweet archive (v1.0.12 features) - mirror
29. unrollnow.com/status/2060865350036750847 - GPT-Realtime 2.0 thread - mirror
30. explainx.ai blog - 3M-view demo analysis - blog
31. neatprompts.com - 15M views, 7.3k stars, PH #6 - analysis
32. everydev.ai/tools/hey-clicky - feature listing - directory
33. makerstack.co/reviews/clicky-review - 7.6/10, MIT/Windows waitlist - review
34. therundown.ai/tools/clicky - pricing + privacy audit, no SOC2 - review
35. chatableapps.com/tools/heyclicky - user reviews - review
36. theaiway.net/products/clicky - pros/cons - review
37. hokai.io/hub/tools/heyclicky - pricing/limits table - directory
38. pivotnews.ai/build/story/heyclicky - site mirror incl FAQ - mirror
39. macaiapps.com/apps/clicky - listing - directory
40. macfolio.com blog - YC-backed app guide - blog
41. artofsm.art review - hands-on: agents fail Blender/game engine, guides instead - review
42. returner.fund/founders/farza-majeed + /companies/heyclicky - IG archive incl GPT Realtime 2.0 - profile
43. f.inc/portfolio/heyclicky - founded 2025, Farza - investor
44. superhuman.ai newsletter - "can now click directly on your screen" - newsletter
45. whatsupinai.beehiiv.com - same click claim - newsletter
46. github.com/marvkr/clicky - fork driving local claude/codex CLIs - community
47. github.com/lefterisloukas/clicky-windows-parallel-and-memory - community Windows port (pynput observe-only) - community
48. github.com/jasonkneen/openclicky - OpenClicky rebuild w/ Sparkle - community
49. Forks: Arshad-Suhale/Hey-clicky, dep/clicky, aharlap/heyclicky-demo, mospective/clicky, Milkmange/clicky - community
50. clicky-redesigned.vercel.app - fan redesign - unofficial
