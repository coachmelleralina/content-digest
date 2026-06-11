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
