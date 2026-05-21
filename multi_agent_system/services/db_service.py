import asyncpg
from pathlib import Path
from datetime import datetime
from common.utils import logger
from common.settings import settings


class DatabaseService:
    def __init__(self, uri: str | None = None):
        self.uri = uri or settings.POSTGRES_URI
        self.pool = None

    async def init(self, run_migrations: bool = True):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(self.uri, min_size=1, max_size=5)
        logger.info("Database connection pool initialized.")
        if run_migrations:
            await self.apply_migrations()

    async def close(self):
        """Close connection pool cleanly."""
        if self.pool is not None:
            await self.pool.close()
            logger.info("Database connection pool closed.")

    async def apply_migrations(self):
        """Apply SQL files from migrations directory in lexical order."""
        migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
        if not migrations_dir.exists():
            logger.warning("Migrations directory not found: %s", migrations_dir)
            return

        migration_files = sorted(migrations_dir.glob("*.sql"))
        if not migration_files:
            logger.info("No migration files found in: %s", migrations_dir)
            return

        async with self.pool.acquire() as conn:
            for migration_file in migration_files:
                sql = migration_file.read_text(encoding="utf-8").strip()
                if not sql:
                    continue

                # Execute each statement individually to avoid multi-statement driver issues.
                statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
                for statement in statements:
                    await conn.execute(statement)

                logger.info("Applied migration: %s", migration_file.name)

    async def insert_audit_log(self, log: dict):
        """Insert audit log into database."""
        async with self.pool.acquire() as conn:
            # Convert timestamp string to datetime object
            timestamp_str = log.get("timestamp")
            if isinstance(timestamp_str, str):
                try:
                    # Try parsing ISO format timestamp
                    timestamp_obj = datetime.fromisoformat(timestamp_str)
                except (ValueError, TypeError):
                    # Fall back to current time if parsing fails
                    timestamp_obj = datetime.utcnow()
            else:
                # Use provided datetime or current time
                timestamp_obj = timestamp_str or datetime.utcnow()
            
            await conn.execute(
                """
                INSERT INTO audit_logs (id, source, content, status, timestamp)
                VALUES ($1, $2, $3, $4, $5)
                """,
                log.get("id"),
                log.get("source"),
                log.get("content"),
                log.get("status"),
                timestamp_obj,
            )
            logger.info("Audit log inserted: %s", log.get("id"))

    async def fetch_logs(self, limit: int = 10):
        """Fetch recent audit logs."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, source, content, status, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT $1",
                limit,
            )
            return [dict(row) for row in rows]

    async def insert_escalation(self, escalation: dict):
        """Insert escalation event into database."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO escalations (id, issue, source, timestamp, action)
                VALUES ($1, $2, $3, $4, $5)
                """,
                escalation.get("id"),
                escalation.get("issue"),
                escalation.get("source"),
                escalation.get("timestamp"),
                escalation.get("action"),
            )
            logger.info("Escalation recorded: %s", escalation.get("id"))
