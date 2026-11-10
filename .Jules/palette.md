# Palette's Journal — Critical UX & Accessibility Learnings

## 2026-11-04 - Accessible Tablists and Non-blocking Async Feedback in Vanilla Dashboards
**Learning:** In minimalist dashboards with vanilla JS and Tailwind, native `alert()` disrupts asynchronous workflows and keyboard navigation breaks if tab switching relies on `event.target` (which can reference inner text or emoji nodes). Incorporating standard WAI-ARIA tab semantics (`role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"`, `aria-labelledby`) alongside targeted ID-based tab button activation and polite live regions (`role="status"`, `aria-live="polite"`) delivers screen reader support, clear focus visibility, and responsive inline status feedback without external component libraries.
**Action:** Always prefer ARIA-annotated tab widgets with `focus-visible:ring-2` and polite live regions over native modal alerts for async form actions.

## 2026-11-10 - Keyboard Tab Navigation with Roving Tabindex in Vanilla Tablists
**Learning:** Adding ARIA roles to tabs without implementing keyboard navigation leaves keyboard and screen reader users trapped having to Tab through panel content sequentially instead of cycling between tabs using standard arrow keys. Implementing a roving tabindex pattern (`tabindex="0"` on active tab, `tabindex="-1"` on inactive tabs) with keydown listeners for ArrowRight, ArrowLeft, Home, and End provides seamless WAI-ARIA compliant tab navigation without introducing third-party UI framework dependencies.
**Action:** Whenever implementing or refining tab widgets, always pair `role="tablist"` with roving tabindex and Arrow/Home/End keyboard navigation.
