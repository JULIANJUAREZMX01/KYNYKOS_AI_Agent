# Palette's Journal — Critical UX & Accessibility Learnings

## 2026-11-04 - Accessible Tablists and Non-blocking Async Feedback in Vanilla Dashboards
**Learning:** In minimalist dashboards with vanilla JS and Tailwind, native `alert()` disrupts asynchronous workflows and keyboard navigation breaks if tab switching relies on `event.target` (which can reference inner text or emoji nodes). Incorporating standard WAI-ARIA tab semantics (`role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"`, `aria-labelledby`) alongside targeted ID-based tab button activation and polite live regions (`role="status"`, `aria-live="polite"`) delivers screen reader support, clear focus visibility, and responsive inline status feedback without external component libraries.
**Action:** Always prefer ARIA-annotated tab widgets with `focus-visible:ring-2` and polite live regions over native modal alerts for async form actions.

## 2026-11-06 - WAI-ARIA Tab Keyboard Arrow Navigation Pattern
**Learning:** Screen reader users and keyboard navigators expect horizontal tablists to support arrow key navigation (ArrowLeft / ArrowRight) with roving `tabindex` (`tabindex="0"` on the active tab, `-1` on inactive tabs) as well as Home/End shortcuts to jump to the start or end of the tablist. Without roving tabindex and keydown listeners, keyboard users must tab through every tab header sequentially instead of tabbing once into the tablist and moving horizontally with arrow keys.
**Action:** Pair `role="tablist"` with keydown event handlers handling ArrowLeft/Right/Home/End and dynamic roving `tabindex` toggling on active/inactive states.
