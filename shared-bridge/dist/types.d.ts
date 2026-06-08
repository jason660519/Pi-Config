export interface PluginCapability {
    capabilityName: string;
    version: string;
    direction: 'inbound' | 'outbound' | 'bidirectional';
    providerApp: AppId;
    consumerApp: AppId;
    transport: 'local-ipc' | 'http-api' | 'file-handoff' | 'event-queue';
}
export type AppId = 'project-manager' | 'saydo' | 'realestate-management' | 'company-standards' | 'openclaw';
export interface OpenClawBridgeConfig {
    gatewayUrl: string;
    workspaceRoot: string;
    projectRoots: Record<AppId, string>;
}
export interface CrossAppEvent {
    source: AppId;
    target: AppId;
    eventType: string;
    payload: unknown;
    timestamp: string;
}
export interface AppHealth {
    appId: AppId;
    isRunning: boolean;
    typecheck: 'pass' | 'fail' | 'unknown';
    lastBuilt: string | null;
    port?: number;
}
//# sourceMappingURL=types.d.ts.map