CREATE INDEX IF NOT EXISTS idx_problems_dataset_active
ON problems(dataset_tier, is_active, topic, difficulty);

CREATE TABLE IF NOT EXISTS premium_problem_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    statement_md TEXT NOT NULL,
    constraints_md TEXT NOT NULL,
    examples_md TEXT NOT NULL,
    editorial_md TEXT NOT NULL,
    reference_solution TEXT NOT NULL,
    starter_code TEXT NOT NULL,
    time_complexity TEXT NOT NULL,
    space_complexity TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    learning_objectives_json TEXT NOT NULL,
    common_mistakes_json TEXT NOT NULL,
    recommendation_graph_json TEXT NOT NULL,
    is_current INTEGER DEFAULT 1 CHECK (is_current IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS premium_problem_hints (
    hint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    hint_order INTEGER NOT NULL,
    hint_md TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS premium_problem_tests (
    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    visibility TEXT NOT NULL CHECK (visibility IN ('visible', 'hidden')),
    input_json TEXT NOT NULL,
    expected_json TEXT NOT NULL,
    explanation TEXT,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS premium_problem_relationships (
    edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    related_problem_id TEXT NOT NULL,
    edge_type TEXT NOT NULL CHECK (edge_type IN ('prerequisite', 'alternative', 'follow_up', 'review', 'recovery', 'related')),
    weight REAL DEFAULT 1.0,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE,
    FOREIGN KEY (related_problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS premium_problem_rag_chunks (
    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    chunk_type TEXT NOT NULL CHECK (chunk_type IN ('statement', 'editorial', 'hints', 'common_mistakes', 'learning_objectives')),
    chunk_text TEXT NOT NULL,
    embedding_model TEXT,
    embedding_vector TEXT,
    content_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems (problem_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_premium_problem_versions_unique
ON premium_problem_versions(problem_id, version);

CREATE UNIQUE INDEX IF NOT EXISTS idx_premium_problem_versions_current
ON premium_problem_versions(problem_id)
WHERE is_current = 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_premium_problem_hints_unique
ON premium_problem_hints(problem_id, version, hint_order);

CREATE INDEX IF NOT EXISTS idx_premium_problem_tests_visibility
ON premium_problem_tests(problem_id, version, visibility);

CREATE UNIQUE INDEX IF NOT EXISTS idx_premium_problem_relationships_unique
ON premium_problem_relationships(problem_id, related_problem_id, edge_type);

CREATE INDEX IF NOT EXISTS idx_premium_problem_rag_chunks_lookup
ON premium_problem_rag_chunks(problem_id, version, chunk_type);

UPDATE problems
SET dataset_tier = 'legacy', is_active = 0
WHERE COALESCE(dataset_tier, 'premium') = 'premium'
  AND problem_id NOT IN (
        SELECT DISTINCT problem_id FROM premium_problem_versions
  );

DELETE FROM recommendations
WHERE problem_id IN (
    SELECT problem_id FROM problems WHERE dataset_tier = 'legacy'
);

DELETE FROM revision_schedule
WHERE problem_id IN (
    SELECT problem_id FROM problems WHERE dataset_tier = 'legacy'
);

DELETE FROM bookmarks
WHERE problem_id IN (
    SELECT problem_id FROM problems WHERE dataset_tier = 'legacy'
);

DELETE FROM notes
WHERE problem_id IN (
    SELECT problem_id FROM problems WHERE dataset_tier = 'legacy'
);
