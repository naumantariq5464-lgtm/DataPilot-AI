import { useState } from 'react'
import api from '../services/api'
import { useDatasetStore } from '../store/datasetStore'
import type { DatasetUploadResponse, DatasetListItem } from '../types/dataset'

export function useDataset() {
  const { datasets, activeDataset, setDatasets, setActive, addDataset, removeDataset } =
    useDatasetStore()
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const uploadCSV = async (file: File): Promise<DatasetUploadResponse | null> => {
    setUploading(true)
    setUploadError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post<DatasetUploadResponse>('/datasets/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      // Add to list summary
      addDataset({
        dataset_id:   data.dataset_id,
        filename:     data.filename,
        row_count:    data.row_count,
        column_count: data.column_count,
        uploaded_at:  new Date().toISOString(),
      })
      setActive(data)
      return data
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
      return null
    } finally {
      setUploading(false)
    }
  }

  const fetchDatasets = async () => {
    setLoading(true)
    try {
      const { data } = await api.get<DatasetListItem[]>('/datasets/')
      setDatasets(data)
    } catch {
      // silent — empty list is fine
    } finally {
      setLoading(false)
    }
  }

  const deleteDataset = async (id: string) => {
    try {
      await api.delete(`/datasets/${id}`)
      removeDataset(id)
      if (activeDataset?.dataset_id === id) setActive(null)
    } catch (err) {
      throw err
    }
  }

  return {
    datasets,
    activeDataset,
    uploading,
    uploadError,
    loading,
    uploadCSV,
    fetchDatasets,
    deleteDataset,
    setActive,
  }
}
