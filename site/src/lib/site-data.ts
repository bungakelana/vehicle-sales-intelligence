/** Baca JSON hasil export Python saat build/SSR (dipakai di frontmatter Astro). */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export function readData<T = any>(name: string): T {
  return JSON.parse(readFileSync(join(process.cwd(), 'public', 'data', name), 'utf-8'));
}
