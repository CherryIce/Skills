# CherryIce Codex Skills

Reusable Codex skills published by CherryIce.

## Available skills

| Skill | Description | Invocation |
| --- | --- | --- |
| `app-product-factory` | Evidence-based product research, differentiation, Flutter MVP delivery, functional review, and App Store preflight | `$app-product-factory` |

## Install with Codex

Ask the built-in skill installer to install the skill from this repository:

```text
$skill-installer

Install app-product-factory from:
https://github.com/CherryIce/Skills/tree/main/skills/app-product-factory
```

The skill becomes available on the next turn after installation. It is explicit-only, so invoke it with `$app-product-factory` whenever you want the workflow to run.

## Install from the command line

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --path skills/app-product-factory
```

To install the immutable `v1.0.0` release instead of the latest `main` branch:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --ref v1.0.0 \
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

## Requirements

- Codex with the built-in `skill-installer` skill, or Python 3 for direct installation.
- Flutter and Dart when the selected workflow includes implementation or quality gates.
- macOS and Xcode for iOS build/archive evidence.
- Network access for current product research and official App Store policy verification.

## Safety boundary

`app-product-factory` does not authorize purchases, account changes, production certificate changes, deployment, App Store Connect upload, or review submission. Those actions require separate, explicit user confirmation.

Generated templates and mechanical preflight results are evidence scaffolds, not legal advice or a guarantee of App Store approval.

## Repository layout

```text
skills/
└── app-product-factory/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

## License

No license has been selected yet. Installation is technically available, but reuse and redistribution rights remain unspecified until the repository owner adds a license.
