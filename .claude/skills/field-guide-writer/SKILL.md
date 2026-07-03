---
name: field-guide-writer
description: Use when drafting or R&D-researching NEW Field Guide content for the OpenDiabetic library — new guides, evidence sourcing, clinical-alignment review, or feeding drafts into the knowledge-graph review queue. This is the DRAFT WRITER (distinct from field-guide-author, which is the formatting/routing standard). Use for the research-through-first-draft stage of any guide.
---

# Field Guide Writer (Draft + R&D)

The drafting engine for the guide library. Turns a clinical topic into a
citable, plain-language draft that enters the epistemology state-machine
review queue. Pairs with field-guide-author (structure/routing) and
wellness-language (register law).

## Evidence spine — anchor to authority, never to vibes
Primary source: IWGDF Guidelines (iwgdfguidelines.org), current edition 2023.
Every clinical claim in a draft carries a provenance tag → the knowledge
graph's write path expects {claim, source, source_year, strength}. Use the
IWGDF risk model as the organizing backbone:

| IWGDF risk | Meaning | Maps to our tier language |
|---|---|---|
| 0 | no LOPS/PAD | routine daily-check habit |
| 1 | LOPS or PAD | "worth watching" register |
| 2 | LOPS+PAD or LOPS+deformity | heightened daily attention |
| 3 | prior ulcer/amputation/ESRD | "in remission" — lifelong care |

Guideline-backed cornerstones a draft may educate on (self-care only):
daily wash + careful drying between toes, emollients on dry skin, toenails
straight across, never barefoot / no thin-soled slippers, daily self-exam,
once-daily skin-temperature self-monitoring for higher risk, and rapid
contact with a professional on any suspected pre-ulcer sign. Do NOT exceed
the self-care scope — assessment, debridement, offloading prescription, and
wound treatment are clinician scope and out of bounds for guides.

## The line we never cross (compliance)
IWGDF language is written FOR CLINICIANS. Our guides are FOR PATIENTS and are
educational, not a device, never diagnostic. Translate recommendations into
habits and "worth showing your care team" — never into "you have X" or
"do this medical procedure." wellness-language + banned-vocab.txt bind here.

## R&D workflow (research → draft → queue)
1. Scope the guide to ONE observation/habit; pick its ObservationTag(s).
2. Pull current IWGDF (and, if needed, ADA Standards of Care) support; record
   {source, year, recommendation strength}. Search live — guidelines update.
3. Draft to field-guide-author's template.md, grade 6–7, 600–900 words.
4. Attach provenance block; submit to review queue (FastAPI write path →
   HTMX review UI). Draft state = "proposed", never "published" by the writer.
5. Verify Bee routing: intended tags must retrieve the new guide.

## Standing rule
The writer proposes; a human reviewer promotes. No guide goes live from the
draft stage without passing the epistemology gate. File research gaps to
OPEN_ITEMS.md rather than inventing a citation.
