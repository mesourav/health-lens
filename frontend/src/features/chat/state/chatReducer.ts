import { createId } from '@/lib/id';
import type { ChatMessage, ChatMode, QuickReply, Sender } from '../types';

export interface ChatState {
  conversationId: string;
  messages: ChatMessage[];
  replies: QuickReply[];
  mode: ChatMode;
  isTyping: boolean;
}

export type ChatAction =
  | { type: 'reset'; conversationId: string }
  | { type: 'messageAdded'; message: ChatMessage }
  | { type: 'typingChanged'; isTyping: boolean }
  | { type: 'repliesChanged'; replies: QuickReply[] }
  | { type: 'modeChanged'; mode: ChatMode };

export function createInitialState(conversationId: string): ChatState {
  return { conversationId, messages: [], replies: [], mode: 'bot', isTyping: false };
}

export function createMessage(sender: Sender, text: string, author?: string): ChatMessage {
  return { id: createId(), sender, text, author, createdAt: Date.now() };
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'reset':
      return createInitialState(action.conversationId);
    case 'messageAdded':
      return { ...state, messages: [...state.messages, action.message] };
    case 'typingChanged':
      return state.isTyping === action.isTyping ? state : { ...state, isTyping: action.isTyping };
    case 'repliesChanged':
      return { ...state, replies: action.replies };
    case 'modeChanged':
      return { ...state, mode: action.mode };
    default: {
      const unhandled: never = action;
      return unhandled;
    }
  }
}
