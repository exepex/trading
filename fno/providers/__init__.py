from .base import Provider

AUTO_PROVIDER = "auto"


def get_provider(name: str, config: dict) -> Provider:
    """`auto` uses Groww when its credentials are set (the owner's PC) and the free NSE website otherwise."""
    name = (name or "nse").lower()
    if name == AUTO_PROVIDER:
        from .groww import has_groww_credentials

        name = "groww" if has_groww_credentials() else "nse"
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


__all__ = ["Provider", "get_provider"]
