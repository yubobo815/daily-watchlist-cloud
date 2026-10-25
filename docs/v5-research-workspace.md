# Daily Trade Copilot v5.0.0

## Boundary

This release changes presentation, filtering, sorting and navigation only. Scanner Python, API signal normalisation, gate checks, classification and all judgement-producing functions remain unchanged. Existing conclusions and DO NOT ENTER labels are retained.

## Design contract

One warm-ivory research desk for the homepage and individual stock page: Georgia serif titles, Geist/system sans body, tabular numbers, quiet grey badges, sage selected/near-zone accents and coral only for risk/direction. No night mode, broker controls, real-time quotes, illustrations, gradients or card wall. The generated visual references are layout references only: invented navigation, marketing slogans, NEUTRAL labels and financial narratives in those images are explicitly excluded. Source data and existing judgement text are authoritative.

## Data definitions

- Signed distance is zero inside the inclusive planned zone; below the zone it is `(close − lower) / lower × 100`; above it is `(close − upper) / upper × 100`. Default order is increasing absolute distance, ticker as deterministic tie-breaker; unavailable values last. This is proximity, not an execution recommendation.
- Active frozen execution plans use their frozen zone, never a current replacement zone. Missing/invalid prices or bounds show Unavailable.
- Price-position ruler shows the existing latest close and zone bounds on a linear padded scale. It is not historical price action. Missing inputs suppress the ruler, with a text explanation instead.
- State changes come only from dated ticker history, ignoring unchanged sessions. Show the most recent available changes; never fabricate transitions to fill a minimum.
- Coverage details use run metadata's failed symbols and dated/stale rows. If the run provides a stale count but not the identities, disclose the limitation rather than invent names. Ticker pages enrich this with the same latest watchlist directory.
- Probability strip uses the report's immutable Bull/Base/Bear probabilities. It is one proportional strip, not three independent progress bars. The visible Not a trade signal label is at least as large as its segment labels.

## Acceptance checks

Coverage expands to named failures and stale inputs; brief opens and collapses with headline/summary retained; distance order and neutral default badges are deterministic; empty risk/protection columns disappear; count filters and sticky controls work; selection has a left rule and additional reasons/history; pagination and back-to-top work; mobile cards do not create a horizontal table; stock page ruler/readiness/previous/next share the same visual system. Static publication and per-ticker loading boundaries remain intact.

## Visual verification

The user superseded the generated concepts with the existing Grok desktop/mobile preview on 25 October. Its paper/card contrast, serif wordmark and headline, subdued default labels, compact market strip, lightly framed evidence panel and inline mobile expansion are the accepted visual baseline. No additional generated concept is needed for this reference-led revision.

Fidelity ledger (reference versus rendered 1440px, 1280px, 390px and automated 320px):

- Palette/container: warm paper backdrop with lighter, subtly rounded research/list/detail surfaces; no gradients or decorative assets.
- Typography: remove the duplicate oversized product masthead; serif report title, small sans controls, restrained default labels and tabular distances.
- Density: background metrics become a wrapping single-line strip; count filters are compact; duplicate mobile category filters are removed. Search, near-zone and favourites remain usable.
- Selection/evidence: amber rule and light selected row; original supporting reasons form three continuous paragraphs; two latest actual transitions are immediately visible, earlier changes expandable.
- Mobile: selecting a card expands evidence directly below that card; selecting it again closes it. No horizontal table or forced stock-page navigation.
- Intentional data-preserving differences: retain all original brief paragraphs, mandatory percentage distances, the original meaning column, genuine conditional frozen-plan risk fields and source judgement labels. Do not import the reference's 12 demo rows, sample BUY, invented prices, narratives or history. Full stock detail retains the minimal ruler/readiness/navigation.

The preview is read-only; cloud favourite writes are not exercised. Browser plugin/skill is absent, so the existing Playwright/Docker workflow verifies rendering and interactions; desktop and mobile screenshots are compared directly with the accepted reference. Source algorithms, API validation and snapshot data are unchanged.
