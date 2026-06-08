// Plugin capability contract
export interface PluginCapability {
  capabilityName: string;
  version: string;
  direction: 'inbound' | 'outbound' | 'bidirectional';
  providerApp: AppId;
  consumerApp: AppId;
  transport: 'local-ipc' | 'http-api' | 'file-handoff' | 'event-queue';
}

export type AppId = 'project-manager' | 'saydo' | 'realestate-management' | 'company-standards' | 'openclaw';

// OpenClaw bridge
export interface OpenClawBridgeConfig {
  gatewayUrl: string; // default http://127.0.0.1:18790
  workspaceRoot: string;
  projectRoots: Record<AppId, string>;
}

// Cross-app event
export interface CrossAppEvent {
  source: AppId;
  target: AppId;
  eventType: string;
  payload: unknown;
  timestamp: string;
}

// Health check response
export interface AppHealth {
  appId: AppId;
  isRunning: boolean;
  typecheck: 'pass' | 'fail' | 'unknown';
  lastBuilt: string | null;
  port?: number;
}
