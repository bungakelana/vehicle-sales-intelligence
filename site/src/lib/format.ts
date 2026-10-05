const nf0 = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const num = (v: number) => nf0.format(v);
export const num1 = (v: number) => nf1.format(v);

/** Persentase dari proporsi 0–1 → "12,3%" */
export const pct = (v: number, digits = 1) =>
  new Intl.NumberFormat('id-ID', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v * 100) + '%';

/** Rupiah dari nilai dalam juta rupiah → "Rp 1,2 M" / "Rp 350 jt" */
export function rpJt(jt: number): string {
  const abs = Math.abs(jt);
  if (abs >= 1_000_000) return `Rp ${nf1.format(jt / 1_000_000)} T`;
  if (abs >= 1_000) return `Rp ${nf1.format(jt / 1_000)} M`;
  return `Rp ${nf0.format(jt)} jt`;
}

/** Rupiah dari nilai penuh */
export const rp = (v: number) => rpJt(v / 1e6);

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
export const ym = (s: string) => `${MONTHS[Number(s.slice(5, 7)) - 1]} ${s.slice(2, 4)}`;
