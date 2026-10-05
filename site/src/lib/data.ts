/** Fetch + cache JSON, state filter di URL, filter & groupBy fakta di browser. */
// Base path di-set oleh Base.astro (<html data-base>) agar bisa dipasang sebagai sub-path portofolio
const BASE = document.documentElement.dataset.base ?? '';
const cache = new Map<string, Promise<any>>();

export function load<T = any>(name: string): Promise<T> {
  if (!cache.has(name)) {
    cache.set(name, fetch(`${BASE}/${name}`).then((r) => {
      if (!r.ok) throw new Error(`Gagal memuat ${name}`);
      return r.json();
    }));
  }
  return cache.get(name)!;
}

export type Columnar = { cols: string[]; rows: any[][] };
export const toObjects = <T = Record<string, any>>(c: Columnar): T[] =>
  c.rows.map((r) => Object.fromEntries(c.cols.map((k, i) => [k, r[i]])) as T);

export interface FactRow {
  year_month: string; kabupaten: string; model_family: string; payment_type: string; sales_point: string;
  units: number; gross: number; discount: number; net: number;
  stnk_days_sum: number; stnk_n: number; stnk_breach: number;
}

export async function fact(): Promise<FactRow[]> {
  const f = await load<Columnar>('data/fact_monthly.json');
  return toObjects<FactRow>(f);
}

// ---------------------------------------------------------------- filters
export interface Filters { period: string; branch: string; kabupaten: string; type: string; pay: string }
export const FILTER_KEYS: (keyof Filters)[] = ['period', 'branch', 'kabupaten', 'type', 'pay'];
const EMPTY: Filters = { period: '', branch: '', kabupaten: '', type: '', pay: '' };

export function getFilters(): Filters {
  const p = new URLSearchParams(location.search);
  return Object.fromEntries(FILTER_KEYS.map((k) => [k, p.get(k) ?? ''])) as unknown as Filters;
}

export function setFilters(patch: Partial<Filters>) {
  const next = { ...getFilters(), ...patch };
  const p = new URLSearchParams(location.search);
  FILTER_KEYS.forEach((k) => (next[k] ? p.set(k, next[k]) : p.delete(k)));
  const qs = p.toString();
  history.replaceState(null, '', qs ? `?${qs}` : location.pathname);
  window.dispatchEvent(new CustomEvent('filters:change', { detail: next }));
}

export const resetFilters = () => setFilters({ ...EMPTY });

function matchPeriod(ymStr: string, period: string) {
  if (!period) return true;
  if (/^\d{4}$/.test(period)) return ymStr.startsWith(period);
  const m = period.match(/^(\d{4})Q([1-4])$/);
  if (m) {
    const month = Number(ymStr.slice(5, 7));
    return ymStr.startsWith(m[1]) && Math.ceil(month / 3) === Number(m[2]);
  }
  return ymStr === period;
}

export function applyFilters(rows: FactRow[], f: Filters, ignore: (keyof Filters)[] = []) {
  const on = (k: keyof Filters) => f[k] && !ignore.includes(k);
  return rows.filter((r) =>
    (!on('period') || matchPeriod(r.year_month, f.period)) &&
    (!on('branch') || r.sales_point === f.branch) &&
    (!on('kabupaten') || r.kabupaten === f.kabupaten) &&
    (!on('type') || r.model_family === f.type) &&
    (!on('pay') || r.payment_type === f.pay));
}

export interface Agg { units: number; gross: number; discount: number; net: number; stnk_days_sum: number; stnk_n: number; stnk_breach: number; leasing: number }
const zero = (): Agg => ({ units: 0, gross: 0, discount: 0, net: 0, stnk_days_sum: 0, stnk_n: 0, stnk_breach: 0, leasing: 0 });

export function sum(rows: FactRow[]): Agg {
  const a = zero();
  for (const r of rows) {
    a.units += r.units; a.gross += r.gross; a.discount += r.discount; a.net += r.net;
    a.stnk_days_sum += r.stnk_days_sum; a.stnk_n += r.stnk_n; a.stnk_breach += r.stnk_breach;
    if (r.payment_type === 'Leasing') a.leasing += r.units;
  }
  return a;
}

export function groupBy(rows: FactRow[], key: keyof FactRow | ((r: FactRow) => string)): Map<string, Agg> {
  const fn = typeof key === 'function' ? key : (r: FactRow) => String(r[key]);
  const groups = new Map<string, FactRow[]>();
  for (const r of rows) {
    const k = fn(r);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k)!.push(r);
  }
  return new Map([...groups].map(([k, v]) => [k, sum(v)]));
}

export const sortedEntries = (m: Map<string, Agg>, by: keyof Agg = 'units') =>
  [...m.entries()].sort((a, b) => b[1][by] - a[1][by]);

export function debounce<T extends (...a: any[]) => void>(fn: T, ms = 150) {
  let t: number | undefined;
  return (...a: Parameters<T>) => { clearTimeout(t); t = window.setTimeout(() => fn(...a), ms); };
}

export function downloadCsv(filename: string, cols: string[], rows: any[][]) {
  const esc = (v: any) => (v == null ? '' : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  const csv = [cols, ...rows].map((r) => r.map(esc).join(',')).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
