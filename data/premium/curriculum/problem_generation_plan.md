# Problem Generation Plan (Post-Phase 3C)

This document is an execution plan for generating premium problems in later phases.

## Inputs (Locked)

- `data/premium/curriculum/curriculum.json`
- `data/premium/curriculum/recommendation_graph.json`
- `data/premium/curriculum/learning_path.json`
- `data/premium/problem_template.json`

## Output Target

Generate approximately 75 premium executable problems, each compliant with template-required fields.

## Batching Strategy

### Batch 1: Foundations (Phases 1-2, 19 problems)

- Goal: stable easy/medium base with full executable assets
- Topics: Arrays & Hashing, Two Pointers, core primitives

### Batch 2: State Patterns (Phases 3-4, 18 problems)

- Goal: sliding window, stack, binary search, linked list/tree core
- Add first dependency-heavy chains

### Batch 3: Graph/Tree/Heap Expansion (Phases 5-7, 26 problems)

- Goal: major medium-hard coverage
- Include graph topology and heap hard tasks

### Batch 4: DP/Greedy/Intervals/Bit/Math Completion (Phases 8-10, 12 problems)

- Goal: finalize advanced curriculum and capstone readiness

## Per-Problem Generation Checklist

Every generated problem must include:

1. Metadata (`topic`, `subtopic`, `pattern`, `difficulty`, `estimated_minutes`, tags)
2. Educational assets (`statement_md`, `constraints_md`, `examples_md`, `editorial_md`)
3. Ordered hints
4. Reference solution with complexity claims
5. Starter code
6. Visible tests (>=3)
7. Hidden tests (>=3)
8. Learning objectives
9. Common mistakes
10. Recommendation graph links
11. RAG chunks by required chunk type
12. Versioning metadata

## Quality Gates per Batch

Batch passes only if all are true:

1. Validator pass:
   - `problem_validator.py`
   - `metadata_validator.py`
   - `curriculum_validator.py`
   - `solution_validator.py`
   - `testcase_validator.py`
2. Judge pass for all reference solutions
3. Recommendation edge integrity pass (no broken slugs)
4. RAG chunk completeness pass for all five chunk types
5. No legacy dataset leakage in runtime APIs

## Recommendation Graph Activation Plan

1. Insert prerequisite edges first.
2. Insert alternative/review/recovery/stretch edges.
3. Run duplicate-edge and orphan-edge checks.
4. Recompute recommendation seed strategy by phase.

## Spaced-Repetition Activation Plan

1. Apply baseline schedule policy from `curriculum.md`.
2. Attach first review tasks on first Accepted verdict.
3. Escalate review interval only when mastery criteria pass.
4. Route failed reviews via `recovery_edges`.

## Risk Controls

- Do not generate problems without full hidden tests.
- Do not ship problems with missing editorial or complexity metadata.
- Do not allow direct manual DB inserts bypassing template schema checks.
- Do not activate recommendations for problems missing prerequisites metadata.

## Completion Criteria

Generation phase completes only when:

1. All 75 planned slugs exist as active premium problems.
2. All validators pass with no critical issues.
3. Recommendation graph is fully connected per curriculum design.
4. Spaced-repetition scheduling works end-to-end for all difficulties.
