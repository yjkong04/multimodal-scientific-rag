"""Networking helpers for ingestion.

On machines behind a TLS-inspecting proxy (common on managed/corporate laptops),
the OS trust store holds the proxy's CA but Python's OpenSSL bundle does not, so
HTTPS to NCBI fails with CERTIFICATE_VERIFY_FAILED. `truststore` routes Python's
TLS verification through the OS trust store, matching what curl already trusts.
It's a no-op on machines without such a proxy.
"""

from __future__ import annotations


def enable_os_trust_store() -> bool:
    """Make Python verify TLS against the OS trust store. Returns True if applied."""
    try:
        import truststore

        truststore.inject_into_ssl()
        return True
    except Exception:
        # Not installed or unsupported platform: fall back to the default bundle.
        return False
