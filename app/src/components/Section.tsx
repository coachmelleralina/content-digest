// Render-only section component (feature 005, issue #2; feature 016, issue #15).
// One board section: category heading + its cards, in the order given.

import type { CSSProperties } from 'react';
import type { Section as SectionModel } from '../types';
import { Card } from './Card';

const heading: CSSProperties = {
  fontSize: '1.3rem',
  margin: '2rem 0 0.75rem',
  textAlign: 'left',
};

export function Section({
  section,
  onDelete,
  onTagClick,
  activeTag,
}: {
  section: SectionModel;
  onDelete: (id: string) => void;
  onTagClick: (tag: string) => void;
  activeTag: string | null;
}) {
  return (
    <section>
      <h2 style={heading}>{section.category}</h2>
      {section.cards.map((card) => (
        <Card
          key={card.id}
          card={card}
          onDelete={onDelete}
          onTagClick={onTagClick}
          activeTag={activeTag}
        />
      ))}
    </section>
  );
}
