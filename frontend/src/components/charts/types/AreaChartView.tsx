import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import type { ChartData } from '../../../types/analysis'

export default function AreaChartView({ chart }: { chart: ChartData }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={chart.data} margin={{ top: 5, right: 20, left: 0, bottom: 40 }}>
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#111111" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#111111" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#666' }} angle={-30} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11, fill: '#666' }} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E5E5' }} />
        <Area type="monotone" dataKey="value" stroke="#111111" strokeWidth={2} fill="url(#areaGrad)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}
