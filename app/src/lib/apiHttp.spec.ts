// Spec for feature 012 (issue #10) — the fetch-based Backend implementation.
// globalThis.fetch is stubbed; no network.

import { afterEach, describe, expect, it, vi } from 'vitest';
import { createHttpBackend } from './api';
import { ApiError } from './apiError';
import type { Card } from '../types';

const CARD: Card = {
  id: '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d',
  url: 'https://example.com/a',
  title: 'A Title',
  summary: 'A summary.',
  keyPoints: ['one'],
  tags: ['x'],
  category: 'Engineering',
  createdAt: '2026-06-11T10:00:00+00:00',
};

const jsonResponse = (status: number, body: unknown): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('createHttpBackend', () => {
  it('digestUrl POSTs the url to /api/digest and returns the card', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, CARD));
    vi.stubGlobal('fetch', fetchMock);

    const card = await createHttpBackend().digestUrl('https://example.com/a');

    expect(card).toEqual(CARD);
    const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(path).toBe('/api/digest');
    expect(init.method).toBe('POST');
    expect(init.headers).toMatchObject({ 'content-type': 'application/json' });
    expect(JSON.parse(init.body as string)).toEqual({ url: 'https://example.com/a' });
  });

  it('listCards GETs /api/cards', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, [CARD]));
    vi.stubGlobal('fetch', fetchMock);

    const cards = await createHttpBackend().listCards();

    expect(cards).toEqual([CARD]);
    expect(fetchMock.mock.calls[0]?.[0]).toBe('/api/cards');
  });

  it('deleteCard DELETEs /api/cards/{id} and resolves on 204', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(createHttpBackend().deleteCard(CARD.id)).resolves.toBeUndefined();
    const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(path).toBe(`/api/cards/${CARD.id}`);
    expect(init.method).toBe('DELETE');
  });

  it('maps backend {detail} errors to ApiError with status', async () => {
    // Fresh Response per call — a Response body can only be consumed once.
    const fetchMock = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(jsonResponse(422, { detail: 'Could not extract this article.' })),
      );
    vi.stubGlobal('fetch', fetchMock);

    const promise = createHttpBackend().digestUrl('https://example.com/a');
    await expect(promise).rejects.toBeInstanceOf(ApiError);
    await expect(
      createHttpBackend().digestUrl('https://example.com/a'),
    ).rejects.toMatchObject({ message: 'Could not extract this article.', status: 422 });
  });

  it('maps non-JSON error bodies to a generic ApiError with status', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response('Bad Gateway', { status: 502 }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(createHttpBackend().listCards()).rejects.toMatchObject({ status: 502 });
  });

  it('maps network failures to a user-displayable ApiError without status', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('fetch failed'));
    vi.stubGlobal('fetch', fetchMock);

    const rejection = expect(createHttpBackend().listCards()).rejects;
    await rejection.toBeInstanceOf(ApiError);
    await expect(createHttpBackend().listCards()).rejects.toMatchObject({
      status: undefined,
    });
  });
});
