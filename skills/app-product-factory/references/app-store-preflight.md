# App Store preflight

Apple requirements and platform submission details change. Before each App Store assessment, browse current official Apple Developer sources and cite the pages used. Do not rely solely on this reference or memory.

Start with the current App Review Guidelines and check all sections relevant to the product. Always inspect at least:

- 2.1 App Completeness;
- 2.3 Accurate Metadata;
- 3.1 payments when digital goods, features, or subscriptions are monetized;
- 4.1 Copycats;
- 4.2 Minimum Functionality, including template-generated apps;
- 4.3 Spam and repeated/indistinguishable apps;
- 4.8 login services when third-party primary login exists;
- 5.1 privacy, data minimization, permissions, account deletion, and data sharing;
- 5.2 intellectual-property and third-party service authorization.

Add category rules for children, health, finance, crypto, gambling, user-generated content, location, VPN, AI, or other regulated/sensitive functions.

## Store evidence matrix

For each applicable rule, record:

- requirement and official source;
- applicability and rationale;
- source-code/configuration evidence;
- test or runtime evidence;
- metadata/App Store Connect evidence;
- missing evidence and owner;
- severity and verdict.

## Submission checks

- final version has no placeholders, broken links, dormant or undocumented features;
- review account or approved demo mode exposes the full reviewed functionality;
- production backend and reviewer path are available;
- app name, icon, screenshots, description, privacy answers, age rating, review notes, and actual behavior agree;
- privacy policy and support URLs are public, accurate, durable, and accessible in-app where required;
- permission strings and privacy manifests match actual SDK and API behavior;
- account deletion, Sign in with Apple requirements, IAP visibility/restore, and UGC controls are complete when applicable;
- identifiers, entitlements, signing, minimum OS, symbols, and archive contents match the intended release;
- assets, fonts, content, data, and third-party services have documented usage rights;
- the app provides durable utility and meaningful differentiation beyond a website wrapper or reused template.

## Verdicts

- `blocked`: clear policy, rights, privacy, safety, crash, access, or release-input blocker.
- `high_risk`: material evidence or differentiation is missing; do not recommend submission.
- `candidate`: no known blocking issue and the required evidence layers are present.

`candidate` is not a probability or guarantee of approval. App Review is an external human decision. Upload and submission require explicit user confirmation.
