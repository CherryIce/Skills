# Flutter delivery and validation

Read this before writing Flutter code or claiming build/runtime validation.

## Baseline

- Prefer the repository's pinned Flutter or FVM version and existing dependency strategy.
- Check `pubspec.yaml`, `pubspec.lock`, Dart SDK constraints, flavors, platform targets, and generated files before edits.
- If the project was moved or copied, check generated Flutter/Xcode/CocoaPods paths before diagnosing missing headers or plugins as source defects. Regenerate only the affected local build artifacts with the project's pinned toolchain; do not upgrade dependencies as a first response.
- Keep business logic in testable Dart layers. Isolate platform channels and third-party SDKs behind narrow interfaces.
- Follow the project's existing state-management, navigation, persistence, localization, and design-system patterns unless the approved PRD requires a change.
- Do not add a backend, account system, analytics, advertising, subscription, or online AI merely to create apparent product depth.

## Vertical-slice order

1. domain model and repository boundary;
2. one end-to-end happy path;
3. persistence and recovery;
4. empty, loading, error, offline, and permission-denied states;
5. accessibility, localization, dark mode, and responsive layout;
6. export, sharing, notifications, widgets, or other native value only when required by the product loop.

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

Run the visual acceptance cases in [ui-acceptance.md](ui-acceptance.md) on rendered screens. Recheck affected screens after fixes; a screenshot taken before the last UI change is stale evidence.

Do not run dependency upgrades, CocoaPods updates, production signing changes, or broad generated-file rewrites unless required and within scope. An explicitly requested Android debug build may create or use a local debug keystore; record that side effect and never treat it as release-signing evidence. For iOS CocoaPods projects, use `Runner.xcworkspace`. Use temporary DerivedData for diagnosis when appropriate.

## Evidence wording

- Analyze/tests passing proves only the checked code paths.
- A simulator screenshot proves only the shown state on that simulator configuration.
- A no-sign or Debug build does not prove production signing or Archive readiness.
- Archive success does not prove upload, App Store Connect processing, TestFlight availability, device installation, live backend behavior, or App Review acceptance.
