import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Hide the Next.js dev-mode floating indicator. It was clumping with the
  // AuthPill + Ask/Runner/Map tab strip in the bottom-left corner, making
  // the overlay area read as a pile of disconnected chrome. Build/runtime
  // errors still surface in the terminal + browser overlay; we just don't
  // want the persistent floating chip.
  devIndicators: false,
};

export default nextConfig;
