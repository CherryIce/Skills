# Changelog

## v1.4.0 — 2026-10-15

- Publish `app-store-release-kit` with per-app fact collection, listing drafts, real-runtime screenshot rendering, bilingual website and privacy templates, and a release-material validation gate.
- Make the published release kit's script commands work from either a Codex installation or a project-local copy.
- Document installation and invocation for both available skills.

## v1.3.0 — 2026-10-13

- Default generated bilingual products to system-following locale resolution with English fallback and persistence only for explicit user overrides.
- Default appearance to system light/dark until the user explicitly selects and persists an override.
- Define scroll-end safe-area behavior as dynamic trailing content inset rather than a fixed blank partition, with no double-counted bottom obstruction.
- Default alert, confirmation, destructive-choice, and action-sheet presentation to iOS/Cupertino style.

## v1.2.0 — 2026-09-17

- Add project-local, structured retrospectives for each invoked run, with explicit outcomes and evidence limits.
- Add an opt-in cross-run lesson summarizer that reads only supplied records and distinguishes repeat attempts in one project from independent project evidence.
- Keep Skill changes, Git pushes, tags, and releases behind separate human review; retrospective candidates are never auto-adopted.
- Add behavioral tests for the retrospective scaffold and candidate-summary thresholds.

## v1.1.0 — 2026-09-17

- Add UI and interaction acceptance guidance for information hierarchy, realistic content, small screens, accessibility settings, and rendered-screen review.
- Require focused regression coverage for modal dismissal, animation lifetime, re-entry, and unintended state changes.
- Distinguish app exceptions from moved-project generated paths and shared-simulator termination during Flutter validation.
- Extend product, functional-review, and evidence templates with explicit visual and runtime acceptance records.

## v1.0.0 — 2026-09-08

- Publish the explicit-only `app-product-factory` Codex skill.
- Default implementation stack to Flutter and Dart.
- Add scope-aware product, review, and release document templates.
- Add repeatable Flutter quality-gate and release-preflight scripts.
- Preserve evidence-layer boundaries and require confirmation for consequential external actions.
