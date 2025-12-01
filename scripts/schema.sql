-- XPBot Database Schema
-- Table for tracking user XP and voice statistics

CREATE TABLE IF NOT EXISTS user_stats (
    guild_id        BIGINT NOT NULL,
    user_id         BIGINT NOT NULL,
    total_xp        INTEGER NOT NULL DEFAULT 0,
    level           INTEGER NOT NULL DEFAULT 0,
    xp_into_level   INTEGER NOT NULL DEFAULT 0,
    total_voice_sec BIGINT NOT NULL DEFAULT 0,
    last_voice_join TIMESTAMPTZ NULL,  -- tracking last join for recovery after restart
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, user_id)
);

-- Index for leaderboard queries (sorted by XP descending)
CREATE INDEX IF NOT EXISTS idx_user_stats_leaderboard
ON user_stats (guild_id, total_xp DESC, total_voice_sec DESC);

-- Index for timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_user_stats_updated
ON user_stats (updated_at);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on every update
CREATE TRIGGER update_user_stats_updated_at
    BEFORE UPDATE ON user_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
