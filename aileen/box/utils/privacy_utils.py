import hashlib
import binascii

from django.conf import settings


def hash_mac_address(mac_address: str) -> str:
    """This is the one method Aileen uses for hashing mac addresses.
    The sha256, with an app-specific salt and a high number of rounds."""
    if settings.HASH_MAC_ADDRESSES is False:
        return mac_address
    iterations = settings.HASH_ITERATIONS
    hashed_mac = hashlib.pbkdf2_hmac(
        "sha256", mac_address.encode("utf-8"), settings.SECRET_KEY.encode(), iterations
    )
    hash_hex = binascii.hexlify(hashed_mac).decode("ascii")
    return hash_hex
