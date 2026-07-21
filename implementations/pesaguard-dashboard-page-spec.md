# PesaGuard — Dashboard (Overview) Page Spec

The first page a logged-in user sees. Its single job: answer "is everything okay right now?" 
in under 3 seconds of looking at it.

---

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ Sidebar │  Top bar: logo mark, search, user menu     │
│         ├─────────────────────────────────────────────
│ nav     │  System status banner (only if degraded)   │
│ icons   │  ─────────────────────────────────────────  │
│         │  [Stat] [Stat] [Stat] [Stat]  ← top row     │
│         │  ─────────────────────────────────────────  │
│         │  Match-rate trend chart  │  Live activity   │
│         │  (7/30 day toggle)       │  feed (scrolling) │
│         │  ─────────────────────────────────────────  │
│         │  [Review Anomalies card] [Unmatched card]   │
└─────────────────────────────────────────────────────┘
```

## Content — What It Must Contain

1. **System status banner** (conditional — only renders if something's wrong)
   - Green/hidden when healthy — don't show "All systems normal" banners permanently, 
     that's noise. Silence = health.
   - Amber/red banner only appears on degraded state, states plainly what's affected 
     ("Webhook processing delayed — investigating") — never vague

2. **Top-line stat cards (4)**
   - Transactions processed today (count)
   - Reconciliation match rate (%, with trend arrow vs. yesterday)
   - Open anomalies (count, colored by whether any are high-severity)
   - System uptime (last 24h, %)
   - Each card: big number, small label, one supporting data point — no filler stats

3. **Match-rate trend chart**
   - Line chart, 7-day / 30-day toggle
   - Single accent-green line, minimal gridlines, hover tooltip shows exact values
   - Not a generic "gradient area chart" — a clean precise line, control-room style

4. **Live activity feed**
   - Scrolling list of most recent transactions as they're processed
   - Each row: timestamp, amount, status icon (matched/pending/flagged), one-line description
   - New items animate in at the top — subtle, not distracting (see animation section)

5. **Quick-access cards**
   - "Review Anomalies" — shows count, one-click to Anomalies page
   - "Unmatched Transactions" — shows count, one-click to Reconciliation page
   - Empty state matters here: if zero anomalies, the card should read reassuring 
     ("No anomalies right now") not just "0"

---

## Design Direction (Premium/Modern Execution)

**Palette (from the established system):**
- Background: `#0A1F2E` → `#0B2E24` subtle gradient, very dark
- Card surface: `#0F241D`, with a barely-visible 1px border in `#1A3A2E` for separation 
  without harsh lines
- Accent (healthy/success): `#2ECC87`
- Accent (warning): `#F1A83C`
- Accent (critical): `#E11D48`
- Text: `#F4FBF8` primary, `#8FA69C` muted/secondary

**Typography:**
- Numbers/data: a monospace or tabular-figure font (e.g. JetBrains Mono or similar) — 
  numbers should feel measured and precise, not decorative
- Headings/labels: clean geometric sans (e.g. Inter or similar), restrained weight usage — 
  don't over-bold everything

**Signature element:** the pulse/heartbeat line motif — a thin animated line that runs 
subtly behind the top bar or as a divider, pulsing at a calm, steady rhythm when the system 
is healthy. This is the one place to spend visual "boldness" on this page — everything else 
stays quiet and disciplined around it.

---

## Modernization / Premium Touches

- Glassmorphism restraint: a very subtle backdrop-blur on the top bar only (not overused 
  everywhere) — signals depth without looking dated
- Numbers that count up on load (from 0 to actual value) instead of appearing instantly — 
  reinforces the "live system" feeling, but only on first load, not on every re-render
- Skeleton loading states shaped exactly like the real content (not generic gray bars) — 
  card skeletons should already look like a stat card, chart skeleton like a chart
- Real-time indicator: a small pulsing dot next to "Live activity feed" showing the 
  connection is actually live (not just static data)
- Subtle hover elevation on cards (slight shadow lift + border brightening), not scale-transform 
  (scaling cards on hover reads as templated)

## Animations (Deliberate, Not Decorative)

- **Page load:** stat cards fade/slide in with a very slight stagger (50–80ms between each), 
  numbers count up over ~600ms
- **Live feed:** new transaction rows slide in from top with a soft fade, existing rows shift 
  down smoothly — never an abrupt jump
- **Status banner:** if it appears, slides down smoothly rather than popping in
- **Pulse motif:** continuous, slow (roughly 1 pulse per 1.5–2s), calm — should feel like a 
  heartbeat monitor, not an urgent alarm
- **Respect `prefers-reduced-motion`** — all of the above should have a static fallback

## Explicit Restraint Notes
- No confetti, no celebratory animations for "good" numbers — this is a financial monitoring 
  tool, not a gamified app
- No more than one animated/live element competing for attention at a time
- Avoid gradient-mesh backgrounds or glowing orbs — reads as generic AI-generated SaaS

---

## Modifications to Existing Plan
- None yet — this is the first concrete page spec. Once built, review against this doc 
  before moving to Transactions (the next "Now" priority page).

## Additional (Not for First Build)
- Customizable dashboard widget order (drag to rearrange) — nice-to-have, not now
- Per-user saved chart date-range preference — later
