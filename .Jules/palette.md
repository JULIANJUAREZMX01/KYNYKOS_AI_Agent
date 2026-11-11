# Palette's Journal — Critical UX & Accessibility Learnings

## 2026-11-04 - Accessible Tablists and Non-blocking Async Feedback in Vanilla Dashboards
**Learning:** In minimalist dashboards with vanilla JS and Tailwind, native `alert()` disrupts asynchronous workflows and keyboard navigation breaks if tab switching relies on `event.target` (which can reference inner text or emoji nodes). Incorporating standard WAI-ARIA tab semantics (`role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"`, `aria-labelledby`) alongside targeted ID-based tab button activation and polite live regions (`role="status"`, `aria-live="polite"`) delivers screen reader support, clear focus visibility, and responsive inline status feedback without external component libraries.
**Action:** Always prefer ARIA-annotated tab widgets with `focus-visible:ring-2` and polite live regions over native modal alerts for async form actions.

## 2026-11-08 - Roving Tabindex and Arrow Navigation in Composite Tab Widgets
**Learning:** Adding `role="tablist"` and `role="tab"` is insufficient for complete keyboard compliance according to the W3C WAI-ARIA Authoring Practices Guide (APG); without roving `tabindex` (`tabindex="0"` on the active tab and `-1` on inactive tabs) and arrow key listeners (`ArrowLeft`/`ArrowRight`/`Home`/`End`), keyboard users are forced to tab through every single tab button before reaching the panel content, rather than cycling through tabs seamlessly with arrow keys.
**Action:** In vanilla tab implementations, bind arrow navigation and Home/End handlers on the tablist container and dynamically synchronize roving `tabindex` on tab change.
