export type Sender = 'user' | 'bot' | 'agent' | 'system';
export type ChatMode = 'bot' | 'agent';

export interface ChatMessage {
  id: string;
  sender: Sender;
  text: string;
  /** Display name shown above agent messages, e.g. "Sam · Member advocate". */
  author?: string;
  createdAt: number;
}

/** A suggested reply chip. Its `intent` is sent to the backend instead of free text. */
export interface QuickReply {
  label: string;
  intent: string;
}

/** One message the assistant side wants to show. */
export interface BotStep {
  sender: Exclude<Sender, 'user'>;
  text: string;
  author?: string;
}

/** What the client sends for every user action. Set either `intent` or `text`. */
export interface ChatRequest {
  conversationId: string;
  mode: ChatMode;
  /** The user tapped a quick reply. */
  intent?: string;
  /** The user typed a message. */
  text?: string;
}

/** The backend's answer to one request. */
export interface ChatTurn {
  steps: BotStep[];
  replies: QuickReply[];
  /** Switch the conversation to a human agent (or back to the bot). */
  mode?: ChatMode;
  /** Run another intent automatically after a delay, e.g. an agent joining from the queue. */
  followUp?: { intent: string; delayMs: number };
}

export interface ChatService {
  respond(request: ChatRequest, signal: AbortSignal): Promise<ChatTurn>;
}
