# Premium Curriculum Design (Phase 3C)

## Scope

- Curriculum size: **75 problems**
- Status: **design-only specification**
- Explicitly excluded in this phase:
  - problem statements
  - editorials
  - hints
  - testcase content

## Artifacts

- `curriculum.json`: full 75-problem catalog with required metadata and dependencies
- `learning_path.json`: ordered path, phase plan, and dependency source
- `recommendation_graph.json`: prerequisite/alternative/review/recovery/stretch edges
- `topic_statistics.json`: coverage, outcomes, and quality checks
- `problem_generation_plan.md`: generation execution plan for next phase

## Curriculum Coverage

| Topic | Count |
|---|---:|
| Arrays & Hashing | 7 |
| Two Pointers | 5 |
| Sliding Window | 5 |
| Stack | 5 |
| Binary Search | 5 |
| Linked List | 5 |
| Trees | 7 |
| Heap | 4 |
| Backtracking | 4 |
| Graphs | 7 |
| Dynamic Programming | 8 |
| Greedy | 3 |
| Intervals | 3 |
| Bit Manipulation | 3 |
| Math | 4 |
| **Total** | **75** |

## Difficulty Mix

| Difficulty | Count |
|---|---:|
| Easy | 20 |
| Medium | 46 |
| Hard | 9 |

## Learning Path Structure

The complete ordered path is in `learning_path.json.linear_path`.

Phase-wise progression:

1. Core Foundations
2. Hashing and Two-Pointer Expansion
3. Sliding Window and Stack Fluency
4. Rotations, Linked Lists, and Tree Core
5. Tree Depth and Heap Basics
6. Graph and DP Intermediate
7. Advanced Windows, Heaps, and Graphs
8. Dynamic Programming Deepening
9. Greedy and Interval Systems
10. Final Math/Bit Consolidation

## Recommendation Design

Graph design is in `recommendation_graph.json` with:

- `prerequisite_edges`
- `alternative_edges`
- `review_edges`
- `recovery_edges`
- `stretch_edges`

This graph is intended for:

- cold-start progression
- weak-topic recovery routing
- post-success stretch routing
- spaced revision linkage

## Spaced Repetition Policy

### Baseline schedule

1. Initial review: **+1 day**
2. Second review: **+3 days**
3. Third review: **+7 days**
4. Fourth review: **+21 days**

### Difficulty-adjusted schedule

- Easy: 1, 3, 7, 14 days
- Medium: 1, 3, 7, 21 days
- Hard: 1, 4, 10, 28 days

### Mastery criteria

A problem is marked mastery-ready when all hold:

1. 2 accepted submissions on separate days
2. 1 successful delayed recall at or after third review
3. Time-to-solve within topic benchmark range
4. No repeated critical error pattern in last two attempts

## Topic Learning Outcomes

Per-topic outcomes (skills, mistakes, exit criteria) are defined in:

- `topic_statistics.json.learning_outcomes`

## Quality Validation (Design-Time)

Design checks and status are in:

- `topic_statistics.json.quality_checks`

Current status:

- duplicate concepts: not detected
- prerequisite cycles/impossible chains: not detected
- progression balance: satisfied

## Notes for Phase 3D/3E Implementation

- `curriculum.json` is the source of truth for problem metadata planning.
- `recommendation_graph.json` is the source of truth for edge creation.
- Problem generation must follow `data/premium/problem_template.json`.
- No problem should bypass template-required fields.
