"""Small per-Streamlit-session reuse layer; intentionally NO shared/global caching.

Student records never leave the individual session's in-memory state. Each
namespace keeps only its latest input/output to bound retained memory.
"""
from __future__ import annotations
import hashlib
import json


def fingerprint(*parts):
    """Stable digest of input identifiers; do not include identifiable data in logs."""
    digest = hashlib.sha256()
    for value in parts:
        if isinstance(value, bytes):
            digest.update(b'b')
            digest.update(value)
        else:
            digest.update(b'j')
            digest.update(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode())
        digest.update(b'\0')
    return digest.hexdigest()


def reuse(session_state, namespace, key, compute):
    """Calculate at most once per namespace and input within an active session.

    Replaces the prior value when the input changes, preventing unbounded
    per-session retention. Never use st.cache_data or st.cache_resource here.
    """
    slot = '_dbsjp_private_' + namespace
    cached = session_state.get(slot)
    if cached is not None and cached['key'] == key:
        return cached['value']
    value = compute()
    session_state[slot] = {'key': key, 'value': value}
    return value


def clear_private(session_state):
    for k in list(session_state.keys()):
        if str(k).startswith('_dbsjp_private_'):
            del session_state[k]
