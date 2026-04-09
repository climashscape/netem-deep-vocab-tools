# NETEM Deep Vocab Tools - Full App Design System

This file is a project-specific design specification extracted from the current production UI and behavior in:

- `app/index.html`
- `app/static/js/db.js`
- `app/static/js/local_api.js`
- `app/static/js/llm.js`
- `app/static/js/ebbinghaus.js`
- `docs/guidelines/UI_UX_GUIDELINES.md`

It defines not only visuals, but also interaction patterns, page-level structure, state feedback, and AI-content presentation style.

---

## 1. Product Design Intent

NETEM is a long-session study tool, not a short-session social feed.

- Design objective: reduce cognitive friction and preserve attention for memorization
- Core emotional tone: calm, focused, reliable, slightly warm
- Visual language: mobile-first soft neumorphism with low-contrast depth
- Functional emphasis: clear progress, clear due status, clear next action

Top-level principles:

1. Reading and recall come before decoration.
2. Status and progression must always be perceivable at a glance.
3. Every interaction should provide immediate tactile or visual confirmation.

---

## 2. Information Architecture (Current App Reality)

Primary navigation is a 5-tab bottom bar:

1. `philosophy` (intro/start)
2. `learn` (main learning batch)
3. `review` (due words and session/library)
4. `mastery` (core + notebook)
5. `me` (dashboard, streak, breakdown, utilities)

Global shells:

- Sticky header with search and compact stats
- Scrollable content region
- Fixed bottom navigation
- Modal layer stack for learning flow and settings confirmations

Design implication: every new page must respect this shell and not introduce alternate navigation patterns.

---

## 3. Visual Theme and Core Tokens

### 3.1 Light Theme

- `bg.base`: `#e0e5ec`
- `text.primary`: `#4a5568`
- `text.secondary`: `#6b7280`
- `accent.primary`: `#3b82f6`
- `accent.hover`: `#2563eb`
- `success`: `#22c55e`
- `warning`: `#f59e0b`
- `danger`: `#ef4444`
- `neutral.inactive`: `#a0aec0`
- `surface.highlight`: `#ffffff`

Neumorphic shadow family:

- Raised: `6px 6px 10px rgba(163,177,198,0.7), -6px -6px 10px rgba(255,255,255,0.8)`
- Inset: `inset 4px 4px 6px rgba(163,177,198,0.7), inset -4px -4px 6px rgba(255,255,255,0.8)`

### 3.2 Dark Theme Mapping

- background: `#1a1a1a`
- surface: `#2d2d2d`
- text primary: `#e5e7eb`
- text secondary: `#9ca3af`
- accent: `#60a5fa`

Dark mode keeps geometry and hierarchy the same while reducing soft-shadow dependence.

---

## 4. Typography and Content Density

Primary stack (current app truth):

- `'Times New Roman', Times, 'Georgia', serif`

Scale guidance:

- Hero/display: `28-34px`, `700-800`
- Section titles: `20-24px`, `700`
- Card titles: `16-20px`, `700-800`
- Body reading: `14-16px`, line-height `1.55-1.75`
- Status chips/meta: `10-12px`, often uppercase and bold

Reading rules:

- Keep content blocks narrow and vertically segmented.
- Prefer muted gray body text with selective color emphasis.
- AI explanation markdown must prioritize hierarchy and whitespace.

---

## 5. Component System (Canonical)

### 5.1 Foundations

- Radius:
  - small `10-12px`
  - medium `16px`
  - large `20-24px`
  - pill `9999px`
- Touch target minimum: `44x44px`
- Spacing rhythm: 4 / 8 / 12 / 16 / 24 / 32

### 5.2 Buttons and Press States

Key classes/patterns: `neumorphic-btn`, `neumorphic-btn-sm`, `neumorphic-toggle-btn`, `chip-btn`

- Default: raised soft surface
- Pressed (`.is-pressed`): scale `0.95-0.98`, opacity drop, inset-shift shadow
- Tab toggles: active tab uses brighter background and accent text

### 5.3 Cards and Blocks

Key classes/patterns: `verb-card`, `verb-card-block`, `learning-insight-card`, `neumorphic`

- Cards must visually separate title, phonetic, meaning, and auxiliary actions
- Hard borders are secondary; depth mostly from shadow and subtle gradient
- Review/mastery cards prioritize scanning over decoration

### 5.4 Progress and Status

- Progress bars use blue/indigo gradients and smooth width transitions
- Header summary displays total/review/mastered/today with distinct color coding
- Badges are compact, high-contrast, and semantically colored

### 5.5 Navigation

- Fixed bottom nav on `bg.base`
- Inactive: neutral gray
- Active: blue accent
- Review badge (`nav-review-badge`) is red, compact, high urgency

### 5.6 Modals

Core modal types:

- Learning modal (`learningModal`) with staged controls
- Confirmation modals (`confirmModal`, `resetModal`, `refreshConfirmModal`)
- Utility modals (search, analytics, excluded words, import/export flows)

Modal rules:

- Dark translucent backdrop (`~40-50%`) + subtle blur
- Content surface uses same neumorphic family as main app
- Enter/exit transitions should stay within `200-300ms`

---

## 6. Interaction and Motion Specification

### 6.1 Global Interaction Pattern

- Tap feedback must be immediate and visible
- Long press reserved for advanced actions (audio, overlays, card shortcuts)
- Body scroll remains locked; scrolling is delegated to content containers

### 6.2 Gesture Patterns

- Pull to refresh in learn page
- Swipe left/right for navigation in card contexts
- Long-press actions in mastery/word cards

### 6.3 Motion Budget

- Standard transitions: `200-300ms`
- Press transitions: `80-150ms`
- Progress transitions: `300-1000ms`
- Avoid complex blur stacks in repeated list items

---

## 7. Learning Flow UI Contract

Learning flow is staged and must remain explicit:

- Stage progress indicator in modal
- Separate containers for explanation content and essence content
- Distinct control groups for study mode vs review mode
- Reset/refresh actions always confirmed for destructive or expensive operations

Review outcomes:

- `remembered` advances stage
- `forgotten` returns to stage 1
- Mastered state must visually and semantically differ from learning state

Any redesign must preserve these cognitive landmarks.

---

## 8. State Design (Data-Driven UI)

### 8.1 Essential State Categories

- Loading: skeleton/placeholder/progress text
- Empty: clear call to action (start learning, open analytics, switch tab)
- Offline/strict-cache: explicit fallback notice in explanation blocks
- Success: soft affirmative coloring and concise message
- Error: clear actionable copy; no vague failure text

### 8.2 Persistence-Driven UX Expectations

Data comes from IndexedDB and LocalStorage. UI must feel resilient:

- Never block the whole app for single-item failures
- Show cached data first when available
- Surface "refresh explanation" as recoverable action
- Keep settings-dependent behavior transparent (API key, image provider, daily goal)

---

## 9. Copywriting and Tone Rules

Language style:

- Concise, practical, academically oriented
- Encouraging but not gamified-noisy
- Action labels should be verb-first and clear (`Refresh`, `Reset`, `Import`, `Review`)

Message hierarchy:

- Title: what happened
- Body: why / what changed
- Action: next safest step

For AI explanation fallback text, explicitly state offline/strict-cache context.

---

## 10. Accessibility and Device Constraints

- Maintain minimum text/background contrast for all chips and badges
- Preserve safe area support (`safe-area-inset-*`) in shell and nav
- Avoid placing critical actions only in color; include icon/text cues
- Keep one-hand mobile reachability for frequent actions

---

## 11. Do / Don't

Do:

- Keep neumorphism soft and consistent across new components
- Maintain bottom-nav + sticky-header information hierarchy
- Prioritize scanability in review/mastery lists
- Keep feedback immediate and deterministic

Don't:

- Introduce unrelated flat-enterprise UI blocks
- Use aggressive animations in dense reading regions
- Replace serif reading stack without measurable readability gains
- Hide important learning state transitions behind subtle visuals

---

## 12. Agent Prompt Contract (For Future UI Work)

When generating or refactoring UI in this repo, follow this exact instruction set:

1. Use NETEM soft neumorphic design (`#e0e5ec` base, dual-direction shadows, rounded 16/24).
2. Preserve the 5-tab bottom navigation architecture and sticky stats header.
3. Keep mobile-first layout and safe-area correctness.
4. Keep learning/review/mastery stage visibility explicit.
5. Apply touch-first feedback (`is-pressed`, inset transition, subtle scale).
6. Keep AI explanation areas readable, structured, and markdown-friendly.
7. Design for resilient offline/cached behavior, not ideal-network-only scenarios.

Prompt template:

> "Use the repository DESIGN.md as strict source of truth. Preserve NETEM's full app shell (sticky header + bottom nav), soft neumorphic study aesthetic, stage-driven learning flow, and mobile-first interaction details. Improve clarity and density without changing the product's memorization-first behavior."
