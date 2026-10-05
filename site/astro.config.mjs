import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [tailwind({ applyBaseStyles: false })],
  vite: { optimizeDeps: { include: ['echarts/core', 'echarts/charts', 'echarts/components', 'echarts/renderers'] } },
  // base: '/projects/sales-intelligence', // aktifkan jika dipasang sebagai sub-path portofolio
});
