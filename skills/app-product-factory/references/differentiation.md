# Differentiation and originality review

This is an internal product-quality gate, not a prediction or guarantee of store approval.

## Hard failures

Return `needs_revision` when any of these is true:

- differentiation is limited to name, icon, color, text, locale, region, or Bundle ID;
- the screen hierarchy and primary action sequence substantially reproduce one competitor;
- the proposal uses copied screenshots, artwork, branding, text, datasets, or other protected material without documented rights;
- it is another nearly identical app from the same template or codebase with no independently valuable product loop;
- added login, feed, ads, subscription, chat, or AI has no necessary role in the user's job;
- the primary intent is to evade an earlier rejection or obscure the relationship to another app.

## Scorecard

Score each dimension from 0 to 5 and explain the evidence:

1. target-user specificity;
2. unmet problem severity and frequency;
3. distinct core workflow;
4. distinct data model, decision support, or durable output;
5. meaningful platform-native advantage;
6. privacy, offline, accessibility, localization, or reliability advantage;
7. original information architecture and visual identity;
8. ability to prove the promised value with tests and runtime evidence.

Suggested internal interpretation:

- any hard failure: `needs_revision` regardless of score;
- average below 2.5: weak concept;
- average 2.5–3.4: plausible but needs a stronger core loop;
- average 3.5 or higher with no dimension below 2: implementation candidate.

The thresholds are a planning heuristic, not Apple policy.

## Strengthening a weak concept

Propose at most three coherent directions. Prefer:

- a narrower audience with a painful repeated job;
- a complete lifecycle rather than a one-shot utility;
- recovery, audit trail, comparison, collaboration, export, or offline continuity that directly serves the job;
- an original domain model or output users can keep and reuse;
- native capabilities such as camera, files, share sheets, widgets, shortcuts, notifications, or accessibility when they materially improve the workflow.

For every proposed addition, state the user problem, where it fits in the core loop, why existing products underserve it, required data/permissions, validation method, and implementation cost. Reject decorative differentiation.
