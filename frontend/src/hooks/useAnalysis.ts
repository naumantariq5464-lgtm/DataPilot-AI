import { useState } from 'react'
import api from '../services/api'
import { useAnalysisStore } from '../store/analysisStore'
import type { AnalysisResult, AnalysisHistoryItem } from '../types/analysis'

export function useAnalysis() {
  const {
    currentResult, history, isRunning,
    setResult, setHistory, setRunning, addToHistory,
    clearResult, setRequestId,
  } = useAnalysisStore()
  const [error, setError] = useState<string | null>(null)

  const runAnalysis = async (
    datasetId: string,
    prompt: string,
  ): Promise<AnalysisResult | null> => {
    // Generate a unique ID for this request — lets us ignore stale responses
    const requestId = crypto.randomUUID()

    setRequestId(requestId)
    setRunning(true)
    setError(null)
    setResult(null)

    try {
      const { data } = await api.post<AnalysisResult>('/analysis/run', {
        dataset_id: datasetId,
        prompt,
      })

      // Only update state if this is still the current (latest) request
      const currentId = useAnalysisStore.getState().currentRequestId
      if (requestId !== currentId) {
        console.warn(`[Analysis] Ignoring stale response for request ${requestId}`)
        return null
      }

      setResult(data)
      addToHistory({
        analysis_id: data.analysis_id,
        dataset_id:  data.dataset_id,
        prompt:      data.prompt,
        chart_count: data.charts.length,
        created_at:  data.created_at,
      })
      setRequestId(null)
      return data

    } catch (err) {
      if (requestId === useAnalysisStore.getState().currentRequestId) {
        const msg = err instanceof Error ? err.message : 'Analysis failed. Please try again.'
        setError(msg)
        setRequestId(null)
      }
      return null

    } finally {
      if (requestId === useAnalysisStore.getState().currentRequestId) {
        setRunning(false)
      }
    }
  }

  const fetchHistory = async () => {
    try {
      const { data } = await api.get<AnalysisHistoryItem[]>('/analysis/history')
      setHistory(data)
    } catch {
      // silent — empty history is fine
    }
  }

  const fetchResult = async (analysisId: string): Promise<AnalysisResult | null> => {
    try {
      const { data } = await api.get<AnalysisResult>(`/analysis/${analysisId}`)
      setResult(data)
      return data
    } catch {
      return null
    }
  }

  return {
    currentResult,
    history,
    isRunning,
    error,
    runAnalysis,
    fetchHistory,
    fetchResult,
    clearResult,
  }
}
