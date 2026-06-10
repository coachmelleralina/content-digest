// Pure URL validation/normalization for the UrlInput component (feature 006, issue #3).
// All decision logic lives here so the component only renders.
// Rules: docs/requirements/feature-006-url-input.md

export type ValidateUrlResult =
  | { ok: true; url: string }
  | { ok: false; reason: string };

const REASON_EMPTY = 'Enter a URL.';
const REASON_SCHEME = 'Only http(s) URLs are supported.';
const REASON_INVALID = "That doesn't look like a valid URL.";

// RFC 3986 scheme shape: ALPHA *( ALPHA / DIGIT / "+" / "-" / "." ) ":"
const SCHEME_RE = /^([a-zA-Z][a-zA-Z0-9+.-]*):/;
// Plausible public host: dotted alphanumeric/hyphen labels (example.com, www.example.com).
const HOST_RE = /^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)+$/;

export function validateUrl(input: string): ValidateUrlResult {
  const trimmed = input.trim();
  if (trimmed === '') {
    return { ok: false, reason: REASON_EMPTY };
  }

  let candidate = trimmed;
  const schemeMatch = SCHEME_RE.exec(trimmed);
  const scheme = (schemeMatch?.[1] ?? '').toLowerCase();
  if (schemeMatch && scheme !== 'http' && scheme !== 'https') {
    // A "scheme" containing a dot is almost certainly host:port (example.com:8080).
    if (scheme.includes('.')) {
      candidate = `https://${trimmed}`;
    } else {
      return { ok: false, reason: REASON_SCHEME };
    }
  } else if (!schemeMatch) {
    candidate = `https://${trimmed}`;
  }

  let url: URL;
  try {
    url = new URL(candidate);
  } catch {
    return { ok: false, reason: REASON_INVALID };
  }

  if (url.hostname !== 'localhost' && !HOST_RE.test(url.hostname)) {
    return { ok: false, reason: REASON_INVALID };
  }

  return { ok: true, url: url.href };
}

// Rejected-onSubmit-promise → inline error message. Never renders "[object Object]".
export function toErrorMessage(err: unknown): string {
  if (err instanceof Error && err.message !== '') {
    return err.message;
  }
  return 'Something went wrong.';
}
