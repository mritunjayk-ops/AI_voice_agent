import re
import uuid


MAX_SESSION_ID_LENGTH = 128
SESSION_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9._:-]+$"
)


def create_session_id():
    return uuid.uuid4().hex


def resolve_session_id(session_id=None):
    if session_id is None:
        return create_session_id()

    normalized_session_id = session_id.strip()

    if not normalized_session_id:
        return create_session_id()

    if len(normalized_session_id) > MAX_SESSION_ID_LENGTH:
        raise ValueError("session_id is too long")

    if not SESSION_ID_PATTERN.fullmatch(normalized_session_id):
        raise ValueError("session_id contains unsupported characters")

    return normalized_session_id
