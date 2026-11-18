import type { BotStep, ChatMode, ChatTurn, QuickReply } from '../types';
import { ChatServiceError } from './errors';

type UnknownRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is UnknownRecord =>
  typeof value === 'object' && value !== null;

const STEP_SENDERS: ReadonlySet<string> = new Set<BotStep['sender']>(['bot', 'agent', 'system']);

function parseStep(value: unknown): BotStep {
  if (!isRecord(value) || typeof value.text !== 'string' || typeof value.sender !== 'string') {
    throw new ChatServiceError('Invalid step in chat response');
  }
  if (!STEP_SENDERS.has(value.sender)) {
    throw new ChatServiceError(`Unknown sender "${value.sender}" in chat response`);
  }
  return {
    sender: value.sender as BotStep['sender'],
    text: value.text,
    author: typeof value.author === 'string' ? value.author : undefined,
  };
}

function parseReply(value: unknown): QuickReply {
  if (!isRecord(value) || typeof value.label !== 'string' || typeof value.intent !== 'string') {
    throw new ChatServiceError('Invalid quick reply in chat response');
  }
  return { label: value.label, intent: value.intent };
}

/**
 * Validates an untrusted backend payload and normalises it to a ChatTurn.
 * Missing or null optional fields (common from Python serializers) are dropped.
 */
export function parseChatTurn(value: unknown): ChatTurn {
  if (!isRecord(value) || !Array.isArray(value.steps)) {
    throw new ChatServiceError('Chat response is missing "steps"');
  }
  const { mode, followUp } = value;
  return {
    steps: value.steps.map(parseStep),
    replies: Array.isArray(value.replies) ? value.replies.map(parseReply) : [],
    mode: mode === 'bot' || mode === 'agent' ? (mode satisfies ChatMode) : undefined,
    followUp:
      isRecord(followUp) &&
      typeof followUp.intent === 'string' &&
      typeof followUp.delayMs === 'number'
        ? { intent: followUp.intent, delayMs: followUp.delayMs }
        : undefined,
  };
}
