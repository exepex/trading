import logging

from .base import Provider

log = logging.getLogger(__name__)

AUTO_PROVIDER = "auto"


def get_provider(name: str, config: dict) -> Provider:
    """`auto` uses Groww when its credentials are set (the owner's PC) and the free NSE website otherwise."""
    name = (name or "nse").lower()
    if name == AUTO_PROVIDER:
        return _auto_provider(config)
    if name == "nse":
        from .public import NSEProvider

        return NSEProvider(config)
    if name == "groww":
        from .groww import GrowwProvider

        return GrowwProvider(config)
    if name == "sample":
        from .sample import SampleProvider

        return SampleProvider(config)
    raise ValueError(f"Unknown provider: {name}")


def _auto_provider(config: dict) -> Provider:
    """Groww when credentials and its SDK are usable (the owner's PC), the free NSE website otherwise."""
    from .public import NSEProvider

    try:
        from .groww import GrowwProvider, has_groww_credentials

        if has_groww_credentials():
            return GrowwProvider(config)
    except (ImportError, RuntimeError) as exc:
        log.warning("Groww unavailable (%s); using the NSE website for option chains", exc)
    return NSEProvider(config)


__all__ = ["Provider", "get_provider"]
