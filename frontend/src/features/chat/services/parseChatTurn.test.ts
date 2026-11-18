import { describe, expect, it } from 'vitest';
import { parseChatTurn } from './parseChatTurn';

describe('parseChatTurn', () => {
  it('accepts a valid turn and drops null optionals', () => {
    const turn = parseChatTurn({
      steps: [{ sender: 'bot', text: 'Hi', author: null }],
      replies: [{ label: 'Claims', intent: 'claims' }],
      mode: null,
      followUp: null,
    });
    expect(turn).toEqual({
      steps: [{ sender: 'bot', text: 'Hi', author: undefined }],
      replies: [{ label: 'Claims', intent: 'claims' }],
      mode: undefined,
      followUp: undefined,
    });
  });

  it('keeps mode and followUp when present', () => {
    const turn = parseChatTurn({
      steps: [],
      replies: [],
      mode: 'agent',
      followUp: { intent: 'agentJoin', delayMs: 4000 },
    });
    expect(turn.mode).toBe('agent');
    expect(turn.followUp).toEqual({ intent: 'agentJoin', delayMs: 4000 });
  });

  it('rejects unknown senders and missing steps', () => {
    expect(() => parseChatTurn({ steps: [{ sender: 'user', text: 'x' }] })).toThrow();
    expect(() => parseChatTurn({ replies: [] })).toThrow();
  });
});
