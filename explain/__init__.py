"""Explanation layer: facts computed from the engine, narrated by an LLM.

Three modules, in the order they run:

  facts.py     pure computation — what changed, what it did, and how much of
               the movement each lever is responsible for. No network, no LLM.
  narrate.py   sends those facts to Claude and returns prose. The model
               narrates; it never calculates.
  fallback.py  deterministic Spanish templates over the same facts, used
               whenever narrate.py cannot run (no key, no network, API error).

The split is the point: every number the user reads comes from `facts`, which
comes from `engine.spain` — the same engine `tests/fixtures/engine_anchors.json`
pins. The LLM only chooses words.
"""
from explain.facts import ExplanationFacts, build_facts
from explain.fallback import fallback_narration
from explain.narrate import NarrationResult, narrate

__all__ = ["ExplanationFacts", "build_facts", "fallback_narration",
           "NarrationResult", "narrate"]
