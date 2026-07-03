from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """Abstract base for notification channel senders.

    Implementations must provide a :meth:`send` method that returns ``True``
    on success.  Concrete classes may add richer methods (e.g.
    ``send_markdown``) that raise on failure.
    """

    @abstractmethod
    def send(self, text: str) -> bool:
        """Send a simple text notification.

        Returns ``True`` on success.  Should not raise — implementation
        is expected to catch and log errors internally.
        """
        ...
