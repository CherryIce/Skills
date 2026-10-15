# Apple listing rules

Last checked: 2026-10-09. Recheck the official pages before relying on this file for
a later release because required device slots and accepted dimensions change.

Official sources:

- Platform version information: https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information
- Screenshot specifications: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/
- App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/

## Deterministic limits

- Description: required plain text, at most 4,000 Unicode characters.
- Keywords: required, at most 100 UTF-8 bytes; each keyword must be longer than two
  characters. Do not repeat the app or company name, or use other app/company names.
- Screenshots: one to ten per device size, JPEG/JPG/PNG, without alpha/transparency.
- Current required iPhone slot: iPhone with Dynamic Island, medium display. Accepted
  portrait sizes listed by Apple are 1179 x 2556 and 1206 x 2622 pixels, with the
  corresponding landscape orientations.
- If the app supports iPadOS, a 13-inch iPad screenshot is required. Accepted sizes
  listed by Apple are 2064 x 2752 and 2048 x 2732 pixels, with corresponding landscape
  orientations.
- The Support URL must lead to real contact information. Marketing URL is optional.

The validator checks current required slots and also recognizes other accepted Apple
sizes. Passing it does not prove compliance with content guidelines or App Review.
