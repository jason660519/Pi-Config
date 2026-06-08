import { PluginCapability, AppId } from './types.js';

const CAPABILITIES: Map<string, PluginCapability> = new Map();

// Register known capabilities
export function registerCapability(cap: PluginCapability): void {
  CAPABILITIES.set(cap.capabilityName, cap);
}

export function getCapability(name: string): PluginCapability | undefined {
  return CAPABILITIES.get(name);
}

export function listCapabilitiesByApp(appId: AppId): PluginCapability[] {
  return Array.from(CAPABILITIES.values())
    .filter(c => c.providerApp === appId || c.consumerApp === appId);
}

// Register all v0 contracts
export function registerAllCapabilities(): void {
  registerCapability({
    capabilityName: 'realestate.task.export',
    version: '0.1.0',
    direction: 'outbound',
    providerApp: 'realestate-management',
    consumerApp: 'project-manager',
    transport: 'http-api',
  });
  registerCapability({
    capabilityName: 'saydo.text.handoff',
    version: '0.1.0',
    direction: 'outbound',
    providerApp: 'saydo',
    consumerApp: 'realestate-management',
    transport: 'local-ipc',
  });
  // OpenClaw capability (new)
  registerCapability({
    capabilityName: 'openclaw.agent.dispatch',
    version: '0.1.0',
    direction: 'outbound',
    providerApp: 'openclaw',
    consumerApp: 'project-manager',
    transport: 'http-api',
  });
}
