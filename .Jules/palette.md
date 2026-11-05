# Palette's Journal — Critical UX & Accessibility Learnings

## 2026-11-04 - Accessible Tablists and Non-blocking Async Feedback in Vanilla Dashboards
**Learning:** In minimalist dashboards with vanilla JS and Tailwind, native `alert()` disrupts asynchronous workflows and keyboard navigation breaks if tab switching relies on `event.target` (which can reference inner text or emoji nodes). Incorporating standard WAI-ARIA tab semantics (`role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"`, `aria-labelledby`) alongside targeted ID-based tab button activation and polite live regions (`role="status"`, `aria-live="polite"`) delivers screen reader support, clear focus visibility, and responsive inline status feedback without external component libraries.
**Action:** Always prefer ARIA-annotated tab widgets with `focus-visible:ring-2` and polite live regions over native modal alerts for async form actions.

## 2026-11-05 - WAI-ARIA Keyboard Navigation & Roving Tabindex for Tabs
**Learning:** Adding ARIA roles to tabs is insufficient for keyboard users if roving tabindex and Arrow key handlers are missing. Under WAI-ARIA APG standards, tabs in a `role="tablist"` should support `ArrowRight` / `ArrowLeft` (and `Home` / `End`) to cycle focus and selection, with inactive tabs set to `tabindex="-1"` and the active tab set to `tabindex="0"`. This prevents Tab key trap/clutter and allows single-stroke navigation across panels.
**Action:** Always pair `role="tablist"` with roving `tabindex` and Arrow key event handling on the container.
