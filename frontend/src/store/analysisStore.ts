import { create } from 'zustand'
import type { AnalysisResult, AnalysisHistoryItem } from '../types/analysis'

interface AnalysisState {
  currentResult:    AnalysisResult | null
  history:          AnalysisHistoryItem[]
  isRunning:        boolean
  currentRequestId: string | null          // race-condition guard
  setResult:        (result: AnalysisResult | null) => void
  setHistory:       (history: AnalysisHistoryItem[]) => void
  setRunning:       (running: boolean) => void
  addToHistory:     (item: AnalysisHistoryItem) => void
  clearResult:      () => void              // called when dataset changes
  setRequestId:     (id: string | null) => void
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  currentResult:    null,
  history:          [],
  isRunning:        false,
  currentRequestId: null,

  setResult:    (currentResult) => set({ currentResult }),
  setHistory:   (history)       => set({ history }),
  setRunning:   (isRunning)     => set({ isRunning }),
  setRequestId: (currentRequestId) => set({ currentRequestId }),

  addToHistory: (item) =>
    set((state) => ({ history: [item, ...state.history] })),

  clearResult: () => set({
    currentResult:    null,
    isRunning:        false,
    currentRequestId: null,
  }),
}))
