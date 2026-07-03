"""GuideWriter contract + gate tests. No GPU — validates a synthetic draft
and the content gate, plus reading-level of the prose."""
import pytest

from app.authoring.writer import ContentGateError, content_gate
from app.schemas.foot_check import ObservationTag
from app.schemas.guide_draft import (
    ClaimSource, ClaimStrength, GraphClaim, GuideBrief, GuideDraft,
    GuideSection, VideoBeat,
)

PROV = [
    ClaimSource(claim="wash and dry feet daily, especially between the toes",
                source="IWGDF 2023 Prevention Rec 4", source_year=2023,
                strength=ClaimStrength.strong),
    ClaimSource(claim="check your feet every day",
                source="IWGDF 2023 Prevention Rec 5", source_year=2023,
                strength=ClaimStrength.strong),
]

SECTIONS = [
    GuideSection(heading="What you might be seeing",
                 body="You may notice dry, flaky skin on your heels or the sides of your feet. "
                      "Sometimes the skin looks tight or feels rough when you touch it. "
                      "This is common and often easy to help at home.",
                 pull_quote="Dry skin is common and often easy to help."),
    GuideSection(heading="What helps day to day",
                 body="Wash your feet each day in warm water. Dry them gently, and be sure to "
                      "dry between your toes. Put a little lotion on the tops and bottoms, but "
                      "not between the toes. Check your feet every day in good light.",
                 pull_quote="Dry between your toes every time."),
    GuideSection(heading="What to bring up with your care team",
                 body="If the dry skin does not get better, or you see a crack that will not close, "
                      "that is worth showing your care team at your next visit. They can look "
                      "closely and help you make a plan.",
                 pull_quote="Cracks that won't close are worth showing your care team."),
    GuideSection(heading="When sooner is better",
                 body="If you see an open area, a color change, or swelling, sooner is better. "
                      "Reach out to your care team rather than waiting for your next visit.",
                 pull_quote="Open areas: sooner is better."),
]

BEATS = [
    VideoBeat(on_screen_text="Dry skin? You're not alone.",
              voiceover="Dry skin on your feet is common with diabetes.",
              b_roll_hint="soft close-up of a heel, warm light"),
    VideoBeat(on_screen_text="Wash, dry, moisturize.",
              voiceover="Wash daily, dry gently between the toes, then moisturize.",
              b_roll_hint="hands drying a foot with a towel"),
    VideoBeat(on_screen_text="Worth showing your care team.",
              voiceover="If a crack won't close, show your care team.",
              b_roll_hint="calm clinic waiting room"),
]


def _draft(**over) -> GuideDraft:
    base = dict(
        guide_id="FG-002", title="Caring for dry skin on your feet",
        tags=[ObservationTag.dryness_fissure], season=1,
        sections=SECTIONS, bee_body="dry skin, cracking, fissures on heels; how to moisturize feet safely.",
        video_beats=BEATS,
        graph_claims=[GraphClaim(subject_tag=ObservationTag.dryness_fissure,
                                 predicate="is_helped_by", object_text="daily washing and moisturizing",
                                 provenance_index=0)],
        provenance=PROV, writer_model_id="qwen3.5-32b-footguide",
        prompt_sha256="p" * 64,
    )
    base.update(over)
    return GuideDraft(**base)


class TestSchemaShape:
    def test_canonical_headings_enforced(self):
        bad = [GuideSection(heading="Intro", body="x" * 20) for _ in range(4)]
        with pytest.raises(ValueError):
            _draft(sections=bad)

    def test_requires_four_sections(self):
        with pytest.raises(ValueError):
            _draft(sections=SECTIONS[:3])

    def test_downstream_hooks_present(self):
        d = _draft()
        assert d.bee_body and len(d.video_beats) >= 3 and d.graph_claims


class TestContentGate:
    def test_clean_draft_passes(self):
        content_gate(_draft(), GuideBrief(
            guide_id="FG-002", title="Caring for dry skin on your feet",
            tags=[ObservationTag.dryness_fissure], season=1, provenance=PROV))

    def test_banned_word_in_voiceover_rejected(self):
        dirty = list(BEATS)
        dirty[0] = VideoBeat(on_screen_text="ok", voiceover="this could be an ulcer",
                             b_roll_hint="x")
        with pytest.raises(ContentGateError):
            content_gate(_draft(video_beats=dirty), GuideBrief(
                guide_id="FG-002", title="t", tags=[ObservationTag.dryness_fissure],
                season=1, provenance=PROV))

    def test_provenance_index_out_of_range_rejected(self):
        bad = [GraphClaim(subject_tag=ObservationTag.dryness_fissure,
                          predicate="is_helped_by", object_text="x", provenance_index=9)]
        with pytest.raises(ContentGateError):
            content_gate(_draft(graph_claims=bad), GuideBrief(
                guide_id="FG-002", title="t", tags=[ObservationTag.dryness_fissure],
                season=1, provenance=PROV))

    def test_dropped_provenance_rejected(self):
        with pytest.raises(ContentGateError):
            content_gate(_draft(provenance=PROV[:1]), GuideBrief(
                guide_id="FG-002", title="t", tags=[ObservationTag.dryness_fissure],
                season=1, provenance=PROV))


class TestBookletLayout:
    def _layout(self):
        from app.schemas.guide_draft import BookletSection
        return [
            BookletSection(title="THE CASE", maps_to=["What you might be seeing"], body="why a photo beats memory"),
            BookletSection(title="THE ROUTINE", maps_to=["What helps day to day"], body="four views per foot"),
            BookletSection(title="THE SIGNALS", maps_to=["What you might be seeing", "What to bring up with your care team"], body="worth watching vs showing"),
            BookletSection(title="CONSISTENCY", maps_to=["What helps day to day"], body="build your history"),
            BookletSection(title="ESCALATION", maps_to=["When sooner is better", "What to bring up with your care team"], body="sharing with care team"),
        ]

    def test_none_falls_back_to_canonical_four(self):
        r = _draft().booklet_render()
        assert [s["ordinal"] for s in r] == ["01", "02", "03", "04"]

    def test_five_section_layout_numbers_derived(self):
        r = _draft(booklet_layout=self._layout()).booklet_render()
        assert [s["ordinal"] for s in r] == ["01", "02", "03", "04", "05"]
        assert r[0]["title"] == "THE CASE"

    def test_layout_must_cover_all_canonical(self):
        from app.schemas.guide_draft import BookletSection
        with pytest.raises(ValueError):
            _draft(booklet_layout=[BookletSection(
                title="only one", maps_to=["What you might be seeing"], body="x")])

    def test_layout_unknown_heading_rejected(self):
        from app.schemas.guide_draft import BookletSection
        bad = self._layout()[:4] + [BookletSection(title="X", maps_to=["Not Real"], body="x")]
        with pytest.raises(ValueError):
            _draft(booklet_layout=bad)


class TestReadingLevel:
    def test_prose_is_grade_7_or_below(self):
        import textstat
        grade = textstat.flesch_kincaid_grade(_draft().full_text())
        assert grade <= 8.0, f"reading level too high: {grade}"
