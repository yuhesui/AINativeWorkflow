# T01 scoring lock

The official verifier remains authoritative. Database integrity, one read-only SQLite SELECT/CTE statement, the 2,000-character ceiling, exact columns, exact row order/values, and exact semantic equality are hard gates. Any failed gate receives continuous score 0.

For a candidate that passes every semantic/format/integrity gate, the continuous score is `50 + 50 * progress`, where `progress` is the clipped log-runtime improvement from the supplied unoptimized query to the official golden query. The unoptimized/golden ratio is measured once during environment qualification and frozen in `BASELINE_LOCK.json`; each grade scales that ratio by its contemporaneous golden median, avoiding a multi-minute baseline query inside every grade. Thus semantic correctness contributes the dominant, discontinuous half of the scale; the original correct query anchors 50 and golden-or-better performance anchors 100. The official native performance pass (`candidate median <= 1.05 * golden median`) is retained separately and never replaced by the continuous score.

Raw alternating candidate/golden timings, medians, the frozen baseline measurement, exact gate outcomes, verifier threshold, SQL/database hashes, native pass, and continuous score are written together. Scored runs use seven timing iterations; qualification may use three or more.
