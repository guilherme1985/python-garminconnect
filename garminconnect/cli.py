"""Command-line interface for python-garminconnect (F5-03).

Entry point registered in pyproject.toml as ``garminconnect``.

Subcommands:
    login              authenticate and persist tokens
    logout             remove persisted tokens
    stats DATE         daily summary
    activities         list recent activities
    heart-rate DATE    intra-day heart rate
    sleep DATE         sleep stages
    body-battery       7-day body battery
    weight             90-day weigh-ins

Global flags:
    --tokenstore PATH  tokenstore directory (default $GARMINTOKENS or ~/.garminconnect)
    --format json|csv  output format (default json)
    --cache            enable disk cache under <tokenstore>/cache
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import sys
from datetime import date, timedelta
from getpass import getpass
from pathlib import Path
from typing import Any, Sequence

from . import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


def _yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def _resolve_tokenstore(arg: str | None) -> str:
    return str(Path(arg or os.getenv("GARMINTOKENS", "~/.garminconnect")).expanduser())


def _emit(data: Any, fmt: str) -> int:
    """Print ``data`` as JSON or CSV; return process exit code."""
    if fmt == "json":
        json.dump(data, sys.stdout, default=str, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    if fmt == "csv":
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list) or not data:
            sys.stderr.write("CSV: dados não-tabulares ou vazios\n")
            return 1
        cols = sorted({k for row in data if isinstance(row, dict) for k in row})
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=cols)
        writer.writeheader()
        for row in data:
            if isinstance(row, dict):
                writer.writerow({k: row.get(k, "") for k in cols})
        sys.stdout.write(out.getvalue())
        return 0
    sys.stderr.write(f"formato desconhecido: {fmt}\n")
    return 2


def _build_client(args: argparse.Namespace) -> Garmin:
    """Construct an authenticated Garmin from saved tokens (no prompts)."""
    tokenstore = _resolve_tokenstore(args.tokenstore)
    cache = None
    if args.cache:
        from .cache import DiskCache
        cache = DiskCache(Path(tokenstore) / "cache")
    g = Garmin(cache=cache)
    g.login(tokenstore)
    return g


# ---------- subcommands ------------------------------------------------ #


def cmd_login(args: argparse.Namespace) -> int:
    tokenstore = _resolve_tokenstore(args.tokenstore)
    email = args.email or os.getenv("GARMIN_EMAIL") or os.getenv("EMAIL") \
        or input("Email: ").strip()
    password = args.password or os.getenv("GARMIN_PASSWORD") \
        or os.getenv("PASSWORD") or getpass("Senha: ")

    g = Garmin(
        email=email, password=password,
        is_cn=args.cn, login_timeout=args.timeout,
        prompt_mfa=lambda: input("Código MFA: ").strip(),
    )
    try:
        g.login(tokenstore)
    except GarminConnectAuthenticationError as e:
        sys.stderr.write(f"Falha de autenticação: {e}\n")
        return 1
    except GarminConnectTooManyRequestsError as e:
        sys.stderr.write(f"Rate limit: {e}\n")
        return 2
    except GarminConnectConnectionError as e:
        sys.stderr.write(f"Erro de conexão: {e}\n")
        return 3
    print(f"OK — tokens em {tokenstore}")
    return 0


def cmd_logout(args: argparse.Namespace) -> int:
    tokenstore = Path(_resolve_tokenstore(args.tokenstore))
    removed = 0
    for f in tokenstore.glob("*"):
        if f.is_file() and f.suffix in (".json", ""):
            f.unlink()
            removed += 1
    print(f"Removidos {removed} arquivo(s) de {tokenstore}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    g = _build_client(args)
    return _emit(g.get_user_summary(args.date), args.format)


def cmd_activities(args: argparse.Namespace) -> int:
    g = _build_client(args)
    return _emit(g.get_activities(0, args.limit), args.format)


def cmd_heart(args: argparse.Namespace) -> int:
    g = _build_client(args)
    return _emit(g.get_heart_rates(args.date), args.format)


def cmd_sleep(args: argparse.Namespace) -> int:
    g = _build_client(args)
    return _emit(g.get_sleep_data(args.date), args.format)


def cmd_body_battery(args: argparse.Namespace) -> int:
    g = _build_client(args)
    return _emit(g.get_body_battery(args.start, args.end), args.format)


def cmd_weight(args: argparse.Namespace) -> int:
    g = _build_client(args)
    return _emit(g.get_weigh_ins(args.start, args.end), args.format)


# ---------- parser ----------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="garminconnect", description=__doc__)
    p.add_argument("--tokenstore", help="diretório de tokens (default $GARMINTOKENS)")
    p.add_argument("--format", choices=["json", "csv"], default="json",
                   help="formato de saída (default: json)")
    p.add_argument("--cache", action="store_true",
                   help="usa DiskCache em <tokenstore>/cache")

    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("login", help="login + salva tokens")
    pl.add_argument("--email")
    pl.add_argument("--password")
    pl.add_argument("--cn", action="store_true", help="região China (garmin.cn)")
    pl.add_argument("--timeout", type=float, default=180.0)
    pl.set_defaults(func=cmd_login)

    pout = sub.add_parser("logout", help="remove tokens persistidos")
    pout.set_defaults(func=cmd_logout)

    pst = sub.add_parser("stats", help="resumo do dia")
    pst.add_argument("date", nargs="?", default=_yesterday())
    pst.set_defaults(func=cmd_stats)

    pa = sub.add_parser("activities", help="lista de atividades recentes")
    pa.add_argument("--limit", type=int, default=20)
    pa.set_defaults(func=cmd_activities)

    ph = sub.add_parser("heart-rate", help="FC intra-dia")
    ph.add_argument("date", nargs="?", default=_yesterday())
    ph.set_defaults(func=cmd_heart)

    psl = sub.add_parser("sleep", help="dados de sono")
    psl.add_argument("date", nargs="?", default=_yesterday())
    psl.set_defaults(func=cmd_sleep)

    pb = sub.add_parser("body-battery", help="body battery em intervalo")
    pb.add_argument("--start", default=_days_ago(7))
    pb.add_argument("--end", default=_yesterday())
    pb.set_defaults(func=cmd_body_battery)

    pw = sub.add_parser("weight", help="pesagens em intervalo")
    pw.add_argument("--start", default=_days_ago(90))
    pw.add_argument("--end", default=_yesterday())
    pw.set_defaults(func=cmd_weight)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=os.getenv("GARMIN_LOG", "WARNING"),
                        format="%(asctime)s [%(levelname)s] %(message)s")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (GarminConnectAuthenticationError,
            GarminConnectConnectionError,
            GarminConnectTooManyRequestsError) as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
