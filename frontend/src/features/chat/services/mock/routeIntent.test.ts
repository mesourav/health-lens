import { describe, expect, it } from 'vitest';
import type { FlowId } from './flows';
import { routeIntent } from './routeIntent';

const cases: Array<[text: string, flow: FlowId]> = [
  ['Is my MRI covered?', 'mri'],
  ['I want to talk to a human', 'handoff'],
  ['How much of my deductible is left?', 'deductible'],
  ['Do I need a referral for a dermatologist?', 'referral'],
  ['Does the plan cover therapy?', 'therapy'],
  ['What is prior approval?', 'prior'],
  ['My doctor said something', 'fallback'],
];

describe('routeIntent', () => {
  it.each(cases)('routes %j to %s', (text, flow) => {
    expect(routeIntent(text)).toBe(flow);
  });
});
