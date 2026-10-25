# Daily Trade Copilot v5.0.0

## Boundary

This release changes presentation, filtering, sorting and navigation only. Scanner Python, API signal normalisation, gate checks, classification and all judgement-producing functions remain unchanged. Existing conclusions and DO NOT ENTER labels are retained.

## Design contract

One warm-ivory research desk for the homepage and individual stock page: Georgia serif titles, Geist/system sans body, tabular numbers, quiet grey badges, sage selected/near-zone accents and coral only for risk/direction. No night mode, broker controls, real-time quotes, illustrations, gradients or card wall. The generated visual references are layout references only: invented navigation, marketing slogans, NEUTRAL labels and financial narratives in those images are explicitly excluded. Source data and existing judgement text are authoritative.

## Data definitions

- Signed distance is numerically zero inside the inclusive planned zone, displayed as Inside from v5.1; below the zone it is `(close − lower) / lower × 100`; above it is `(close − upper) / upper × 100`. Tiny outside distances retain their direction as signed <0.01%, never Inside. Default order is increasing absolute distance, ticker as deterministic tie-breaker; unavailable values last. This is proximity, not an execution recommendation.
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

## v5.1.0 approved revision

Version 5.1.0 is retained in package/release metadata, asset URLs and the non-visible UI marker only. The user explicitly removed all visible brand/header version labels.

The 25 October follow-up supersedes the v5.0 layout, not the data/decision boundary:

- A real two-column desk contains the brief, count filters and list in its left column; sticky evidence starts at the top of the right column, aligned with the brief. Maximum reading width is 1200px, gap 24px, evidence width 320px.
- The compact brief opens by default. It retains the original first complete summary sentence, immutable forecast and signed metrics. Read full brief reveals the exact full summary, original paragraphs and scenario boundaries. Source descriptions for metrics remain available as tooltips; actual session/publication dates remain visible.
- The watchlist has exactly five columns. The user explicitly removed What it means, including the corresponding mobile summary. Genuine protection and stopped-loss values move into conditional evidence sections.
- Sidebar evidence retains the original explanations, two immediately visible recorded changes plus expandable earlier changes, conditional plan facts and previous/next navigation. Mobile expands supporting evidence under the card without repeating its identity, and removes the redundant bottom tab bar.
- Inside replaces a zero-distance percentage only when the close is actually within the inclusive zone. Numeric distance and sorting are unchanged; all original entry restrictions remain.

Verification compares the live Grok reference with renders at 1440x900, 1280x800, 390x844, 320x844 and the 2880px reference width. Intentional deviations remain source accuracy, the approved percentage/Inside convention, five real-data columns, original reasons (not demo narratives), and the approved secondary full-brief disclosure. The shared stylesheet is consolidated rather than another layer of v5 overrides.
