---
name: app-product-factory
description: "Use only when the user explicitly invokes $app-product-factory to turn an app idea into an evidence-based, differentiated Flutter MVP, review its functionality, assess store-readiness, and plan focused revisions. Never activate implicitly for ordinary app development or review requests."
---

# App Product Factory

Build an independent product, not a reskinned or duplicate app. Treat competitor products as research evidence for user needs, category conventions, and unmet jobs; never copy their protected assets, branding, text, screenshots, or distinctive implementation.

## Invocation boundary

- Run this workflow only in the turn where the user explicitly invokes `$app-product-factory`.
- Do not carry activation into later turns unless the user invokes it again.
- An invocation authorizes analysis and the requested local implementation work. It does not authorize purchases, account changes, certificate creation, production deployment, App Store Connect uploads, or review submission.
- Require explicit confirmation immediately before any consequential external action, even if earlier phases pass.

## Defaults

- Use Flutter and Dart for implementation unless the user explicitly chooses another stack.
- Keep platform-specific Swift, Objective-C, Kotlin, or Java code limited to integrations Flutter cannot correctly provide on its own.
- When the request is about Apple review, build a portable Flutter product but evaluate the iOS target and App Store evidence separately.
- Prefer a small complete user workflow over a large collection of disconnected features.
- Preserve unrelated work and existing project conventions. Inspect the Git root, branch, dirty state, Flutter/FVM version, lockfiles, targets, and existing product capabilities before editing.

## Choose the run scope

Infer the narrowest scope that fulfills the invocation:

- `discovery`: research, opportunity assessment, and differentiation only.
- `product_design`: discovery plus product brief, PRD, flows, and visual direction.
- `mvp`: design and implement the smallest complete Flutter product loop.
- `audit`: independently review an existing product and produce gaps without editing unless fixes were requested.
- `release_candidate`: run the full evidence-based store preflight; do not upload or submit.

Ask a question only when the missing answer would materially change the product, regulated category, data handling, monetization, or external action. Otherwise state a reversible assumption and proceed.

## Required workflow

Read [references/workflow.md](references/workflow.md) for phase gates and iteration rules. Use these routed references when their phase is in scope:

- Before approving a concept or proposing extra features, read [references/differentiation.md](references/differentiation.md).
- Before creating or changing Flutter code, or claiming build/runtime validation, read [references/flutter-delivery.md](references/flutter-delivery.md).
- Before functional review, release-candidate work, or claiming feature completeness, read [references/functional-review.md](references/functional-review.md).
- Before any App Store assessment, read [references/app-store-preflight.md](references/app-store-preflight.md) and verify current official Apple requirements live.
- When producing persistent project documents, read [references/artifacts.md](references/artifacts.md) and adapt its schemas to the repository.
- For `mvp` or `release_candidate` runs, read [references/automation.md](references/automation.md) and use its scripts/templates for repeatable mechanical steps.

Never implement a concept that fails the originality gate. Return it for product revision with concrete alternative directions instead.

## Script and template boundary

- Use `scripts/bootstrap_factory_run.py` to initialize the selected scope's honest `not_evaluated` documents from `assets/templates/`; never treat generated scaffolds as evidence.
- After the implementation/revision loop is frozen, use `scripts/flutter_quality_gate.py` for non-mutating format checks, analyzer, tests, and only the locally requested builds.
- Only for `release_candidate`, before Store Reviewer writes the final assessment, use `scripts/flutter_release_preflight.py` to record mechanical release blockers, hashes, archive contents, privacy manifests, identifiers, icon, and screenshot properties.
- Do not use `--force` to replace existing project reports unless their replacement is intentional and reviewed.
- Script results inform reviewers but never decide originality, legal compliance, live URL content, device behavior, or store approval.

## Roles and independence

Keep the Coordinator responsible for scope, gates, evidence, and the final verdict. Use these logical roles:

1. Researcher: collects sources and category evidence; does not design or code.
2. Product Planner: defines audience, problem, core loop, differentiation, and acceptance criteria.
3. Designer: defines navigation, states, accessibility, localization, and original visual direction.
4. Flutter Executor: implements only approved slices.
5. Functional Reviewer: reviews behavior and evidence without editing.
6. Store Reviewer: reviews policy, metadata, privacy, payments, and submission evidence without editing.

For complex invocations, use parallel subagents for independent read-heavy research and review when the environment permits skill-directed delegation. Avoid parallel writes to the same files. Wait for all required reviews, then have the Coordinator resolve conflicts and decide `passed`, `needs_revision`, or `blocked`.

## Evidence rules

Maintain an evidence register that separates:

- static source inspection;
- analyzer and unit/widget tests;
- simulator or emulator runtime;
- physical-device behavior;
- signed Release/Archive contents;
- upload acceptance and store processing;
- App Review decision.

Never use one layer as proof of another. A green local audit means “candidate for the next gate,” not “guaranteed approval.” Every product or store claim must be supported by current code, runtime evidence, an official source, or be labeled an assumption.

## Revision strategy

When a review fails, rank gaps by:

1. policy or safety risk;
2. broken core workflow;
3. user value;
4. meaningful differentiation;
5. accessibility, privacy, reliability, and evidence quality;
6. implementation cost.

Prefer deepening the product loop—capture, plan, act, verify, recover, and export—over decorative accounts, feeds, ads, subscriptions, or superficial AI features. Implement one coherent revision slice, re-run the narrowest relevant checks, and repeat the failed reviews.

## Final delivery

Report:

- product thesis and target user;
- sources inspected and important uncertainties;
- differentiation verdict and why;
- artifacts and code changed;
- functional-review verdict;
- store-readiness verdict by guideline/risk;
- validation performed by evidence layer;
- remaining gaps and the next highest-value revision;
- external actions that still require explicit user confirmation.
