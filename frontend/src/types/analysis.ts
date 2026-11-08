export type ChartType =
  | 'bar'
  | 'horizontal_bar'
  | 'line'
  | 'area'
  | 'pie'
  | 'donut'
  | 'scatter'
  | 'histogram'
  | 'boxplot'
  | 'heatmap'
  | 'grouped_bar'
  | 'correlation_matrix'

export interface ChartData {
  type:    ChartType
  title:   string
  x_label: string
  y_label: string
  data:    Record<string, unknown>[]
}

export interface AnalysisResult {
  analysis_id:       string
  dataset_id:        string
  prompt:            string
  insights:          string
  statistics:        Record<string, unknown>
  charts:            ChartData[]
  execution_time_ms: number
  retry_count:       number
  created_at:        string
}

export interface AnalysisHistoryItem {
  analysis_id: string
  dataset_id:  string
  prompt:      string
  chart_count: number
  created_at:  string
}
