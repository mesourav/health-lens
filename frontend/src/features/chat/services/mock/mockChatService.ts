import { sleep } from '@/lib/sleep';
import type { ChatService } from '../../types';
import { AGENT_REPLY, FLOWS, isFlowId } from './flows';
import { routeIntent } from './routeIntent';

/** Offline stand-in for the backend: scripted answers, no network. */
export function createMockChatService({ latencyMs = 0 } = {}): ChatService {
  return {
    async respond(request, signal) {
      if (latencyMs > 0) await sleep(latencyMs, signal);

      if (request.mode === 'agent' && request.text) {
        return { steps: [AGENT_REPLY], replies: [] };
      }
      const intent = request.intent ?? routeIntent(request.text ?? '');
      return isFlowId(intent) ? FLOWS[intent] : FLOWS.fallback;
    },
  };
}
