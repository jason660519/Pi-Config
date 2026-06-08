// OpenClaw gateway API wrapper
export class OpenClawBridge {
    gatewayUrl;
    constructor(gatewayUrl = 'http://127.0.0.1:18790') {
        this.gatewayUrl = gatewayUrl;
    }
    /** Dispatch a cross-app event to OpenClaw */
    async dispatchEvent(event) {
        return fetch(`${this.gatewayUrl}/api/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(event),
        });
    }
    /** Query app health through OpenClaw */
    async getAppHealth(appId) {
        try {
            const res = await fetch(`${this.gatewayUrl}/api/health/${appId}`);
            if (!res.ok)
                return null;
            return res.json();
        }
        catch {
            return null;
        }
    }
    /** Send a task to OpenClaw agent dispatch */
    async sendAgentTask(task) {
        try {
            const res = await fetch(`${this.gatewayUrl}/api/dispatch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(task),
            });
            return res.json();
        }
        catch (e) {
            return { error: String(e) };
        }
    }
}
//# sourceMappingURL=openclaw.js.map