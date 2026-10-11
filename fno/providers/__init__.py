from .base import Provider


def get_provider(name: str, config: dict) -> Provider:
    name = (name or "nse").lower()
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
