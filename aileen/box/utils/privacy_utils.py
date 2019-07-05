import binascii
import hashlib

from django.conf import settings


def hash_observable_ids(observable_id: str) -> str:
    """This is the one method Aileen uses for hashing observable IDs.
    The sha256, with an app-specific salt and a high number of rounds."""
    if settings.HASH_OBSERVABLE_IDS is False:
        return observable_id
    iterations = settings.HASH_ITERATIONS
    hashed_id = hashlib.pbkdf2_hmac(
        "sha256",
        observable_id.encode("utf-8"),
        settings.SECRET_KEY.encode(),
        iterations,
    )
    hash_hex = binascii.hexlify(hashed_id).decode("ascii")
    return hash_hex
