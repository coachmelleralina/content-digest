// Mock card fixtures (feature 003, issue #1). Drive the board UI until the
// real /api/cards endpoint lands (PLAN build steps 2-4). Categories include
// one near-duplicate pair ("AI" vs "Artificial Intelligence") on purpose, so
// the feature-002 merge behavior is visible on the board.

import type { Card } from '../types';

export const mockCards: Card[] = [
  {
    id: 'c1',
    url: 'https://stratechery.com/2026/the-agent-economy-arrives',
    title: 'The Agent Economy Arrives: Why 2026 Is the Year of Delegated Work',
    summary:
      'Argues that AI agents have crossed from demos to dependable delegation, and that the winners of this shift are platforms that own the trust layer — auth, payments, and audit trails — rather than the models themselves.',
    keyPoints: [
      {
        takeaway: 'Agent reliability passed the "unattended hour" threshold in late 2025',
        quote:
          'For the first time, median enterprise agents ran a full hour unattended without a single human intervention — the threshold operators told us mattered most.',
      },
      {
        takeaway: 'Value accrues to trust infrastructure, not raw model capability',
        quote: 'The models are becoming commodities; the audit trail is becoming the product.',
      },
      {
        takeaway: 'Enterprises adopt agents department-by-department, starting with ops',
        quote: null,
      },
    ],
    tags: ['ai-agents', 'strategy', 'platforms'],
    category: 'AI',
    language: 'uk',
    createdAt: '2026-06-09T08:15:00Z',
  },
  {
    id: 'c2',
    url: 'https://www.quantamagazine.org/sparse-models-learn-more-with-less',
    title: 'Sparse Models Learn More With Less, New Scaling Study Finds',
    summary:
      'A large-scale study from EPFL shows sparsely activated networks matching dense models with a third of the training compute, reviving interest in conditional computation and challenging the "bigger is better" orthodoxy.',
    keyPoints: [
      {
        takeaway: 'Sparse mixture models matched dense baselines at ~35% of the FLOPs',
        quote:
          'Across all three benchmark families, the sparse models reached dense-baseline quality using roughly 35 percent of the training FLOPs.',
      },
      {
        takeaway: 'Gains held across language, vision, and protein-folding benchmarks',
        quote: null,
      },
      {
        takeaway: 'Routing instability remains the main blocker for production use',
        quote:
          'Routing collapse remains the one failure mode we cannot yet predict from training curves alone.',
      },
    ],
    tags: ['research', 'scaling-laws', 'efficiency'],
    category: 'Artificial Intelligence',
    language: 'uk',
    createdAt: '2026-05-28T14:40:00Z',
  },
  {
    id: 'c3',
    url: 'https://hbr.org/2026/05/the-quiet-rise-of-the-fractional-executive',
    title: 'The Quiet Rise of the Fractional Executive',
    summary:
      'HBR profiles the post-2024 boom in fractional C-suite roles: seasoned operators splitting time across two or three scale-ups, what it does to founder trust, and how boards are rewriting comp to make it work.',
    keyPoints: [
      {
        takeaway: 'Fractional CMO and CFO postings tripled since 2024',
        quote:
          'Listings for fractional CMO and CFO roles have tripled since early 2024, according to three of the largest executive marketplaces.',
      },
      {
        takeaway: 'Works best between Series A and C, before full-time depth is needed',
        quote:
          'The sweet spot sits between Series A and Series C, when the problems are senior but the calendar is not yet full-time.',
      },
      {
        takeaway: 'Equity-light, milestone-based comp packages are becoming standard',
        quote: null,
      },
    ],
    tags: ['leadership', 'hiring', 'scale-ups'],
    category: 'Startups',
    language: 'uk',
    createdAt: '2026-06-02T09:00:00Z',
  },
  {
    id: 'c4',
    url: 'https://every.to/p/founders-are-shipping-without-engineers',
    title: 'Founders Are Shipping Without Engineers — and Investors Have Noticed',
    summary:
      'A look at the new cohort of solo, non-technical founders reaching meaningful revenue on agent-built software, why seed investors now screen for distribution instead of engineering, and where this approach still breaks.',
    keyPoints: [
      {
        takeaway: 'Dozens of agent-built products crossed $1M ARR with no engineering hires',
        quote:
          'At least a few dozen agent-built products have crossed one million dollars in annual recurring revenue without a single engineering hire.',
      },
      {
        takeaway: 'Diligence is shifting from technical moats to distribution proof',
        quote: null,
      },
      {
        takeaway: 'Maintenance and security debt surface around the 18-month mark',
        quote: 'The bill for deferred maintenance tends to arrive around month eighteen.',
      },
    ],
    tags: ['founders', 'no-code', 'venture'],
    category: 'Startups',
    language: 'uk',
    createdAt: '2026-06-07T17:25:00Z',
  },
  {
    id: 'c5',
    url: 'https://www.nature.com/articles/sleep-glymphatic-2026',
    title: 'Deep Sleep Acts as the Brain’s Overnight Rinse Cycle, Imaging Study Confirms',
    summary:
      'New human imaging work in Nature confirms that slow-wave sleep drives glymphatic clearance of metabolic waste, and that even one shortened night measurably slows the process — strengthening the sleep-dementia link.',
    keyPoints: [
      {
        takeaway: 'First direct human imaging of glymphatic flow during slow-wave sleep',
        quote:
          'This is, to our knowledge, the first direct visualization of glymphatic transport in the sleeping human brain.',
      },
      {
        takeaway: 'A single 4-hour night cut measured clearance by roughly 30%',
        quote:
          'After a single night restricted to four hours, measured clearance rates fell by roughly thirty percent.',
      },
      {
        takeaway: 'Authors caution against supplements marketed on the back of the finding',
        quote: null,
      },
    ],
    tags: ['sleep', 'neuroscience', 'longevity'],
    category: 'Health',
    language: 'uk',
    createdAt: '2026-05-21T11:05:00Z',
  },
  {
    id: 'c6',
    url: 'https://www.outsideonline.com/health/zone-2-backlash-what-science-says',
    title: 'The Zone 2 Backlash: What the Science Actually Says About Easy Miles',
    summary:
      'After three years of zone-2 evangelism, sports scientists push back: the aerobic-base benefits are real but plateau quickly for recreational athletes, and most people would gain more from two weekly high-intensity sessions.',
    keyPoints: [
      {
        takeaway: 'Zone 2 benefits plateau around 4-5 weekly hours for amateurs',
        quote:
          'For recreational athletes, the aerobic-base benefits of zone 2 plateau at around four to five hours per week.',
      },
      {
        takeaway: 'Polarized plans beat pure zone-2 plans in 8 of 9 recent trials',
        quote:
          'In eight of the nine randomized trials we reviewed, polarized programs outperformed pure low-intensity volume.',
      },
      {
        takeaway: 'Heart-rate-zone wearable accuracy remains a confounder in field studies',
        quote: null,
      },
    ],
    tags: ['fitness', 'endurance', 'training'],
    category: 'Health',
    language: 'uk',
    createdAt: '2026-06-05T07:50:00Z',
  },
  {
    id: 'c7',
    url: 'https://www.coachingfederation.org/blog/ai-supervision-coaching-2026',
    title: 'ICF Issues First Guidance on AI-Assisted Coaching Supervision',
    summary:
      'The International Coaching Federation published its first formal guidance on using AI tools in coaching supervision: allowed for session preparation and pattern-spotting, but reflective practice and client confidentiality lines stay human-only.',
    keyPoints: [
      {
        takeaway: 'AI may support prep and theme analysis, not replace supervision dialogue',
        quote:
          'AI tools may inform preparation and surface patterns, but the reflective dialogue at the heart of supervision must remain between humans.',
      },
      {
        takeaway: 'Client transcripts may not be fed to third-party models without consent',
        quote:
          'Client session material may not be shared with third-party models without explicit, revocable consent.',
      },
      {
        takeaway: 'Credential renewals from 2027 will require an AI-ethics module',
        quote: null,
      },
    ],
    tags: ['coaching', 'ethics', 'icf'],
    category: 'Coaching',
    language: 'uk',
    createdAt: '2026-06-10T13:30:00Z',
  },
];
