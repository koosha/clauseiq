# DDR-0001 · Adopt the "Workbench" UI layout with a command palette

- **Status:** Accepted
- **Date:** 2026-04-19
- **Deciders:** Product / Engineering (solo lead)
- **Supersedes:** —
- **Superseded by:** —
- **Related:** `docs/design/wireframes/ClauseIQ_UI_Plan_v0.1.html`, `docs/architecture/PrecedentIQ_MVP_Plan_Consolidated.md`

---

## Context

ClauseIQ's MVP is a clause retrieval tool for in-house counsel drafting new SaaS MSAs from prior executed precedents. The backend plan (see `PrecedentIQ_MVP_Plan_Consolidated.md`) is locked: hybrid BM25 + kNN search over clause-level chunks, with citations back to source contracts. The MVP plan explicitly defers UI — but we need the UI's *shape* settled now so backend response shapes, latency budgets, and keyboard-shortcut semantics are pinned down before engineering work begins.

Three directions were explored in the v0.1 wireframes:

- **A · Classic two-pane** — sidebar filters + results list + dedicated contract-viewer page. Westlaw/Lexis mental model.
- **B · Command bar** — palette-first, filter chips inline, scratchpad as right drawer. Linear/Raycast feel.
- **C · Workbench** — three columns (filters · results · live preview) with scratchpad docked to the bottom. No page navigation.

The core usage pattern is an iterative funnel run dozens of times per session: *query → skim → pin → (verify) → next query → export*. The decision hinges on which layout minimizes friction between those steps.

## Decision

**Adopt Direction C (Workbench) as the primary layout, with Direction B's command palette grafted on as the global entry point.**

Concretely:

1. The home screen is the three-column workbench: filters (left, 200px) · results list (center) · live clause preview (right).
2. The scratchpad docks to the bottom of the viewport as a persistent horizontal strip.
3. A command palette opens on `⌘K` or `/` from anywhere, accepting queries, paste-and-match input, and jump-to commands (e.g. `family:termination`, `recent:`, `open contract`).
4. No page-level navigation for the core loop. Drilling into a contract opens a focused reader view in place of the preview column (URL-addressable so deep links work).
5. Export is a modal over the workbench, not a separate page.

## Rationale

**Why C over A.** A lawyer running 20–40 queries in a session cannot afford full-page navigation between results and source contracts. Direction A's dedicated contract viewer adds a back-button round-trip to every verification — multiplied across a session, that's real friction. The workbench's live preview pane collapses "skim → verify" into a single arrow-key press.

**Why C over B.** B's right-drawer scratchpad is collapsible, which is elegant — but the scratchpad is the *progress indicator* for the session. Hiding it behind a toggle understates its role. The bottom dock in C keeps the pin count, clause tiles, and "Export" button visible without costing result-list real estate.

**Why graft in B's palette.** The palette's instant-focus entry and keyboard-first affordances are strictly additive. Keeping the workbench as "home" and the palette as a universal jump surface gives us both: scannable UI for new users, keyboard speed for power users.

**Why not hybrid A+C.** A's dedicated contract-viewer page is URL-addressable, which is genuinely useful for team collaboration. We preserve that by making drill-in push a route (`/contract/:id#clause=:clauseId`) even though the view stays in the workbench shell. No navigation, full addressability.

## Consequences

### Positive

- Zero page transitions in the core loop — session momentum preserved.
- Live preview makes verification nearly free, which encourages deeper checking and raises trust.
- Scratchpad dock turns pinning into a visible progress bar.
- Command palette entry is future-proof: new commands (paste-and-match, recent queries, saved filters, admin actions) slot in without UI changes.
- Post-MVP features (compare, diff, cross-clause highlighting) fit naturally in the preview column.

### Negative / risks

- **Density.** Three columns + dock is information-dense on first load. Mitigation: generous whitespace, careful type hierarchy, a short first-run hint overlay.
- **Small screens.** The workbench needs ~1280px horizontal to breathe. Mitigation: below 1200px, collapse the filter rail to an icon-only strip; below 1000px, route to a stacked single-column variant. MVP is desktop-only — document this.
- **Engineering surface area.** Three coordinated panes + a palette + a dock is more to build than A's simpler layout. Mitigation: build each pane as an independent component; the command palette can ship in a second release if needed (the search input on the topbar covers the MVP path).
- **Discoverability of shortcuts.** Keyboard-first tools penalize mouse-only users. Mitigation: every keyboard shortcut must have a visible equivalent (button, chip, or icon). The palette itself is a discovery surface.

### Neutral

- Commits us to desktop-first. A mobile ClauseIQ is not on the roadmap; this decision does not block it.
- Commits us to the Linear/Raycast aesthetic family (neutral grays, one accent, dense rows, no card shadows). Downstream design tokens should reflect this.

## Scope boundaries — explicitly out of this decision

The following are **not** decided here and should not be inferred from it:

- AI chat surface — explicitly out of MVP.
- Word add-in — Phase 2.
- Scratchpad scoping (global vs per-matter) — open question.
- Citation style in exported DOCX — open question.
- Pretty-label mapping for clause family names — open question.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| **A · Classic two-pane alone** | Full-page navigation is a tax we pay on every query. Fine for low-frequency tools; wrong for iterative retrieval. |
| **B · Command bar alone** | Drawer scratchpad hides the session's most important progress signal. Filter chips are less scannable than a stable rail for 20 families. |
| **Pure chat UI** | Off-roadmap. Retrieval is the product; a chat surface invites drafting-scope creep we've explicitly deferred. |
| **Pure document-first (Notion-style)** | Prioritizes reading over searching; ClauseIQ is a search tool, not a reading tool. |

## Validation plan

How we'll know this was right within 30 days:

1. **Interactive prototype** tested with 2–3 in-house lawyers.
2. Metrics:
   - *Time to first pin* < 60 seconds (median)
   - *Queries per session* ≥ 6 (median) in a 15-minute task
   - *Preview-pane engagement* ≥ 50% of results viewed
   - Qualitative: zero users say "where did my pinned clauses go?"
3. If density scores badly, fall back to Direction A as-is — no architectural change needed, just a route/component swap.

## Revisit trigger

Revisit this DDR if any of:

- User research shows the preview column is used on < 20% of results (preview is dead weight).
- Engineering estimates for the three-pane build exceed the single-pane build by > 50%.
- A significant mobile or tablet workflow is added to the roadmap.
- We decide to unify ClauseIQ with a drafting surface (not just export) — that likely calls for a fundamentally different layout.
