"""Replays the desk's rules on past 5-minute prices to give rule weights an evidence-based start.

An approximation, labelled as such everywhere: option prices are modelled (Black-Scholes from realised volatility),
not historical quotes, and only the rules that can be judged from price history vote."""
