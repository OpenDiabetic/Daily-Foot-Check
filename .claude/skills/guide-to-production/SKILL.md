---
name: guide-to-production
description: Use when turning an approved GuideDraft into finished deliverables — Claude-Design booklets/one-pagers, short-form vertical videos, knowledge-graph nodes, Bee corpus entries, or the published library. The content-supply-chain skill: one guide source → every downstream artifact. Use whenever rendering, packaging, or distributing guide content.
---

# Guide → Production

One approved GuideDraft is the SOURCE ARTIFACT. This skill governs how it fans
out. Never author net-new clinical content here — production renders what the
writer wrote and the reviewer approved. If content is missing, go back to
field-guide-writer, not into the renderer.

## Precondition (hard gate)
Only `state=published` GuideDrafts enter production. A proposed/in_review draft
NEVER renders to a distributable. The draft's provenance + disclaimer travel
with every artifact — booklet colophon, video end-card, graph node metadata.

## The five renderers (all read the same GuideDraft fields)
1. **Booklet / one-pager (Claude Design):** sections → spreads; pull_quotes →
    display callouts; Hive Calm tokens (propolis/wax/honey, Fraunces +
    Atkinson Hyperlegible). Large-type, screen-reader-sane, high contrast —
    the audience has elevated low-vision rates. Every piece ends on the
    disclaimer. Output PDF/PNG via canvas-design or Claude Design.
2. **Short-form video:** video_beats → vertical 30–60s. on_screen_text is the
    caption track (always-on captions, not optional — accessibility + silent
    autoplay). voiceover is the script. b_roll_hint guides footage (own
    footage or licensed only — never scrape). End card: "worth showing your
    care team" + disclaimer.
3. **Knowledge graph:** graph_claims → edges {subject_tag → predicate →
    object_text}, each carrying provenance_index → source. This is the
    intelligence layer; claims are queryable and every edge is sourced.
4. **Bee corpus:** bee_body → FTS5 row for retrieval; verify the guide's tags
    actually retrieve it post-index (routing test).
5. **Library page:** full guide, canonical URL by guide_id, tags faceted.

## Long-form layout law (booklet / library)
Feature guides carry an optional `booklet_layout` — 4-6 editorial sections
(e.g. THE CASE / THE ROUTINE / THE SIGNALS / CONSISTENCY / ESCALATION). Rules:
- Section NUMBERS ("01 · 02 · 03") are DERIVED at render from list position
  via `booklet_render()` — never stored, so numbering cannot lie.
- Every booklet section `maps_to` real canonical heading(s); the four
  canonical sections remain the clinical spine that tier/graph/Bee read.
- Booklet layout REORGANIZES canonical content — it introduces no new clinical
  claims. If `booklet_layout` is None, the renderer falls back to the four
  canonical sections directly.
- The provenance colophon lists every sourced claim; verify each traces to a
  `provenance[]` entry before publishing.

## Wellness-language + zero-retention still bind
No banned vocabulary survives into any rendered surface (the writer's content
gate already ran; re-assert on any human-edited copy). Production analytics
are PHI-free and aggregate (see adoption skill). Distribution never attaches
user data to content.

## Distribution law
Care-team channel first (verifiable PDF), then ZimaOS/library, then social
shorts. Every distributed artifact is idempotent from its GuideDraft hash —
re-render is deterministic, so versions are traceable. File any renderer gap
to OPEN_ITEMS.md.

## Build recipe
1. Fetch published GuideDraft by guide_id.
2. Select renderer(s); map fields (never invent content).
3. Apply Hive Calm tokens / caption rules / graph schema as above.
4. Re-assert disclaimer + vocab on final surface.
5. Emit artifact + record {guide_id, draft_sha256, renderer, artifact_hash}
    for traceability. Test: artifact contains disclaimer; graph edges resolve
    to sources; Bee retrieves by tag.
