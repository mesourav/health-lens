import { useCallback, useEffect, useReducer, useRef } from 'react';
import { env } from '@/config/env';
import { createId } from '@/lib/id';
import { isAbortError, sleep } from '@/lib/sleep';
import { DEFAULT_TIMING, ERROR_TEXT, START_INTENT, type ChatTiming } from '../constants';
import { chatReducer, createInitialState, createMessage } from '../state/chatReducer';
import type { BotStep, ChatRequest, ChatService, QuickReply } from '../types';

export interface UseChatOptions {
  /** Must be stable (create it once), or the conversation restarts on every render. */
  service: ChatService;
  timing?: Partial<ChatTiming>;
}

/**
 * Owns the conversation: sends each user action to the service and plays the
 * answer back step by step with a typing indicator. Starting a new action
 * cancels whatever is still playing (including a pending follow-up).
 */
export function useChat({ service, timing }: UseChatOptions) {
  const [state, dispatch] = useReducer(chatReducer, '', createInitialState);
  const controllerRef = useRef<AbortController | null>(null);

  const typingMs = timing?.typingMs ?? DEFAULT_TIMING.typingMs;
  const betweenStepsMs = timing?.betweenStepsMs ?? DEFAULT_TIMING.betweenStepsMs;
  const systemNoticeMs = timing?.systemNoticeMs ?? DEFAULT_TIMING.systemNoticeMs;

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
  }, []);

  const play = useCallback(
    async (initialRequest: ChatRequest) => {
      cancel();
      const controller = new AbortController();
      controllerRef.current = controller;
      const { signal } = controller;

      const showStep = async (step: BotStep, alreadyWaitedMs: number) => {
        if (step.sender === 'system') {
          dispatch({ type: 'typingChanged', isTyping: false });
          dispatch({ type: 'messageAdded', message: createMessage('system', step.text) });
          await sleep(systemNoticeMs, signal);
          return;
        }
        dispatch({ type: 'typingChanged', isTyping: true });
        await sleep(Math.max(0, typingMs - alreadyWaitedMs), signal);
        dispatch({
          type: 'messageAdded',
          message: createMessage(step.sender, step.text, step.author),
        });
        dispatch({ type: 'typingChanged', isTyping: false });
        await sleep(betweenStepsMs, signal);
      };

      dispatch({ type: 'repliesChanged', replies: [] });
      let request = initialRequest;

      try {
        for (;;) {
          dispatch({ type: 'typingChanged', isTyping: true });
          const startedAt = performance.now();
          const turn = await service.respond(request, signal);
          signal.throwIfAborted();

          // Time spent waiting on the network counts towards the first typing delay.
          let waited = performance.now() - startedAt;
          for (const step of turn.steps) {
            await showStep(step, waited);
            waited = 0;
          }

          dispatch({ type: 'typingChanged', isTyping: false });
          if (turn.mode) dispatch({ type: 'modeChanged', mode: turn.mode });
          dispatch({ type: 'repliesChanged', replies: turn.replies });

          if (!turn.followUp) break;
          await sleep(turn.followUp.delayMs, signal);
          request = {
            conversationId: request.conversationId,
            mode: turn.mode ?? request.mode,
            intent: turn.followUp.intent,
          };
        }
      } catch (error) {
        if (isAbortError(error)) return;
        if (env.isDev) console.error('[chat]', error);
        dispatch({ type: 'typingChanged', isTyping: false });
        dispatch({ type: 'messageAdded', message: createMessage('bot', ERROR_TEXT) });
      } finally {
        if (controllerRef.current === controller) controllerRef.current = null;
      }
    },
    [cancel, service, typingMs, betweenStepsMs, systemNoticeMs],
  );

  const { conversationId, mode } = state;

  const sendText = useCallback(
    (raw: string) => {
      const text = raw.trim();
      if (!text) return;
      dispatch({ type: 'messageAdded', message: createMessage('user', text) });
      void play({ conversationId, mode, text });
    },
    [play, conversationId, mode],
  );

  const selectReply = useCallback(
    (reply: QuickReply) => {
      dispatch({ type: 'messageAdded', message: createMessage('user', reply.label) });
      void play({ conversationId, mode, intent: reply.intent });
    },
    [play, conversationId, mode],
  );

  const restart = useCallback(() => {
    cancel();
    const nextId = createId();
    dispatch({ type: 'reset', conversationId: nextId });
    void play({ conversationId: nextId, mode: 'bot', intent: START_INTENT });
  }, [cancel, play]);

  useEffect(() => {
    restart();
    return cancel;
  }, [restart, cancel]);

  return {
    messages: state.messages,
    replies: state.replies,
    isTyping: state.isTyping,
    mode: state.mode,
    sendText,
    selectReply,
    restart,
  };
}
