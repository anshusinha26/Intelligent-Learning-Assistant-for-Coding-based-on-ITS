CREATE INDEX IF NOT EXISTS idx_attempts_user_attempted_at
ON attempts(user_id, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_submissions_user_submitted_at
ON submissions(user_id, submitted_at DESC);
