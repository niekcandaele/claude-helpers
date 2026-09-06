# Skill evaluations with actionable reports

Status: proposed implementation specification. Updated: 6 September 2026.

## Problem Statement

The maintainer needs evidence that changing a skill improves its behavior across realistic requests. Today, packaging validation confirms that skills install correctly. It does not establish whether a harness selects the right skill, follows its procedure, or produces useful results.

Manual experiments provide scattered examples without a consistent baseline or a view across the repository. The maintainer cannot readily identify which skills need attention, which scenarios fail, or whether a recent change caused a regression.

The repository contains 40 skills and nine experimental cases across two skills. Those cases came from ad hoc skill-creator experiments. Their formats and assertions are not compatibility requirements.

Evaluations must work through the maintainer's Claude Code and Codex subscriptions. Requiring separately billed API calls for either execution or grading would discourage routine use. Subscription allowance and elapsed time remain limited resources.

## Solution

Introduce a small evaluation workflow built on Promptfoo. Run realistic scenarios through locally authenticated Claude Code and Codex, grade observable behavior, and retain enough evidence to explain each result.

Make reporting part of the first usable release. Provide a repository overview, scenario-level results, comparisons against a baseline, and exportable reports. The maintainer should be able to move from a failing skill to the failed expectation and supporting evidence without reading raw logs first.

Begin with six to ten scenarios across approximately three skills. Prefer deterministic checks, add optional model judgment for subjective criteria, and expand coverage from observed failures. Reuse useful ideas from the experimental cases while replacing their storage and grading conventions.

## User Stories

1. As a maintainer, I want to list available evaluation scenarios, so that I know what can be measured before spending subscription allowance.
2. As a maintainer, I want to evaluate one skill, so that I can get feedback while editing it.
3. As a maintainer, I want to rerun one failing scenario, so that iteration remains quick and affordable.
4. As a maintainer, I want to evaluate all configured skills explicitly, so that I can assess broader changes.
5. As a maintainer, I want to select Claude Code, Codex, or both, so that I can evaluate the harnesses I actually use.
6. As a maintainer, I want execution to use my existing subscriptions, so that evaluations do not require an API budget.
7. As a maintainer, I want grading to work without API keys, so that judgment does not introduce hidden inference charges.
8. As a maintainer, I want to see planned trials and grading calls before execution, so that I can choose an affordable scope.
9. As a maintainer, I want bounded execution and clear quota errors, so that an evaluation cannot consume allowance indefinitely.
10. As a skill author, I want realistic prompts and fixtures, so that results reflect actual user tasks.
11. As a skill author, I want positive and negative selection scenarios, so that broader descriptions do not cause over-triggering.
12. As a skill author, I want explicit-invocation behavior scenarios, so that I can evaluate a skill independently of discovery.
13. As a skill author, I want fresh trial workspaces, so that earlier outputs cannot make later trials pass.
14. As a skill author, I want declared skill dependencies available, so that a suite can execute correctly.
15. As a skill author, I want a no-skill or previous-version baseline, so that I can measure the contribution of a change.
16. As a skill author, I want identical scenario inputs across harnesses, so that differences remain interpretable.
17. As a skill author, I want deterministic checks for objective requirements, so that routine grading is inexpensive and repeatable.
18. As a skill author, I want evidence-based rubric grading, so that subjective judgments explain what needs improvement.
19. As a maintainer, I want repeated trials when needed, so that I can distinguish consistent behavior from a lucky result.
20. As a maintainer, I want every skill represented in the overview, so that missing coverage remains visible.
21. As a maintainer, I want results separated by harness and scenario, so that one good configuration does not hide another's failures.
22. As a maintainer, I want failures and regressions surfaced first, so that I can decide where to direct work.
23. As a maintainer, I want to filter results by skill, harness, scenario, and outcome, so that I can investigate a specific concern.
24. As a maintainer, I want to inspect the prompt, expected behavior, output, and failed checks together, so that I can judge whether a failure is fair.
25. As a maintainer, I want links to transcripts and generated artifacts, so that I can verify claims made by the grader.
26. As a maintainer, I want readable HTML reports and machine-readable exports, so that results remain useful outside the live viewer.
27. As a maintainer, I want retained evaluation history, so that I can compare revisions without rerunning old work.
28. As a maintainer, I want stale and partial results clearly labeled, so that historical success is not mistaken for current coverage.
29. As a maintainer, I want infrastructure errors distinguished from skill failures, so that I fix the correct problem.
30. As a maintainer, I want duration and token measurements alongside quality, so that improvements have visible resource tradeoffs.
31. As a skill author, I want to add a case through configuration and fixtures, so that expanding coverage rarely requires runner changes.
32. As a maintainer, I want useful experimental scenarios migrated and weak ones retired, so that legacy formats do not constrain the new workflow.
33. As a contributor, I want ordinary validation to work without model credentials, so that pull requests remain straightforward to check.
34. As an implementing assistant, I want reproducible failing cases and exported evidence, so that the maintainer can give precise follow-up instructions.

## Implementation Decisions

### Framework and repository integration

1. Use Promptfoo for evaluation scheduling, provider integration, assertions, detailed comparison views, and result export. Use its existing features before adding repository-specific code. Its documented skill evaluation workflow already covers Claude Code and Codex. [Skill evaluation guide](https://www.promptfoo.dev/docs/guides/test-agent-skills/)
2. Keep repository-owned tooling narrow: case discovery, fixture preparation, harness configuration, artifact collection, and any missing overview aggregation. Do not introduce a second general evaluation framework or a separate web application.
3. Use Promptfoo-native case configuration as the source of truth. Add stable metadata for skill, scenario, evaluation kind, and coverage category. Avoid maintaining duplicate cases in the experimental format.
4. Extend the existing development command surface with discovery, validation, execution, report viewing, and export actions. Ordinary repository validation remains deterministic and requires no model login.
5. Pin framework and adapter dependencies. Keep model choice configurable by harness and cost tier. Record the requested model and settings, plus the resolved model identity when the harness reports it; mark unavailable identity as unknown. The current Codex SDK does not expose the backend-resolved model through Promptfoo. Update repository guidance to explain the distinction between packaging validation and behavioral evaluation. [Model identity limitations](https://www.promptfoo.dev/docs/providers/openai-codex-sdk/)

### Evaluation boundary and vocabulary

6. Use one primary test boundary: select cases and a harness configuration, execute them in prepared workspaces, and inspect the resulting report and artifacts.
7. Preserve the repository glossary. A harness loads and executes skills; a suite is a set of dependent skills. Use evaluation, scenario, trial, assertion, and baseline for evaluation concepts. Do not repurpose the glossary's unqualified run, which belongs to player-coach.
8. Separate two evaluation kinds. Selection scenarios send an ordinary user request and observe whether the harness consults the target skill. Behavior scenarios explicitly invoke the skill and grade the task outcome. Behavior scenarios do not establish automatic-selection quality.
9. Selection scenarios include plausible positive requests and nearby negative requests. Record observable skill-loading evidence and its limitations. Codex skill detection is currently heuristic; unavailable evidence must not become a confident positive or negative result. [Codex provider limitations](https://www.promptfoo.dev/docs/providers/openai-codex-sdk/)
10. Express behavior requirements in harness-neutral terms. A question, file edit, or investigation is the behavior being measured. A particular vendor tool name is adapter evidence, not a portable acceptance criterion.

### Subscription execution and limits

11. The default configuration uses the maintainer's existing local subscription authentication for execution and any optional model judge. Perform preflight checks before starting trials. Missing authentication or conflicting paid-provider configuration stops the affected evaluation with a clear explanation; it does not select paid inference automatically.
12. Prefer Promptfoo's native Codex integration. Its Claude integration can reuse local authentication; an adapter invoking the installed, unmodified Claude Code CLI is an acceptable alternative. Validate the chosen path through a small live pilot before expanding coverage. [Codex authentication](https://www.promptfoo.dev/docs/providers/openai-codex-sdk/), [Claude authentication](https://www.promptfoo.dev/docs/providers/claude-agent-sdk/)
13. Subscription usage is not unlimited. Anthropic currently includes noninteractive Claude usage within subscription limits, following its paused billing change. Keep paid overage disabled for the acceptance pilot and document the selected authentication method without recording credentials. [Anthropic usage update](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)
14. Default to one trial per case and serial execution. Offer bounded repetition and concurrency explicitly. Show the selected cases, harnesses, baseline arms, repetitions, and planned judge passes before execution; this preview does not require another confirmation prompt.
15. Bound trial duration and overall evaluation duration. Stop scheduling further work on quota exhaustion or cancellation, terminate active child processes, and retain completed evidence. Record retries separately; a failed behavioral attempt must not disappear behind an automatic retry.

### Cases, fixtures, and isolation

16. Each case has a stable identifier, target skill, evaluation kind, realistic task prompt, expected behavior, fixture inputs, harness applicability, and at least one observable assertion. Keep the underlying task separate from any skill invocation added for a behavior arm. Selection cases also declare whether the skill should trigger. Validate identifiers, fixture availability, and assertions before inference.
17. Resolve required skill dependencies recursively. Optional dependencies belong to explicit scenario requirements. Missing capabilities produce an unsupported or setup-error result with a reason; they do not produce a passing row.
18. Create a fresh workspace and conversation for each case, harness, baseline arm, and repetition. Stage only declared fixtures, the intended skills, and required supporting resources. Keep grading expectations and reference answers outside the executor's accessible workspace.
19. Prevent personal skills, repository instructions, saved sessions, and prior artifacts from contaminating the comparison. Verify the effective skill catalog and instructions during the pilot while retaining authentication through supported harness mechanisms. Record unavoidable harness-provided instructions and skills.
20. Keep trial permissions appropriate to fixture work. Cases that would normally publish, push, or modify external services use local fixtures or test doubles in the first release. Preserve the real skill-loading and tool-use behavior while keeping effects within the prepared environment.
21. Prefer fixed source material for the initial cases. Live web research belongs to an explicitly labeled scenario and must record its sources and execution date. Do not interpret a changing website or unavailable network as a deterministic skill regression.
22. The first release supports single-turn cases and cases whose expected outcome is a clarification. Completion after a user reply requires a real scripted continuation; do not count a correctly phrased pause as completed work. Full multi-turn scenario support is deferred.

### Grading and comparison

23. Use deterministic assertions for facts that code can establish: output existence, data values, structured-output validity, file changes, and tool-use evidence. Validate browser behavior by exercising the artifact when required. Merely finding a CSS class or permissively parsing HTML does not establish that a widget works.
24. Make model grading optional and explicitly choose a subscription-backed judge. Text rubrics use the recorded response; artifact judgments receive the relevant artifact or rendered evidence. A final message claiming success is insufficient evidence of an artifact's quality. [Rubric grading](https://www.promptfoo.dev/docs/configuration/expected-outputs/model-graded/llm-rubric/)
25. Require each grader to produce a result and supporting evidence. Validate structured judge output; malformed output or missing evidence is a grading error. Use known acceptable and unacceptable examples to calibrate rubrics. Human inspection remains part of judging subjective work.
26. Required assertions determine pass or fail. Optional scores describe qualities such as readability or visual preference without compensating for failed required assertions. Cases awaiting required grading remain ungraded. A case with no applicable checks cannot pass.
27. Behavior comparisons support no-skill and selected previous-version baselines; selection comparisons use previous-version snapshots. Share the underlying task, fixtures, harness settings, and outcome assertions across arms. Apply explicit invocation and skill-loading checks only to arms containing the target skill. A no-skill baseline receives the task without an instruction to invoke the absent skill. Record each arm's complete skill/dependency snapshot, making suite changes visible as part of the comparison.
28. Separate skill-revision comparisons from harness comparisons. A regression claim requires matching scenario, fixture, grader, explicitly selected model, and harness fingerprints; otherwise label the comparison as informational. Compare resolved model identities when available and disclose missing backend identity as a limitation. A shared default or mutable alias alone does not establish model equivalence. Added or removed cases appear separately from shared-case deltas.
29. Fresh measurements disable response caching. Reopening or exporting saved results never invokes a model. Any future regrading operation creates a distinct grading revision and preserves the original evidence. Promptfoo can reuse cached responses across repeated invocations unless caching is disabled. [Caching behavior](https://www.promptfoo.dev/docs/configuration/caching/)
30. Report raw trial counts before percentages. With repetition, show passes and failures for each scenario and flag observed inconsistency. One successful trial establishes an observation, not reliability. Preserve a small set of unseen scenarios when repeated prompt tuning makes overfitting a concern.

### Reporting as a release requirement

31. Use Promptfoo's local web viewer for detailed results. It provides outcome and metadata filters, result details, comparisons, and history selection. Its HTML and JSON exports provide a portable reporting basis. No hosted account or external reporting service is required. [Web viewer](https://www.promptfoo.dev/docs/usage/web-ui/), [Exports](https://www.promptfoo.dev/docs/configuration/outputs/)
32. Provide a repository overview listing every discovered skill. Show scenario coverage, supported harnesses, latest measurement time, measured revision, pass/fail counts, execution or grading errors, and freshness. A skill with no cases appears as untested.
33. Implement missing overview information as a small generated HTML index over saved results and the skill catalog. Link to Promptfoo details and exported evidence. Do not build a second results browser, API service, or database. The overview contract is required even if native viewer configuration cannot express it.
34. Let the maintainer filter by skill, harness, scenario, evaluation kind, and outcome. Surface regressions and failed scenarios, then errors, incomplete coverage, and stale measurements. Display a reason for each category rather than reducing everything to a single quality score.
35. Use the following reporting contract:

| View | Required information |
| --- | --- |
| Repository overview | Every skill, coverage, per-harness status, freshness, latest evaluation, and links to scenarios |
| Skill detail | Scenario purpose, harness, baseline/candidate outcomes, raw trial counts, and failed expectations |
| Trial detail | Exact request, expected behavior, assertion results, evidence, final response, transcript, artifacts, duration, and available token usage |
| Comparison | Matched scenarios, changes in outcomes, baseline identity, newly added or removed cases, and configuration differences |
| Saved report | Readable HTML summary, machine-readable results, and referenced evidence that remains accessible after execution ends |

36. Keep execution status and grading outcome separate. Distinguish assertion failure, execution error, grading error, cancellation, not executed, unsupported, and ungraded. Show explanatory text alongside status colors.
37. Calculate pass rate from completed, fully graded trials and show its denominator. Display errors, skipped trials, and ungraded trials beside that rate. A skill is fully passing only when all required cases for the selected configuration have completed and passed.
38. Track latest trial sets per scenario, harness configuration, and comparison-arm snapshot, retaining every repetition in each set. A filtered rerun updates only its selected sets; it cannot erase failures in other scenarios or replace a baseline with candidate results. Pair comparison arms using explicit evaluation identities and the matching rules above, never simply the latest available rows. Show that the overview combines measurements and retain each set's timestamps and revision.
39. Mark evidence stale when the relevant skill/dependency snapshot, case, fixture, grading contract, or selected harness configuration has changed. Never relabel old results as current simply because a newer report was generated.
40. Save immutable raw execution and grading results with evaluation identity, timestamps, source revision, dirty-worktree fingerprints, requested and available resolved model identities, framework/harness versions, comparison-arm identity, repetition index, and selected scope. Treat viewer annotations as review notes; they must not silently overwrite automated evidence used for comparisons.
41. Generate reports after successful, failed, or interrupted evaluations whenever initialization completed. Store transcripts and artifacts with the report, outside versioned source by default. Export a portable report package without inference or automatic upload. Missing or removed artifacts must have visible explanations.
42. Display duration and available token usage as resource measurements. Clearly label any dollar figure as an API-rate estimate when subscription authentication was used. Do not present that estimate as an invoice or remaining subscription quota.
43. Render model text as untrusted content. Escape text in generated reports and isolate previews of executable HTML artifacts. Viewing an overview must not execute arbitrary generated scripts in the overview's origin.

### Initial coverage and experimental-case migration

44. Start with six to ten cases chosen for useful signal and modest execution cost. Candidate skills are catchup, research, and rich-page; this selection can change if a better low-cost fixture emerges.
45. Cover a known Git-state summary, selection boundaries, a workflow constraint, and an artifact-producing task. Include at least one negative selection case and one failure example that validates the grader.
46. Audit the nine experimental cases for intent. Migrate, rewrite, or retire each, recording a short disposition in implementation notes. Useful scenarios survive; their identifiers, file formats, assertion objects, and count do not need to survive.
47. Replace missing inputs with complete fixtures. Rewrite vendor-specific and implementation-shaped checks around observable outcomes. Retire unsupported multi-turn cases or preserve their first-turn behavior as explicitly different scenarios.
48. Remove superseded experimental files after the retained scenarios are represented in the new framework. Do not add a permanent compatibility reader or keep two authoritative formats.

## Testing Decisions

Tests should verify the public evaluation workflow and the evidence it produces. A useful test catches a plausible incorrect implementation or misleading report. Avoid tests that mirror helper functions or assert incidental internal structures.

The primary seam is the development command boundary: fixture and configuration inputs become execution outcomes, saved artifacts, and reports. Test doubles replace model execution behind the provider boundary for routine checks. A small live pilot verifies the real harness integration separately.

1. Exercise case discovery and preflight through the public command surface. Invalid cases, missing fixtures, unsupported capabilities, and missing authentication must fail before unintended inference.
2. Feed deterministic provider doubles through execution, grading, and reporting. Include passing output, a real assertion failure, malformed judge output, timeout, quota exhaustion, cancellation, and incomplete grading.
3. Verify no-key operation for discovery, deterministic checks, report viewing, and export. Test that conflicting paid-provider configuration is rejected instead of silently changing the authentication route.
4. Verify isolation with a fixture that leaves output behind, then repeat the case in a new workspace. Confirm baselines cannot consult the target skill or grader answers accidentally.
5. Prove each deterministic grader accepts a known-good artifact and rejects a plausible bad artifact. Exercise rendered behavior for browser-based checks. Do not require new tests solely for static prose changes.
6. Test report aggregation with different numbers of cases per skill, partial reruns, changed skill fingerprints, missing artifacts, and an entirely untested skill. Include a candidate-only rerun that preserves the baseline and other scenario results. Include a fully graded pass alongside a quota error; the overview must not become fully green.
7. Verify comparisons reject mismatched criteria as regression evidence and disclose unknown resolved model identities. Confirm repeated trials are fresh executions and preserve both successful and unsuccessful attempts within their comparison arms.
8. Open the overview and detailed viewer in a browser. Filter to one skill and harness, inspect a failure, compare revisions, and follow artifact links. Repeat report inspection after stopping the evaluation process.
9. Open an exported report package without a running Promptfoo viewer or model connection. Confirm the summary, result details, and packaged evidence remain usable.
10. Run a small authenticated pilot through both Claude Code and Codex with paid API credentials absent and paid overage disabled. Verify a skill is loaded, an artifact is graded, and an optional subscription-backed judge produces a valid result.
11. Measure both candidate and baseline for the initial cases, inspect their evidence manually, and retain the resulting report. A deliberately bad fixture or assertion must produce a visible failure.
12. Keep ordinary CI deterministic. Use the existing packaging validator as prior art for command-level failure reporting; the repository currently has no behavioral runner tests to extend. Add model-free checks for the new tooling without requiring subscription credentials in CI.
13. Finish implementation with `just validate` and `/verify`. If delivery is split into phases, run `/verify --mode=report-only --scope=branch` after each intermediate phase and `/verify` last.

Acceptance requires the initial cases to be runnable on both selected harnesses, with genuine differences in behavior permitted. Completion means the workflow measures and explains results correctly; it does not require every evaluated skill to pass every scenario.

The maintainer must be able to identify a failing skill, isolate its scenario, inspect the evidence, and compare the relevant baseline from the delivered reports. Untested, stale, and incomplete coverage must remain visible throughout that workflow.

## Out of Scope

- Evaluating every skill or achieving a universal passing score in the first release.
- A custom dashboard application, hosted reporting service, account system, or production observability stack.
- Mandatory API-key execution, paid grading services, or subscription credentials in ordinary pull-request CI.
- Automated skill rewriting, description optimization loops, model training, or automatic commits and publishing.
- Full multi-turn simulated users, unrestricted external-service workflows, and live-web benchmarking by default.
- A compatibility layer for the experimental eval format or reproducing every historical assertion.
- Statistical significance claims from the small initial dataset, a model leaderboard, or comparisons that conceal configuration changes.

## Further Notes

This document specifies local development tooling for a skills source repository. It does not change how consumers install skills or introduce packaging and versioning infrastructure.

The reported quality belongs to a skill, scenario, harness, model, and configuration together. A strong Codex result does not establish Claude Code behavior. An aggregate number should always lead back to concrete cases.

The Agent Skills guidance supports starting with a few realistic cases, using baselines, and refining graders after inspecting outputs. Anthropic likewise recommends distinct execution and grading evidence and checking that failures are fair. These inform the methodology; the reporting and delivery requirements above are repository decisions. [Agent Skills guidance](https://agentskills.io/skill-creation/evaluating-skills), [Anthropic evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

Framework and authentication capabilities were checked against current documentation on 6 September 2026. Subscription execution and the exact export package remain live-pilot acceptance checks. No behavioral benchmark results have been collected for this specification.

This spec is delivered as a local file at the maintainer's request. Tracker publication and implementation are separate follow-up actions.
