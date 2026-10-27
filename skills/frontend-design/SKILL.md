---
name: frontend-design
description: Use when building new UI or reshaping an existing one and the result must look distinctive and intentional, not templated. Guides aesthetic direction, typography, layout, and copy so the page has a specific point of view for this brief.
triggers: [user, model]
---

# Frontend Design

Approach this as the design lead at a studio known for giving every client a
distinct visual identity. This client has already rejected proposals that
felt cliche or templated, and is paying for a distinctive point of view:
make deliberate, opinionated choices about palette, typography, and layout
that are specific to this brief, and take aesthetic risk if justified.

Source: Apache-2.0 port of https://github.com/anthropics/skills/tree/main/skills/frontend-design
(Anthropic skills repo, SKILL.md).

Relationship to `impeccable`: this skill sets the aesthetic direction up
front (palette, type, layout concept, principles). `impeccable` is the
polish pass afterward (details, consistency, finish). Use frontend-design
before building; use impeccable before shipping.

## Ground designs in the subject matter

If the brief does not identify the product or subject matter, identify it
first and confirm with the client. Propose one concrete subject, the
audience, and the design's primary job. Use memory or project context for
preference hints. The subject's industry, materials, and vernacular are
where distinctive visual choices come from: a toy for kids aged 8-11 and
a dashboard for financial analysts are aesthetically different worlds.
Build with the brief's real content throughout.

## Design principles

For web designs, the hero is the first thing viewers see. Open with the
most characteristic thing in the subject's world, in the most appropriate
form: a headline, an image, an animation, a live demo, an interactive
moment. Be deliberate: a big number with a small label, supporting stats,
and a gradient accent is the default treatment, so only use it if that is
truly the best option.

Typography carries the personality of the page. You do not need a different
typeface for display and body: use one family or two, and if two, make them
clearly distinct. Choose typefaces deliberately, not the defaults you would
reach for on any other project, and set a clear type scale following The
Elements of Typographic Style guidance with intentional weights, widths,
and spacing. When type is a headline or visual element, use the type
treatment itself as an active part of the design, not a neutral delivery
vehicle.

Default to line lengths under 80 characters. Serif faces can run slightly
longer; give serif body text slightly more line-height than sans-serif.

Avoid these default typographic treatments; they are the commonest tells of
a generated page:

- Accenting just a single word or phrase in a headline (one word in
  italic/bold or a different color).
- Using all caps for labels.
- Adding unnecessary typographic labels above content.

Visual structure is information. Outlines, borders, numbering, eyebrows,
dividers, and labels encode information about the content rather than
decorate it. Many generic designs use numbered markers (01 / 02 / 03), but
that is only appropriate if the content actually is a sequence, like a
stepped process or a timeline. Check before adding numbered markers.

Use non-user-triggered motion sparingly and deliberately, only to draw
attention. A single orchestrated moment (one page-load sequence or one
reveal) lands better than scattered effects; fade-and-slide-up entrances
on each section and hover transitions on every card are the generic
default and read as generated. Motion that answers a person's action
(opening, expanding, confirming) is welcome when it shows what changed.

Consider written content carefully. A brief may not contain real content,
so write copy and placeholders yourself. Copy can make a design feel as
templated as the visuals. See "More on writing in design" below.

## Process: plan, review against the brief, build, critique

For calibration, generated design right now clusters around these traits:

1. A warm cream background (near #F4F1EA) with high-contrast serif display
   and a terracotta or warm-clay accent (often near #D97757).
2. A near-black background with a single bright acid-green or vermilion
   accent.
3. A broadsheet-style layout with hairline rules, zero border-radius, and
   dense newspaper-like columns.
4. The SaaS-card kit: identical rounded cards, one border-radius on
   everything regardless of hierarchy, the same soft grey shadow
   (rgba(0,0,0,.1)) under each, gradient washes as decoration.
5. Template chrome that appears whatever the subject: tracked-out ALL-CAPS
   eyebrow labels above every heading; meta strings joined with middle
   dots; labels built as 'WORD : fragment'; tinted near-black (#0B0B0B,
   #111) standing in for black; a monospace face for small data labels; an
   arrow appended to every link and button.

All traits are legitimate for some briefs, but they are defaults rather
than choices, and they appear regardless of subject. Where the brief pins
down a visual direction, follow it exactly, including when it asks for one
of these looks. Where it leaves an axis free, do not spend that freedom on
a default.

Work in two passes.

Pass 1: brainstorm a short design plan from the brief. Create a compact
token system:

- Color: 4-6 named hex values for the core base palette.
- Type: the typefaces and their roles.
- Layout: a layout concept using one-sentence prose descriptions and ASCII
  wireframes to ideate and compare. Include alignment guidance: left,
  center, or justified.
- Principles: high-level guidance for what makes this page unique.

Then review the plan against the brief before building. If any part reads
like the generic default you would produce for any similar page rather
than a choice made for this specific brief, revise that part, say what you
changed and why. Only after confirming relative uniqueness, write code
following the revised plan.

When writing code, manage CSS selector specificity carefully. Classes that
cancel each other out are a common failure (a type-based selector like
`.section` versus an element selector like `.cta`), especially with
padding/margin between sections.

## Restraint and self-critique

Spend your boldness in one place. Let one element be the memorable thing,
keep everything around it quiet and disciplined, and cut any decoration
that does not serve the brief. Build to a quality floor without announcing
it: responsive down to mobile, visible keyboard focus, reduced motion
respected, visually accessible, harmonious palettes. Critique your own
work as you build, taking screenshots to review if your environment
supports it. Chanel's advice applies: before leaving the house, look in
the mirror and remove one accessory. If you have a place to jot notes about
what you have tried, it helps future passes stay fresh.

## More on writing in design

Words appear in a design for one reason: to make it easier to understand
and use. They are design content, not decoration. Bring the same
intentionality to copywriting that you bring to spacing and color. Before
writing anything, ask what the design needs to say and how it can best be
said to help the person navigate the experience.

Write from the end user's perspective. Name things by what users will
understand, not by how the system is built. A user manages notifications,
not webhook config. Describe what something is or does in plain terms
rather than selling it. Specific and legible beats clever.

Use active voice by default. A CTA says exactly what happens when used:
"Save changes," not "Submit." An action keeps the same name through the
flow, so the button that says "Publish" produces a toast that says
"Published." Consistent vocabulary is how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain
what went wrong and how to fix it, in the interface's voice. Errors do not
apologize and are never vague. An empty screen is an invitation to act.

Keep the tone conversational: plain verbs, sentence case, no filler, tone
matched to brand and audience. Each written element does exactly one job.
