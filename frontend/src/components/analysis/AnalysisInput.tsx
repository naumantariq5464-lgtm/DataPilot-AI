import { useState, type FormEvent } from 'react'

interface AnalysisInputProps {
  onSubmit:  (prompt: string) => void
  isRunning: boolean
  disabled?: boolean
}

const SUGGESTIONS = [
  'Show me the distribution of key columns',
  'Find outliers and anomalies in the data',
  'Show correlation between numeric columns',
  'Identify top 10 values by frequency',
  'Calculate summary statistics for all columns',
  'Show trends over time',
]

export default function AnalysisInput({ onSubmit, isRunning, disabled }: AnalysisInputProps) {
  const [prompt, setPrompt] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = prompt.trim()
    if (!trimmed || isRunning || disabled) return
    onSubmit(trimmed)
    setPrompt('')
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit}>

        {/* Textarea */}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ask anything about your data… e.g. 'Show me sales trends by month'"
          rows={3}
          disabled={disabled || isRunning}
          className="w-full border border-[#E5E5E5] rounded-xl px-4 py-3
                     text-sm text-[#111] placeholder:text-[#AAAAAA] bg-white
                     focus:outline-none focus:ring-2 focus:ring-[#111]/10 focus:border-[#111]
                     resize-none transition-colors duration-150
                     disabled:opacity-50 disabled:cursor-not-allowed"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit(e as unknown as FormEvent)
            }
          }}
        />

        {/* Bottom row: hint + button */}
        <div className="flex items-center justify-between mt-2.5">
          <p className="text-xs text-[#AAAAAA]">Enter to analyze · Shift+Enter for new line</p>

          <button
            type="submit"
            disabled={!prompt.trim() || isRunning || disabled}
            className="inline-flex items-center gap-2 bg-[#111111] text-white
                       text-sm font-medium px-5 py-2.5 rounded-xl
                       hover:bg-[#333] active:bg-black transition-colors
                       disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
          >
            {isRunning ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Analyzing…
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
                Analyze
              </>
            )}
          </button>
        </div>
      </form>

      {/* Quick suggestions */}
      {!disabled && !isRunning && (
        <div className="flex flex-wrap gap-2 pt-1">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setPrompt(s)}
              className="text-xs px-3 py-1.5 rounded-full
                         border border-[#E5E5E5] bg-white text-[#666]
                         hover:text-[#111] hover:border-[#AAAAAA] hover:bg-[#F5F5F5]
                         transition-colors duration-150"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
