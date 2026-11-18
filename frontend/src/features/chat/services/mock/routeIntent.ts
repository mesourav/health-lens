import type { FlowId } from './flows';

// Keyword routing for the mock only. The real backend replaces this with RAG.
const RULES: ReadonlyArray<readonly [RegExp, FlowId]> = [
  [/\b(person|human|agent|someone|representative|call)\b/i, 'handoff'],
  [/\b(mri|scan|imaging|x-ray|ct)\b/i, 'mri'],
  [/\b(prior|approval|authori[sz])/i, 'prior'],
  [/\b(deductible|out[- ]of[- ]pocket|left|owe)\b/i, 'deductible'],
  [/\b(referral|specialist|dermatolog|cardiolog)/i, 'referral'],
  [/\b(therap|mental|counsel|psych)/i, 'therapy'],
];

export function routeIntent(text: string): FlowId {
  return RULES.find(([pattern]) => pattern.test(text))?.[1] ?? 'fallback';
}
