"""Advisory engine: a wealth-manager review of a pushed multi-account book.

The finance app pushes holdings, asks for a review, and gets back structured
recommendations. Every recommendation is priced from market data at the time
it is made and tracked afterwards against the untouched book and SPY, so the
agent's calls build a verifiable track record without any order being placed.
"""
