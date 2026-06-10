# Feature 006 — UrlInput component with loading/error states

Tracks GitHub issue [#3](https://github.com/coachmelleralina/content-digest/issues/3).
Part of PLAN build step 1 ("Frontend shell, no AI yet"): the input control through which a
URL enters the system. Per the working agreement, all decision logic lives in a pure module
(`validateUrl`); the component only renders state and delegates.

## User story

As the board's only user, I want to paste an article link into a single input, press one
button, and either see the app start digesting or get an immediate, plain-language message
about what's wrong with my input — so a bad paste never silently does nothing and a slow
digest never lets me double-submit.

## Scope

1. **`app/src/lib/validateUrl.ts`** — pure module, spec-first:

   ```ts
   export type ValidateUrlResult =
     | { ok: true; url: string } // normalized URL string
     | { ok: false; reason: string }; // human-readable message

   export function validateUrl(input: string): ValidateUrlResult;
   export function toErrorMessage(err: unknown): string; // rejected-promise → inline message
   ```

2. **`app/src/components/UrlInput.tsx`** — render-only component:

   ```ts
   type UrlInputProps = { onSubmit: (url: string) => Promise<void> };
   ```

## Behavior of `validateUrl`

- **Trims** leading/trailing whitespace before any other rule.
- **Empty** (or whitespace-only) input → `{ ok: false }` with reason `"Enter a URL."`.
- **Explicit `http://` / `https://`** (scheme case-insensitive) → parsed with the WHATWG
  `URL` constructor; unparseable input is rejected.
- **Missing scheme with a plausible host** → `https://` is prepended, then parsed.
  "Plausible host" = dotted hostname of alphanumeric/hyphen labels (e.g. `example.com`,
  `www.example.com/path`, `example.com:8080/x`). A scheme-looking prefix that contains a
  dot (`example.com:8080`) is treated as host:port, not as a scheme.
- **Non-http(s) schemes** (`ftp:`, `mailto:`, `javascript:`, `file:`, `data:`, …) →
  `{ ok: false }` with reason `"Only http(s) URLs are supported."`.
- **Garbage** (unparseable input, hosts without a dot like `foo`, text with spaces) →
  `{ ok: false }` with reason `"That doesn't look like a valid URL."`. Exception:
  `localhost` is accepted as a host **only** with an explicit scheme
  (`http://localhost:8000` ok; bare `localhost:8000` is not — out of scope for an
  article-digest app).
- **Normalization**: the returned `url` is `URL.href` — scheme/host lowercased, default
  path `/` added (`HTTPS://Example.COM` → `https://example.com/`), query/hash preserved.
- `toErrorMessage(err)`: `err.message` for `Error` instances (empty message falls back),
  otherwise the generic `"Something went wrong."` — never renders `[object Object]`.

## Behavior of `UrlInput`

Three states, driven only by `validateUrl` + the `onSubmit` promise:

- **idle** — text input + "Digest" submit button, both enabled.
- **loading** — entered after a *valid* submit, while `onSubmit` is pending: input and
  button disabled, button label `"Digesting…"`.
- **error** — inline message (`role="alert"`) below the controls. Sources: a
  `validateUrl` failure reason, or a rejected `onSubmit` promise via
  `toErrorMessage(err)`. The message persists until the next submit attempt.

Flow on submit (form submit / Enter):

1. `validateUrl(value)` — if `{ ok: false }`, show `reason` and **do not** call `onSubmit`.
2. If valid: clear any error, enter loading, call `onSubmit(normalizedUrl)`.
3. Resolve → clear the input, back to idle. Reject → show `toErrorMessage(err)`, keep the
   input value so the user can retry, back to idle.

Minimal inline styles only (no styling framework, per constraints): a flex row with the
input growing, consistent with the existing `system-ui` look in `App.tsx`.

## Acceptance criteria

- `validateUrl` spec covers: trimming; https-prepending; explicit http/https pass-through;
  scheme case-insensitivity; host:port without scheme; query/hash preservation;
  normalization to `href`; rejection of empty/whitespace, no-dot hosts, spaces/garbage,
  `http://` alone, and every non-http(s) scheme listed above; `localhost` with/without
  explicit scheme; exact reason strings as listed.
- `toErrorMessage` spec covers: `Error` with message, `Error` with empty message,
  non-Error throwables (string, undefined).
- Red run captured before implementation; then all green.
- Component compiles under strict TS, renders the three states, never calls `onSubmit`
  with an invalid URL, and contains no validation/branching beyond delegating to the pure
  module and the promise outcome.
- `npm run test:run`, `npm run lint`, `npm run build` all clean.

## Out of scope

- Wiring into `App.tsx` — owned by the orchestrator at merge time (issue #2 owns App).
- `lib/api.ts` / any real `POST /api/digest` call — issue #4. `onSubmit` is injected.
- DOM-level component tests — would need React Testing Library, which requires an ADR
  (working agreement rule 5); specs target the pure module.
- Schemeless `localhost`, IPv6 hosts, punycode/IDN edge cases.
