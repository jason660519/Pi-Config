const CAPABILITIES = new Map();
// Register known capabilities
export function registerCapability(cap) {
    CAPABILITIES.set(cap.capabilityName, cap);
}
export function getCapability(name) {
    return CAPABILITIES.get(name);
}
export function listCapabilitiesByApp(appId) {
    return Array.from(CAPABILITIES.values())
        .filter(c => c.providerApp === appId || c.consumerApp === appId);
}
// Register all v0 contracts
export function registerAllCapabilities() {
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
//# sourceMappingURL=registry.js.map