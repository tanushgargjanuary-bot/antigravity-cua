from __future__ import annotations

import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

STATE_DIR = Path.home() / ".antigravity-cua"
STATE_DB = STATE_DIR / "state.db"

@dataclass
class SandboxSession:
    space_id: str
    provider: str
    image: str
    status: str
    created_at: float
    lease_expires_at: float
    endpoint_url: str
    owner_pid: int

class SessionManager:
    """Production-grade SQLite persistence layer with lease management and auto-reaping."""

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.db_path = Path(db_path) if db_path else STATE_DB
        self._init_db()

    def _execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                cursor = conn.execute(query, params)
                return cursor
        finally:
            conn.close()

    def _init_db(self) -> None:
        self._execute("""
            CREATE TABLE IF NOT EXISTS sandboxes (
                space_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                image TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL,
                lease_expires_at REAL NOT NULL,
                endpoint_url TEXT NOT NULL,
                owner_pid INTEGER NOT NULL
            )
        """)

    def register_session(
        self,
        space_id: str,
        provider: str,
        image: str,
        lease_seconds: int = 900,
        endpoint_url: str = "",
        owner_pid: Optional[int] = None
    ) -> SandboxSession:
        now = time.time()
        expires_at = now + lease_seconds
        pid = owner_pid or os.getpid()

        self._execute("""
            INSERT OR REPLACE INTO sandboxes 
            (space_id, provider, image, status, created_at, lease_expires_at, endpoint_url, owner_pid)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
        """, (space_id, provider, image, now, expires_at, endpoint_url, pid))

        return SandboxSession(
            space_id=space_id,
            provider=provider,
            image=image,
            status="active",
            created_at=now,
            lease_expires_at=expires_at,
            endpoint_url=endpoint_url,
            owner_pid=pid
        )

    def renew_lease(self, space_id: str, extend_seconds: int = 900) -> float:
        now = time.time()
        new_expiry = now + extend_seconds
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                cursor = conn.execute("""
                    UPDATE sandboxes 
                    SET lease_expires_at = ?
                    WHERE space_id = ?
                """, (new_expiry, space_id))
                if cursor.rowcount == 0:
                    raise KeyError(f"Sandbox {space_id} not found in state store.")
        finally:
            conn.close()
        return new_expiry

    def get_session(self, space_id: str) -> Optional[SandboxSession]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT space_id, provider, image, status, created_at, lease_expires_at, endpoint_url, owner_pid
                FROM sandboxes
                WHERE space_id = ?
            """, (space_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return SandboxSession(*row)
        finally:
            conn.close()

    def list_active(self) -> List[SandboxSession]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT space_id, provider, image, status, created_at, lease_expires_at, endpoint_url, owner_pid
                FROM sandboxes
                WHERE status = 'active'
            """)
            return [SandboxSession(*row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def list_expired(self) -> List[SandboxSession]:
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT space_id, provider, image, status, created_at, lease_expires_at, endpoint_url, owner_pid
                FROM sandboxes
                WHERE lease_expires_at < ?
            """, (now,))
            return [SandboxSession(*row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def remove_session(self, space_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                cursor = conn.execute("DELETE FROM sandboxes WHERE space_id = ?", (space_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def close(self) -> None:
        """Explicitly release any open handles (no-op since connections close per transaction)."""
        pass

