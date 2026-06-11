// Text-fragment deep links (feature 016, issue #15). A key point's grounding
// quote becomes a https://wicg.github.io/scroll-to-text-fragment/ link so the
// takeaway opens the original article scrolled to the exact passage.

/**
 * Deep link to the quoted passage inside the article, or null when the key
 * point has no grounding quote (renders as plain text). Any existing
 * #fragment on the article url is stripped before the text fragment is added.
 */
export const takeawayHref = (articleUrl: string, quote: string | null): string | null => {
  if (quote === null) return null;
  const hashIndex = articleUrl.indexOf('#');
  const base = hashIndex === -1 ? articleUrl : articleUrl.slice(0, hashIndex);
  // encodeURIComponent leaves "-" unescaped, but it is special in the
  // text-directive syntax (prefix-/textStart/-suffix) — escape it ourselves.
  const encoded = encodeURIComponent(quote).replace(/-/g, '%2D');
  return `${base}#:~:text=${encoded}`;
};
