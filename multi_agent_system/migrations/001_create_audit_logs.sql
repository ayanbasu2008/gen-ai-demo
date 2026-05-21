CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT,
  source TEXT,
  content TEXT,
  status TEXT,
  timestamp TIMESTAMP
);
