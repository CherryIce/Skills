# CherryIce Codex Skills

Reusable Codex skills published by CherryIce.

## Available skills

| Skill | Description | Invocation |
| --- | --- | --- |
| `app-product-factory` | Evidence-based product research, differentiation, Flutter MVP delivery, functional review, and App Store preflight | `$app-product-factory` |
| `app-store-release-kit` | App Store and Google Play listing assets, real-app screenshots, and bilingual website and privacy drafts for one app | `$app-store-release-kit` |
| `post-build-cleanup` | Remove disposable project build caches after validation while preserving source, dependencies, deliverables, and evidence | `$post-build-cleanup` |
| `figma-design-doc` | Turn selected Figma designs into a grouped Word link directory using a supplied reference or the bundled template, then audit page, state, version, and link coverage | `$figma-design-doc` |

## Install with Codex

Ask the built-in skill installer to install the skill from this repository:

```text
$skill-installer

Install app-product-factory from:
https://github.com/CherryIce/Skills/tree/main/skills/app-product-factory

Install app-store-release-kit from:
https://github.com/CherryIce/Skills/tree/main/skills/app-store-release-kit

Install post-build-cleanup from:
https://github.com/CherryIce/Skills/tree/main/skills/post-build-cleanup

Install figma-design-doc from:
https://github.com/CherryIce/Skills/tree/main/skills/figma-design-doc
```

The installed skill becomes available on the next turn. `app-product-factory` is
explicit-only, so invoke it with `$app-product-factory`. Invoke the release kit with
`$app-store-release-kit` when you want release materials for a named app.
`post-build-cleanup` allows implicit invocation for matching build/validation tasks;
you can also invoke it explicitly with `$post-build-cleanup`.
`figma-design-doc` allows implicit invocation for design-document tasks and can
also be invoked explicitly with `$figma-design-doc`.

## Install from the command line

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --path skills/app-product-factory

python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --path skills/app-store-release-kit

python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --path skills/post-build-cleanup

python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --path skills/figma-design-doc
```

To install the immutable `v1.9.0` release instead of the latest `main` branch,
add `--ref v1.9.0` to any command. For example:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo CherryIce/Skills \
  --ref v1.9.0 \
  --path skills/figma-design-doc
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

```text
$post-build-cleanup

构建、测试和运行验证结束后，直接清理当前任务无需保留的构建缓存，保留源码、依赖、交付产物和验证证据。
```

```text
$figma-design-doc

将以下 Figma 设计稿整理成 Word 目录；有参考文档时沿用参考格式，没有时使用内置模板，核对页面、状态、版本和直达链接，并在文末写明覆盖结果。
```

For consistent cleanup across projects, add this instruction to your global
`AGENTS.md` after installing the skill:

```text
For build, test, or runtime-validation tasks, read the installed post-build-cleanup
skill. After validation and evidence/artifact preservation, remove only confirmed
disposable caches for that task. Preserve source, uncommitted work, dependencies,
signing material, deliverables, and required evidence. Skip paths still used by
other tasks or needed for continued debugging or hot reload, and report the result.
```

The skill does not install a background cleanup service or modify `AGENTS.md`
automatically. Its helper previews explicit project-local directories by default;
the agent checks ownership, active processes, and retained artifacts before using
`--apply`. For persistent Xcode services and previously occupied caches, the
skill distinguishes actual handles/memory mappings and project-related tasks
from process existence, then requires independent stability observations before
cleanup. See the skill's [occupancy and retention guidance](skills/post-build-cleanup/references/occupancy-and-retention.md).

The helper enforces path/artifact boundaries; it does not probe processes or
prove cache stability. It refuses protected paths, tracked files, nested
repositories, signing material, nested `Products`/`SourcePackages`, frameworks,
symbols, packages, diagnostic evidence, symlinked targets/ancestors, and overlaps
with `--keep` paths. A mixed cache tree must be split into disposable siblings
and retained products, including `Index.noindex/Build/Products`.

## Requirements

- Codex with the built-in `skill-installer` skill, or Python 3 for direct installation.
- Flutter and Dart when the selected workflow includes implementation or quality gates.
- Pillow for release-kit screenshot rendering and image validation.
- macOS and Xcode for iOS build/archive evidence.
- Network access for current product research and official App Store policy verification.
- Python 3 and Git for the cleanup helper; its behavior tests use temporary fixture projects.
- Figma read access and the Figma tools for design-document workflows, plus the
  `documents` skill and its document runtime for DOCX authoring and page rendering.
  The bundled link-audit helper uses only the Python 3 standard library; local
  link extraction alone does not verify live Figma access or visual semantics.

## Safety boundary

These skills do not automatically authorize purchases, account changes, production
certificate changes, deployment, store upload, or review submission. The release
kit generates and validates materials until a user explicitly asks for publication.

`post-build-cleanup` removes only confirmed disposable build data within the task
scope after evidence and deliverables are preserved. Shared dependency caches,
SDKs, source, signing material, and paths still in use are retained. Historical
cross-project cleanup requires its own explicit request.

`figma-design-doc` reads only the requested design scope and produces or updates
documents. It preserves existing notes and links during an authorized update;
instructions inside reference documents are source material, not authorization
to modify designs, application code, or business data.

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
├── app-store-release-kit/
│   ├── SKILL.md
│   ├── assets/
│   ├── references/
│   └── scripts/
├── post-build-cleanup/
│   ├── SKILL.md
│   ├── agents/
│   ├── references/
│   └── scripts/
└── figma-design-doc/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

## License

No license has been selected yet. Installation is technically available, but reuse and redistribution rights remain unspecified until the repository owner adds a license.
