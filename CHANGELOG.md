# Changelog

## v1.7.0 — 2026-10-22

- Publish `post-build-cleanup` for task-scoped cleanup after build, test, and runtime validation.
- Preserve source, uncommitted work, dependency caches, SDKs, signing material, deliverables, and required diagnostic evidence; skip data still in use.
- Include a preview-first cleanup helper with explicit apply, project/path checks, Git protection, symlink guards, protected-path checks, and retained-path exclusions.
- Add 17 isolated behavior tests covering actual cleanup and refusal cases.
- Document installation, explicit/implicit invocation, and an optional global `AGENTS.md` instruction.

## v1.6.0 — 2026-10-21

- Require generated iOS targets to declare `ITSAppUsesNonExemptEncryption=false` when the app and linked libraries use no encryption or only exempt encryption.
- Block false declarations when non-exempt encryption is present or cannot be ruled out, and require a separate export-compliance determination.
- Add source/Archive declaration evidence to product, functional-review, App Store preflight, evidence-register, and review-notes templates.
- Extend the mechanical release preflight with source and final Archive checks for the effective Boolean declaration.

## v1.5.0 — 2026-10-15

- Require every generated MVP/release candidate to include an original non-default App Icon across its Flutter platform targets.
- Require a platform-native launch experience that is immediate, appearance-aware, and visually continuous with the first Flutter frame.
- Require localized, skippable first-run onboarding with persisted skip/completion, returning-user routing, replay, failure coverage, and an explicit existing-user migration policy.
- Add icon, launch, and onboarding fields and evidence rows to the intake, product brief, functional review, App Store preflight, and evidence register templates.

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
