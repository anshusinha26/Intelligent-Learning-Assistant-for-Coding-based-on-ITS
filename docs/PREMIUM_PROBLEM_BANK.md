# Premium Problem Bank

## Active Runtime Dataset

The application runs on the premium dataset located at:

- `data/premium/problem_bank.json`

Current active size:

- **75 premium problems** (`dataset_tier='premium' AND is_active=1`)

Legacy content is archived at:

- `data/archive/legacy_problem_bank/`

Legacy rows remain in DB for archive traceability but are inactive:

- `dataset_tier='legacy'`
- `is_active=0`

## Schema Overview

Core runtime table:

- `problems`

Premium educational tables:

- `premium_problem_versions`
- `premium_problem_hints`
- `premium_problem_tests`
- `premium_problem_relationships`
- `premium_problem_rag_chunks`

## Educational Assets Stored

For each premium problem:

- statement, constraints, examples
- editorial
- reference solution
- starter code
- 3 progressive hints
- visible and hidden tests
- learning objectives
- common mistakes
- recommendation graph metadata
- RAG chunks by type

## Loader Contract

Loader: `load_sample_data.py`

Default behavior:

- Uses premium dataset
- Upserts premium core + educational assets
- Creates/updates demo user and sample activity

Optional legacy loading:

- Controlled by `LOAD_LEGACY_PROBLEM_BANK=true`
- Not enabled by default

## Runtime Query Filtering

Active APIs/services filter to premium active records:

- problem listing/detail
- attempts/submissions
- recommendations
- learner analytics
- revisions
- bookmarks/notes problem references
- AI tutor context

## Validation and Integrity

Validators:

- `problem_validator.py`
- `metadata_validator.py`
- `curriculum_validator.py`
- `solution_validator.py`
- `testcase_validator.py`

Migration introducing premium architecture:

- `migrations/0003_premium_problem_bank_architecture.up.sql`
