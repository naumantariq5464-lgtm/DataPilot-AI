import type { ChartData } from '../../types/analysis'
import BarChartView      from './types/BarChartView'
import HorizontalBarView from './types/HorizontalBarView'
import LineChartView     from './types/LineChartView'
import AreaChartView     from './types/AreaChartView'
import PieChartView      from './types/PieChartView'
import DonutChartView    from './types/DonutChartView'
import ScatterChartView  from './types/ScatterChartView'
import HistogramView     from './types/HistogramView'
import BoxPlotView       from './types/BoxPlotView'
import HeatmapView       from './types/HeatmapView'
import GroupedBarView    from './types/GroupedBarView'

interface Props { chart: ChartData }

export default function ChartRenderer({ chart }: Props) {
  if (!chart.data?.length) {
    return (
      <div className="bg-white border border-[#EBEBEB] rounded-2xl p-8 flex items-center justify-center">
        <p className="text-sm text-[#999]">No chart data available</p>
      </div>
    )
  }

  const render = () => {
    switch (chart.type) {
      case 'bar':                return <BarChartView chart={chart} />
      case 'horizontal_bar':     return <HorizontalBarView chart={chart} />
      case 'line':               return <LineChartView chart={chart} />
      case 'area':               return <AreaChartView chart={chart} />
      case 'pie':                return <PieChartView chart={chart} />
      case 'donut':              return <DonutChartView chart={chart} />
      case 'scatter':            return <ScatterChartView chart={chart} />
      case 'histogram':          return <HistogramView chart={chart} />
      case 'boxplot':            return <BoxPlotView chart={chart} />
      case 'heatmap':            return <HeatmapView chart={chart} />
      case 'grouped_bar':        return <GroupedBarView chart={chart} />
      case 'correlation_matrix': return <HeatmapView chart={chart} />
      default:                   return <BarChartView chart={chart} />
    }
  }

  return (
    <div className="bg-white border border-[#EBEBEB] rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#F5F5F5]">
        <h3 className="text-sm font-semibold text-[#111]">{chart.title}</h3>
        {(chart.x_label || chart.y_label) && (
          <p className="text-xs text-[#999] mt-0.5">
            {[chart.x_label, chart.y_label].filter(Boolean).join(' · ')}
          </p>
        )}
      </div>
      {/* Chart */}
      <div className="p-4">{render()}</div>
    </div>
  )
}
