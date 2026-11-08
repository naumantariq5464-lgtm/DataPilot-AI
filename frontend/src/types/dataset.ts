export interface ColumnInfo {
  name:          string
  dtype:         string
  null_count:    number
  sample_values: string[]
}

export interface DatasetUploadResponse {
  dataset_id:    string
  filename:      string
  row_count:     number
  column_count:  number
  columns:       ColumnInfo[]
  preview:       Record<string, unknown>[]
}

export interface DatasetListItem {
  dataset_id:   string
  filename:     string
  row_count:    number
  column_count: number
  uploaded_at:  string
}
