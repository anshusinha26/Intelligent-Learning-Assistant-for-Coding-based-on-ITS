DROP INDEX IF EXISTS idx_premium_problem_rag_chunks_lookup;
DROP INDEX IF EXISTS idx_premium_problem_relationships_unique;
DROP INDEX IF EXISTS idx_premium_problem_tests_visibility;
DROP INDEX IF EXISTS idx_premium_problem_hints_unique;
DROP INDEX IF EXISTS idx_premium_problem_versions_current;
DROP INDEX IF EXISTS idx_premium_problem_versions_unique;
DROP INDEX IF EXISTS idx_problems_dataset_active;

DROP TABLE IF EXISTS premium_problem_rag_chunks;
DROP TABLE IF EXISTS premium_problem_relationships;
DROP TABLE IF EXISTS premium_problem_tests;
DROP TABLE IF EXISTS premium_problem_hints;
DROP TABLE IF EXISTS premium_problem_versions;
