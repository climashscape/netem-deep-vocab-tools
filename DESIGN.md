# NETEM Deep Vocab Tools - Apple HIG Design System

This file is the project-specific design specification for the Apple Human Interface Guidelines (HIG) redesign.

It references:
- `app/index.html` (CSS variables + HTML structure)
- `app/static/js/db.js`
- `app/static/js/local_api.js`
- `app/static/js/llm.js`
- `app/static/js/ebbinghaus.js`

---

## 1. Product Design Intent

NETEM is a long-session study tool, not a short-session social feed.

- Design objective: reduce cognitive friction and preserve attention for memorization
- Core emotional tone: calm, focused, reliable, native-feeling
- Visual language: **Apple HIG** — flat, clear hierarchy, system fonts, safe areas, light/dark adaptive
- Functional emphasis: clear progress, clear due status, clear next action

Top-level principles:

1. Reading and recall come before decoration.
2. Status and progression must always be perceivable at a glance.
3. Every interaction should provide immediate visual confirmation.
4. Follow iOS platform conventions for familiarity and predictability.

---

## 2. Information Architecture

Primary navigation is a 5-tab bottom bar (iOS Tab Bar style):

1. `philosophy` (intro/start)
2. `learn` (main learning batch)
3. `review` (due words and session/library)
4. `mastery` (core + notebook)
5. `me` (dashboard, streak, breakdown, utilities)

Global shells:

- iOS Navigation Bar (sticky) with Large Title + search + compact stats
- Scrollable content region (safe-area-aware)
- Fixed bottom Tab Bar with frosted glass background
- iOS Sheet-style modal layer for learning flow
- iOS Alert-style dialogs for confirmations

---

## 3. Visual Theme and Core Tokens

All tokens are defined as CSS custom properties in `:root` (light) and `prefers-color-scheme: dark` media query.

### 3.1 iOS System Colors

| Token | Light | Dark |
|-------|-------|------|
| `--ios-blue` | `#007AFF` | `#0A84FF` |
| `--ios-red` | `#FF3B30` | `#FF453A` |
| `--ios-green` | `#34C759` | `#30D158` |
| `--ios-orange` | `#FF9500` | `#FF9F0A` |
| `--ios-indigo` | `#5856D6` | `#5E5CE6` |
| `--ios-purple` | `#AF52DE` | `#BF5AF2` |
| `--ios-cyan` | `#32ADE6` | `#64D2FF` |
| `--ios-teal` | `#5AC8FA` | `#64D2FF` |

### 3.2 Semantic Background Tokens

| Token | Light | Dark |
|-------|-------|------|
| `--bg-primary` | `#F2F2F7` (grouped) | `#000000` |
| `--bg-secondary` | `#FFFFFF` | `#1C1C1E` |
| `--bg-tertiary` | `#F2F2F7` | `#2C2C2E` |
| `--text-primary` | `#1C1C1E` | `#FFFFFF` |
| `--text-secondary` | `#3A3A3C` | `#EBEBF5` |
| `--text-tertiary` | `#8E8E93` | `#8E8E93` |
| `--separator` | `rgba(60,60,67,0.12)` | `rgba(84,84,88,0.36)` |
| `--fill-primary` | `rgba(120,120,128,0.20)` | `rgba(120,120,128,0.36)` |

### 3.3 Tab Bar

| Token | Light | Dark |
|-------|-------|------|
| `--tab-bar-bg` | `rgba(249,249,249,0.94)` | `rgba(34,34,36,0.92)` |
| `--tab-bar-active` | `#007AFF` | `#0A84FF` |
| `--tab-bar-inactive` | `#8E8E93` | `#8E8E93` |

### 3.4 Navigation Bar

| Token | Light | Dark |
|-------|-------|------|
| `--nav-bar-bg` | `rgba(249,249,249,0.94)` | `rgba(34,34,36,0.92)` |

---

## 4. Typography

Primary stack:

```css
--font-system: -apple-system, 'SF Pro Display', 'SF Pro Text',
               'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
--font-mono: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
```

iOS text style scale:

| Style | Size | Weight | Letter-spacing |
|-------|------|--------|----------------|
| Large Title | `34px` | `700` | `0.37px` |
| Title 2 | `22px` | `700` | `0.35px` |
| Title 3 | `20px` | `600` | `0.38px` |
| Headline | `17px` | `600` | `-0.43px` |
| Body | `17px` | `400` | `-0.43px` |
| Footnote | `13px` | `400` | `-0.08px` |
| Caption | `12px` | `400` | `0px` |

Reading rules:

- Keep content blocks narrow and vertically segmented.
- Prefer muted body text with selective color emphasis.
- AI explanation markdown must prioritize hierarchy and whitespace.

---

## 5. Component System

### 5.1 Foundations

- Radius:
  - small `8-10px` (iOS pills, search fields)
  - medium `12-14px` (cards, modals, buttons)
  - large `14px` (modal sheets)
  - pill `9999px`
- Touch target minimum: `44x44px`
- Spacing rhythm: 4 / 8 / 12 / 16 / 20 / 24 / 32

### 5.2 Buttons and Press States

Key classes: `neumorphic-btn`, `neumorphic-btn-sm`, `neumorphic-toggle-btn`, `chip-btn`

- **Primary**: blue background (`--ios-blue`), white text, flat
- **Secondary**: `--fill-tertiary` background, default text color
- **Pressed** (`.is-pressed`): opacity drop to `0.7`, no transform
- **Segmented Control toggle**: active uses `--bg-secondary` + shadow, inactive uses `--fill-tertiary`

### 5.3 Cards and Blocks

Key classes: `verb-card`, `neumorphic` (now iOS card style)

- Cards use `--bg-secondary` background, `0.5px` subtle border (`--separator`)
- Shadows: `0 1px 3px rgba(0,0,0,0.08)` — very subtle depth only
- Hard borders replaced with `--separator` hairline
- Review/mastery cards prioritize scanning over decoration

### 5.4 Progress and Status

- Progress bars: thin `4px` track, `--ios-blue` fill, `0.7s` ease transition
- Header summary: compact stats row with `--fill-tertiary` background
- Badges: compact, high-contrast, semantically colored

### 5.5 Navigation

- **Tab Bar**: fixed bottom, frosted glass (`backdrop-filter: blur(20px)`), 5 tabs
  - Inactive: `--tab-bar-inactive` (`#8E8E93`)
  - Active: `--tab-bar-active` (`#007AFF`)
- **Nav Bar**: sticky top, frosted glass, Large Title, search bar below
- Review badge: red, compact, high urgency

### 5.6 Modals

Core modal types:

- **Learning modal** (`learningModal`): iOS Sheet style (bottom-anchored, rounded top corners, slide-up animation)
- **Alert modals** (`confirmModal`, `resetModal`, `refreshConfirmModal`): iOS Alert style (centered card, rounded `14px`)
- **Utility modals** (search, analytics, settings): iOS Card style

Modal rules:

- Dark backdrop (`rgba(0,0,0,0.4)`) + blur
- Content surface uses `--bg-secondary`
- Enter/exit transitions: `250-400ms`, cubic-bezier `(0.22, 1, 0.36, 1)`

---

## 6. Interaction and Motion

### 6.1 Global Interaction Pattern

- Tap feedback via JS-controlled `.is-pressed` class (opacity drop)
- Long press reserved for advanced actions
- Body scroll locked; scrolling delegated to content containers

### 6.2 Gesture Patterns

- Pull to refresh in learn page
- Swipe left/right for navigation in card contexts
- Long-press actions in mastery/word cards

### 6.3 Motion Budget

- Standard transitions: `200-300ms`
- Press transitions: `100-150ms`
- Progress transitions: `300-1000ms`
- Modal sheet enter: `400ms` cubic-bezier `(0.22, 1, 0.36, 1)`

---

## 7. Learning Flow UI Contract

Learning flow is staged and must remain explicit:

- Stage progress indicator in modal
- Separate containers for explanation content and essence content
- Distinct control groups for study mode vs review mode
- Reset/refresh actions always confirmed for destructive/expensive operations

Review outcomes:

- `remembered` advances stage
- `forgotten` returns to stage 1
- Mastered state must visually and semantically differ from learning state

Any redesign must preserve these cognitive landmarks.

---

## 8. State Design (Data-Driven UI)

### 8.1 Essential State Categories

- Loading: spinner/text in modal overlay
- Empty: clear call to action
- Offline/strict-cache: explicit fallback notice in explanation blocks
- Success: soft affirmative coloring and concise message
- Error: clear actionable copy; no vague failure text

### 8.2 Persistence-Driven UX

Data comes from IndexedDB and LocalStorage. UI must feel resilient:

- Never block the whole app for single-item failures
- Show cached data first when available
- Surface "refresh explanation" as recoverable action
- Keep settings-dependent behavior transparent

---

## 9. Copywriting and Tone Rules

- Concise, practical, academically oriented
- Encouraging but not gamified-noisy
- Action labels should be verb-first and clear

---

## 10. Accessibility and Device Constraints

- `safe-area-inset-*` support for notched devices
- Minimum text/background contrast for all elements
- Avoid placing critical actions only in color
- One-hand mobile reachability for frequent actions
- Dark mode follows system preference (`prefers-color-scheme`)

---

## 11. Do / Don't

Do:

- Maintain iOS visual consistency across all components
- Use CSS variables for all colors (never hardcode)
- Keep bottom-nav + nav-bar information hierarchy
- Prioritize scanability in review/mastery lists
- Keep feedback immediate and deterministic
- Support light/dark mode automatically

Don't:

- Use neumorphism shadows or `#e0e5ec` backgrounds
- Use external icon libraries for static icons (use inline SVG)
- Use aggressive animations in dense reading regions
- Hide important learning state transitions behind subtle visuals
- Hardcode platform-specific colors

---

## 12. Agent Prompt Contract (For Future UI Work)

When generating or refactoring UI in this repo, follow this exact instruction set:

1. Use Apple HIG design system (CSS variables from `:root`, `--bg-*`, `--text-*`, `--ios-*`).
2. Preserve the 5-tab bottom navigation architecture and sticky stats header.
3. Keep mobile-first layout and safe-area correctness.
4. Keep learning/review/mastery stage visibility explicit.
5. Apply touch-feedback via `.is-pressed` (opacity, not transform).
6. Use inline SVG icons for static icons; keep Font Awesome for JS-dynamic icons only.
7. Keep AI explanation areas readable, structured, and markdown-friendly.
8. Design for resilient offline/cached behavior, not ideal-network-only scenarios.
9. Dark mode uses `prefers-color-scheme: dark` media query; do not add manual toggle.
