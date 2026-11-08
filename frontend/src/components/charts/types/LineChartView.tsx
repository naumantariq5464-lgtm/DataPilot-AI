import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Dot,
} from 'recharts'
import type { ChartData } from '../../../types/analysis'

export default function LineChartView({ chart }: { chart: ChartData }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chart.data} margin={{ top: 5, right: 20, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#666' }} angle={-30} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11, fill: '#666' }} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E5E5' }} />
        <Line
          type="monotone" dataKey="value" stroke="#111111" strokeWidth={2}
          dot={<Dot r={3} fill="#111111" />} activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
