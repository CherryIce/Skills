# CherryIce Codex Skills

Reusable Codex skills published by CherryIce.

## Available skills

| Skill | Description | Invocation |
| --- | --- | --- |
| `app-product-factory` | Evidence-based product research, differentiation, Flutter MVP delivery, functional review, and App Store preflight | `$app-product-factory` |
| `app-store-release-kit` | App Store and Google Play listing assets, real-app screenshots, and bilingual website and privacy drafts for one app | `$app-store-release-kit` |

## Install with Codex

Ask the built-in skill installer to install the skill from this repository:

```text
$skill-installer

Install app-product-factory from:
https://github.com/CherryIce/Skills/tree/main/skills/app-product-factory

Install app-store-release-kit from:
https://github.com/CherryIce/Skills/tree/main/skills/app-store-release-kit
```

The installed skill becomes available on the next turn. `app-product-factory` is
explicit-only, so invoke it with `$app-product-factory`. Invoke the release kit with
`$app-store-release-kit` when you want release materials for a named app.

## Install from the command line

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --path skills/app-product-factory

python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --path skills/app-store-release-kit
```

To install the immutable `v1.5.0` release instead of the latest `main` branch,
add `--ref v1.5.0` to either command. For example:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --ref v1.5.0 \
  --path skills/app-product-factory
```

The installer refuses to overwrite an existing skill directory. Back up and remove or rename an older installation before reinstalling.

## Example

```text
$app-product-factory

目标：本地离线数据质量工具
范围：mvp
要求：Flutter、中英文、离线优先
禁止动作：不上传 App Store，不修改生产证书
```

```text
$app-store-release-kit

为 apps/example 生成并检查 App Store 和 Google Play 发布素材。
```

## Requirements

- Codex with the built-in `skill-installer` skill, or Python 3 for direct installation.
- Flutter and Dart when the selected workflow includes implementation or quality gates.
- Pillow for release-kit screenshot rendering and image validation.
- macOS and Xcode for iOS build/archive evidence.
- Network access for current product research and official App Store policy verification.

## Safety boundary

Neither skill automatically authorizes purchases, account changes, production
certificate changes, deployment, store upload, or review submission. The release
kit generates and validates materials until a user explicitly asks for publication.

Generated templates and mechanical preflight results are evidence scaffolds, not legal advice or a guarantee of App Store approval.

## Learning loop

Each invoked run can leave a project-local `docs/factory/RETROSPECTIVE.json` recording observed outcomes, failures, and untested layers. If prior record paths are explicitly supplied through `learning_records`, the included summarizer identifies recurring patterns for human review. It does not scan other projects, modify the Skill, or publish updates automatically. Adopting a proposed improvement requires a separate Skill-maintenance decision and validation.

## Repository layout

```text
skills/
├── app-product-factory/
│   ├── SKILL.md
│   ├── agents/
│   ├── assets/
│   ├── references/
│   └── scripts/
└── app-store-release-kit/
    ├── SKILL.md
    ├── assets/
    ├── references/
    └── scripts/
```

## License

No license has been selected yet. Installation is technically available, but reuse and redistribution rights remain unspecified until the repository owner adds a license.
