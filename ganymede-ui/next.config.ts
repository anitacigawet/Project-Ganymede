import type { NextConfig } from 'next';
import path from 'node:path';

// Force-disable the Next.js 16 dev-tools indicator (the floating Next-logo
// button in the bottom-left that spins during Fast Refresh compiles).
//
// In Next 16.2.4, `devIndicators: false` (below) only governs the LEGACY
// static-route / build badge — it does NOT hide the new dev-tools indicator,
// which is a separate component rendered inside the <nextjs-portal> shadow
// root (id `#devtools-indicator`). That component gates its own visibility on
// `process.env.__NEXT_DEV_INDICATOR?.toString() === 'false'` (verified in
// node_modules/next/dist/compiled/next-devtools/index.js). Setting the env
// var here — next.config.ts runs in-process before Next inlines client env —
// is the native, cross-platform kill switch (no launcher/env-file/dep needed;
// works for `npm run dev`, run_dev.bat, and the Mac stack alike). Errors still
// surface via the full-screen error overlay + terminal.
process.env.__NEXT_DEV_INDICATOR = 'false';

const showroomBuild = process.env.NEXT_PUBLIC_GANYMEDE_DEMO_MODE === '1';

const nextConfig: NextConfig = {
  // Legacy static-route / build-activity badge. Harmless to keep; the new
  // dev-tools indicator is handled by the env var above.
  devIndicators: false,
  // This checkout sits below another lockfile in the user profile. Pinning
  // the project root keeps Turbopack from watching the entire profile and
  // makes the real UI runnable in restricted QA/deployment environments.
  turbopack: {
    root: path.resolve(process.cwd()),
  },
  // The hosted portfolio copy is a static export. All interactive state stays
  // in the browser, so visitors cannot start backend or model work.
  output: showroomBuild ? 'export' : undefined,
  trailingSlash: showroomBuild,
};

export default nextConfig;
