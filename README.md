# Tetum Morphology — DFA Engine

A focused, rule-driven morphology detector for the Tetum language using a deterministic finite automaton (DFA). This project targets segmentation and morpheme labeling (derivational/inflectional affixes, clitics, reduplication, compounding) for Tetum tokens.

---

## Scope
This repository implements a compact DFA-based analyzer tailored to Tetum morphology:
- segmentation into stems and affixes
- detection of reduplication and common compounding patterns
- handling of clitics and particles via preprocessing
- deterministic, rule-readable analyses suited for linguists and downstream pipelines

This README is solely about Tetum morphology and the DFA approach used to detect it.

---

## Tetum morphological notes (concise)
- Primary processes: concatenative affixation (prefixes/suffixes), reduplication, and compounding.
- Function words and particles play a strong role in syntax; some morphological marking appears via clitics/particles rather than rich inflection.
- Reduplication is productive for plurality/intensification/iterativity in many Austronesian languages; the engine provides explicit handling for repeated segments.
- Orthographic variants and simple alternations (e.g., vowel changes at morpheme boundaries) should be captured with orthographic rules in the builder.

(These notes are descriptive constraints used to design the DFA and rule set. Specific lexical entries and affix inventories live in the rules files.)

---

## Approach
1. Rules + lexicon → DFA builder: compile stems, prefixes, suffixes, reduplication patterns, and orthographic alternations into a deterministic automaton.
2. Preprocess tokens:
   - normalize orthography
   - separate/flag clitics and particles where predictable
3. Walk each token through the DFA to produce candidate segmentations and labels.
4. Rank analyses by rule priority and simple heuristics (longest-stem, rule weight).
5. Provide multiple analyses when ambiguity exists, with confidence scores.

Special handling:
- Reduplication: options include explicit copied transitions, a reduplication operator in rules, or a short-circuit module that recognizes repeated segments and proposes base+redup analyses.
- Clitics/particles: either peeled off before DFA pass or represented as optional transitions.

---

## Rules format (example — Tetum-focused)
Rules are JSON/YAML files edited by linguists. Minimal example (illustrative):

```json
{
  "lexicon": {
    "hanesan": {"pos": "ADJ"},
    "main": {"pos": "V"},
    "maun": {"pos": "N"}
  },
  "prefixes": [
    {"form": "ma", "tag": "DERIV", "type": "derivational"}
  ],
  "suffixes": [
    {"form": "n", "tag": "INF", "type": "inflectional"}
  ],
  "reduplication": [
    {"pattern": "full", "tag": "REPD"},
    {"pattern": "partial", "tag": "REPD_PART"}
  ],
  "clitics": [
    {"form": "ba", "tag": "DIR"},
    {"form": "mai", "tag": "MOTION"}
  ],
  "config": {
    "longest_match": true,
    "max_analyses": 6,
    "apply_clitic_preprocessing": true
  }
}
```

Note: the example entries are placeholders illustrating structure — replace with a curated Tetum lexicon and affix inventory.

---

## Quick start
Requirements:
- Python 3.8+

Install & run:
```bash
git clone <repo-url>
cd <repo>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# build DFA from rules
python scripts/build_dfa.py --rules rules/tetum_rules.json --out dfa_tetum.bin
# analyze tokens
python -m morphdfa.analyze --dfa dfa_tetum.bin --input tokens.txt --output analyses.json
```

Output: JSON per token with candidate segmentations, lemma (if determinable), morpheme tags, and confidence.

---

## Evaluation (recommended)
- Create a small gold standard of Tetum tokens with morpheme boundaries and labels.
- Metrics: segmentation accuracy (boundary F1), lemma accuracy, tag precision/recall/F1, coverage (tokens analyzed).
- Use iterative rule refinement: high-frequency error types → update orth/affix rules → rebuild DFA → re-evaluate.

---

## Limitations
- A purely deterministic DFA struggles with non-concatenative alternations unless explicitly encoded.
- Ambiguity and unseen neologisms require fallback strategies (e.g., lexicon expansion, ML fallback).
- Quality depends on the completeness of the Tetum lexicon and the coverage of reduplication/orthographic rules.

---

## Project layout (recommended)
- rules/            — Tetum rule files (JSON/YAML)
- src/              — DFA engine (Tetum-specific hooks)
- scripts/          — build, inspect, and test utilities
- data/             — annotated Tetum samples and lexicon
- tests/            — unit & evaluation tests

---

## Contact
Maintainer: Ediko-eng — your-email@example.com

If you provide a small Tetum lexicon or sample annotations, the rule-set and DFA can be adapted and tuned to improve segmentation accuracy.
