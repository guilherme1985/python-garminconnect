"""Domain mixins for Garmin Connect API.

Each module in this package provides a mixin class that groups related API
methods by domain (health, body, activities, etc). The main Garmin class
composes these mixins to expose all 134+ methods of the public API.

This package is part of the modular refactor described in nova_arquitetura.txt
(Camada 5 — Domínio). Migration from the legacy monolithic __init__.py is
incremental; mixins are extracted one at a time without breaking the public API.

Each mixin assumes the host class provides:
    - self.connectapi(url, **kwargs)
    - self.connectwebproxy(url, **kwargs)
    - self.download(url, **kwargs)
    - self._require_display_name()
    - self.garmin_connect_* URL attributes (legacy — being migrated to Endpoints)
"""
