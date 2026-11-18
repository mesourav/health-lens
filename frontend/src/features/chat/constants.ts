import type { ChatMode } from './types';

interface ModeCopy {
  title: string;
  subtitle: string;
  placeholder: string;
}

export const CHAT_COPY: Record<ChatMode, ModeCopy> = {
  bot: {
    title: 'Health Lens',
    subtitle: 'Answers based on your plan',
    placeholder: 'Ask about your coverage…',
  },
  agent: {
    title: 'Sam, Member advocate',
    subtitle: 'Live chat · usually replies in a minute',
    placeholder: 'Message Sam…',
  },
};

export interface ChatTiming {
  /** Minimum time the typing indicator shows before each assistant message. */
  typingMs: number;
  /** Pause after each assistant message. */
  betweenStepsMs: number;
  /** Pause after a system notice such as "Sam joined the chat". */
  systemNoticeMs: number;
}

export const DEFAULT_TIMING: ChatTiming = {
  typingMs: 900,
  betweenStepsMs: 300,
  systemNoticeMs: 400,
};

export const START_INTENT = 'start';
export const MAX_MESSAGE_LENGTH = 1000;
export const ERROR_TEXT = "Sorry, I couldn't reach the server. Please try again in a moment.";
