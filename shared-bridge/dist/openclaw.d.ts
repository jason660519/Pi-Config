import { AppId, AppHealth, CrossAppEvent } from './types.js';
export declare class OpenClawBridge {
    private gatewayUrl;
    constructor(gatewayUrl?: string);
    /** Dispatch a cross-app event to OpenClaw */
    dispatchEvent(event: CrossAppEvent): Promise<Response>;
    /** Query app health through OpenClaw */
    getAppHealth(appId: AppId): Promise<AppHealth | null>;
    /** Send a task to OpenClaw agent dispatch */
    sendAgentTask(task: {
        projectRoot: string;
        prompt: string;
        model?: string;
        toolAllow?: string[];
    }): Promise<{
        sessionId: string;
    } | {
        error: string;
    }>;
}
//# sourceMappingURL=openclaw.d.ts.map