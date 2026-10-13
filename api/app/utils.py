import hashlib
import os
import re
import unicodedata


IP_HASH_SALT_DEFAULT = "CHANGE_THIS_SALT_IN_PRODUCTION"

IP_HASH_SALT = os.getenv("IP_HASH_SALT", IP_HASH_SALT_DEFAULT)


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def hash_ip(ip: str) -> str:
    return hashlib.sha256(f"{IP_HASH_SALT}:{ip}".encode()).hexdigest()
