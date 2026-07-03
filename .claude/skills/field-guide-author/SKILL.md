---
name: field-guide-author
description: Use when writing, editing, or structuring Field Guide content — the educational guide collection, guide metadata, Bee FTS5 routing bodies, seasonal drops, or reading-level review of any educational content.
---

# Field Guide Authoring

Guides are the payoff of every check: observation → guide → action the user
can actually take. 22 guides / 3 seasons; FG-003 (Foot Photos) is the
canonical next drop.

## Structure → template.md
guide_id (FG-NNN), title (verb-forward, plain), body sections: What you
might be seeing / What helps day to day / What to bring up with your care
team / When sooner is better. 600–900 words. One idea per paragraph.

## Language rules (wellness-language skill applies + these)
- Reading level: grade 6–7. Short sentences. Second person.
- Audience has retinopathy rates worth respecting: content must survive
  screen readers and large type — no meaning carried by images alone.
- Never "you have X." Always "worth showing your care team."
- Every guide ends with the disclaimer line.

## Bee routing law
The FTS5 body must contain the retrieval terms for its ObservationTags
(see _TAG_QUERIES in app/bee/retrieve.py). New guide = verify every intended
tag actually retrieves it (test: each tag routes to ≥1 guide; none_noted
routes to FG-003). Content ships as data (FOOTCHECK_GUIDES_PATH), not code.
