---
name: frontend-design
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a collapsible left sidebar, consistent spacing, and a polished professional look. Use this skill when asked to redesign, restyle, or modernize a Vue app's layout or navigation.
---

# Frontend Design — SaaS-Style Vue 3 Redesign

Transform a Vue 3 application from a basic layout (typically a top nav bar) into a polished, modern SaaS-style interface. This skill is app-agnostic: discover the app's structure first, then apply the design system below.

## Phase 1 — Discover before touching anything

1. Locate the root layout component (usually `App.vue`) and how navigation is rendered (router-links vs conditional views).
2. Inventory the existing global styles: where do shared classes like cards, tables, badges live? Redesign them in place — do not fork a parallel style system.
3. Note every widget mounted in the current header (logo, language/profile menus, search) — each must survive the migration to the new layout.
4. Check for a global filter/toolbar row; it stays with the content column, not the sidebar.
5. Respect the app's existing i18n: nav labels must keep using the translation function, never hardcoded strings.

## Phase 2 — Layout transformation

**Structure**: replace the top nav with a two-column app shell:

```
┌─────────┬──────────────────────────────┐
│ sidebar │  toolbar / filter row         │
│ (fixed) │──────────────────────────────│
│         │  scrollable content area      │
└─────────┴──────────────────────────────┘
```

- Sidebar: `position: fixed; top: 0; bottom: 0; left: 0;` — content column gets `margin-left: var(--sidebar-width)`.
- Expanded width **240px**, collapsed **64px**. Store both as CSS variables; transition `width` and `margin-left` at `0.2s ease`.
- The sidebar holds: logo/app name at top, vertical nav links, then secondary widgets (language switcher, profile) pinned to the bottom with `margin-top: auto`.

**Collapsible (icons-only) mode — required**:
- A toggle button at the sidebar's top or bottom collapses it to icons-only.
- Each nav item needs an icon (inline SVG, 20px, `stroke="currentColor"`) plus a label; in collapsed mode hide labels (`opacity`/`width` transition, not `display:none` snap) and show a `title` tooltip.
- Persist the collapsed state in `localStorage`; default expanded on desktop, collapsed under 1024px (media query or resize listener).

## Phase 3 — Design system

**Light sidebar aesthetic** (Notion-style):
- Sidebar: white or near-white (`#ffffff` / `#f8fafc`) with a `1px` right border (`#e2e8f0`).
- Nav links: muted text (`#64748b`), `8px` radius hover background (`#f1f5f9`); active link gets a tinted background (`#eef2ff` or brand-tint) + strong text color + optional 3px left accent bar.
- Content background: `#f8fafc`; cards white with `1px #e2e8f0` border, `10–12px` radius, subtle shadow (`0 1px 2px rgb(0 0 0 / 0.05)`).

**Spacing scale** — use multiples of 4px only: 4 / 8 / 12 / 16 / 24 / 32. Page padding 24–32px; card padding 20–24px; consistent `gap` in grids (16–24px).

**Typography**: page titles 22–26px/600; card titles 15–16px/600; section labels 11–12px uppercase with letter-spacing; body 13–14px. Never more than 3 font sizes per view.

**Keep, don't replace**: existing status colors, badge classes, chart styles, and table patterns stay — restyle their containers, not their semantics. No emojis in business UI. No new dependencies (no UI kits, no icon fonts — inline SVG only).

## Phase 4 — Migration checklist

- [ ] Root layout converted to sidebar + content shell; all routes render correctly
- [ ] Every nav destination present, with icon + translated label, correct active state
- [ ] Header widgets (profile, language, etc.) relocated and functional
- [ ] Filter/toolbar row spans the content column below any content header
- [ ] Collapse toggle works; state persists across reloads; small screens default collapsed
- [ ] Global styles updated in place — no orphaned top-nav CSS left behind
- [ ] Spot-check each view for spacing/overflow regressions (tables, modals, dropdowns)
- [ ] Both locales render correctly in the sidebar (long labels must not clip)

## Verification

Run the app and click through every route in both expanded and collapsed sidebar modes; verify modals and dropdown menus aren't clipped by the fixed sidebar (z-index), and take before/after screenshots of at least the main dashboard view.
