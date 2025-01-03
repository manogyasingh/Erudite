CREATE TABLE IF NOT EXISTS knowledge_graphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'started',
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_graphs_user_id ON knowledge_graphs(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_graphs_uuid ON knowledge_graphs(uuid);

-- Trigger to update the updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_knowledge_graphs_timestamp 
    AFTER UPDATE ON knowledge_graphs
BEGIN
    UPDATE knowledge_graphs SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
