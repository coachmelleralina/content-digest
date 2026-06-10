// Pure category-normalization module (feature 002, issue #12).
// Merges near-duplicate AI-chosen labels so board sections don't split.

const collapse = (raw: string): string => raw.trim().replace(/\s+/g, ' ');

const fold = (raw: string): string =>
  collapse(raw.replace(/[-_]/g, ' ')).toLowerCase();

// Trailing-s plural fold on the last word; words shorter than 4 chars are left
// alone so labels like "AI" or "iOS" are never mangled.
const singularFold = (folded: string): string => {
  const words = folded.split(' ');
  const last = words[words.length - 1];
  if (last !== undefined && last.length >= 4 && last.endsWith('s')) {
    words[words.length - 1] = last.slice(0, -1);
  }
  return words.join(' ');
};

const initials = (folded: string): string | null => {
  const words = folded.split(' ');
  if (words.length < 2) return null;
  return words.map((w) => w.charAt(0)).join('');
};

const levenshtein = (a: string, b: string): number => {
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const curr = [i];
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min((curr[j - 1] ?? 0) + 1, (prev[j] ?? 0) + 1, (prev[j - 1] ?? 0) + cost);
    }
    prev = curr;
  }
  return prev[b.length] ?? 0;
};

const typoMatches = (a: string, b: string): boolean => {
  if (a.length < 5 || b.length < 5) return false;
  const threshold = Math.min(a.length, b.length) >= 8 ? 2 : 1;
  return levenshtein(a, b) <= threshold;
};

/**
 * Given an AI-proposed category label and the labels already on the board,
 * returns the label to file the card under: an existing label when the new
 * one is a near-duplicate (case/whitespace, plural, acronym, single typo),
 * otherwise the cleaned-up new label.
 */
export const resolveCategory = (raw: string, existing: string[]): string => {
  const cleaned = collapse(raw);
  if (cleaned === '') return 'Uncategorized';
  const f = fold(raw);

  const rules: Array<(e: string) => boolean> = [
    (e) => fold(e) === f,
    (e) => singularFold(fold(e)) === singularFold(f),
    (e) => initials(fold(e)) === f || initials(f) === fold(e),
    (e) => typoMatches(fold(e), f),
  ];
  for (const matches of rules) {
    const hit = existing.find(matches);
    if (hit !== undefined) return hit;
  }
  return cleaned;
};
