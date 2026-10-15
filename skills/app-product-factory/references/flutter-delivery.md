# Flutter delivery and validation

Read this before writing Flutter code or claiming build/runtime validation.

## Baseline

- Prefer the repository's pinned Flutter or FVM version and existing dependency strategy.
- Check `pubspec.yaml`, `pubspec.lock`, Dart SDK constraints, flavors, platform targets, and generated files before edits.
- If the project was moved or copied, check generated Flutter/Xcode/CocoaPods paths before diagnosing missing headers or plugins as source defects. Regenerate only the affected local build artifacts with the project's pinned toolchain; do not upgrade dependencies as a first response.
- Keep business logic in testable Dart layers. Isolate platform channels and third-party SDKs behind narrow interfaces.
- Follow the project's existing state-management, navigation, persistence, localization, and design-system patterns unless the approved PRD requires a change.
- Do not add a backend, account system, analytics, advertising, subscription, or online AI merely to create apparent product depth.

## Generated-product UI defaults

Unless the approved PRD says otherwise, apply these defaults to generated products:

- Create an original product-specific App Icon and retain its rights-cleared source asset or reproducible generation input in the repository. Replace Flutter's default launcher icon on every generated platform. Populate the platform's current icon mechanism, including Android adaptive/legacy variants where applicable, and design within mask/safe-region constraints. Verify the installed launcher result at representative sizes; source files and configuration alone do not prove it renders correctly.
- Configure the launch experience in the native iOS and Android projects so something appropriate appears before Flutter's first frame. Keep it visually continuous with the first app screen for the current appearance, with no artificial wait, fake progress, advertisements, changing content, or localized text. A Flutter widget shown after engine startup is not a substitute for native launch configuration. Use the platform mechanism supported by the project's pinned toolchain; do not add a splash dependency or Android theme parent that the project does not actually provide.
- Show onboarding after native launch on a clean install. Use only the number of pages needed to explain the real core value, important privacy/offline boundaries, and the first useful action. Localize it, support the same system-following appearance behavior as the app, allow skip, persist explicit skip or completion durably, route later launches directly to the product, and provide a replay entry under Settings or Help without clearing completion. Defer nonessential setup and permission prompts until contextual use. When adding onboarding to a previously released app, define a migration that does not unexpectedly force existing users through it unless the approved PRD explicitly requires that behavior.
- For a bilingual Chinese/English product, include `zh-Hans` and `en`. Leave the app locale override unset while the user preference is “follow system.” Resolve any Chinese (`zh`) system locale to the product's supported Chinese localization unless the product intentionally provides separate script variants; otherwise resolve an exact or language-compatible supported locale, and use English when none match. Make the English fallback explicit rather than relying on incidental `supportedLocales` ordering. Do not save the automatically resolved locale. Save only an explicit user choice; selecting “follow system” removes that override so later OS language changes take effect.
- Start with `ThemeMode.system`. Do not persist the brightness currently observed from the OS as if it were a user choice. Persist only an explicit light or dark override; selecting “follow system” removes the override so later OS appearance changes take effect.
- Present alerts, confirmations, destructive choices, and action sheets with the iOS/Cupertino visual hierarchy by default, including clear cancel/destructive semantics. In Flutter, prefer the appropriate Cupertino dialog or action-sheet route rather than a Material `AlertDialog` unless the product design explicitly overrides this default. Preserve accessibility labels, focus behavior, localization, dismissal rules, and the existing lifecycle regression checks.

For a scrollable page, let the scroll viewport use the available screen instead of wrapping the whole body in a fixed bottom safe-area spacer. Put the protective inset at the end of the scroll content or sliver so ordinary content can use the viewport, while the final content or action can be scrolled fully above the home indicator or system gesture region. Derive the inset from current `MediaQuery` data; for a page without another bottom obstruction, use the equivalent of `max(designBottomGap, MediaQuery.viewPaddingOf(context).bottom)` rather than blindly adding both values. Account separately for a real bottom navigation bar, fixed CTA, or keyboard, and apply each occupied height exactly once. Do not hard-code a device-specific inset or double-count a `SafeArea`, `Scaffold`, navigation bar, and content padding.

## Vertical-slice order

1. domain model and repository boundary;
2. original App Icon source plus native launch configuration;
3. first-run onboarding state, skip/complete persistence, replay, and existing-user migration when applicable;
4. one end-to-end happy path;
5. persistence and recovery;
6. empty, loading, error, offline, and permission-denied states;
7. accessibility, localization, dark mode, and responsive layout;
8. export, sharing, notifications, widgets, or other native value only when required by the product loop.

## Validation ladder

Choose commands supported by the project and report exact versions, target, and result:

1. formatting and generated-code consistency;
2. `flutter analyze`;
3. focused Dart/unit/widget tests;
4. full relevant test suite;
5. platform build using the correct flavor and entry point;
6. simulator/emulator launch and key-path interaction;
7. physical-device checks for permissions, camera, notifications, sharing, lifecycle, offline, performance, and accessibility;
8. signed Release/Archive and final bundle inspection when release-candidate work is requested.

For simulator evidence, use an available destination that is not being shut down or rebuilt by another task. Record the device ID, OS, build mode, and launch result. If Xcode reports `SIGTERM` or a framework assertion, inspect the first exception and process/device logs before calling it an app crash; a shared simulator shutdown or stale generated path is a different failure class. Never disturb another active test session merely to reuse its device.

Automated widget tests should cover the actual interaction sequence for new routes, dialogs, sheets, and text inputs: open, edit if relevant, cancel or dismiss (including the barrier/back action), wait for exit animation, then reopen. Own controllers, focus nodes, and animation resources for at least as long as the widgets/routes that use them. Assert no uncaught framework exception and no unintended data mutation. Add one regression case for each reproduced failure, not a catalog of speculative cases.

Add focused tests for system-following preferences and scroll-end reachability when those surfaces exist. Verify that Chinese system locales resolve to the supported Chinese localization, another compatible supported locale resolves correctly, and an unsupported device locale resolves to English; no locale or theme override is stored before an explicit choice; a saved override survives relaunch; returning to “follow system” clears it. For scrollable screens, verify the final interactive element can be brought above the current bottom system inset without a permanent blank band consuming the initial viewport. Widget tests do not replace rendered checks on gesture-navigation and non-gesture devices.

Add focused first-run tests for a clean install, skip, completion, relaunch, replay, back navigation, state-write failure, supported locales, both appearances, large text, and the smallest supported screen. When an existing product gains onboarding, cover the chosen migration for existing data. Inspect cold launch and the installed App Icon on each generated platform; a widget test cannot verify native pre-Flutter presentation or launcher masking.

Run the visual acceptance cases in [ui-acceptance.md](ui-acceptance.md) on rendered screens. Recheck affected screens after fixes; a screenshot taken before the last UI change is stale evidence.

Do not run dependency upgrades, CocoaPods updates, production signing changes, or broad generated-file rewrites unless required and within scope. An explicitly requested Android debug build may create or use a local debug keystore; record that side effect and never treat it as release-signing evidence. For iOS CocoaPods projects, use `Runner.xcworkspace`. Use temporary DerivedData for diagnosis when appropriate.

## Evidence wording

- Analyze/tests passing proves only the checked code paths.
- A simulator screenshot proves only the shown state on that simulator configuration.
- A no-sign or Debug build does not prove production signing or Archive readiness.
- Archive success does not prove upload, App Store Connect processing, TestFlight availability, device installation, live backend behavior, or App Review acceptance.
