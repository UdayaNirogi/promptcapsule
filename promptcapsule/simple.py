"""The two-function API: ``pack(text) -> str`` and ``unpack(capsule) -> str``.

Short prompts become self-contained inline capsules. Long prompts are stored in a
vault; by default a local SQLite file that is created on first use, so nothing needs
to be configured.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

from .backends import SQLiteBackend
from .core import PromptCapsule, VaultBackend
from .exceptions import VaultError

VAULT_ENV_VAR = "PROMPT_CAPSULE_VAULT"

VaultLike = Union[VaultBackend, str, os.PathLike, None]

_pc = PromptCapsule()
_opened: dict[str, SQLiteBackend] = {}


def default_vault_path() -> Path:
    """Where ``pack``/``unpack`` keep long prompts when no vault is given.

    ``$PROMPT_CAPSULE_VAULT`` if set, otherwise ``~/.promptcapsule/vault.db``.
    """
    configured = os.environ.get(VAULT_ENV_VAR)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".promptcapsule" / "vault.db"


def _sqlite_vault(path: Path, *, create: bool) -> SQLiteBackend:
    path = path.expanduser().resolve()
    cache_key = str(path)
    if cache_key in _opened and path.is_file():
        return _opened[cache_key]
    if not path.is_file():
        if not create:
            raise VaultError(
                f"Vault database not found: {path}. Vault capsules can only be unpacked "
                f"where the vault they were packed into is available."
            )
        # Prompts can be sensitive: keep the vault private to the current user.
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.close(os.open(path, os.O_CREAT | os.O_WRONLY, 0o600))
    backend = SQLiteBackend(str(path))
    _opened[cache_key] = backend
    return backend


def resolve_vault(vault: VaultLike, *, create: bool) -> VaultBackend:
    if isinstance(vault, VaultBackend):
        return vault
    path = default_vault_path() if vault is None else Path(vault)
    return _sqlite_vault(path, create=create)


def pack(text: str, *, sign: bool | str | None = None, vault: VaultLike = None) -> str:
    """Turn a prompt into a capsule string.

    Args:
        text: The prompt (any non-empty string up to 10 MiB of UTF-8).
        sign: Optional HMAC key (str), or True to use ``$PROMPT_CAPSULE_HMAC_KEY``.
        vault: Where long prompts are stored: a ``VaultBackend``, a path to a SQLite
            file, or None for :func:`default_vault_path`. Short prompts (up to 500
            bytes) never touch the vault.

    Returns:
        The capsule string.
    """
    if not isinstance(text, str):
        raise TypeError("Input text must be a string")
    size = len(text.encode("utf-8"))
    if size <= _pc.INLINE_THRESHOLD or size > _pc.MAX_PROMPT_SIZE:
        # No vault needed (or the prompt is rejected anyway): don't create one.
        return _pc.compress(text, sign=sign)
    return _pc.compress(text, vault_backend=resolve_vault(vault, create=True), sign=sign)


def unpack(
    capsule: str,
    *,
    verify_signature: bool | str | None = None,
    vault: VaultLike = None,
) -> str:
    """Turn a capsule string back into the exact original prompt.

    Always fail-closed: raises instead of returning text that does not verify.

    Args:
        capsule: A capsule string produced by :func:`pack` or ``PromptCapsule.compress``.
        verify_signature: HMAC key (str), or True to use ``$PROMPT_CAPSULE_HMAC_KEY``.
            When given, unsigned capsules are rejected.
        vault: Same as for :func:`pack`. A missing vault file is never created.

    Raises:
        IntegrityError, SignatureError, FormatError, SizeLimitError, VaultError
    """
    backend = None
    if isinstance(capsule, str) and capsule.startswith("cap_v_"):
        backend = resolve_vault(vault, create=False)
    return _pc.decompress(
        capsule, vault_backend=backend, strict=True, verify_signature=verify_signature
    ).text
