"""Minimal VeighNa/vn.py 4.x launcher.

Install dependencies from requirements-veighna4.txt first. The CTP gateway is
optional so the UI can still start on macOS while the CTP package/toolchain is
being prepared.
"""

from __future__ import annotations

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_ctabacktester import CtaBacktesterApp
from vnpy_ctastrategy import CtaStrategyApp


def load_optional_ctp_gateway():
    """Return CtpGateway when vnpy_ctp is installed."""
    try:
        from vnpy_ctp import CtpGateway
    except ModuleNotFoundError:
        return None

    return CtpGateway


def main() -> None:
    """Start VeighNa Trader with the common CTA apps."""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    ctp_gateway = load_optional_ctp_gateway()
    if ctp_gateway:
        main_engine.add_gateway(ctp_gateway)

    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
