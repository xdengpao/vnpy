"""Check whether the current Python environment can run VeighNa/vn.py 4.x."""

from __future__ import annotations

import platform
import sys
from pathlib import Path
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_PACKAGES = [
    "vnpy",
    "PySide6",
    "numpy",
    "pandas",
    "talib",
    "deap",
    "zmq",
]

OPTIONAL_PACKAGES = [
    "vnpy_ctastrategy",
    "vnpy_ctabacktester",
    "vnpy_sqlite",
    "vnpy_rqdata",
    "vnpy_ctp",
]

OPTIONAL_CRYPTO_PACKAGES = [
    "pytz",
    "websocket",
    "vnpy.api.rest",
    "vnpy.api.websocket",
    "vnpy.gateway.binance",
    "vnpy.gateway.binances",
    "vnpy.gateway.bitfinex",
    "vnpy.gateway.bitmex",
    "vnpy.gateway.bitstamp",
    "vnpy.gateway.bybit",
    "vnpy.gateway.coinbase",
    "vnpy.gateway.deribit",
    "vnpy.gateway.gateios",
    "vnpy.gateway.huobi",
    "vnpy.gateway.huobif",
    "vnpy.gateway.huobio",
    "vnpy.gateway.huobis",
    "vnpy.gateway.okex",
    "vnpy.gateway.onetoken",
]

DIST_NAMES = {
    "talib": "ta-lib",
    "zmq": "pyzmq",
    "websocket": "websocket-client",
}


def get_dist_version(module_name: str) -> str:
    """Return installed distribution version for an import module name."""
    dist_name = DIST_NAMES.get(module_name, module_name)
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return "not installed"


def check_import(module_name: str) -> tuple[bool, str]:
    """Import a module and return status plus version text."""
    try:
        module = import_module(module_name)
    except Exception as exc:
        return False, f"{get_dist_version(module_name)} ({exc.__class__.__name__}: {exc})"

    dist_version = get_dist_version(module_name)
    if dist_version != "not installed":
        return True, dist_version

    module_version = getattr(module, "__version__", "source tree")
    return True, f"{module_version} (source)"


def main() -> int:
    """Run environment checks."""
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.system()} {platform.release()} {platform.machine()}")

    ok = sys.version_info >= (3, 10)
    print(f"Python >= 3.10: {'OK' if ok else 'FAIL'}")

    print("\nRequired packages:")
    for module_name in REQUIRED_PACKAGES:
        imported, detail = check_import(module_name)
        ok = ok and imported
        print(f"  {module_name}: {'OK' if imported else 'FAIL'} - {detail}")

    print("\nOptional VeighNa packages:")
    for module_name in OPTIONAL_PACKAGES:
        imported, detail = check_import(module_name)
        print(f"  {module_name}: {'OK' if imported else 'MISSING'} - {detail}")

    print("\nOptional cryptocurrency compatibility APIs:")
    for module_name in OPTIONAL_CRYPTO_PACKAGES:
        imported, detail = check_import(module_name)
        print(f"  {module_name}: {'OK' if imported else 'MISSING'} - {detail}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
