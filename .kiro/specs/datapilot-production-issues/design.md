# DataPilot Production Issues Bugfix Design

## Overview

This design addresses five critical production bugs in DataPilot AI that prevent reliable demonstration and user experience. The fixes target: (1) frontend rendering of complex data structures (rankings display as object references), (2) state management during dataset switching (stale analysis persists), (3) race conditions in concurrent analysis requests (outdated results overwrite new ones), (4) insufficient error diagnostics (generic messages hide root causes), and (5) AI system prompt ambiguity (produces unrenderable data structures).

The fix approach maintains a minimal footprint: enhance the frontend statistics renderer to detect and format arrays/objects, add a clear method to the analysis store and invoke it during dataset switching, implement request ID tracking for race condition prevention, enrich error responses with diagnostic details, and refine the AI system prompt to specify consistent data schemas. All existing functionality—authentication, dataset management, chart rendering, and sandbox execution—remains unchanged.

## Glossary

- **Bug_Condition (C)**: The set of conditions that trigger each of the five bugs
- **Property (P)**: The desired behavior when bug conditions are met
- **Preservation**: All existing features and behaviors that must remain unchanged
- **AnalysisResult Component**: Frontend component at `frontend/src/components/analysis/AnalysisResult.tsx` that renders analysis outputs
- **Statistics Rendering**: The logic that converts statistics key-value pairs to displayable strings
- **Dataset Store**: Zustand store at `frontend/src/store/datasetStore.ts` managing dataset list and active dataset
- **Analysis Store**: Zustand store at `frontend/src/store/analysisStore.ts` managing current analysis result and history
- **setActive()**: Dataset store method that sets the active dataset
- **Request ID**: Unique identifier generated for each analysis request to track response ordering
- **Sandbox Service**: Backend service at `backend/app/services/sandbox_service.py` executing Python code in Docker
- **AI Service**: Backend service at `backend/app/services/ai_service.py` generating Python code via Vultr LLM
- **System Prompt**: Instructions given to the AI model defining output format and constraints

## Bug Details

### Bug 1: Ranking Display Issue

The bug manifests when the AI service returns statistics containing JavaScript arrays or objects (such as employee rankings structured as `[{name: "Ayesha", value: 22}, {name: "Nauman", value: 20}]`). The AnalysisResult component's statistics rendering logic converts all values to strings using `String(val)`, which produces `[object Object],[object Object],...` for arrays of objects, making the data unreadable.

**Formal Specification:**
```
FUNCTION isBugCondition_Ranking(statValue)
  INPUT: statValue of type any (value from statistics dictionary)
  OUTPUT: boolean
  
  RETURN (typeof statValue === 'object')
         AND (statValue !== null)
         AND (Array.isArray(statValue) OR isPlainObject(statValue))
         AND displayedText === "[object Object]" OR displayedText.includes("[object Object]")
END FUNCTION
```

### Bug 2: Dataset Switching State Management

The bug manifests when a user uploads or selects a new dataset after running analysis on a previous dataset. The `setActive()` method in the dataset store updates `activeDataset` but does not trigger any cleanup in the analysis store. The `currentResult`, `history`, and `isRunning` states in the analysis store persist from the previous dataset, causing old visualizations and statistics to display in the UI even though a new dataset is active.

**Formal Specification:**
```
FUNCTION isBugCondition_Switching(event)
  INPUT: event of type DatasetSwitchEvent
  OUTPUT: boolean
  
  RETURN event.action === "setActive"
         AND event.newDatasetId !== event.previousDatasetId
         AND analysisStore.currentResult !== null
         AND analysisStore.currentResult.dataset_id === event.previousDatasetId
END FUNCTION
```

### Bug 3: Race Condition in Analysis Requests

The bug manifests when multiple analysis requests are submitted in rapid succession (e.g., user types quickly or clicks "Analyze" multiple times). Each request initiates an independent async operation with no tracking mechanism. If Request A is slow (e.g., 5 seconds) and Request B completes quickly (e.g., 1 second), Request B's result displays first, then Request A's stale result overwrites it after 5 seconds, leaving the user with outdated data.

**Formal Specification:**
```
FUNCTION isBugCondition_RaceCondition(requestSequence)
  INPUT: requestSequence of type Array<AnalysisRequest>
  OUTPUT: boolean
  
  LET req1 = requestSequence[i]
  LET req2 = requestSequence[i+1] WHERE req2.timestamp > req1.timestamp
  
  RETURN req2.completionTime < req1.completionTime
         AND req1.response.timestamp > req2.response.timestamp
         AND analysisStore.currentResult.analysis_id === req1.response.analysis_id
END FUNCTION
```

### Bug 4: Generic Error Messages

The bug manifests when Docker code execution fails. The sandbox service checks for non-empty stderr to construct error messages, but many failure modes (Python exceptions caught and printed to stdout, timeout kills, Docker image issues) do not produce stderr output. The service returns "Code execution failed: No error details available" without including stdout, exit code, or Docker-specific error information, making debugging impossible.

**Formal Specification:**
```
FUNCTION isBugCondition_ErrorMessages(executionResult)
  INPUT: executionResult of type SandboxExecutionResult
  OUTPUT: boolean
  
  RETURN executionResult.exitCode !== 0
         AND executionResult.stderr.trim() === ""
         AND errorMessage === "Code execution failed: No error details available"
         AND NOT errorMessage.includes(executionResult.stdout)
         AND NOT errorMessage.includes(executionResult.exitCode)
END FUNCTION
```

### Bug 5: AI System Prompt Ambiguity

The bug manifests when the AI service system prompt instructs the model to include rankings or complex structures in statistics. The prompt does not specify a schema or format for such structures, leading the model to generate nested arrays of objects (e.g., `{"top_performers": [{name: "...", value: ...}, ...]}`). When these structures reach the frontend, Bug 1's rendering issue displays them as unreadable object references.

**Formal Specification:**
```
FUNCTION isBugCondition_PromptAmbiguity(systemPrompt, generatedCode)
  INPUT: systemPrompt of type string, generatedCode of type string
  OUTPUT: boolean
  
  RETURN systemPrompt.includes("statistics")
         AND NOT systemPrompt.includes("schema for arrays")
         AND NOT systemPrompt.includes("convert arrays to strings")
         AND generatedCode.includes("RESULT = {")
         AND generatedCode.includes("[{")  // nested array of objects
         AND typeof eval(extractResultFromCode(generatedCode)).statistics[key] === 'object'
END FUNCTION
```

### Examples

**Bug 1 - Ranking Display:**
- AI generates: `{"top_performers": [{name: "Ayesha", value: 22}, {name: "Nauman", value: 20}]}`
- Frontend displays: "Top Performers: [object Object],[object Object]"
- Expected: "Top Performers: 1. Ayesha — 22 | 2. Nauman — 20"

**Bug 2 - Dataset Switching:**
- User analyzes "employees.csv" → sees bar chart of salaries
- User uploads "sales.csv" and sets it active
- UI still shows salary bar chart from employees.csv
- Expected: Empty analysis panel ready for new query

**Bug 3 - Race Condition:**
- User submits "show salary distribution" (Request A, takes 5s)
- User immediately submits "count departments" (Request B, takes 1s)
- Request B completes first, shows department count chart
- Request A completes 4s later, replaces department chart with salary distribution
- Expected: Only Request B's result displays (latest request wins)

**Bug 4 - Generic Error Messages:**
- AI generates code with syntax error: `df.gropby('dept')` (typo)
- Python traceback goes to stdout (not stderr)
- User sees: "Code execution failed: No error details available"
- Expected: "Code execution failed: AttributeError: 'DataFrame' object has no attribute 'gropby'"

**Bug 5 - AI System Prompt:**
- System prompt says "include rankings in statistics"
- AI generates: `RESULT = {"statistics": {"rankings": [{name: "...", value: ...}]}}`
- Combines with Bug 1 to produce unreadable output
- Expected: AI generates string format `"rankings": "1. Ayesha (22) | 2. Nauman (20)"` or frontend handles arrays

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Mouse clicks on buttons, form submissions, and all UI interactions must continue to work exactly as before
- Authentication via Firebase including token validation and session management must remain unchanged
- Dataset upload, validation, parsing, and storage must continue to function identically
- All chart types (bar, line, scatter, pie, donut, area, histogram, boxplot, heatmap, grouped_bar) must render correctly
- Docker sandbox security limits (CPU, memory, network isolation, timeouts) must remain enforced
- AI code generation for successful analysis requests must produce equivalent code quality
- Analysis history tracking and display must continue to work
- Dataset preview showing first 5 rows must remain unchanged
- Protected endpoints requiring authentication must continue to enforce authorization
- Loading indicators during analysis execution must continue to display
- Export functionality for charts must continue to work

**Scope:**
All inputs that do NOT involve (1) statistics containing arrays/objects, (2) dataset switching with existing analysis, (3) concurrent analysis requests, (4) execution failures, or (5) AI-generated complex statistics should be completely unaffected by this fix. This includes:
- Successful analysis requests that return scalar statistics only
- Single analysis requests without concurrency
- Dataset operations without prior analysis results
- Successful code executions that produce valid JSON
- All non-analysis features (authentication, file upload, chart interactions)

## Hypothesized Root Cause

Based on the bug descriptions and code review, the root causes are:

### Bug 1: Ranking Display Issue
1. **Naive Type Coercion**: The AnalysisResult component uses `String(val)` for all statistics values, which invokes JavaScript's default `toString()` method on objects, producing `"[object Object]"`.
2. **No Type Detection**: The rendering logic only checks `typeof val === 'number'` and treats everything else as a simple string, failing to handle arrays or plain objects.
3. **Missing Array Formatting**: No code exists to iterate over array elements and format them as a readable list.

### Bug 2: Dataset Switching State Management
1. **Incomplete Store Coupling**: The dataset store and analysis store operate independently with no inter-store communication.
2. **Missing Clear Logic**: The `setActive()` method updates `activeDataset` but does not invoke any cleanup method on the analysis store.
3. **No Clear Method**: The analysis store lacks a `clearResult()` or `reset()` method that would allow external calls to reset its state.

### Bug 3: Race Condition in Analysis Requests
1. **No Request Tracking**: The frontend does not generate or track unique request IDs for analysis operations.
2. **No Response Validation**: The analysis API response handler updates `currentResult` immediately upon receiving any response without checking if it's still relevant.
3. **No Cancellation Mechanism**: Previous requests continue processing even when new requests are initiated.

### Bug 4: Generic Error Messages
1. **Stderr-Only Error Handling**: The sandbox service checks `if stderr.strip()` and returns a generic message when stderr is empty, ignoring stdout which often contains Python tracebacks.
2. **Missing Diagnostic Fields**: Error responses do not include exit code, stdout content, or Docker-specific errors (ImageNotFound, timeout details).
3. **Incomplete Timeout Handling**: The timeout exception handler returns a generic message without including which timeout limit was hit or partial stdout.

### Bug 5: AI System Prompt Ambiguity
1. **Schema-Free Instructions**: The system prompt tells the AI to include rankings in statistics but does not specify whether they should be strings, arrays, or objects.
2. **No Frontend Contract**: No documented schema exists between the AI service and frontend defining supported data types for statistics values.
3. **Conflicting Instructions**: The prompt says "assign to statistics" (implying structured data) but the frontend only handles scalars and strings.

## Correctness Properties

Property 1: Bug Condition - Statistics Rendering for Complex Data

_For any_ analysis result where statistics contain arrays or plain objects (isBugCondition_Ranking returns true), the fixed AnalysisResult component SHALL detect the data type and render arrays as numbered lists with formatted items (e.g., "1. Ayesha — 22") and objects as key-value pairs, producing human-readable output instead of "[object Object]".

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Bug Condition - Dataset Switching Clears Analysis

_For any_ dataset switch event where a previous analysis result exists (isBugCondition_Switching returns true), the fixed setActive() method SHALL invoke the analysis store's clear method, resetting currentResult to null, isRunning to false, and error to null, ensuring a clean slate for the new dataset.

**Validates: Requirements 2.4, 2.5, 2.6**

Property 3: Bug Condition - Race Condition Prevention

_For any_ sequence of analysis requests where a later request completes before an earlier one (isBugCondition_RaceCondition returns true), the fixed analysis handler SHALL generate unique request IDs, track the most recent request ID, and ignore responses that do not match the current request ID, ensuring only the latest result updates the UI.

**Validates: Requirements 2.7, 2.8, 2.9, 2.10**

Property 4: Bug Condition - Detailed Error Messages

_For any_ sandbox execution failure where stderr is empty (isBugCondition_ErrorMessages returns true), the fixed sandbox service SHALL check stdout for error content, include exit code in the error message, check Docker logs for diagnostic information, and categorize the error type (timeout, Python error, Docker issue), providing actionable debugging information.

**Validates: Requirements 2.11, 2.12, 2.13**

Property 5: Bug Condition - AI System Prompt Consistency

_For any_ AI code generation request, the fixed system prompt SHALL specify that statistics values must be either numbers or human-readable strings, instruct the AI to convert arrays/rankings to formatted strings (e.g., "1. Name (value) | 2. Name (value)"), and include an example of proper ranking formatting, ensuring frontend compatibility.

**Validates: Requirements 2.14, 2.15**

Property 6: Preservation - Non-Complex Statistics

_For any_ analysis result where statistics contain only numbers and simple strings (isBugCondition_Ranking returns false), the fixed AnalysisResult component SHALL produce exactly the same rendered output as the original component, preserving display format, truncation behavior, and grid layout.

**Validates: Requirements 3.1, 3.2, 3.3**

Property 7: Preservation - Dataset Operations Without Analysis

_For any_ dataset operation (upload, selection, removal) where no analysis result exists in the analysis store (isBugCondition_Switching returns false), the fixed setActive() method SHALL produce exactly the same behavior as the original method, preserving dataset list updates and activeDataset state changes.

**Validates: Requirements 3.4, 3.5, 3.6**

Property 8: Preservation - Single Analysis Requests

_For any_ single analysis request with no concurrency (isBugCondition_RaceCondition returns false), the fixed analysis handler SHALL produce exactly the same behavior as the original handler, preserving result display, history tracking, and loading states.

**Validates: Requirements 3.9, 3.10, 3.11, 3.12, 3.13**

Property 9: Preservation - Successful Code Execution

_For any_ sandbox execution that completes successfully with exit code 0 and valid JSON output (isBugCondition_ErrorMessages returns false), the fixed sandbox service SHALL produce exactly the same parsed result as the original service, preserving insights, statistics, and charts structure.

**Validates: Requirements 3.9, 3.10**

Property 10: Preservation - Authentication and Authorization

_For any_ authentication or authorization operation, the fixed system SHALL produce exactly the same behavior as the original system, preserving Firebase token validation, session management, and endpoint protection.

**Validates: Requirements 3.7, 3.8**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

#### Fix 1: Frontend Statistics Rendering (AnalysisResult.tsx)

**File**: `frontend/src/components/analysis/AnalysisResult.tsx`

**Function**: Statistics rendering logic in the `stats.map()` callback

**Specific Changes**:
1. **Add Type Detection**: Before the existing `typeof val === 'number'` check, add checks for `Array.isArray(val)` and plain objects
2. **Array Formatting**: When `val` is an array, iterate over elements:
   - If elements are objects with `name` and `value` properties: format as "1. Name — Value"
   - If elements are primitives: format as bulleted list
   - Join formatted items with " | " separator
3. **Object Formatting**: When `val` is a plain object (not array, not null):
   - Convert to entries and format as "Key: Value" pairs
   - Join with " | " separator
4. **Preserve Existing Logic**: Keep number formatting (toLocaleString, toFixed) and string truncation unchanged
5. **Helper Function**: Add `isPlainObject(val)` helper to distinguish plain objects from arrays/null/dates

**Implementation Approach**:
```typescript
// Add before stats.map()
const formatComplexValue = (val: any): string => {
  if (Array.isArray(val)) {
    if (val.length === 0) return "[]"
    // Check if array of objects with name/value
    if (typeof val[0] === 'object' && val[0] !== null && 'name' in val[0]) {
      return val.map((item, i) => 
        `${i+1}. ${item.name}${item.value !== undefined ? ` — ${item.value}` : ''}`
      ).join(" | ")
    }
    // Array of primitives
    return val.map((item, i) => `${i+1}. ${String(item)}`).join(" | ")
  }
  if (val !== null && typeof val === 'object' && !Array.isArray(val)) {
    // Plain object
    return Object.entries(val).map(([k, v]) => `${k}: ${v}`).join(" | ")
  }
  return String(val)
}

// In stats.map(), update displayVal logic:
const displayVal = typeof val === 'number'
  ? (Number.isInteger(val) ? val.toLocaleString() : Number(val).toFixed(2))
  : (Array.isArray(val) || (val !== null && typeof val === 'object'))
    ? formatComplexValue(val)
    : String(val)
```

#### Fix 2: Dataset Store Clear Integration (datasetStore.ts + analysisStore.ts)

**File**: `frontend/src/store/analysisStore.ts`

**Function**: Add `clearResult()` method

**Specific Changes**:
1. **Add Clear Method**: Add a new method `clearResult: () => void` to the store interface
2. **Implementation**: `clearResult: () => set({ currentResult: null, isRunning: false, error: null })`
3. **Export**: Ensure the method is accessible to other stores

**File**: `frontend/src/store/datasetStore.ts`

**Function**: `setActive()` method

**Specific Changes**:
1. **Import Analysis Store**: Add `import { useAnalysisStore } from './analysisStore'`
2. **Call Clear Method**: Inside `setActive`, after `set({ activeDataset })`, call `useAnalysisStore.getState().clearResult()`
3. **Conditional Clearing**: Only clear if `activeDataset?.dataset_id !== state.activeDataset?.dataset_id` to avoid unnecessary clears

**Implementation Approach**:
```typescript
// analysisStore.ts
interface AnalysisState {
  // ... existing fields
  clearResult: () => void
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  // ... existing fields
  clearResult: () => set({ currentResult: null, isRunning: false, error: null }),
}))

// datasetStore.ts
import { useAnalysisStore } from './analysisStore'

setActive: (activeDataset) => {
  set((state) => {
    const isChanged = activeDataset?.dataset_id !== state.activeDataset?.dataset_id
    if (isChanged) {
      useAnalysisStore.getState().clearResult()
    }
    return { activeDataset }
  })
}
```

#### Fix 3: Request ID Tracking (analysisStore.ts + API call site)

**File**: `frontend/src/store/analysisStore.ts`

**Function**: Add request ID tracking

**Specific Changes**:
1. **Add State Field**: Add `currentRequestId: string | null` to the state interface
2. **Add Setter**: Add `setRequestId: (id: string | null) => void` method
3. **Update Interface**: Export the new fields and methods

**File**: Location where analysis API is called (likely `AnalysisInput.tsx` or similar)

**Function**: Analysis submission handler

**Specific Changes**:
1. **Generate Request ID**: Before API call, generate UUID: `const requestId = crypto.randomUUID()`
2. **Store Request ID**: Call `setRequestId(requestId)` before making the API request
3. **Response Validation**: After receiving response, check `if (requestId === useAnalysisStore.getState().currentRequestId)`
4. **Ignore Stale**: If IDs don't match, log warning and skip `setResult()` call
5. **Clear on Error**: Set `currentRequestId` to null after successful update or error

**Implementation Approach**:
```typescript
// analysisStore.ts
interface AnalysisState {
  // ... existing
  currentRequestId: string | null
  setRequestId: (id: string | null) => void
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  // ... existing
  currentRequestId: null,
  setRequestId: (currentRequestId) => set({ currentRequestId }),
}))

// In API call site (e.g., AnalysisInput.tsx handleAnalyze)
const handleAnalyze = async () => {
  const requestId = crypto.randomUUID()
  setRequestId(requestId)
  setRunning(true)
  
  try {
    const response = await fetch(...)
    const result = await response.json()
    
    // Validate request is still current
    if (requestId !== useAnalysisStore.getState().currentRequestId) {
      console.warn(`Ignoring stale response for request ${requestId}`)
      return
    }
    
    setResult(result)
    setRequestId(null)
  } catch (err) {
    if (requestId === useAnalysisStore.getState().currentRequestId) {
      // handle error
      setRequestId(null)
    }
  } finally {
    if (requestId === useAnalysisStore.getState().currentRequestId) {
      setRunning(false)
    }
  }
}
```

#### Fix 4: Enhanced Sandbox Error Handling (sandbox_service.py)

**File**: `backend/app/services/sandbox_service.py`

**Function**: `_run_docker_container()` error handling section

**Specific Changes**:
1. **Check Stdout on Empty Stderr**: After `if exit_code != 0`, check `if not stderr.strip() and stdout.strip()`
2. **Include Exit Code**: Add exit code to all error messages: `f"Code execution failed (exit {exit_code}):\n..."`
3. **Parse Stdout for Errors**: Look for Python traceback patterns in stdout (lines starting with "Traceback", "Error:", "Exception:")
4. **Timeout Error Details**: In the timeout exception handler, include partial stdout: `f"Execution timed out after {settings.sandbox_timeout_seconds}s. Partial output:\n{stdout[:500]}"`
5. **Docker Error Categorization**: In the except blocks, distinguish ImageNotFound, ContainerError, APIError and provide specific messages
6. **Structured Error Response**: Add optional fields to error dict: `exit_code`, `stdout_preview`, `error_type`

**Implementation Approach**:
```python
# In _run_docker_container after getting stdout/stderr

if exit_code != 0:
    # Check stdout if stderr is empty
    error_detail = stderr.strip()
    if not error_detail and stdout.strip():
        # Look for Python tracebacks in stdout
        stdout_lines = stdout.strip().splitlines()
        traceback_start = -1
        for i, line in enumerate(stdout_lines):
            if line.startswith("Traceback"):
                traceback_start = i
                break
        if traceback_start >= 0:
            error_detail = "\n".join(stdout_lines[traceback_start:])
        else:
            error_detail = stdout.strip()[:800]
    
    if not error_detail:
        error_detail = "No error output captured"
    
    return {
        "success": False,
        "insights": "",
        "statistics": {},
        "charts": [],
        "error": f"Code execution failed (exit {exit_code}):\n{error_detail}",
        "exit_code": exit_code,
        "stdout_preview": stdout[:300] if stdout else "",
    }

# In timeout exception handler
except Exception:
    container.kill()
    container.remove(force=True)
    stdout_partial = ""
    try:
        stdout_partial = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")[:500]
    except:
        pass
    
    return {
        "success": False,
        "insights": "",
        "statistics": {},
        "charts": [],
        "error": f"Execution timed out after {settings.sandbox_timeout_seconds}s.\nPartial output:\n{stdout_partial}",
        "error_type": "timeout",
    }
```

#### Fix 5: AI System Prompt Schema Specification (ai_service.py)

**File**: `backend/app/services/ai_service.py`

**Constant**: `_CODE_SYSTEM_PROMPT`

**Specific Changes**:
1. **Add Statistics Schema Section**: After the RESULT structure example, add a new section "STATISTICS VALUE TYPES:"
2. **Specify Allowed Types**: "Statistics values MUST be either numbers or human-readable strings. Do NOT use arrays or objects."
3. **Ranking Format Instruction**: "For rankings/lists, convert to string format: '1. Name (value) | 2. Name (value) | ...'"
4. **Provide Example**: Show example of proper ranking formatting
5. **Emphasize Conversion**: Add instruction to use `.tolist()` for numpy arrays and convert to string before assignment

**Implementation Approach**:
```python
_CODE_SYSTEM_PROMPT = """You are an expert Python data analyst. Your job is to write clean, executable Python code to analyze CSV datasets.

# ... existing content ...

5. At the end, assign a variable called RESULT with this exact structure:

RESULT = {
    "insights": "A clear, human-readable explanation of what was found (2-4 sentences)",
    "statistics": {
        "key_metric": value,
        "another_metric": value
    },
    "charts": [...]
}

STATISTICS VALUE TYPES (CRITICAL):
- Statistics values MUST be either numbers (int/float) or human-readable strings
- Do NOT assign arrays, lists, or objects to statistics keys
- For rankings/top-N lists, convert to formatted string:
  
  Example — CORRECT:
  top_employees = df.nlargest(3, 'sales')
  ranking_str = " | ".join([f"{i+1}. {row['name']} ({row['sales']})" 
                            for i, row in enumerate(top_employees.itertuples())])
  RESULT["statistics"]["top_performers"] = ranking_str
  
  Example — INCORRECT (will cause rendering issues):
  RESULT["statistics"]["top_performers"] = [{"name": "...", "value": ...}]  # NO!
  
- If you have a list/array to display, convert it to a string before assigning

# ... rest of existing content ...
"""
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate each bug on unfixed code, then verify the fixes work correctly and preserve existing behavior. Each bug will be tested independently to isolate failures and confirm root cause hypotheses.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate each bug BEFORE implementing fixes. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate each bug condition on the UNFIXED code to observe failures and understand root causes. Run tests sequentially to avoid interference.

**Test Cases**:

1. **Bug 1 - Ranking Display Test**: 
   - Create a mock analysis result with `statistics: { rankings: [{name: "Ayesha", value: 22}, {name: "Nauman", value: 20}] }`
   - Render AnalysisResult component with this data
   - Assert that rendered text contains "[object Object]" (will fail on unfixed code, confirming the bug)
   - Expected counterexample: Display shows unreadable object references

2. **Bug 2 - Dataset Switching Test**:
   - Set up initial state: dataset A active, analysis result from dataset A in store
   - Call `setActive(datasetB)`
   - Assert that `currentResult` is null after switch (will fail on unfixed code)
   - Expected counterexample: Previous analysis result persists after dataset switch

3. **Bug 3 - Race Condition Test**:
   - Mock API with delayed responses: Request A (2000ms delay), Request B (100ms delay)
   - Submit Request A, then immediately submit Request B
   - Wait for both to complete
   - Assert that `currentResult.analysis_id === requestB.analysis_id` (will fail on unfixed code if Request A overwrites)
   - Expected counterexample: Stale Request A result overwrites newer Request B result

4. **Bug 4 - Error Message Test**:
   - Mock sandbox execution that returns `exit_code=1`, `stderr=""`, `stdout="Traceback: AttributeError: ..."`
   - Call sandbox service
   - Assert error message includes "AttributeError" (will fail on unfixed code showing generic message)
   - Expected counterexample: Generic "No error details available" message despite traceback in stdout

5. **Bug 5 - AI Prompt Test**:
   - Create test prompt requesting rankings: "Show top 3 employees by sales"
   - Mock AI service to generate code that assigns array of objects to statistics
   - Execute generated code
   - Verify that AI produces array structure (confirms ambiguity in system prompt)
   - Expected counterexample: AI generates `RESULT["statistics"]["top_3"] = [{...}, {...}]`

### Fix Checking

**Goal**: Verify that for all inputs where bug conditions hold, the fixed functions produce the expected behavior.

**Pseudocode:**

```
# Bug 1: Ranking Display
FOR ALL statValue WHERE isBugCondition_Ranking(statValue) DO
  renderedText := renderStatistic_fixed(statValue)
  ASSERT NOT renderedText.includes("[object Object]")
  ASSERT renderedText.includes("1.") AND renderedText.includes("—")
END FOR

# Bug 2: Dataset Switching
FOR ALL event WHERE isBugCondition_Switching(event) DO
  setActive_fixed(event.newDatasetId)
  ASSERT analysisStore.currentResult === null
  ASSERT analysisStore.isRunning === false
END FOR

# Bug 3: Race Condition
FOR ALL requestSequence WHERE isBugCondition_RaceCondition(requestSequence) DO
  results := executeAnalysisRequests_fixed(requestSequence)
  ASSERT results.displayedResult.requestId === max(requestSequence.map(r => r.requestId))
END FOR

# Bug 4: Error Messages
FOR ALL execResult WHERE isBugCondition_ErrorMessages(execResult) DO
  errorResponse := handleSandboxError_fixed(execResult)
  ASSERT errorResponse.error.includes(execResult.exitCode)
  ASSERT (execResult.stdout.trim() === "" OR errorResponse.error.includes(execResult.stdout))
END FOR

# Bug 5: AI Prompt
FOR ALL prompt WHERE prompt.includes("ranking") OR prompt.includes("top") DO
  generatedCode := generateCode_fixed(prompt)
  resultStructure := extractResultStructure(generatedCode)
  FOR ALL key IN resultStructure.statistics DO
    value := resultStructure.statistics[key]
    ASSERT typeof value === 'number' OR typeof value === 'string'
  END FOR
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where bug conditions do NOT hold, the fixed functions produce the same results as the original functions.

**Pseudocode:**

```
# Bug 1: Simple Statistics
FOR ALL statValue WHERE NOT isBugCondition_Ranking(statValue) DO
  ASSERT renderStatistic_original(statValue) === renderStatistic_fixed(statValue)
END FOR

# Bug 2: Dataset Operations Without Analysis
FOR ALL event WHERE NOT isBugCondition_Switching(event) DO
  originalState := captureDatasetStoreState()
  setActive_fixed(event.newDatasetId)
  fixedState := captureDatasetStoreState()
  
  setActive_original(event.newDatasetId)
  originalResultState := captureDatasetStoreState()
  
  ASSERT fixedState === originalResultState
END FOR

# Bug 3: Single Analysis Requests
FOR ALL request WHERE isSingleRequest(request) DO
  resultOriginal := executeAnalysis_original(request)
  resultFixed := executeAnalysis_fixed(request)
  ASSERT resultOriginal.analysis_id === resultFixed.analysis_id
  ASSERT resultOriginal.insights === resultFixed.insights
END FOR

# Bug 4: Successful Execution
FOR ALL execResult WHERE execResult.exitCode === 0 DO
  ASSERT parseSandboxOutput_original(execResult) === parseSandboxOutput_fixed(execResult)
END FOR

# Bug 5: Code Generation Quality
FOR ALL prompt WHERE isValidAnalysisPrompt(prompt) DO
  codeOriginal := generateCode_original(prompt)
  codeFixed := generateCode_fixed(prompt)
  
  resultOriginal := executeSandbox(codeOriginal)
  resultFixed := executeSandbox(codeFixed)
  
  IF resultOriginal.success AND resultFixed.success THEN
    ASSERT resultFixed.insights.length > 0
    ASSERT resultFixed.statistics.size > 0 OR resultFixed.charts.length > 0
  END IF
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss (e.g., deeply nested objects, very long arrays, special characters in rankings)
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs
- For frontend rendering, it can generate random statistics dictionaries with various data types
- For state management, it can generate random sequences of dataset operations
- For concurrency, it can generate random request timings and delays

**Test Plan**: Observe behavior on UNFIXED code first for each preservation scenario, then write property-based tests capturing that behavior. Run tests with 100+ generated examples to ensure statistical confidence.

**Test Cases**:

1. **Scalar Statistics Preservation**:
   - Generate 100 random statistics objects containing only numbers and simple strings
   - Render with both original and fixed components
   - Assert pixel-perfect match of rendered output

2. **Dataset Operations Preservation**:
   - Generate random sequences of dataset additions, removals, and selections
   - Execute on both original and fixed stores
   - Assert identical final state

3. **Single Request Preservation**:
   - Generate random valid analysis prompts
   - Execute one at a time with sufficient delay
   - Assert identical analysis results

4. **Successful Execution Preservation**:
   - Generate valid Python code that produces correct JSON
   - Execute in sandbox with both original and fixed error handlers
   - Assert identical parsed results

5. **Authentication Preservation**:
   - Run existing authentication test suite
   - Assert all tests pass with no changes to behavior

### Unit Tests

**Bug 1 Tests**:
- Test array of objects with name/value properties renders as numbered list
- Test array of primitives renders as bulleted list
- Test plain object renders as key-value pairs
- Test null and undefined values don't crash renderer
- Test empty arrays render as "[]"

**Bug 2 Tests**:
- Test `clearResult()` method resets all analysis store fields
- Test `setActive()` calls `clearResult()` when dataset ID changes
- Test `setActive()` does not call `clearResult()` when dataset ID is unchanged
- Test analysis store state after dataset switch

**Bug 3 Tests**:
- Test `crypto.randomUUID()` generates unique IDs
- Test request ID is stored before API call
- Test stale responses are ignored (log warning, don't update state)
- Test current responses update state normally
- Test request ID is cleared after successful update

**Bug 4 Tests**:
- Test error message includes exit code for non-zero exits
- Test stdout is checked when stderr is empty
- Test Python traceback extraction from stdout
- Test timeout error includes partial stdout
- Test Docker ImageNotFound error is caught and reported

**Bug 5 Tests**:
- Test system prompt includes statistics schema section
- Test system prompt includes ranking format example
- Test generated code follows schema (mock AI responses)
- Test statistics values are numbers or strings (no arrays/objects)

### Property-Based Tests

**Bug 1 PBT**:
- Generate random nested data structures (arrays, objects, mixed types)
- Test that no "[object Object]" appears in rendered output
- Test that all array elements are present in output string
- Test that output length is reasonable (not truncated unexpectedly)

**Bug 2 PBT**:
- Generate random dataset switching sequences
- Test that after every switch, analysis store is cleared
- Test that dataset store state is correct after every switch

**Bug 3 PBT**:
- Generate random sequences of overlapping requests with random delays
- Test that final displayed result always matches the last-initiated request
- Test that no intermediate stale results remain visible

**Bug 4 PBT**:
- Generate random Python code errors (syntax, runtime, logical)
- Test that error messages always contain actionable information
- Test that error messages never show "No error details available" when details exist

**Bug 5 PBT**:
- Generate random analysis prompts requesting rankings, lists, or top-N
- Test that generated code always produces statistics values as numbers or strings
- Test that AI follows the schema specification consistently

### Integration Tests

**Full Flow Test with Ranking Bug**:
- Upload a CSV with employee data
- Submit prompt: "Show top 5 employees by sales"
- Verify AI generates code that produces string-formatted rankings
- Verify frontend displays formatted list (not object references)
- Verify charts render correctly alongside rankings

**Dataset Switching Flow Test**:
- Upload and analyze dataset A (produces results)
- Upload dataset B
- Set dataset B as active
- Verify analysis panel is empty
- Submit new analysis on dataset B
- Verify results are from dataset B only

**Concurrent Analysis Test**:
- Submit analysis request A (slow query)
- Wait 500ms
- Submit analysis request B (fast query)
- Verify only result B displays
- Check browser console for "Ignoring stale response" log

**Error Handling Flow Test**:
- Submit analysis with intentionally broken prompt (to trigger Python error)
- Verify error message contains specific Python exception details
- Verify error message includes exit code
- Verify error is actionable for debugging

**End-to-End Preservation Test**:
- Run full authentication flow
- Upload dataset, run successful analysis
- Export chart
- Verify all existing features work identically to unfixed version
