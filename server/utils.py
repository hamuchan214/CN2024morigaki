import hashlib
import time


def generate_session_id(user_id):
    """Generate a session ID using user ID and current timestamp."""
    return hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()
