---
name: app-store-release-kit
description: Generate or refresh one app's App Store and Google Play screenshots, shared English listing copy, bilingual Chinese-English static website, and bilingual HTML privacy policy from repository evidence. Use for repeatable release-material work in an apps directory; do not use for uploading, publishing, or submitting without an explicit request.
---

# App Store Release Kit

Build a reviewable iOS and Android release-material package for exactly one target
app. Treat the target app's implementation as the source of truth; sibling apps
provide layout examples only.

Resolve the directory containing this `SKILL.md` before running its scripts. For
an installation through Codex's skill installer, use:

```bash
release_kit_skill_root="${CODEX_HOME:-$HOME/.codex}/skills/app-store-release-kit"
```

For a project-local copy, set `release_kit_skill_root` to that copy's absolute
directory instead. Run the commands below from the target app's repository root.

## Boundaries

- Scope every read and write to the named app plus this skill. Preserve unrelated
  dirty worktree changes.
- Generate and validate by default. Do not deploy the website, upload metadata or
  media, start a signed build, or submit either store review unless explicitly asked.
- Do not invent product features, privacy behavior, legal identity, support contact,
  production domains, runtime screenshots, or device evidence.
- Store screenshots must contain real target-app UI captured on the corresponding
  platform. Generated imagery is limited to decorative backgrounds and the Google
  Play feature graphic; it must not imitate functional UI.
- A privacy policy is a product-specific draft, not legal advice. Derive every data,
  permission, storage, account, analytics, advertising, AI, network, backup, export,
  and sharing statement from evidence or an explicit user-provided fact.

## Start

1. Resolve the target app root. Support both `apps/name` and nested roots such as
   `apps/name/name` by locating the relevant `pubspec.yaml`, Xcode project, Android
   app, or source. Stop on ambiguity instead of selecting a sibling.
2. Read [references/app-manifest.md](references/app-manifest.md). If the app has no
   `release-kit.yml`, run:

   ```bash
   python3 "$release_kit_skill_root/scripts/scaffold_release_kit.py" <app-root>
   ```

   Fill inferable values. Ask once for missing material facts that cannot be safely
   inferred, especially operator, support email, production domain, and privacy
   effective date. Save confirmed values so later runs need only the app path.
3. Read [references/output-contract.md](references/output-contract.md),
   [references/apple-rules.md](references/apple-rules.md), and
   [references/google-play-rules.md](references/google-play-rules.md). Refresh the
   linked official rules if current limits or image requirements may have changed.

## Evidence pass

Run the facts collector before drafting claims:

```bash
python3 "$release_kit_skill_root/scripts/collect_app_facts.py" \
  <app-root> --output <app-root>/artifacts/release-kit/app-facts.json
```

Then inspect the cited source files. The collector reports signals, not legal
conclusions. Confirm important behavior through code, configuration, permissions,
privacy manifests, dependencies, and user-visible flows. Record unresolved facts in
`artifacts/release-kit/OPEN_ITEMS.md`; do not turn absence of evidence into a claim
such as "no data collection" or "fully offline."

## Generate the package

### Shared English listing

- Write the shared App Store and Google Play full description to
  `artifacts/app-store-listing/description-en.txt`; keep it at 4,000 characters or
  fewer.
- Write Apple-only comma-separated English keywords to
  `artifacts/app-store-listing/keywords-en.txt`; keep them at 100 UTF-8 bytes or
  fewer.
- Write the Google Play English short description to
  `artifacts/google-play-listing/short-description-en.txt`; keep it at 80 characters
  or fewer on one line.
- Keep claims repository-backed and user-focused. Avoid unprovable superlatives,
  competitor names, prices, rankings, calls to action, and future promises.
- Do not duplicate the full description into a second Google-only file unless an
  established project workflow requires it. One source prevents copy drift.

### Bilingual website and privacy policy

- Adapt `assets/website/index.html.tmpl`, `privacy.html.tmpl`, `styles.css`, and
  `site.js` into `<app-root>/website/`. Replace every marker and remove inapplicable
  sections.
- Each HTML file must contain complete English and Simplified Chinese content, not
  only bilingual navigation. Keep both versions semantically aligned and grounded in
  the same evidence.
- Preserve the language switch. It uses `?lang=en` or `?lang=zh`, remembers the
  selection locally, falls back to the browser language, and updates the document
  title, metadata, and `<html lang>` value. HTML-escape any generated copy placed in
  attributes.
- The product page must link to `privacy.html` and expose a real support contact.
- Both privacy versions must explain actual collection, storage, permissions,
  network services, retention/deletion, exports/sharing, children's handling when
  relevant, changes, and contact details. Phrase conditional OS or third-party
  processing precisely.
- Copy the target app's production icon and approved product images into
  `website/assets/`; do not silently substitute a sibling's branding.

### Store screenshots and Google Play feature graphic

1. Reuse existing real runtime captures or capture stable target-app states. Use
   iOS captures for App Store images and Android captures for Google Play images. If
   a repeatable demo state or capture path is absent, report the gap rather than
   fabricating UI or data.
2. Choose three to six distinct implemented scenes per store. Google Play requires
   at least two phone screenshots; target four or more high-resolution screenshots.
   Keep overlay text factual, localized, and within roughly the top 20% of a Play
   screenshot.
3. Create these specifications from [references/output-contract.md](references/output-contract.md):

   - `artifacts/app-store-previews/preview-spec.json`
   - `artifacts/google-play-listing/preview-spec.json`

   Run the renderer once for each specification:

   ```bash
   python3 "$release_kit_skill_root/scripts/render_previews.py" \
     --spec <app-root>/artifacts/app-store-previews/preview-spec.json
   python3 "$release_kit_skill_root/scripts/render_previews.py" \
     --spec <app-root>/artifacts/google-play-listing/preview-spec.json
   ```

4. The Google Play specification also produces a 1024 x 500 feature graphic. Keep
   it brand-led: no device frame, UI screenshot, tiny text, price, ranking, badge, or
   prominent duplicated app icon.
5. Inspect generated contact sheets and full-resolution output. Rendering success is
   not visual approval; check cropping, safe areas, localized text, text proportion,
   contrast, scene order, real-data exposure, and consistency with the current app.

## Validate

Run the deterministic gate and save its report:

```bash
python3 "$release_kit_skill_root/scripts/validate_release_kit.py" \
  <app-root> --report <app-root>/artifacts/release-kit/QA_REPORT.md
```

Resolve all errors. Review warnings instead of deleting them mechanically. Open both
HTML pages, switch between English and Chinese, and inspect every final image. If
runtime capture, public URL reachability, legal review, or device proof was not
performed, state that boundary explicitly.

## Completion report

Report:

- exact target app and files created or changed;
- full-description character count, Apple keyword UTF-8 byte count, and Google Play
  short-description character count;
- App Store and Google Play screenshot counts, locales, dimensions, color modes,
  feature-graphic dimensions, and visual-review status;
- bilingual website/privacy checks and unconfirmed facts;
- what was not done: publishing, App Store Connect or Play Console mutation, signed
  builds, IPA/AAB upload, processing, TestFlight/internal testing, review submission,
  and physical-device verification unless each is separately evidenced.
