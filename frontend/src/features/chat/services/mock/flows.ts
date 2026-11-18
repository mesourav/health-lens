import type { BotStep, ChatTurn, QuickReply } from '../../types';

// Scripted demo conversation for the mock service. Member details are placeholder data.

const AGENT_NAME = 'Sam · Member advocate';
export const HANDOFF_WAIT_MS = 4000;

const bot = (text: string): BotStep => ({ sender: 'bot', text });
const system = (text: string): BotStep => ({ sender: 'system', text });
const agent = (text: string): BotStep => ({ sender: 'agent', text, author: AGENT_NAME });

const PERSON: QuickReply = { label: 'Talk to a person', intent: 'handoff' };
const MORE: QuickReply = { label: 'Ask something else', intent: 'menu' };
const MAIN: QuickReply[] = [
  { label: 'Is an MRI covered?', intent: 'mri' },
  { label: 'How much deductible is left?', intent: 'deductible' },
  { label: 'Do I need a referral?', intent: 'referral' },
  { label: 'Is therapy covered?', intent: 'therapy' },
  PERSON,
];

export const AGENT_REPLY = agent(
  'Got it. Let me pull up your account so I can look into that. One moment.',
);

export const FLOWS = {
  start: {
    steps: [
      bot(
        "Hi Jordan! I can answer questions about your Silver PPO plan: what's covered, what you'll pay, and how things work. If you'd rather talk to a real person, I can get you to one.",
      ),
    ],
    replies: MAIN,
  },
  menu: {
    steps: [bot('Happy to help. What else is on your mind?')],
    replies: MAIN,
  },
  mri: {
    steps: [
      bot(
        "Good news: MRIs are covered when your doctor orders one. You'll need prior approval first, and your doctor's office usually takes care of that. At an in-network imaging center, you pay 20% once your deductible is met.",
      ),
    ],
    replies: [
      { label: 'What is prior approval?', intent: 'prior' },
      { label: 'How much deductible is left?', intent: 'deductible' },
      PERSON,
    ],
  },
  prior: {
    steps: [
      bot(
        "It means we confirm with your doctor that the scan is needed before you have it. It usually takes 2–3 business days, and we'll text you as soon as it's approved. If you get the scan without it, you could be billed for the full cost, so it's worth waiting.",
      ),
    ],
    replies: [MORE, PERSON],
  },
  deductible: {
    steps: [
      bot(
        "You've paid $860 of your $1,500 deductible this year, so you have $640 to go. After that, you pay 20% of most care until you reach your $5,000 out-of-pocket max. Then we cover 100%.",
      ),
    ],
    replies: [{ label: 'What counts toward it?', intent: 'counts' }, MORE, PERSON],
  },
  counts: {
    steps: [
      bot(
        'Most in-network care you pay for counts: specialist visits, labs, imaging, and hospital stays. Preventive care like your yearly physical is free and doesn’t touch your deductible. Prescriptions have their own copays.',
      ),
    ],
    replies: [MORE, PERSON],
  },
  referral: {
    steps: [
      bot(
        "No, you don't. With a PPO you can book a specialist like a dermatologist directly. If you stay in-network, it's a $50 copay per visit. Out-of-network specialists are covered too, but you'll pay more.",
      ),
    ],
    replies: [MORE, PERSON],
  },
  therapy: {
    steps: [
      bot(
        'Yes. Therapy and other mental health visits are a $30 copay in-network, with no limit on the number of sessions. Video sessions cost the same as in-person ones.',
      ),
    ],
    replies: [MORE, PERSON],
  },
  handoff: {
    steps: [bot("Of course. What's it about? That way I can send you to the right person.")],
    replies: [
      { label: 'A bill or claim', intent: 'queue' },
      { label: 'My coverage', intent: 'queue' },
      { label: 'Something else', intent: 'queue' },
    ],
  },
  queue: {
    steps: [
      bot(
        "Thanks. I'm passing our chat to a member advocate so you won't have to repeat yourself. The wait right now is about 3 minutes.",
      ),
      system("You're #2 in line"),
    ],
    replies: [{ label: 'Call me back instead', intent: 'callback' }],
    followUp: { intent: 'agentJoin', delayMs: HANDOFF_WAIT_MS },
  },
  agentJoin: {
    steps: [
      system('Sam joined the chat'),
      agent("Hi Jordan, I'm Sam. I've read through your chat. What can I help you sort out?"),
    ],
    replies: [],
    mode: 'agent',
  },
  callback: {
    steps: [
      bot(
        "All set. Sam will call you at (•••) •••-4821 within the next 2 hours. You'll get a text a few minutes before. You can close this window.",
      ),
    ],
    replies: [MORE],
  },
  fallback: {
    steps: [
      bot(
        "Hmm, I'm not sure I followed that. I can help with any of these, or connect you with a person.",
      ),
    ],
    replies: MAIN,
  },
} satisfies Record<string, ChatTurn>;

export type FlowId = keyof typeof FLOWS;

export const isFlowId = (value: string): value is FlowId => Object.hasOwn(FLOWS, value);
