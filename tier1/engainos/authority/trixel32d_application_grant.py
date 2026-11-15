"""One-time application grant minted by the 8765 authority after consumption.

The Godot live executor applies geometry only with a grant that verifies
under this process's public key. Godot holds only the public key, so it can
check a grant but never mint one. The key pair is generated in memory per
process: an 8765 restart makes every earlier grant unverifiable.

RSA-3072, PKCS#1 v1.5, SHA-256: the scheme Godot's `Crypto.verify` supports.
The signature covers the exact UTF-8 bytes of `grant_json`; the executor
verifies those bytes before parsing them.

Semantics:
  one-time   the authorization behind it is consumed in the ledger before the
             grant leaves this process; the executor burns grant_id on first use.
  bound      to the consuming client_id, runtime session, scene activation,
             runtime load, Godot observation and artifact hash.
  expiry     expires_at = issued_at + GRANT_TTL_S (unix seconds, same host).
             An expired or otherwise unusable grant is not reissued: its
             authorization is already consumed and its slot stays occupied
             until the next scene load frees it. Failure costs presentation,
             never authority.

Dependency: `cryptography`, pinned in tier1/engainos/requirements-authority.txt.
Absent or of another major version -> AuthorityStateError (no signer, no
grants, no application).
"""

from __future__ import annotations

import base64
import json
import secrets
import time
from typing import Any, Callable, Mapping

from .trixel32d_live_authority_state import AuthorityStateError

GRANT_CONTRACT = "engainos.trixel32d_application_grant.v1"
GRANT_TTL_S = 30
PINNED_CRYPTOGRAPHY_MAJOR = 50  # tier1/engainos/requirements-authority.txt: cryptography==50.0.2
GRANT_FIELDS = frozenset({
    "contract", "grant_id", "client_id", "decision_id", "apply_id", "artifact_sha256",
    "runtime_session_id", "activation_id", "scene_id", "scene_revision", "observed_load",
    "semantic_main_instance_id", "semantic_local_generation", "issued_at", "expires_at",
})


class GrantSigner:
    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        try:
            import cryptography
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding, rsa
        except ImportError as exc:  # fail closed: no signer, no grants, no application
            raise AuthorityStateError("grant signing requires the 'cryptography' package") from exc
        major = str(getattr(cryptography, "__version__", "")).split(".")[0]
        if major != str(PINNED_CRYPTOGRAPHY_MAJOR):
            raise AuthorityStateError(
                f"grant signing is verified against cryptography {PINNED_CRYPTOGRAPHY_MAJOR}.x, "
                f"found {getattr(cryptography, '__version__', 'unknown')}; re-verify and update the pin"
            )
        self._clock = clock
        self._hashes, self._padding = hashes, padding
        self._key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        self.public_key_pem = self._key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("ascii")

    def mint(self, fields: Mapping[str, Any]) -> dict[str, str]:
        issued_at = int(self._clock())
        grant = {"contract": GRANT_CONTRACT, "grant_id": secrets.token_hex(16), **fields,
                 "issued_at": issued_at, "expires_at": issued_at + GRANT_TTL_S}
        if set(grant) != GRANT_FIELDS:
            raise AuthorityStateError("application grant fields are incomplete or unknown")
        grant_json = json.dumps(grant, sort_keys=True, separators=(",", ":"), allow_nan=False)
        signature = self._key.sign(grant_json.encode("utf-8"), self._padding.PKCS1v15(), self._hashes.SHA256())
        return {"grant_json": grant_json, "grant_signature_b64": base64.b64encode(signature).decode("ascii")}

    def verify(self, grant_json: str, grant_signature_b64: str) -> bool:
        """Python-side check, used by tests; Godot performs the same verification."""
        from cryptography.exceptions import InvalidSignature
        try:
            self._key.public_key().verify(
                base64.b64decode(grant_signature_b64, validate=True), grant_json.encode("utf-8"),
                self._padding.PKCS1v15(), self._hashes.SHA256(),
            )
        except (InvalidSignature, ValueError):
            return False
        return True
