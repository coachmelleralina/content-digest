// Feature 019 — DOM id for a card's article element, so "similar" results can
// scroll to it. Kept out of Card.tsx so that file only exports a component
// (react-refresh/only-export-components).

export const cardElementId = (id: string): string => `card-${id}`;
