# Output contract

Use these paths unless the target app already has an equivalent established layout.
Do not create duplicate copies only to satisfy naming.

```text
<app-root>/
├── release-kit.yml
├── website/
│   ├── index.html                   English + Simplified Chinese
│   ├── privacy.html                 English + Simplified Chinese
│   ├── styles.css
│   ├── site.js                      language selection and metadata
│   └── assets/
├── app-store/
│   └── metadata.yml                 optional upload manifest; disabled by default
└── artifacts/
    ├── release-kit/
    │   ├── app-facts.json
    │   ├── OPEN_ITEMS.md             only when facts remain unresolved
    │   └── QA_REPORT.md
    ├── app-store-listing/
    │   ├── description-en.txt        shared full description for both stores
    │   └── keywords-en.txt           App Store only
    ├── app-store-previews/
    │   ├── preview-spec.json
    │   ├── source/                   real iOS runtime captures
    │   ├── final/                    RGB submission images
    │   └── qa/                       contact sheets
    └── google-play-listing/
        ├── short-description-en.txt
        ├── preview-spec.json
        ├── source/                   real Android runtime captures
        ├── final/
        │   ├── en-US/phone/
        │   ├── zh-CN/phone/
        │   ├── feature-graphic-en.png
        │   └── feature-graphic-zh.png
        └── qa/
```

## App Store preview specification

`render_previews.py` accepts JSON so rendering remains dependency-free apart from
Pillow. Paths are relative to the JSON file.

```json
{
  "schema_version": 2,
  "store": "app_store",
  "app_name": "Example App",
  "font_path": "/absolute/path/to/a/font.ttf",
  "qa_dir": "qa",
  "defaults": {
    "background_top": "#0B6B63",
    "background_bottom": "#17312E",
    "text_color": "#FFFFFF",
    "muted_text_color": "#DCE9E6"
  },
  "items": [
    {
      "kind": "screenshot",
      "source": "source/01-home-ios.png",
      "output": "final/iphone/01-home.png",
      "size": [1206, 2622],
      "headline": "Plan With Clarity",
      "subheadline": "See today's work and what comes next.",
      "icon": "../../assets/branding/app-icon.png"
    },
    {
      "kind": "screenshot",
      "source": "source/ipad-01-home-ios.png",
      "output": "final/ipad/01-home.png",
      "size": [2752, 2064],
      "headline": "Everything In View",
      "subheadline": "A spacious workspace for the whole plan."
    }
  ]
}
```

## Google Play preview specification

Use a real Android source capture for every `screenshot` item. A `feature_graphic`
item intentionally has no `source` or `icon`; the renderer creates a brand field,
not simulated UI.

```json
{
  "schema_version": 2,
  "store": "google_play",
  "app_name": "Example App",
  "font_path": "/absolute/path/to/a/font-with-Chinese-glyphs.ttf",
  "qa_dir": "qa",
  "defaults": {
    "background_top": "#0B6B63",
    "background_bottom": "#17312E",
    "text_color": "#FFFFFF",
    "muted_text_color": "#DCE9E6"
  },
  "items": [
    {
      "kind": "screenshot",
      "locale": "en-US",
      "source": "source/01-home-android.png",
      "output": "final/en-US/phone/01-home.png",
      "size": [1080, 1920],
      "headline": "Plan With Clarity"
    },
    {
      "kind": "screenshot",
      "locale": "zh-CN",
      "source": "source/01-home-android.png",
      "output": "final/zh-CN/phone/01-home.png",
      "size": [1080, 1920],
      "headline": "清晰规划每一天"
    },
    {
      "kind": "feature_graphic",
      "locale": "en-US",
      "output": "final/feature-graphic-en.png",
      "size": [1024, 500],
      "headline": "Plan With Clarity"
    },
    {
      "kind": "feature_graphic",
      "locale": "zh-CN",
      "output": "final/feature-graphic-zh.png",
      "size": [1024, 500],
      "headline": "清晰规划每一天"
    }
  ]
}
```

Supported overrides are `background_top`, `background_bottom`, `text_color`,
`muted_text_color`, `font_path`, `app_name`, `headline`, `subheadline`, `source`,
`output`, `size`, `kind`, `store`, and `locale`. Schema version 1 remains accepted
as an App Store screenshot specification for existing apps.

## Bilingual HTML contract

- Both `index.html` and `privacy.html` contain visible content blocks marked
  `data-lang="en"` and `data-lang="zh"`.
- The `<body>` provides localized `data-title-*` and `data-description-*` values.
- Language controls use `data-language-option="en"` and `"zh"`.
- `site.js` is loaded with `defer`, updates the title and description, persists the
  selection, and carries `?lang=` across local product/privacy links.
- English and Chinese privacy sections express the same supported facts. A complete
  translation is required; a language picker alone is not bilingual delivery.

## Definition of done

- All material facts are confirmed or listed as open.
- Shared description, Apple keywords, and Google Play short description pass limits.
- Website and privacy pages contain no template markers, include complete English
  and Chinese content, switch language, and expose real contact information.
- Every store screenshot uses a real platform-appropriate UI capture, has an accepted
  dimension and no alpha, and has passed visual inspection.
- Every Google Play feature graphic is 1024 x 500, RGB, and contains no screenshot or
  device mockup.
- `QA_REPORT.md` contains no errors.
- The final report distinguishes static validation from runtime capture, public
  hosting, store upload, processing, testing distribution, submission, review, and
  device proof.
