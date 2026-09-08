# Repeatable automation runbook

These steps were distilled from a successful Flutter MVP run. They automate stable mechanical work while leaving product judgment, source interpretation, functional findings, and current store policy to the responsible reviewers.

Resolve the skill directory from the loaded `SKILL.md`; do not assume the caller's current directory is the skill directory.

## 1. Create and complete intake

Create an editable config outside the product source first:

```bash
python3 scripts/bootstrap_factory_run.py --init-config /absolute/work/path/factory-intake.json
```

Edit that JSON with confirmed requirements and explicitly labeled assumptions. Then render documents into an existing project directory:

```bash
python3 scripts/bootstrap_factory_run.py \
  --project /absolute/path/to/flutter-project \
  --config /absolute/work/path/factory-intake.json
```

The renderer reads `scope` and creates only that scope's product/release scaffolds with `not_evaluated` verdicts. It preserves existing files by default. Use `--dry-run` to preview. Use `--force` only when replacing the whole generated document set is intentional; inspect the diff afterward.

Stop after the relevant phase: `discovery` and `product_design` do not continue into implementation; `mvp` and `audit` do not continue into release preflight unless that scope is explicitly expanded to `release_candidate`.

## 2. Research and originality gate

Researcher completes `MARKET_EVIDENCE.md`. Product Planner completes `PRODUCT_BRIEF.md` and `DIFFERENTIATION.md`. Do not create app code until the originality verdict is `passed` with no hard failure.

If the working directory contains concepts rather than a Flutter app, preserve them as inputs and create the product in a separate, clearly named directory. Do not present concept screens as implemented runtime evidence.

## 3. Scaffold and implement the smallest loop

For a greenfield app, use Flutter's own scaffold with explicit platforms, organization placeholder, and project name derived from intake. Record that a placeholder organization or Bundle ID is a release blocker. Add only dependencies required by the approved core loop.

Implement domain model and repository boundaries before UI breadth. Exercise cancellation, invalid input, partial state, save failures, recovery, destructive actions, re-evaluation after changes, and bounded resource usage. Run focused tests during each slice.

## 4. Functional review and revision

Freeze a coherent first implementation and send it to an independent Functional Reviewer. Keep findings open until an acceptance test passes. A previous successful run benefited most from checking:

- stable identities across re-evaluation;
- no silent normalization of user input;
- save-before-commit and failure-safe busy/error state;
- quality/status scores that cannot be gamed by “keep” actions;
- bounded issue/card generation for sparse large inputs;
- historical fixed/ignored items reopening when source values change;
- temporary export cleanup on success, failure, and next launch.

These are examples of state-machine and data-safety questions, not universal requirements for every app. Translate them to the current product's invariants.

## 5. Freeze code and run quality gates

After Functional Reviewer has no open P0/P1, run the safe baseline:

```bash
python3 scripts/flutter_quality_gate.py --project /absolute/path/to/flutter-project
```

For a locally requested Android debug build and macOS unsigned iOS archive:

```bash
python3 scripts/flutter_quality_gate.py \
  --project /absolute/path/to/flutter-project \
  --all-local
```

For a flavored project or non-default entry point, supply the values found during project inspection:

```bash
python3 scripts/flutter_quality_gate.py \
  --project /absolute/path/to/flutter-project \
  --all-local \
  --flavor production \
  --target lib/main_production.dart
```

The script runs a non-mutating format check, `flutter analyze --no-pub`, `flutter test --no-pub`, and requested builds. It records timestamped JSON, Markdown, and full logs under `docs/release/evidence/automation/`. It never runs dependency upgrades, production signing, upload, or submission. An explicitly requested Android debug build may create or use the conventional local debug keystore; report that local side effect and never treat it as release-signing evidence.

If a step fails, fix only the relevant scope and run a new timestamped gate. Do not rewrite prior evidence.

## 6. Runtime evidence

Launch the frozen build on the smallest relevant simulator/device matrix. At minimum, inspect phone and tablet layouts when both are supported, primary language variants, dark mode, large text, empty/data/error states, and the full core loop. For platform integrations, add physical-device evidence when simulator behavior is insufficient.

Capture screenshots only after the intended state is visible. Record device, OS, build mode, app version, action path, result, timestamp, and limitations. A simulator capture is runtime evidence, not automatically valid App Store marketing material.

For `mvp` or `audit`, stop here after the Functional Reviewer updates the evidence register and gap backlog. Continue only when `release_candidate` is the selected scope.

## 7. Mechanical release preflight (`release_candidate` only)

Run after the final local archive and screenshots exist:

```bash
python3 scripts/flutter_release_preflight.py \
  --project /absolute/path/to/flutter-project \
  --expected-bundle-id com.yourcompany.yourproduct \
  --privacy-url https://your-domain.example/privacy \
  --support-url https://your-domain.example/support \
  --screenshot /absolute/path/to/screenshot.png \
  --artifact /absolute/path/to/other-file
```

Replace every placeholder argument before running. The preflight checks local source traceability, selected source and Archive identity/version alignment, prototype wording, 1024px icon/alpha, signature/provisioning presence, privacy manifests, embedded frameworks, screenshot PNG properties, explicit artifact presence, and artifact SHA-256 values. It does not infer that a provisioning profile is App Store distribution. Missing signature evidence or URLs correctly keeps it blocked. A syntactically valid URL is still unverified until Store Reviewer opens it.

## 8. Store review and final reports

Store Reviewer reads the latest mechanical reports, final code/release evidence, and current official Apple sources. Complete `APP_STORE_PREFLIGHT.md`, `EVIDENCE_REGISTER.md`, `GAP_BACKLOG.md`, privacy-policy draft, and review-notes draft without overstating evidence.

Stop at `candidate`, `high_risk`, or `blocked`. Upload, signing-account changes, App Store Connect changes, pricing, agreements, and review submission require explicit user confirmation.
