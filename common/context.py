"""Request/event correlation context propagation."""
import contextvars
import uuid
from contextlib import contextmanager
from typing import Optional

CORRELATION_ID: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str:
    """Return the current correlation ID or generate a new one."""
    cid = CORRELATION_ID.get()
    if cid is None:
        cid = uuid.uuid4().hex
        CORRELATION_ID.set(cid)
    return cid


@contextmanager
def correlation_context(cid: Optional[str] = None):
    """Run code within a correlation ID context."""
    token = CORRELATION_ID.set(cid or uuid.uuid4().hex)
    try:
        yield
    finally:
        CORRELATION_ID.reset(token)
