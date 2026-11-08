import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import AnalysisResultView from '../AnalysisResult'
import type { AnalysisResult } from '../../../types/analysis'

describe('AnalysisResult - Bug Condition Tests', () => {
  describe('Bug 1: Ranking Display Issue', () => {
    it('should NOT display [object Object] for array statistics', () => {
      // Task 1.1: Exploration test for ranking display
      // EXPECTED TO FAIL on unfixed code
      const mockResult: AnalysisResult = {
        analysis_id: 'test-123',
        dataset_id: 'dataset-456',
        prompt: 'Show rankings',
        insights: 'Analysis complete',
        statistics: {
          rankings: [
            { name: 'Ayesha', value: 22 },
            { name: 'Nauman', value: 20 },
            { name: 'Sara', value: 18 }
          ]
        },
        charts: [],
        execution_time_ms: 1000,
        retry_count: 0,
        created_at: new Date().toISOString()
      }

      const { container } = render(<AnalysisResultView result={mockResult} />)
      const statisticsSection = container.textContent || ''

      // Expected behavior: should format arrays properly
      expect(statisticsSection).not.toContain('[object Object]')
      
      // Should show formatted ranking instead
      expect(statisticsSection).toMatch(/Ayesha.*22/)
      expect(statisticsSection).toMatch(/Nauman.*20/)
    })

    it('should format plain object statistics', () => {
      const mockResult: AnalysisResult = {
        analysis_id: 'test-124',
        dataset_id: 'dataset-456',
        prompt: 'Show metadata',
        insights: 'Analysis complete',
        statistics: {
          metadata: {
            source: 'CSV',
            format: 'Pandas'
          }
        },
        charts: [],
        execution_time_ms: 1000,
        retry_count: 0,
        created_at: new Date().toISOString()
      }

      const { container } = render(<AnalysisResultView result={mockResult} />)
      const statisticsSection = container.textContent || ''

      expect(statisticsSection).not.toContain('[object Object]')
      expect(statisticsSection).toMatch(/source.*CSV/)
    })
  })
})
