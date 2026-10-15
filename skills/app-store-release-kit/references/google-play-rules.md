# Google Play listing rules

Last checked: 2026-10-09. Recheck the official pages before relying on this file for
a later release because Play Console requirements and recommendations change.

Official sources:

- Main store listing assets: https://support.google.com/googleplay/android-developer/answer/9866151?hl=en
- Core app quality and promotional assets: https://support.google.com/googleplay/android-developer/answer/9859152

## Deterministic limits

- Short description: required, at most 80 characters.
- Full description: required, at most 4,000 characters. This skill intentionally
  reuses `artifacts/app-store-listing/description-en.txt` for both stores.
- App icon: required, 512 x 512, 32-bit PNG with alpha, at most 1,024 KB. The app's
  existing production icon may be reused; this skill does not create a replacement.
- Feature graphic: required, exactly 1,024 x 500, JPEG or 24-bit PNG without alpha.
- Screenshots: at least two across supported device types and at most eight per device
  type. Use JPEG or 24-bit PNG without alpha. Each dimension must be between 320 and
  3,840 pixels, and the longest side must not exceed twice the shortest side.
- For apps, Google recommends at least four high-resolution screenshots: at least
  1,080 pixels, using 9:16 portrait or 16:9 landscape.

## Content rules encoded by this skill

- Screenshots must show the actual in-app experience. Capture the Android build for
  Play assets; do not pass an iOS screen off as Android UI.
- Keep overlay taglines to about 20% or less of each screenshot and localize overlay
  text for every delivered locale. Do not use rankings, awards, prices, discounts,
  calls to action, testimonials, or misleading claims.
- Keep the feature graphic focused near the center. It must be brand-led and must not
  contain a device, UI screenshot, fine detail, tiny text, ad-like calls to action,
  or a prominent duplicate of the launcher icon.

The validator checks file shape, count, dimensions, and alpha. It cannot prove that
a screenshot came from Android runtime, that copy is accurate, or that Play Console
will accept the content after policy review.
