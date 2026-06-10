# Retro 006 — url-input

**Feature:** [feature-006-url-input](../requirements/feature-006-url-input.md) (issue #3)

## What we did

Pure `app/src/lib/validateUrl.ts` (`validateUrl` + `toErrorMessage`) spec-first: red run
captured (`Cannot find module './validateUrl'`), then 52/52 green (31 new tests). Then the
render-only `app/src/components/UrlInput.tsx` with idle/loading/error states driven entirely
by the pure module and the injected `onSubmit` promise. Lint and build clean. `App.tsx` and
`lib/api.ts` deliberately untouched — owned by parallel issues #2/#4; wiring happens at merge.

## What worked

- Splitting `toErrorMessage` out of the component kept the "components only render" rule
  honest: even the rejected-promise → message mapping is specced pure logic, so the component
  has zero testable branching and no RTL/ADR discussion was needed.
- Deciding URL edge-case policy in the requirements doc *before* writing the spec (host:port
  vs scheme ambiguity, `localhost` only with explicit scheme, exact reason strings) made the
  spec mechanical to write — no mid-test rule invention.
- The WHATWG `URL` constructor did most of the validation/normalization work; the only custom
  logic is the scheme sniff and a dotted-host regex. Zero new dependencies.

## Friction

- `example.com:8080` is ambiguous under RFC 3986: `example.com` parses as a legal *scheme*,
  so naive scheme detection rejects a URL users will absolutely paste. Resolved by treating a
  dot-containing "scheme" as host:port; documented in the feature doc. Parallel-agent repos
  should keep recording such micro-policies in the requirements doc, not just in code.
- Working in a shared-parallel slice means the component is committed unrendered (nothing
  imports it until merge). Build/type-check still covers it, but there is no way to eyeball
  the three states without touching `App.tsx`. The exact wiring JSX was handed to the
  orchestrator instead.

## Changes

- None to the working agreement; the existing "decision logic in pure modules" rule scaled
  cleanly to a form component. Suggested "Current state" line for the orchestrator is in the
  handoff report (CLAUDE.md is orchestrator-owned during parallel work).
