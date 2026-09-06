export const GANYMEDE_EDITION =
  process.env.NEXT_PUBLIC_GANYMEDE_EDITION === 'showcase' ? 'showcase' : 'full';

export const GANYMEDE_SHOWCASE_MODE = GANYMEDE_EDITION === 'showcase';
export const GANYMEDE_FULL_MODE = GANYMEDE_EDITION === 'full';
