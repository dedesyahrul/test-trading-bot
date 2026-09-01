# DexScreener API Integration

MemeX uses the official DexScreener REST API at `https://api.dexscreener.com`.

## Endpoints Used

- `GET /token-boosts/latest/v1`: primary discovery source for boosted/trending tokens, as used by the original MemeX flow.
- `GET /token-pairs/v1/{chainId}/{tokenAddress}`: resolves each boosted token into available pairs.
- `GET /latest/dex/search?q={query}`: fallback discovery source.
- `GET /token-profiles/recent-updates/v1` and `GET /tokens/v1/{chainId}/{tokenAddresses}`: available helpers, but not used as the primary discovery flow.

## Secondary Provider

GeckoTerminal is used as a fallback only:

- `GET /api/v2/networks/{network}/trending_pools`
- `GET /api/v2/networks/{network}/pools/{pool_address}`

DexScreener remains primary. GeckoTerminal data is normalized into the same internal pair shape and deduplicated by `chain + pair address`. The discovery worker does not run GeckoTerminal data through the DexScreener normalizer a second time.
- `GET /latest/dex/pairs/{chainId}/{pairId}`: refreshes a watched pair.
- `GET /latest/dex/search?q={query}`: bounded fallback when profile discovery is unavailable.
- `GET /token-boosts/latest/v1`: secondary fallback for boosted tokens.

## Response Shapes

- Token profiles may be a single object or an array depending on the endpoint response.
- Pair detail responses may contain `pair` and/or `pairs`; the worker supports both.
- Pair objects use official fields such as `chainId`, `pairAddress`, `baseToken`, `quoteToken`, `priceUsd`, `txns`, `volume`, `priceChange`, and `liquidity`.

## Rate Limit and Failure Policy

Discovery endpoints document a limit of 60 requests per minute. MemeX uses the original boosts-to-token-pairs flow, short timeout for watched-pair polling, a longer timeout for discovery, bounded concurrency, and no retry storm on network timeouts. A failed provider request keeps the last market snapshot and must not create a new signal.

## Operational Notes

After a clean database reset, run Scanner `Refresh` while DexScreener is reachable. If the provider is unavailable, Scanner reports a temporary discovery error; it does not generate fake tokens.
