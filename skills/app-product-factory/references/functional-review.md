# Functional review

The Functional Reviewer remains read-only and reviews the approved PRD, implementation, tests, and runtime evidence.

## Findings format

Lead with findings ordered by severity:

- `P0 blocker`: data loss, security/privacy breach, crash on core path, or unusable product.
- `P1 high`: broken core workflow, misleading claim, inaccessible required action, or unrecoverable failure.
- `P2 medium`: important edge case, degraded platform behavior, weak localization, or material test gap.
- `P3 low`: polish or maintainability issue with limited user impact.

Each finding includes the affected requirement/flow, evidence, file or screen when available, user impact, and a concrete acceptance test. If no findings exist, say so and list untested evidence layers.

## Review checklist

- Every advertised core task can be started, completed, canceled, retried, and recovered.
- State persists correctly across relaunch, backgrounding, rotation, interruption, and migration where relevant.
- Empty, loading, partial, stale, error, permission-denied, offline, and destructive-action states are understandable.
- Data import/export, backup/restore, deletion, and conflict behavior protect user work where the product promises them.
- Touch targets, contrast, semantics, keyboard/focus, screen readers, text scaling, reduced motion, and orientation are appropriate.
- Supported languages fit real layouts and do not fall back to internal keys or misleading translations.
- Permissions are requested just in time, have complete purpose strings, and have usable denial alternatives when possible.
- Account creation, authentication, logout, deletion, and credential revocation are internally consistent when present.
- Purchases, subscriptions, restore, entitlement loss, cancellation, and offline receipt states are correct when present.
- User-generated content includes the necessary moderation, reporting, blocking, and age controls when present.
- Tests assert meaningful outcomes instead of mirroring implementation details.
- Screenshots and metadata claims are reproducible in the reviewed build.

Verdict is `passed`, `needs_revision`, or `blocked`. Passing requires no open P0/P1; it does not establish store approval.
