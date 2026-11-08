import { create } from 'zustand'
import type { DatasetListItem, DatasetUploadResponse } from '../types/dataset'
import { useAnalysisStore } from './analysisStore'

interface DatasetState {
  datasets:      DatasetListItem[]
  activeDataset: DatasetUploadResponse | null
  setDatasets:   (datasets: DatasetListItem[]) => void
  setActive:     (dataset: DatasetUploadResponse | null) => void
  addDataset:    (dataset: DatasetListItem) => void
  removeDataset: (id: string) => void
}

export const useDatasetStore = create<DatasetState>((set, get) => ({
  datasets:      [],
  activeDataset: null,
  setDatasets:   (datasets) => set({ datasets }),

  setActive: (activeDataset) => {
    // Clear previous analysis results when a different dataset becomes active
    const prev = get().activeDataset
    const isNewDataset = activeDataset?.dataset_id !== prev?.dataset_id
    if (isNewDataset) {
      useAnalysisStore.getState().clearResult()
    }
    set({ activeDataset })
  },

  addDataset: (dataset) =>
    set((state) => ({ datasets: [dataset, ...state.datasets] })),

  removeDataset: (id) =>
    set((state) => ({
      datasets: state.datasets.filter((d) => d.dataset_id !== id),
      // If the removed dataset was active, clear everything
      ...(state.activeDataset?.dataset_id === id
        ? { activeDataset: null }
        : {}),
    })),
}))
