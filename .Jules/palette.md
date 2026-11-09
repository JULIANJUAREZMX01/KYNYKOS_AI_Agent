# Palette's Journal — Critical UX & Accessibility Learnings

## 2026-11-04 - Accessible Tablists and Non-blocking Async Feedback in Vanilla Dashboards
**Learning:** In minimalist dashboards with vanilla JS and Tailwind, native `alert()` disrupts asynchronous workflows and keyboard navigation breaks if tab switching relies on `event.target` (which can reference inner text or emoji nodes). Incorporating standard WAI-ARIA tab semantics (`role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"`, `aria-labelledby`) alongside targeted ID-based tab button activation and polite live regions (`role="status"`, `aria-live="polite"`) delivers screen reader support, clear focus visibility, and responsive inline status feedback without external component libraries.
**Action:** Always prefer ARIA-annotated tab widgets with `focus-visible:ring-2` and polite live regions over native modal alerts for async form actions.

## 2026-11-09 - WAI-ARIA Roving Tabindex & Keyboard Navigation for Tablists
**Learning:** Having `role="tab"` and `role="tabpanel"` alone leaves keyboard and screen reader users trapped if directional keys (ArrowLeft/ArrowRight/Home/End) and roving `tabindex` are omitted: the user would have to Tab through every inactive tab rather than using standard arrow key navigation to cycle tabs and Tab to enter the active panel. Applying roving tabindex (`tabindex="0"` on the active tab, `-1` on inactive tabs) with cyclical arrow key handlers and `tabindex="0"` on tabpanels ensures effortless accessibility and intuitive navigation.
**Action:** Pair every tablist widget with roving tabindex and ArrowLeft/ArrowRight/Home/End listeners, setting `tabindex="0"` on tabpanels for keyboard scrolling.
