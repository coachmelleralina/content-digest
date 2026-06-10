// Render-only section component (feature 005, issue #2).
// One board section: category heading + its cards, in the order given.

import type { CSSProperties } from 'react';
import type { Section as SectionModel } from '../types';
import { Card } from './Card';

const heading: CSSProperties = {
  fontSize: '1.3rem',
  margin: '2rem 0 0.75rem',
  textAlign: 'left',
};

export function Section({ section }: { section: SectionModel }) {
  return (
    <section>
      <h2 style={heading}>{section.category}</h2>
      {section.cards.map((card) => (
        <Card key={card.id} card={card} />
      ))}
    </section>
  );
}
