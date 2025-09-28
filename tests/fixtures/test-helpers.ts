/**
 * Test helper utilities
 */

export function parseCommand(args: string[]): { command: string; params: Record<string, any> } {
  const command = args.slice(0, 2).join(' ');
  const params: Record<string, any> = {};

  for (let i = 2; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].substring(2);
      if (i + 1 < args.length && !args[i + 1].startsWith('--')) {
        params[key] = args[i + 1];
        i++;
      } else {
        params[key] = true;
      }
    }
  }

  return { command, params };
}

export function assertCommandContains(command: string[], ...expectedArgs: string[]) {
  for (const arg of expectedArgs) {
    expect(command).toContain(arg);
  }
}

export function assertCommandInOrder(command: string[], ...expectedArgs: string[]) {
  let lastIndex = -1;
  for (const arg of expectedArgs) {
    const index = command.indexOf(arg);
    expect(index).toBeGreaterThan(lastIndex);
    lastIndex = index;
  }
}