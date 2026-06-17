"""Authentication subsystem for Garmin Connect.

Provides modular token management and (planned) strategy isolation as
described in nova_arquitetura.txt § Camada 2. Migration from the legacy
monolithic client.py is incremental — TokenStore is the first piece
that lands; AuthManager and the per-strategy modules follow.
"""

from .token import TokenStore

__all__ = ["TokenStore"]
