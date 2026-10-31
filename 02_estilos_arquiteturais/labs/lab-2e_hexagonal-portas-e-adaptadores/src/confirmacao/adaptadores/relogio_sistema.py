"""Adaptador de relógio: a hora real do sistema."""
from datetime import datetime, timezone


class RelogioDoSistema:
    def agora(self) -> datetime:
        return datetime.now(timezone.utc)
