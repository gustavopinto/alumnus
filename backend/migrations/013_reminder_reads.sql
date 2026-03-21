-- Per-user read state for reminder notifications (novo lembrete de outro usuário)
CREATE TABLE IF NOT EXISTS reminder_reads (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_id INTEGER NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
    read_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, reminder_id)
);

CREATE INDEX IF NOT EXISTS idx_reminder_reads_user_id ON reminder_reads(user_id);
