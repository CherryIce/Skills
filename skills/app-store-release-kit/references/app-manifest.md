# Per-app manifest

`<app-root>/release-kit.yml` stores durable facts and creative choices that cannot be
rediscovered safely on every run. It is input to the agent; deterministic scripts do
not require a YAML parser.

Use the scaffold script to create it from `assets/release-kit.yml.tmpl`. Preserve
confirmed values on later runs. Do not replace a non-empty value with a guess.

## Required before a complete package

- `identity.app_name`
- `identity.operator`
- `contact.support_email`
- `contact.production_domain`
- `privacy.effective_date`
- `platforms.ios.iphone` and `platforms.ios.ipad`
- `platforms.android.phone`
- `website.default_locale` and both `en` and `zh-Hans` in `website.locales`

Bundle identifiers, package names, and versions should normally be extracted from
project files and recorded only when multiple targets make selection ambiguous.

## Screenshot scenes

Each scene describes a real, reproducible app state. Source paths are relative to the
corresponding `preview-spec.json` unless absolute.

```yaml
screenshots:
  source_policy: real-runtime-only
  app_store:
    locale: en-US
    scenes:
      - id: home
        source: source/01-home-ios.png
        headline: Plan With Clarity
        subheadline: See today's work and what comes next.
  google_play:
    locales:
      - en-US
      - zh-CN
    scenes:
      - id: home
        source: source/01-home-android.png
        headline_en: Plan With Clarity
        headline_zh: 清晰规划每一天
```

Headlines are creative direction, not evidence. Verify them against the app before
using them. A missing iOS or Android source capture is an open item, not permission
to synthesize UI or reuse a capture from the other platform.

## Website localization

Store complete English and Simplified Chinese product and privacy copy. Do not infer
a privacy claim in one language that does not exist in the other. The checked-in HTML
contains both languages; `site.js` chooses the active presentation.

## Privacy review

Use `privacy.confirmed` only for facts supported by code or the user. Keep uncertain
items under `privacy.open_questions`. Typical review topics include:

- account and authentication;
- local and remote storage;
- analytics, diagnostics, advertising, attribution, and tracking;
- camera, photos, microphone, speech, location, contacts, notifications, and files;
- API hosts, cloud sync, AI services, payments, backups, exports, and sharing;
- retention and user-controlled deletion.
