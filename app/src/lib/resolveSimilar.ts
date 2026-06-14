// Feature 019 — resolve AI similarity refs into display matches.
// The server already returns only ids that exist on the board, but we resolve
// against the CURRENT cards (a card may have been deleted since) and drop any
// id we can't find, so the UI never shows a dangling result.

import type { Card, SimilarMatch, SimilarRef } from '../types';

export const resolveSimilar = (refs: SimilarRef[], cards: Card[]): SimilarMatch[] => {
  const titleById = new Map(cards.map((c) => [c.id, c.title]));
  return refs.flatMap((ref) => {
    const title = titleById.get(ref.id);
    return title === undefined ? [] : [{ id: ref.id, title, reason: ref.reason }];
  });
};
