import aiosqlite
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = None

    async def init(self):
        self._conn = await aiosqlite.connect(str(self.db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                nickname TEXT NOT NULL,
                url TEXT NOT NULL,
                sec_uid TEXT NOT NULL,
                folder_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_synced_at TEXT
            );

            CREATE TABLE IF NOT EXISTS download_jobs (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                earliest TEXT,
                latest TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                total_videos INTEGER DEFAULT 0,
                downloaded INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                finished_at TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            );

            CREATE TABLE IF NOT EXISTS download_items (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT,
                FOREIGN KEY (job_id) REFERENCES download_jobs(id)
            );

            CREATE TABLE IF NOT EXISTS analysis_jobs (
                id TEXT PRIMARY KEY,
                video_path TEXT NOT NULL,
                analysis_path TEXT,
                mode TEXT NOT NULL DEFAULT 'summary',
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT,
                created_at TEXT NOT NULL
            );
        """)
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()

    def connect(self):
        return _ConnectionContext(self.db_path)

    # --- Accounts ---

    async def insert_account(self, platform, nickname, url, sec_uid, folder_name):
        account_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        await self._conn.execute(
            "INSERT INTO accounts (id, platform, nickname, url, sec_uid, folder_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (account_id, platform, nickname, url, sec_uid, folder_name, now),
        )
        await self._conn.commit()
        return {
            "id": account_id,
            "platform": platform,
            "nickname": nickname,
            "url": url,
            "sec_uid": sec_uid,
            "folder_name": folder_name,
            "created_at": now,
            "last_synced_at": None,
        }

    async def get_accounts(self):
        cursor = await self._conn.execute("SELECT * FROM accounts ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_account(self, account_id):
        cursor = await self._conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def delete_account(self, account_id):
        await self._conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        await self._conn.commit()

    async def update_account_synced(self, account_id):
        now = datetime.utcnow().isoformat()
        await self._conn.execute(
            "UPDATE accounts SET last_synced_at = ? WHERE id = ?",
            (now, account_id),
        )
        await self._conn.commit()

    # --- Download Jobs ---

    async def insert_download_job(self, account_id, earliest="", latest=""):
        job_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        await self._conn.execute(
            "INSERT INTO download_jobs (id, account_id, earliest, latest, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
            (job_id, account_id, earliest, latest, now),
        )
        await self._conn.commit()
        return {
            "id": job_id,
            "account_id": account_id,
            "earliest": earliest,
            "latest": latest,
            "status": "pending",
            "total_videos": 0,
            "downloaded": 0,
            "failed": 0,
            "created_at": now,
            "finished_at": None,
        }

    async def get_download_job(self, job_id):
        cursor = await self._conn.execute("SELECT * FROM download_jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_download_jobs(self, account_id=None):
        if account_id:
            cursor = await self._conn.execute(
                "SELECT * FROM download_jobs WHERE account_id = ? ORDER BY created_at DESC",
                (account_id,),
            )
        else:
            cursor = await self._conn.execute("SELECT * FROM download_jobs ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_download_job(self, job_id, **kwargs):
        sets = []
        values = []
        for key, value in kwargs.items():
            sets.append(f"{key} = ?")
            values.append(value)
        values.append(job_id)
        await self._conn.execute(
            f"UPDATE download_jobs SET {', '.join(sets)} WHERE id = ?",
            values,
        )
        await self._conn.commit()

    async def delete_download_job(self, job_id):
        await self._conn.execute("DELETE FROM download_items WHERE job_id = ?", (job_id,))
        await self._conn.execute("DELETE FROM download_jobs WHERE id = ?", (job_id,))
        await self._conn.commit()

    # --- Download Items ---

    async def insert_download_item(self, job_id, video_id, title=""):
        item_id = str(uuid4())
        await self._conn.execute(
            "INSERT INTO download_items (id, job_id, video_id, title, status) VALUES (?, ?, ?, ?, 'pending')",
            (item_id, job_id, video_id, title),
        )
        await self._conn.commit()
        return {"id": item_id, "job_id": job_id, "video_id": video_id, "title": title, "status": "pending"}

    async def update_download_item(self, item_id, **kwargs):
        sets = []
        values = []
        for key, value in kwargs.items():
            sets.append(f"{key} = ?")
            values.append(value)
        values.append(item_id)
        await self._conn.execute(
            f"UPDATE download_items SET {', '.join(sets)} WHERE id = ?",
            values,
        )
        await self._conn.commit()

    async def get_download_items(self, job_id):
        cursor = await self._conn.execute(
            "SELECT * FROM download_items WHERE job_id = ?", (job_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # --- Analysis Jobs ---

    async def insert_analysis_job(self, video_path, mode="summary"):
        job_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        await self._conn.execute(
            "INSERT INTO analysis_jobs (id, video_path, mode, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
            (job_id, video_path, mode, now),
        )
        await self._conn.commit()
        return {
            "id": job_id,
            "video_path": video_path,
            "analysis_path": None,
            "mode": mode,
            "status": "pending",
            "created_at": now,
        }

    async def get_analysis_job(self, job_id):
        cursor = await self._conn.execute("SELECT * FROM analysis_jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_analysis_jobs(self, video_path=None):
        if video_path:
            cursor = await self._conn.execute(
                "SELECT * FROM analysis_jobs WHERE video_path = ? ORDER BY created_at DESC",
                (video_path,),
            )
        else:
            cursor = await self._conn.execute("SELECT * FROM analysis_jobs ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_analysis_job(self, job_id, **kwargs):
        sets = []
        values = []
        for key, value in kwargs.items():
            sets.append(f"{key} = ?")
            values.append(value)
        values.append(job_id)
        await self._conn.execute(
            f"UPDATE analysis_jobs SET {', '.join(sets)} WHERE id = ?",
            values,
        )
        await self._conn.commit()


class _ConnectionContext:
    def __init__(self, db_path):
        self.db_path = db_path
        self._conn = None

    async def __aenter__(self):
        self._conn = await aiosqlite.connect(str(self.db_path))
        self._conn.row_factory = aiosqlite.Row
        return self._conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._conn.close()
