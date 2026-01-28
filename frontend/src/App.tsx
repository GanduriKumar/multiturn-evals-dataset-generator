import { useEffect, useMemo, useState } from 'react'

type VerticalConfig = {
  workflows: string[]
  behaviours: string[]
  axes: Record<string, string[]>
}

const VERTICALS = [
  { value: 'commerce', label: 'Commerce' },
  { value: 'banking', label: 'Banking' },
  { value: 'insurance', label: 'Insurance' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'retail', label: 'Retail' },
  { value: 'telecom', label: 'Telecom' },
]

const NAV_PAGES = ['Home', 'Settings', 'Generate', 'Scoring']
const BRAND_COLORS = ['#4285F4', '#EA4335', '#FBBC05', '#34A853']

function App() {
  const [activePage, setActivePage] = useState('Home')
  const [vertical, setVertical] = useState('commerce')
  const [config, setConfig] = useState<VerticalConfig | null>(null)
  const [selectedWorkflows, setSelectedWorkflows] = useState<string[]>([])
  const [selectedBehaviours, setSelectedBehaviours] = useState<string[]>([])
  const [axesSelections, setAxesSelections] = useState<Record<string, string>>({})
  const [generatedDatasets] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [presetName, setPresetName] = useState('')
  const [presetNames, setPresetNames] = useState<string[]>([])

  useEffect(() => {
    let isMounted = true
    const loadConfig = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await fetch(`/config/verticals/${vertical}`)
        if (!response.ok) {
          throw new Error(`Failed to load config (${response.status})`)
        }
        const payload = (await response.json()) as VerticalConfig
        if (!isMounted) return
        setConfig(payload)
        setSelectedWorkflows([])
        setSelectedBehaviours([])
        const defaults: Record<string, string> = {}
        Object.entries(payload.axes ?? {}).forEach(([axis, values]) => {
          defaults[axis] = values[0] ?? ''
        })
        setAxesSelections(defaults)
      } catch (err) {
        if (!isMounted) return
        setError(err instanceof Error ? err.message : 'Unknown error')
        setConfig(null)
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadConfig()
    return () => {
      isMounted = false
    }
  }, [vertical])

  const axesEntries = useMemo(() => Object.entries(config?.axes ?? {}), [config])

  const toggleSelection = (
    value: string,
    list: string[],
    setter: (next: string[]) => void,
  ) => {
    setter(list.includes(value) ? list.filter((item) => item !== value) : [...list, value])
  }

  const pageSubtitle: Record<string, string> = {
    Home: 'Overview of your current configuration and progress.',
    Settings: 'Configure defaults for dataset generation.',
    Generate: 'Pick a vertical to load workflows, behaviours, and axes.',
    Scoring: 'Upload outputs to score model performance.',
  }

  const activeNavColor = BRAND_COLORS[NAV_PAGES.indexOf(activePage) % BRAND_COLORS.length]

  const previewPayload = useMemo(
    () => ({
      vertical,
      workflows: selectedWorkflows,
      behaviours: selectedBehaviours,
      axes: axesSelections,
    }),
    [axesSelections, selectedBehaviours, selectedWorkflows, vertical],
  )

  const presetPrefix = useMemo(() => `eval_preset_${vertical}_`, [vertical])

  const refreshPresetList = () => {
    const keys = Object.keys(localStorage)
      .filter((key) => key.startsWith(presetPrefix))
      .map((key) => key.replace(presetPrefix, ''))
      .sort((a, b) => a.localeCompare(b))
    setPresetNames(keys)
  }

  const savePreset = () => {
    const trimmed = presetName.trim()
    if (!trimmed) return
    const payload = {
      vertical,
      workflows: selectedWorkflows,
      behaviours: selectedBehaviours,
      axes: axesSelections,
    }
    localStorage.setItem(`${presetPrefix}${trimmed}`, JSON.stringify(payload))
    setPresetName('')
    refreshPresetList()
  }

  const loadPreset = (name: string) => {
    const stored = localStorage.getItem(`${presetPrefix}${name}`)
    if (!stored) return
    try {
      const parsed = JSON.parse(stored) as {
        workflows?: string[]
        behaviours?: string[]
        axes?: Record<string, string>
      }
      setSelectedWorkflows(parsed.workflows ?? [])
      setSelectedBehaviours(parsed.behaviours ?? [])
      setAxesSelections(parsed.axes ?? {})
    } catch {
      return
    }
  }

  const deletePreset = (name: string) => {
    localStorage.removeItem(`${presetPrefix}${name}`)
    refreshPresetList()
  }

  useEffect(() => {
    refreshPresetList()
  }, [presetPrefix])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="bg-slate-50 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between rounded-full border border-[#202124] bg-white px-6 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="h-3 w-3 rounded-full bg-[#4285F4]" />
            <span className="text-lg font-semibold text-[#202124]">Eval Dataset Generator</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            {NAV_PAGES.map((page) => (
              <button
                key={page}
                type="button"
                onClick={() => setActivePage(page)}
                className="rounded-full px-3 py-1.5 transition"
                style={
                  activePage === page
                    ? { backgroundColor: activeNavColor, color: '#FFFFFF' }
                    : undefined
                }
              >
                {page}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-6xl px-6 py-8">
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[#5F6368]">{pageSubtitle[activePage]}</p>
            <span className="rounded-full bg-[#E8F0FE] px-3 py-1 text-xs font-medium text-[#4285F4]">
              Active vertical: {vertical}
            </span>
          </div>
        </header>

        {activePage === 'Home' && (
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
              <h2 className="text-sm font-semibold text-[#202124]">Current Vertical</h2>
              <p className="mt-2 text-lg font-semibold text-[#4285F4]">{vertical}</p>
              <p className="mt-1 text-xs text-[#5F6368]">Ready to configure scenarios.</p>
            </div>
            <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
              <h2 className="text-sm font-semibold text-[#202124]">Selections</h2>
              <div className="mt-3 space-y-2 text-sm text-[#5F6368]">
                <div>Workflows: {selectedWorkflows.length}</div>
                <div>Behaviours: {selectedBehaviours.length}</div>
                <div>Axes configured: {Object.keys(axesSelections).length}</div>
              </div>
            </div>
            <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
              <h2 className="text-sm font-semibold text-[#202124]">Next Step</h2>
              <p className="mt-2 text-sm text-[#5F6368]">
                Head to Generate to pick workflows and axes, then build datasets.
              </p>
            </div>
          </div>
        )}

        {activePage === 'Generate' && (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
                <h2 className="text-sm font-semibold text-[#202124]">Vertical</h2>
                <select
                  className="mt-2 w-full rounded border border-[#E5E7EB] bg-white p-2 shadow"
                  value={vertical}
                  onChange={(event) => setVertical(event.target.value)}
                >
                  {VERTICALS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>

                {isLoading && (
                  <p className="mt-3 text-sm text-[#5F6368]">Loading config…</p>
                )}
                {error && <p className="mt-3 text-sm text-[#EA4335]">{error}</p>}
              </div>

              <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
                <h2 className="text-sm font-semibold text-[#202124]">Selected Summary</h2>
                <div className="mt-3 space-y-2 text-sm text-[#5F6368]">
                  <div>Workflows: {selectedWorkflows.length}</div>
                  <div>Behaviours: {selectedBehaviours.length}</div>
                  <div>Axes configured: {Object.keys(axesSelections).length}</div>
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
                <h2 className="text-sm font-semibold text-[#202124]">Workflows</h2>
                <div className="mt-3 grid gap-2">
                  {(config?.workflows ?? []).map((workflow) => (
                    <label
                      key={workflow}
                      className="flex items-center gap-2 text-sm text-[#202124]"
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-gray-300 text-[#4285F4]"
                        checked={selectedWorkflows.includes(workflow)}
                        onChange={() =>
                          toggleSelection(workflow, selectedWorkflows, setSelectedWorkflows)
                        }
                      />
                      <span>{workflow}</span>
                    </label>
                  ))}
                  {!config && (
                    <p className="text-sm text-[#5F6368]">
                      Select a vertical to view workflows.
                    </p>
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
                <h2 className="text-sm font-semibold text-[#202124]">Behaviours</h2>
                <div className="mt-3 grid gap-2">
                  {(config?.behaviours ?? []).map((behaviour) => (
                    <label
                      key={behaviour}
                      className="flex items-center gap-2 text-sm text-[#202124]"
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-gray-300 text-[#4285F4]"
                        checked={selectedBehaviours.includes(behaviour)}
                        onChange={() =>
                          toggleSelection(behaviour, selectedBehaviours, setSelectedBehaviours)
                        }
                      />
                      <span>{behaviour}</span>
                    </label>
                  ))}
                  {!config && (
                    <p className="text-sm text-[#5F6368]">
                      Select a vertical to view behaviours.
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
                <h2 className="text-sm font-semibold text-[#202124]">Axes</h2>
                <div className="mt-3 grid gap-4 md:grid-cols-2">
                  {axesEntries.map(([axis, values]) => (
                    <div key={axis} className="flex flex-col gap-2">
                      <label className="text-sm font-medium text-[#202124]">{axis}</label>
                      <select
                        className="rounded border border-[#E5E7EB] bg-white p-2 shadow-sm"
                        value={axesSelections[axis] ?? ''}
                        onChange={(event) =>
                          setAxesSelections((prev) => ({
                            ...prev,
                            [axis]: event.target.value,
                          }))
                        }
                      >
                        {values.map((value) => (
                          <option key={value} value={value}>
                            {value}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                  {!config && (
                    <p className="text-sm text-[#5F6368]">Select a vertical to view axes.</p>
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-[#202124]">JSON Preview</h2>
                  <span className="rounded-full bg-[#E8F0FE] px-3 py-1 text-xs font-medium text-[#4285F4]">
                    JSON
                  </span>
                </div>
                <pre className="mt-4 max-h-72 overflow-auto rounded bg-gray-900 p-4 text-xs text-green-300">
                  {JSON.stringify(previewPayload, null, 2)}
                </pre>
              </div>
            </div>

            <div className="mt-6 rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-[#202124]">Generated Datasets</h2>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="rounded bg-[#4285F4] px-3 py-1.5 text-xs font-medium text-white"
                    disabled={generatedDatasets.length === 0}
                  >
                    Download JSON
                  </button>
                  <button
                    type="button"
                    className="rounded border border-[#E5E7EB] px-3 py-1.5 text-xs font-medium text-[#202124]"
                    disabled={generatedDatasets.length === 0}
                  >
                    Download CSV
                  </button>
                </div>
              </div>
              <div className="mt-4 space-y-2 text-sm text-[#5F6368]">
                {generatedDatasets.length === 0 && (
                  <p>No datasets generated yet. Generate a run to populate this list.</p>
                )}
                {generatedDatasets.map((dataset) => (
                  <div key={dataset} className="flex items-center justify-between">
                    <span>{dataset}</span>
                    <span className="text-xs text-[#4285F4]">JSON</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
                <h2 className="text-sm font-semibold text-[#202124]">Optional Uploads</h2>
                <div className="mt-3 space-y-3 text-sm text-[#5F6368]">
                  <div>
                    <label className="text-xs font-medium text-[#202124]">Workflow schema</label>
                    <input
                      type="file"
                      className="mt-1 w-full rounded border border-[#E5E7EB] bg-white p-2"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#202124]">Behaviours schema</label>
                    <input
                      type="file"
                      className="mt-1 w-full rounded border border-[#E5E7EB] bg-white p-2"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#202124]">Axes schema</label>
                    <input
                      type="file"
                      className="mt-1 w-full rounded border border-[#E5E7EB] bg-white p-2"
                    />
                  </div>
                </div>
              </div>
              <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
                <h2 className="text-sm font-semibold text-[#202124]">Generate Dataset</h2>
                <p className="mt-3 text-sm text-[#5F6368]">
                  Generate eval and golden datasets for the selected configuration.
                </p>
                <button
                  type="button"
                  className="mt-4 rounded bg-[#4285F4] px-4 py-2 text-sm font-medium text-white hover:bg-[#3367D6]"
                >
                  Generate Dataset
                </button>
              </div>
            </div>
          </>
        )}

        {activePage === 'Settings' && (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
              <h2 className="text-sm font-semibold text-[#202124]">Defaults</h2>
              <div className="mt-3 space-y-3 text-sm text-[#5F6368]">
                <div>
                  <label className="text-xs font-medium text-[#202124]">Language</label>
                  <select className="mt-1 w-full rounded border border-[#E5E7EB] bg-white p-2">
                    <option>en-US</option>
                    <option>en-GB</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-[#202124]">Channel</label>
                  <select className="mt-1 w-full rounded border border-[#E5E7EB] bg-white p-2">
                    <option>web</option>
                    <option>mobile</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
              <h2 className="text-sm font-semibold text-[#202124]">Presets</h2>
              <p className="mt-3 text-sm text-[#5F6368]">
                Save and load preset configurations per vertical.
              </p>
              <div className="mt-4 space-y-3">
                <input
                  type="text"
                  value={presetName}
                  onChange={(event) => setPresetName(event.target.value)}
                  placeholder="Preset name"
                  className="w-full rounded border border-[#E5E7EB] bg-white p-2 text-sm"
                />
                <button
                  type="button"
                  onClick={savePreset}
                  className="rounded bg-[#34A853] px-4 py-2 text-sm font-medium text-white"
                >
                  Save preset
                </button>
              </div>
              <div className="mt-4 space-y-2 text-sm text-[#5F6368]">
                {presetNames.length === 0 && (
                  <p>No presets saved for this vertical yet.</p>
                )}
                {presetNames.map((name) => (
                  <div key={name} className="flex items-center justify-between">
                    <span>{name}</span>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => loadPreset(name)}
                        className="rounded border border-[#E5E7EB] px-2 py-1 text-xs text-[#202124]"
                      >
                        Load
                      </button>
                      <button
                        type="button"
                        onClick={() => deletePreset(name)}
                        className="rounded border border-[#EA4335] px-2 py-1 text-xs text-[#EA4335]"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activePage === 'Scoring' && (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
              <h2 className="text-sm font-semibold text-[#202124]">Upload files</h2>
              <div className="mt-3 space-y-3 text-sm text-[#5F6368]">
                <div>
                  <label className="text-xs font-medium text-[#202124]">Golden dataset</label>
                  <input
                    type="file"
                    className="mt-1 block w-full rounded border border-[#E5E7EB] bg-white p-2"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-[#202124]">Model outputs</label>
                  <input
                    type="file"
                    className="mt-1 block w-full rounded border border-[#E5E7EB] bg-white p-2"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-[#202124]">Model ID</label>
                  <input
                    type="text"
                    placeholder="my-model-v1"
                    className="mt-1 block w-full rounded border border-[#E5E7EB] bg-white p-2"
                  />
                </div>
              </div>
              <button
                type="button"
                className="mt-4 rounded bg-[#EA4335] px-4 py-2 text-sm font-medium text-white"
              >
                Score run
              </button>
            </div>
            <div className="rounded-lg border border-[#E5E7EB] bg-white p-5 shadow">
              <h2 className="text-sm font-semibold text-[#202124]">Results</h2>
              <p className="mt-3 text-sm text-[#5F6368]">
                Upload files to generate a scored_results.jsonl download.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
