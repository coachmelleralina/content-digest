// Typed API client (feature 007, issue #4) — the ONLY frontend↔backend
// boundary. The three exports are shaped exactly like the future HTTP layer
// (PLAN: POST /api/digest {url} → card JSON; GET /api/cards;
// DELETE /api/cards/{id}). Internally they delegate to a `Backend` interface;
// today the only implementation is an in-memory mock. Issue #10 swaps the
// mock for a fetch-based Backend — one internal layer, same exported
// signatures, zero component changes.

import type { Card } from '../types';
import { mockCards } from '../mocks/cards';
import { resolveCategory } from './categories';
import { ApiError } from './apiError';

// Internal contract — mirror of the three /api/* routes. Not exported:
// callers depend on the functions below, never on a backend instance.
interface Backend {
  digestUrl(url: string): Promise<Card>;
  listCards(): Promise<Card[]>;
  deleteCard(id: string): Promise<void>;
}

const DIGEST_LATENCY_MS = 300;
const EXTRACT_FAIL_HOSTNAME = 'fail.example.com';

// Raw labels the fake "AI" proposes; resolveCategory (feature 002) then files
// them against whatever categories are already on the board.
const CANDIDATE_CATEGORIES = ['AI', 'Startups', 'Health', 'Coaching', 'Productivity'];

const delay = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

const titleCase = (words: string): string =>
  words.replace(/\b\w/g, (ch) => ch.toUpperCase());

// "https://example.com/posts/why-deep-work-wins" → "Why Deep Work Wins"
const titleFromUrl = (parsed: URL): string => {
  const slug = parsed.pathname
    .split('/')
    .filter((segment) => segment !== '')
    .pop();
  if (slug === undefined) return `Article from ${parsed.hostname}`;
  return titleCase(slug.replace(/\.[a-z]+$/i, '').replace(/[-_]+/g, ' ').trim()) || parsed.hostname;
};

const generateCard = (url: string, parsed: URL, existingCategories: string[]): Card => {
  const title = titleFromUrl(parsed);
  const hash = [...parsed.hostname].reduce((sum, ch) => sum + ch.charCodeAt(0), 0);
  const rawCategory = CANDIDATE_CATEGORIES[hash % CANDIDATE_CATEGORIES.length] ?? 'Uncategorized';
  return {
    id: crypto.randomUUID(),
    url,
    title,
    summary:
      `A digest of "${title}" from ${parsed.hostname}: the piece lays out its core argument, ` +
      'supports it with concrete examples, and closes with practical takeaways for the reader.',
    keyPoints: [
      `Main argument of "${title}" distilled into one sentence`,
      'Strongest supporting evidence the author offers',
      'One practical takeaway to apply this week',
    ],
    tags: [parsed.hostname.split('.')[0] ?? 'web', 'article', 'digest'],
    category: resolveCategory(rawCategory, existingCategories),
    createdAt: new Date().toISOString(),
  };
};

const createMockBackend = (): Backend => {
  let cards: Card[] = structuredClone(mockCards);

  return {
    async digestUrl(url: string): Promise<Card> {
      await delay(DIGEST_LATENCY_MS);
      let parsed: URL;
      try {
        parsed = new URL(url);
      } catch {
        throw new ApiError('Could not extract this article', 422);
      }
      if (parsed.hostname === EXTRACT_FAIL_HOSTNAME) {
        throw new ApiError('Could not extract this article', 422);
      }
      const existingCategories = [...new Set(cards.map((c) => c.category))];
      const card = generateCard(url, parsed, existingCategories);
      cards = [...cards, card];
      return structuredClone(card);
    },

    async listCards(): Promise<Card[]> {
      return Promise.resolve(structuredClone(cards));
    },

    async deleteCard(id: string): Promise<void> {
      if (!cards.some((c) => c.id === id)) {
        throw new ApiError('Card not found', 404);
      }
      cards = cards.filter((c) => c.id !== id);
      return Promise.resolve();
    },
  };
};

// --- HTTP backend (feature 012, issue #10) ------------------------------------
// In dev the Vite proxy forwards /api/* to the FastAPI server; in prod both
// live on the same Vercel origin. Errors arrive as {detail: string}.

const NETWORK_ERROR_MESSAGE = 'Could not reach the server. Is it running?';

const toApiError = async (response: Response): Promise<ApiError> => {
  let detail = `Request failed (HTTP ${response.status}).`;
  try {
    const body: unknown = await response.json();
    if (
      typeof body === 'object' &&
      body !== null &&
      'detail' in body &&
      typeof (body as { detail: unknown }).detail === 'string'
    ) {
      detail = (body as { detail: string }).detail;
    }
  } catch {
    // non-JSON body — keep the generic message
  }
  return new ApiError(detail, response.status);
};

const request = async (path: string, init?: RequestInit): Promise<Response> => {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new ApiError(NETWORK_ERROR_MESSAGE);
  }
  if (!response.ok) throw await toApiError(response);
  return response;
};

/** Internal — exported only for specs (apiHttp.spec.ts stubs global fetch). */
export const createHttpBackend = (): Backend => ({
  async digestUrl(url: string): Promise<Card> {
    const response = await request('/api/digest', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    return (await response.json()) as Card;
  },

  async listCards(): Promise<Card[]> {
    const response = await request('/api/cards');
    return (await response.json()) as Card[];
  },

  async deleteCard(id: string): Promise<void> {
    await request(`/api/cards/${id}`, { method: 'DELETE' });
  },
});

// The one switchable layer: vitest keeps the mock (MODE === 'test'); dev and
// prod builds talk to the real backend.
let backend: Backend = import.meta.env.MODE === 'test' ? createMockBackend() : createHttpBackend();

/** POST /api/digest {url} → the digested card. Rejects with ApiError (422 on extraction failure). */
export const digestUrl = (url: string): Promise<Card> => backend.digestUrl(url);

/** GET /api/cards → all saved cards. */
export const listCards = (): Promise<Card[]> => backend.listCards();

/** DELETE /api/cards/{id}. Rejects with ApiError 404 for an unknown id. */
export const deleteCard = (id: string): Promise<void> => backend.deleteCard(id);

/** Test-only: reseed the mock store. Deleted with the mock backend in issue #10. */
export const resetApiMock = (): void => {
  backend = createMockBackend();
};
