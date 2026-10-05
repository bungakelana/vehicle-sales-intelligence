/** ECharts modular + tema dari design tokens + lazy init saat terlihat. */
import * as echarts from 'echarts/core';
import { BarChart, BoxplotChart, HeatmapChart, LineChart, MapChart, PieChart, ScatterChart, TreemapChart } from 'echarts/charts';
import {
  AriaComponent, GridComponent, LegendComponent, MarkAreaComponent, MarkLineComponent, MarkPointComponent,
  TooltipComponent, VisualMapComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([BarChart, BoxplotChart, HeatmapChart, LineChart, MapChart, PieChart, ScatterChart, TreemapChart,
  AriaComponent, GridComponent, LegendComponent, MarkAreaComponent, MarkLineComponent, MarkPointComponent,
  TooltipComponent, VisualMapComponent, CanvasRenderer]);

export { echarts };

export function tokens() {
  const s = getComputedStyle(document.documentElement);
  const v = (n: string) => s.getPropertyValue(`--${n}`).trim();
  return {
    bg: v('bg'), surface: v('surface'), border: v('border'), text: v('text'), muted: v('muted'),
    primary: v('primary'), accent: v('accent'), highlight: v('highlight'), positive: v('positive'),
    negative: v('negative'), grey: v('grey'),
    seq: [v('seq-1'), v('seq-2'), v('seq-3'), v('seq-4'), v('seq-5')],
  };
}

/** Palet kategorikal ≤ 6 (kategori lain digabung "Lainnya" oleh pemanggil). */
export function categorical() {
  const t = tokens();
  return [t.accent, t.highlight, t.positive, '#8E6CC9', '#C25B8C', t.muted];
}

export function base(): echarts.EChartsCoreOption {
  const t = tokens();
  return {
    backgroundColor: 'transparent',
    textStyle: { color: t.text, fontFamily: 'Inter, system-ui, sans-serif' },
    color: categorical(),
    grid: { left: 8, right: 16, top: 28, bottom: 8, containLabel: true },
    tooltip: {
      backgroundColor: t.surface, borderColor: t.border, textStyle: { color: t.text, fontSize: 12 },
      confine: true,
    },
    legend: { textStyle: { color: t.muted }, top: 0, itemWidth: 12, itemHeight: 8 },
    aria: { enabled: true },
  };
}

export function axis(extra: Record<string, unknown> = {}) {
  const t = tokens();
  return {
    axisLine: { lineStyle: { color: t.border } },
    axisTick: { show: false },
    axisLabel: { color: t.muted, fontSize: 11 },
    splitLine: { lineStyle: { color: t.border, type: 'dashed' } },
    nameTextStyle: { color: t.muted, fontSize: 11 },
    ...extra,
  };
}

type Build = () => echarts.EChartsCoreOption | Promise<echarts.EChartsCoreOption>;
interface Handle { update: () => Promise<void>; instance: () => echarts.ECharts | undefined }

const handles: Handle[] = [];

/** Pasang chart ke elemen #id; inisialisasi saat terlihat, re-render saat tema berubah. */
export function chart(id: string, build: Build, onReady?: (c: echarts.ECharts) => void): Handle {
  const el = document.getElementById(id);
  let inst: echarts.ECharts | undefined;
  let visible = false;
  const render = async () => {
    if (!el || !visible) return;
    if (!inst) {
      inst = echarts.init(el, undefined, { renderer: 'canvas' });
      new ResizeObserver(() => inst?.resize()).observe(el);
      onReady?.(inst);
    }
    const opt = await build();
    inst.setOption({ ...base(), ...opt }, { notMerge: true });
    el.parentElement?.querySelector('.skeleton')?.remove();
  };
  if (el) {
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { visible = true; io.disconnect(); render(); }
    }, { rootMargin: '200px' });
    io.observe(el);
  }
  const h = { update: render, instance: () => inst };
  handles.push(h);
  return h;
}

window.addEventListener('theme:change', () => handles.forEach((h) => h.update()));

/** Isi tabel fallback di ChartCard (data-table-for="id"). */
export function table(id: string, cols: string[], rows: (string | number | null)[][], numericFrom = 1) {
  const host = document.querySelector<HTMLElement>(`[data-table-for="${id}"]`);
  if (!host) return;
  const th = cols.map((c, i) => `<th class="${i >= numericFrom ? 'n' : ''}" scope="col">${c}</th>`).join('');
  const tr = rows.map((r) => `<tr>${r.map((v, i) => `<td class="${i >= numericFrom ? 'n' : ''}">${v ?? '–'}</td>`).join('')}</tr>`).join('');
  host.innerHTML = `<table class="data"><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table>`;
  (host as any).__csv = { cols, rows };
}

document.addEventListener('click', (e) => {
  const btn = (e.target as HTMLElement).closest<HTMLButtonElement>('[data-csv-for]');
  if (!btn) return;
  const host = document.querySelector<any>(`[data-table-for="${btn.dataset.csvFor}"]`);
  if (!host?.__csv) return;
  import('./data').then(({ downloadCsv }) => downloadCsv(`${btn.dataset.csvFor}.csv`, host.__csv.cols, host.__csv.rows));
});
