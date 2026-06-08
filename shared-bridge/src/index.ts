export type {
  PluginCapability,
  AppId,
  OpenClawBridgeConfig,
  CrossAppEvent,
  AppHealth,
} from './types.js';

export {
  registerCapability,
  getCapability,
  listCapabilitiesByApp,
  registerAllCapabilities,
} from './registry.js';

export { OpenClawBridge } from './openclaw.js';
