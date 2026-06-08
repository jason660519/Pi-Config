import { PluginCapability, AppId } from './types.js';
export declare function registerCapability(cap: PluginCapability): void;
export declare function getCapability(name: string): PluginCapability | undefined;
export declare function listCapabilitiesByApp(appId: AppId): PluginCapability[];
export declare function registerAllCapabilities(): void;
//# sourceMappingURL=registry.d.ts.map