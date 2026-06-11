// Pure tag filtering (feature 016, issue #15). Tags are canonical reusable
// topics (PRD); matching is case-insensitive so 'AI-Agents' and 'ai-agents'
// behave as one topic. Components stay render-only: App calls filterByTag,
// chips use isSameTag to know whether they are the active one.

import type { Card } from '../types';

/** Case-insensitive tag equality; a null active tag matches nothing. */
export const isSameTag = (tag: string, activeTag: string | null): boolean =>
  activeTag !== null && tag.toLowerCase() === activeTag.toLowerCase();

/** Cards carrying the tag (case-insensitive); null tag → no filter, all cards. */
export const filterByTag = (cards: Card[], tag: string | null): Card[] => {
  if (tag === null) return cards;
  return cards.filter((card) => card.tags.some((t) => isSameTag(t, tag)));
};
