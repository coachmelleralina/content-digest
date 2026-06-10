// Shared frontend types (feature 003, issue #1).
// `Card` mirrors the `cards` table in docs/PLAN.md:
// key_points/tags (jsonb) → string[], created_at → ISO 8601 string.

export type Card = {
  id: string;
  url: string;
  title: string;
  summary: string;
  keyPoints: string[];
  tags: string[];
  category: string;
  createdAt: string;
};

export type Section = {
  category: string;
  cards: Card[];
};
