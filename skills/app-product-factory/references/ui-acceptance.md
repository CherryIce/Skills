# UI and interaction acceptance

Use for product design, Flutter MVP delivery, and UI-focused audits. The goal is a clear, original interface that keeps the product's core task usable under realistic content and device constraints. Do not copy a reference app's distinctive layout or style.

## Design before implementation

For each primary screen, state the user's next decision, the one action that matters most, and the information needed to take it. Sketch or describe the screen hierarchy and navigation before building cards and colors. Decide what is always visible, what is progressively disclosed, and how the user reaches later steps without searching through unrelated content. Explain how the visual system—type scale, spacing, contrast, icon meaning, and surface treatment—supports that hierarchy; avoid repeated cards, oversized headers, and decorative density that push the core task out of reach.

Specify a content policy for filenames, translated labels, user-entered text, counts, lists, tables, and errors. Important values should wrap, expand, or open a detail view rather than disappear behind unexplained ellipses. Use representative data and at least one stressful but supported case; do not design only for a short English placeholder or an empty screen.

## Rendered-screen acceptance

Inspect the actual running UI, not just source, theme tokens, or a passing widget tree. Choose a small matrix from the supported product surfaces:

- a compact phone and the larger supported form factor, such as tablet when in scope;
- each primary launch language, light/dark appearance, and large text where supported;
- empty, typical, dense/long-content, error, and completed states of the core path;
- bottom navigation/actions, scroll end, keyboard visible, and modal or sheet states when present.

For each relevant case, check that the primary task and next action are obvious, required content is readable, controls do not collide or clip, all actions remain reachable by scrolling or navigation, safe areas and keyboard do not cover controls, and the layout remains balanced without excessive blank or repeated chrome. Inspect the visible screen and the scrolled end; the first viewport alone cannot prove reachability. A screenshot supports visual review only for the state and build it depicts.

Record screen, device/size, locale, text scale, appearance, content state, action path, screenshot or observation, and finding. Fix the highest-impact issue, rebuild, and inspect the affected case again. Treat hidden or unreachable core actions, clipped essential data, and repeatable framework exceptions as blockers. Note untested surfaces honestly; do not label them passed from analyzer or screenshots of another state.

## Interaction reliability

For newly introduced sheets, dialogs, menus, navigation branches, and text inputs, test the real transition: open, interact, confirm or cancel, dismiss by barrier/back if supported, wait through the closing animation, and reopen. Verify no uncaught exception, stale state, lost focus, or unintended data change. Resource ownership must outlive the route/widget that consumes the resource. When a user reports a failure, reproduce their exact action sequence and preserve it as a focused regression test.
