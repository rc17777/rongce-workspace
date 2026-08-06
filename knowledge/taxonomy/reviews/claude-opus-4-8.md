# Review: claude-opus-4-8

Status: success

---

# Executive Summary

This design presents a **three-tier classification pipeline** for automatically ingesting policy documents into a knowledge base anchored by 12 core audit business lines. The architectural core—rule-based filtering followed by graduated LLM analysis—is sound and shows genuine systems thinking. The "radiation" metaphor (policies ripple outward to affect multiple business lines) accurately models the domain.

**The single most critical flaw** is the **Round 3 novelty detection threshold and incubation logic**. Setting `threshold: 3` independent sources before flagging a new business domain creates a 60–180 day blind spot during which emerging regulatory shifts (e.g., data asset auditing mandates) remain invisible to the business. In a compliance-driven industry, this latency is catastrophic. The system will correctly classify yesterday's work while missing tomorrow's revenue opportunities.

**The strongest element to preserve** is the **bi-directional radiation tracking** (`radiation_signals` in business_lines.yaml + reverse updates from Round 2 results). This turns the taxonomy from a static hierarchy into a living impact graph. It's the foundation for "which SOPs need updates" automation and is architecturally elegant.

**Cost estimates** are plausible if flash/pro pricing holds at ~$0.10/$1.00 per million tokens, but the design lacks fallback handling for model deprecation (DeepSeek-V4 will not be "flash tier" forever). **Timeline**: 9 days is feasible for a working prototype with manual testing, but not for production-grade error handling, backfill tooling, or the keyword AC automaton optimization.

**Catastrophic blind spot the other reviewers missed**: There is **no deduplication or conflict resolution for radiation hits**. A single policy triggering `relevance: high` for L4 in Round 2, after already matching L4 in Round 1, will create duplicate tags and double-count impact. The metadata structure shows `direct_hits: [L4, L12]` and `radiation_hits: [{line: L4, ...}]` coexisting without merge logic. This will pollute downstream RAG retrieval and make "show me all L4-impacting policies" queries return duplicates.

---

# Verdict: **APPROVE WITH CONDITIONS**

## Non-Negotiable Conditions

1. **Round 3 incubation threshold must drop to 1** with confidence gating (≥0.75) instead of evidence counting. Add a **"weak signal dashboard"** where single-source novel domains surface immediately for human triage, rather than waiting for 3 independent confirmations that may never arrive in time.

2. **Implement tag deduplication** in the post-processing layer: `final_business_lines = deduplicate(direct_hits ∪ {r.line for r in radiation_hits if r.relevance in [high, medium]})`. Store the provenance (Round 1 vs Round 2) separately for audit trails, but present a unified tag set.

3. **Add model version pinning and deprecation monitoring** to `business_lines.yaml` schema:
   ```yaml
   llm_config:
     round2_model: "deepseek-v4-flash"
     round2_fallback: "gpt-4o-mini"
     round3_model: "deepseek-v4-pro"
     round3_fallback: "gpt-4o"
     last_verified: "2026-07-11"
   ```
   
4. **Extend timeline to 14 days** or explicitly descope production error handling (retry logic, partial failure recovery, backfill scripts for taxonomy updates) and document these as post-launch debt.

5. **Add explicit handling for cross-cutting themes** discovered in Round 3. The prompt asks for `cross_cutting_theme` but the schema has no storage for it. If "ESG compliance" affects all 12 lines equally, it shouldn't spawn 12 孵化提案—it should trigger a taxonomy-level annotation or a meta-tag system.
