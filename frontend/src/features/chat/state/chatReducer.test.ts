import { describe, expect, it } from 'vitest';
import { chatReducer, createInitialState, createMessage } from './chatReducer';

describe('chatReducer', () => {
  it('appends messages in order', () => {
    const first = createMessage('user', 'Hi');
    const second = createMessage('bot', 'Hello');
    let state = createInitialState('c1');
    state = chatReducer(state, { type: 'messageAdded', message: first });
    state = chatReducer(state, { type: 'messageAdded', message: second });
    expect(state.messages).toEqual([first, second]);
  });

  it('reset clears the conversation and returns to the bot', () => {
    let state = createInitialState('c1');
    state = chatReducer(state, { type: 'modeChanged', mode: 'agent' });
    state = chatReducer(state, { type: 'messageAdded', message: createMessage('user', 'Hi') });
    state = chatReducer(state, { type: 'reset', conversationId: 'c2' });
    expect(state).toEqual(createInitialState('c2'));
  });

  it('keeps the same state object when typing does not change', () => {
    const state = createInitialState('c1');
    expect(chatReducer(state, { type: 'typingChanged', isTyping: false })).toBe(state);
  });
});
