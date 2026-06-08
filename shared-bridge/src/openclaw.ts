import { AppId, AppHealth, CrossAppEvent } from './types.js';

// OpenClaw gateway API wrapper
export class OpenClawBridge {
  private gatewayUrl: string;

  constructor(gatewayUrl = 'http://127.0.0.1:18790') {
    this.gatewayUrl = gatewayUrl;
  }

  /** Dispatch a cross-app event to OpenClaw */
  async dispatchEvent(event: CrossAppEvent): Promise<Response> {
    return fetch(`${this.gatewayUrl}/api/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event),
    });
  }

  /** Query app health through OpenClaw */
  async getAppHealth(appId: AppId): Promise<AppHealth | null> {
    try {
      const res = await fetch(`${this.gatewayUrl}/api/health/${appId}`);
      if (!res.ok) return null;
      return res.json() as Promise<AppHealth>;
    } catch {
      return null;
    }
  }

  /** Send a task to OpenClaw agent dispatch */
  async sendAgentTask(task: {
    projectRoot: string;
    prompt: string;
    model?: string;
    toolAllow?: string[];
  }): Promise<{ sessionId: string } | { error: string }> {
    try {
      const res = await fetch(`${this.gatewayUrl}/api/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task),
      });
      return res.json() as Promise<{ sessionId: string } | { error: string }>;
    } catch (e) {
      return { error: String(e) };
    }
  }
}
