import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import type { ChartData } from '../../../types/analysis'

export default function HorizontalBarView({ chart }: { chart: ChartData }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(280, chart.data.length * 36)}>
      <BarChart data={chart.data} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11, fill: '#666' }} />
        <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#666' }} width={75} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E5E5' }} />
        <Bar dataKey="value" fill="#111111" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
