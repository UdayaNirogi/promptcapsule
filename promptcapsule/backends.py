"""Storage backends for vault mode."""

from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timezone

from .core import VaultBackend


def _new_vault_key(prefix: str) -> str:
    """Unguessable vault key (secrets module, not a counter)."""
    return f"{prefix}_{secrets.token_urlsafe(16)}"


class InMemoryBackend(VaultBackend):
    """In-memory backend for testing."""

    def __init__(self):
        self.store_dict: dict = {}

    def store(self, text: str, checksum: str) -> str:
        key = _new_vault_key("mem")
        self.store_dict[key] = {
            "text": text,
            "checksum": checksum,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return key

    def retrieve(self, key: str) -> str:
        if key not in self.store_dict:
            raise KeyError(f"Key not found: {key}")
        return self.store_dict[key]["text"]

    def retrieve_with_checksum(self, key: str) -> tuple:
        if key not in self.store_dict:
            raise KeyError(f"Key not found: {key}")
        record = self.store_dict[key]
        return record["text"], record["checksum"]


class SQLiteBackend(VaultBackend):
    """SQLite-based vault backend for local storage."""

    def __init__(self, db_path: str = "promptcapsule.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS capsules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    text TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def close(self):
        """Explicitly close any cached connections (Windows file locking fix)."""
        # Force close all connections by connecting and immediately closing
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
        except Exception:  # noqa: S110, BLE001
            pass  # Best-effort cleanup, failures are acceptable

    def store(self, text: str, checksum: str) -> str:
        # Rare collision retry
        for _ in range(8):
            key = _new_vault_key("sql")
            try:
                conn = sqlite3.connect(self.db_path)
                try:
                    conn.execute(
                        "INSERT INTO capsules (key, text, checksum) VALUES (?, ?, ?)",
                        (key, text, checksum),
                    )
                    conn.commit()
                    return key
                finally:
                    conn.close()
            except sqlite3.IntegrityError:
                continue
        raise RuntimeError("Failed to generate unique vault key")

    def retrieve(self, key: str) -> str:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT text FROM capsules WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if row is None:
                raise KeyError(f"Key not found: {key}")
            return row[0]
        finally:
            conn.close()

    def retrieve_with_checksum(self, key: str) -> tuple:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT text, checksum FROM capsules WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if row is None:
                raise KeyError(f"Key not found: {key}")
            return row[0], row[1]
        finally:
            conn.close()


class GitHubGistBackend(VaultBackend):
    """GitHub Gist-based vault backend (requires PyGithub).

    By default, retrieve only succeeds for gists owned by the authenticated
    user (confused-deputy mitigation). Optionally restrict to an allowlist.
    """

    def __init__(
        self,
        token: str,
        *,
        require_owner: bool = True,
        allowed_gist_ids: set[str] | None = None,
    ):
        try:
            from github import Github
        except ImportError as e:
            raise ImportError(
                "PyGithub is required for GitHubGistBackend. "
                "Install with: pip install promptcapsule[vault]"
            ) from e

        self.github = Github(token)
        self.user = self.github.get_user()
        self._login = self.user.login
        self.require_owner = require_owner
        self.allowed_gist_ids: set[str] | None = (
            set(allowed_gist_ids) if allowed_gist_ids is not None else None
        )
        self._checksum_cache: dict = {}

    def store(self, text: str, checksum: str) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        description = f"PromptCapsule [{checksum[:8]}] - {timestamp}"

        files = {
            "prompt.txt": {"content": text},
            "checksum.txt": {"content": checksum},
        }

        gist = self.user.create_gist(
            public=False,
            files=files,
            description=description,
        )
        self._checksum_cache[gist.id] = checksum
        if self.allowed_gist_ids is not None:
            self.allowed_gist_ids.add(gist.id)
        return gist.id

    def retrieve(self, key: str) -> str:
        text, _ = self.retrieve_with_checksum(key)
        return text

    def _assert_gist_allowed(self, key: str, gist) -> None:
        if self.allowed_gist_ids is not None and key not in self.allowed_gist_ids:
            raise KeyError(f"Gist id not in allowlist: refused ({key!r})")
        if self.require_owner:
            owner = getattr(getattr(gist, "owner", None), "login", None)
            if owner is None or owner != self._login:
                raise KeyError(
                    f"Gist not owned by authenticated user {self._login!r}: refused"
                )

    def retrieve_with_checksum(self, key: str) -> tuple:
        try:
            gist = self.github.get_gist(key)
            self._assert_gist_allowed(key, gist)
            if "prompt.txt" in gist.files:
                text = gist.files["prompt.txt"].content
            else:
                first_file = next(iter(gist.files.values()))
                text = first_file.content

            if "checksum.txt" in gist.files:
                stored = gist.files["checksum.txt"].content.strip()
            else:
                stored = self._checksum_cache.get(key, "")
            return text, stored
        except KeyError:
            raise
        except Exception as e:
            raise KeyError(f"Failed to retrieve gist {key}: {e}") from e


class S3Backend(VaultBackend):
    """AWS S3-based vault backend (requires boto3)."""

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        prefix: str = "promptcapsule/",
    ):
        try:
            import boto3
        except ImportError as e:
            raise ImportError(
                "boto3 is required for S3Backend. "
                "Install with: pip install promptcapsule[vault]"
            ) from e

        self.s3_client = boto3.client("s3", region_name=region)
        self.bucket = bucket
        self.prefix = prefix

    def _assert_key_in_prefix(self, key: str) -> None:
        """Reject capsule-controlled keys outside the configured prefix."""
        if not key.startswith(self.prefix):
            raise KeyError(f"S3 key outside allowed prefix {self.prefix!r}: refused")
        # Block path traversal tricks inside the key
        if ".." in key.split("/"):
            raise KeyError("S3 key contains path traversal: refused")

    def store(self, text: str, checksum: str) -> str:
        key = f"{self.prefix}{secrets.token_urlsafe(16)}_{checksum[:8]}.txt"

        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=text.encode("utf-8"),
            Metadata={
                "checksum": checksum,
                "timestamp": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
            },
        )
        return key

    def retrieve(self, key: str) -> str:
        text, _ = self.retrieve_with_checksum(key)
        return text

    def retrieve_with_checksum(self, key: str) -> tuple:
        self._assert_key_in_prefix(key)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            text = response["Body"].read().decode("utf-8")
            stored = response.get("Metadata", {}).get("checksum", "")
            return text, stored
        except KeyError:
            raise
        except Exception as e:
            raise KeyError(f"Failed to retrieve from S3 {key}: {e}") from e
