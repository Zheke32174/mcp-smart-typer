#!/usr/bin/env node

/**
 * Public package entry point.
 *
 * The distributable TypeScript surface is intentionally mock-backed. Real
 * Windows UI automation remains in the separately tested native-helper
 * package until an authenticated, bounded transport contract is implemented.
 */
import './simple-server.js';
