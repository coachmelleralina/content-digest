// Shared frontend types (feature 003, issue #1).
// `Card` mirrors the `cards` table in docs/PLAN.md:
// key_points/tags (jsonb) → KeyPoint[]/string[], created_at → ISO 8601 string.

// Feature 016 (issue #15), coordinated with backend issue #13: each key point
// is a simple-language takeaway plus the verbatim grounding quote from the
// article (null when the model could not ground the point).
export type KeyPoint = {
  takeaway: string;
  quote: string | null;
};

export type Card = {
  id: string;
  url: string;
  title: string;
  summary: string;
  keyPoints: KeyPoint[];
  tags: string[];
  category: string;
  // Feature 017 (issue #16), coordinated with backend issue #14: the card's
  // current display language ('uk' | 'ru' | 'en'; quotes stay original).
  language: string;
  createdAt: string;
};

export type Section = {
  category: string;
  cards: Card[];
};

// Feature 019: a related card the AI picked (id from the board) + why it's
// related. `SimilarMatch` is the display form after resolving the id to a title.
export type SimilarRef = {
  id: string;
  reason: string;
};

export type SimilarMatch = {
  id: string;
  title: string;
  reason: string;
};

// Feature 019: the "similar materials" interaction state + callbacks, bundled
// so Board/Section forward one prop. Each Card derives its own slice by id.
export type SimilarUiProps = {
  resultsByCard: Record<string, SimilarMatch[] | null>;
  findingId: string | null;
  highlightedId: string | null;
  disabled: boolean; // true when the board has fewer than 2 cards
  onFind: (id: string) => void;
  onGoTo: (id: string) => void;
};
