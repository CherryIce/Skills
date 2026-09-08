# Workflow and phase gates

Use only the phases needed by the selected run scope. Do not silently widen discovery into implementation or implementation into submission.

## Phase 0: Intake and authority

Establish:

- target users, problem, usage frequency, and launch regions;
- platform scope and Flutter baseline;
- monetization, login, backend, user-generated content, permissions, and sensitive data;
- supplied competitor references and rights to supplied assets;
- requested stopping point and forbidden external actions.

Classify regulated or high-risk domains early. Financial services, health, children, gambling, crypto, government identity, and safety-critical products require current official policy research and explicit unresolved-risk reporting.

Gate: the proposed product and requested work are legal to assist with, scoped, and do not depend on impersonation, copied assets, or review evasion.

## Phase 1: Workspace and evidence baseline

For an existing repository, inspect the Git root, branch, dirty state, Flutter/FVM version, `pubspec.yaml`, lockfiles, platform folders, build flavors, tests, current screens, data flows, and release configuration. Preserve unrelated changes.

For a greenfield product, record the chosen app identifier placeholders, supported platforms, minimum OS assumptions, persistence approach, navigation, and state-management rationale before scaffolding.

Gate: current capabilities and constraints are documented, and no existing feature will be unknowingly duplicated.

## Phase 2: Category research

Use current, public, permitted sources. Record direct URLs, access dates, exact observations, and inference separately. Analyze multiple products rather than reverse-engineering one product.

Capture:

- audience and primary job;
- core workflow and notable native capabilities;
- business model and account requirements;
- repeated complaints, missing states, trust problems, and accessibility/localization gaps;
- category conventions that are functional rather than brand-specific.

Do not scrape Apple services or copy store assets when their terms or Apple policy prohibit it. Prefer official product pages, public support material, licensed datasets, supplied screenshots, and permitted web research.

Gate: evidence supports a real user problem and exposes at least one plausible opportunity.

## Phase 3: Product thesis and originality

Define one sentence each for the target user, costly problem, product promise, core loop, and durable output. Apply the originality rubric before creating code.

Gate: `passed`, `needs_revision`, or `blocked`. Code may start only after `passed`.

## Phase 4: Product and interaction design

Produce the smallest PRD that fully describes:

- happy path and failure/recovery paths;
- navigation and screen/state inventory;
- domain model and persistence boundaries;
- permission timing, privacy, account, payment, and deletion behavior;
- accessibility, Dynamic Type, dark mode, localization, empty/loading/error/offline states;
- analytics only if necessary and disclosed;
- acceptance criteria traceable to the core loop.

Create an original visual direction. Do not reproduce a competitor screenshot or layout pixel-for-pixel.

Gate: each core claim maps to an interaction, state, data owner, and acceptance criterion.

## Phase 5: Flutter MVP

Implement vertical slices, starting with the smallest end-to-end loop. Keep generated/demo content clearly separated from release content. After each slice, run the narrowest useful validation before broadening.

Gate: the core loop builds, launches, persists or transmits data as designed, and has meaningful automated coverage.

## Phase 6: Independent reviews

Run Functional Reviewer first, then Store Reviewer. Reviewers report findings with severity, evidence, affected flows/files, and an acceptance test for the fix. They do not edit.

Gate: no unresolved blocker or high-severity finding. Medium findings must be accepted explicitly or placed in the revision plan.

## Phase 7: Gap iteration

Convert findings into a ranked backlog. Avoid feature-count inflation. Choose the smallest slice that improves both real utility and differentiation, implement it, and repeat only the affected gates.

Gate: the revision has observable acceptance criteria and does not introduce a new policy, privacy, payment, or platform dependency without review.

## Phase 8: Release-candidate evidence

Verify production identifiers and icons, signing assumptions, privacy manifests and declarations, public privacy/support URLs, metadata, screenshots, reviewer access, backend availability, on-device behavior, archive contents, and any IAP products.

Gate: “release candidate” only. Uploading, submitting, pricing, agreements, certificates, and production mutations require explicit user confirmation.
