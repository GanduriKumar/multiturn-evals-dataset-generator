import { useEffect, useMemo, useRef, useState } from 'react'
import JSZip from 'jszip'

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
  const [axesSelections, setAxesSelections] = useState<Record<string, string[]>>({})
  const [generatedDatasets, setGeneratedDatasets] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [downloadName, setDownloadName] = useState<string | null>(null)
  const [presetName, setPresetName] = useState('')
  const [presetNames, setPresetNames] = useState<string[]>([])
  const [domainSchemaFile, setDomainSchemaFile] = useState<File | null>(null)
  const [behaviourSchemaFile, setBehaviourSchemaFile] = useState<File | null>(null)
  const [axesSchemaFile, setAxesSchemaFile] = useState<File | null>(null)
  const [downloadFormat, setDownloadFormat] = useState<'json' | 'csv'>('json')
  const [minTurns, setMinTurns] = useState(5)
  const [maxTurns, setMaxTurns] = useState(9)
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null)
  const [datasetPreview, setDatasetPreview] = useState<string>('')
  const [zipFileData, setZipFileData] = useState<Blob | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

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
        const defaults: Record<string, string[]> = {}
        Object.entries(payload.axes ?? {}).forEach(([axis, values]) => {
          defaults[axis] = values[0] ? [values[0]] : []
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

  const scenarioCombinationCount = useMemo(() => {
    const entries = Object.values(axesSelections)
    if (entries.length === 0) return 1
    return entries.reduce((total, values) => {
      const count = Array.isArray(values) ? values.length : 0
      return total * (count > 0 ? count : 1)
    }, 1)
  }, [axesSelections])

  const selectedScenarioCount = useMemo(() => {
    return Object.values(axesSelections).reduce((total, values) => {
      if (!Array.isArray(values)) return total
      return total + values.length
    }, 0)
  }, [axesSelections])

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
        axes?: Record<string, string[]>
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

  useEffect(() => {
    const stored = localStorage.getItem('generated_datasets')
    if (!stored) return
    try {
      const parsed = JSON.parse(stored) as string[]
      if (Array.isArray(parsed)) {
        setGeneratedDatasets(parsed)
      }
    } catch {
      return
    }
  }, [])

  useEffect(() => {
    localStorage.setItem('generated_datasets', JSON.stringify(generatedDatasets))
  }, [generatedDatasets])

  useEffect(() => {
    // Load turn settings from localStorage
    const savedMinTurns = localStorage.getItem('eval_min_turns')
    const savedMaxTurns = localStorage.getItem('eval_max_turns')
    if (savedMinTurns) setMinTurns(parseInt(savedMinTurns, 10))
    if (savedMaxTurns) setMaxTurns(parseInt(savedMaxTurns, 10))
  }, [])

  useEffect(() => {
    return () => {
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl)
      }
    }
  }, [downloadUrl])

  const buildGenerationPayload = () => ({
    vertical,
    workflows: selectedWorkflows,
    behaviours: selectedBehaviours,
    axes: axesSelections,
    num_samples_per_combo: 1,
    language_locale: 'en-US',
    channel: 'web',
    random_seed: null,
    min_turns: minTurns,
    max_turns: maxTurns,
  })

  const extractFilename = (contentDisposition: string | null) => {
    if (!contentDisposition) return null
    const match = contentDisposition.match(/filename=([^;]+)/i)
    if (!match) return null
    return match[1]?.replace(/"/g, '').trim() ?? null
  }

  const triggerDownload = (url: string, name: string) => {
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = name
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  }

  const extractFileFromZip = async (filename: string, blob: Blob) => {
    try {
      const zip = new JSZip()
      const zipData = await zip.loadAsync(blob)
      const file = zipData.file(filename)
      if (!file) {
        setDatasetPreview(`File "${filename}" not found in archive`)
        return
      }
      const content = await file.async('string')
      // Limit preview to first 2000 characters for large files
      if (content.length > 2000) {
        setDatasetPreview(content.substring(0, 2000) + '\n\n... (truncated, download to see full content)')
      } else {
        setDatasetPreview(content)
      }
    } catch (err) {
      setDatasetPreview(`Error reading file: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  const generateDataset = async () => {
    if (selectedWorkflows.length === 0) {
      setGenerateError('Select at least one workflow before generating.')
      return
    }
    setGenerateError(null)
    setIsGenerating(true)
    abortControllerRef.current = new AbortController()

    try {
      const formData = new FormData()
      formData.append('config', JSON.stringify(buildGenerationPayload()))
      if (domainSchemaFile) {
        formData.append('domain_schema', domainSchemaFile)
      }
      if (behaviourSchemaFile) {
        formData.append('behaviour_schema', behaviourSchemaFile)
      }
      if (axesSchemaFile) {
        formData.append('axes_schema', axesSchemaFile)
      }

      const response = await fetch('/generate-dataset', {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal,
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || `Failed to generate dataset (${response.status})`)
      }

      const blob = await response.blob()
      const nextUrl = URL.createObjectURL(blob)
      const filename =
        extractFilename(response.headers.get('Content-Disposition')) ?? 'dataset.zip'

      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl)
      }

      setDownloadUrl(nextUrl)
      setDownloadName(filename)
      setZipFileData(blob)
      
      // Extract filenames from ZIP
      try {
        const zip = new JSZip()
        const zipData = await zip.loadAsync(blob)
        const filenames = Object.keys(zipData.files).filter(name => !zipData.files[name].dir)
        setGeneratedDatasets(filenames)
      } catch (err) {
        console.error('Error reading ZIP contents:', err)
        setGeneratedDatasets(['manifest.json'])
      }
      
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setGenerateError('Generation aborted')
      } else {
        setGenerateError(err instanceof Error ? err.message : 'Generation failed')
      }
    } finally {
      setIsGenerating(false)
    }
  }

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
                <h2 className="text-sm font-semibold text-[#202124]">Summary</h2>
                <div className="mt-3 space-y-2 text-sm text-[#5F6368]">
                  <div>Workflows: {selectedWorkflows.length}</div>
                  <div>Behaviours: {selectedBehaviours.length || 1}</div>
                  <div>Selected scenarios: {selectedScenarioCount}</div>
                  <div>Turns per conversation: {minTurns}-{maxTurns}</div>
                  <div className="pt-2 border-t border-[#E5E7EB]">
                    <div className="font-medium text-[#202124]">
                      Total conversations:{' '}
                      {selectedWorkflows.length * (selectedBehaviours.length || 1) * scenarioCombinationCount}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-4">
              <div className="rounded-lg border border-[#E5E7EB] bg-white p-3 shadow">
                <h2 className="text-xs font-semibold text-[#202124]">Workflows</h2>
                <p className="text-xs text-[#5F6368] mt-1">Hold Ctrl/Cmd to select multiple</p>
                <select
                  multiple
                  className="mt-2 w-full h-48 rounded border border-[#E5E7EB] bg-white p-2 text-xs shadow-sm focus:border-[#4285F4] focus:outline-none focus:ring-1 focus:ring-[#4285F4]"
                  value={selectedWorkflows}
                  onChange={(e) => {
                    const options = Array.from(e.target.selectedOptions, option => option.value)
                    setSelectedWorkflows(options)
                  }}
                >
                  {(config?.workflows ?? []).map((workflow) => (
                    <option key={workflow} value={workflow} className="py-1">
                      {workflow}
                    </option>
                  ))}
                </select>
                {!config && (
                  <p className="text-sm text-[#5F6368] mt-2">
                    Select a vertical to view workflows.
                  </p>
                )}
              </div>

              <div className="rounded-lg border border-[#E5E7EB] bg-white p-3 shadow">
                <h2 className="text-xs font-semibold text-[#202124]">Behaviours</h2>
                <p className="text-xs text-[#5F6368] mt-1">Hold Ctrl/Cmd to select multiple</p>
                <select
                  multiple
                  className="mt-2 w-full h-48 rounded border border-[#E5E7EB] bg-white p-2 text-xs shadow-sm focus:border-[#4285F4] focus:outline-none focus:ring-1 focus:ring-[#4285F4]"
                  value={selectedBehaviours}
                  onChange={(e) => {
                    const options = Array.from(e.target.selectedOptions, option => option.value)
                    setSelectedBehaviours(options)
                  }}
                >
                  {(config?.behaviours ?? []).map((behaviour) => (
                    <option key={behaviour} value={behaviour} className="py-1">
                      {behaviour}
                    </option>
                  ))}
                </select>
                {!config && (
                  <p className="text-sm text-[#5F6368] mt-2">
                    Select a vertical to view behaviours.
                  </p>
                )}
              </div>

              <div className="rounded-lg border border-[#E5E7EB] bg-white p-3 shadow">
                <h2 className="text-xs font-semibold text-[#202124]">Scenarios</h2>
                <p className="text-xs text-[#5F6368] mt-1">Hold Ctrl/Cmd to select values (multiple per axis)</p>
                <select
                  multiple
                  size={10}
                  className="mt-2 w-full h-48 rounded border border-[#E5E7EB] bg-white p-2 text-xs shadow-sm focus:border-[#4285F4] focus:outline-none focus:ring-1 focus:ring-[#4285F4]"
                  value={Object.entries(axesSelections).flatMap(([axis, values]) =>
                    values.map((value) => `${axis}:${value}`),
                  )}
                  onChange={(e) => {
                    const selected = Array.from(e.target.selectedOptions, option => option.value)
                    const newSelections: Record<string, string[]> = {}
                    selected.forEach(item => {
                      const [axis, value] = item.split(':')
                      if (!newSelections[axis]) {
                        newSelections[axis] = []
                      }
                      if (!newSelections[axis].includes(value)) {
                        newSelections[axis].push(value)
                      }
                    })
                    setAxesSelections(newSelections)
                  }}
                >
                  {axesEntries.map(([axis, values]) => (
                    <optgroup key={axis} label={axis} className="font-semibold">
                      {values.map((value) => (
                        <option key={`${axis}:${value}`} value={`${axis}:${value}`} className="py-1 pl-3">
                          {value}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {!config && (
                  <p className="text-sm text-[#5F6368] mt-2">Select a vertical to view scenarios.</p>
                )}
              </div>

              <div className="rounded-lg border border-[#E5E7EB] bg-white p-3 shadow">
                <h2 className="text-xs font-semibold text-[#202124]">Generate & Download</h2>
                
                {isGenerating && (
                  <div className="mt-3 space-y-2 text-xs text-[#5F6368]">
                    <p className="text-center font-semibold text-[#202124]">Generating…</p>
                  </div>
                )}

                {!isGenerating && (
                  <div className="mt-2 space-y-2">
                    <button
                      type="button"
                      onClick={generateDataset}
                      className="w-full rounded bg-[#4285F4] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#3367D6]"
                    >
                      Generate
                    </button>
                    {generateError && (
                      <p className="text-xs text-[#EA4335]">{generateError}</p>
                    )}
                    <select
                      value={downloadFormat}
                      onChange={(e) => setDownloadFormat(e.target.value as 'json' | 'csv')}
                      className="w-full rounded border border-[#E5E7EB] bg-white p-1 text-xs"
                      disabled={!downloadUrl}
                    >
                      <option value="json">JSON</option>
                      <option value="csv">CSV</option>
                    </select>
                    <button
                      type="button"
                      className="w-full rounded bg-[#34A853] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#2D8E47] disabled:opacity-60"
                      disabled={!downloadUrl || generatedDatasets.length === 0}
                      onClick={() => {
                        if (downloadUrl && downloadName) {
                          triggerDownload(downloadUrl, downloadName)
                        }
                      }}
                    >
                      Download
                    </button>
                  </div>
                )}

                {generatedDatasets.length > 0 && !isGenerating && (
                  <div className="mt-2 text-xs text-[#5F6368]">
                    <p className="font-medium">Ready:</p>
                    {generatedDatasets.map((dataset) => (
                      <p key={dataset} className="truncate">{dataset}</p>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-[#E5E7EB] bg-white p-3 shadow">
                <h2 className="text-xs font-semibold text-[#202124]">Generated Datasets</h2>
                {generatedDatasets.length === 0 ? (
                  <p className="mt-3 text-xs text-[#5F6368]">No datasets generated yet. Generate a dataset to see files here.</p>
                ) : (
                  <div className="mt-2 space-y-1">
                    {generatedDatasets.map((dataset) => (
                      <button
                        key={dataset}
                        type="button"
                        onClick={() => {
                          setSelectedDataset(dataset)
                          if (zipFileData) {
                            extractFileFromZip(dataset, zipFileData)
                          } else {
                            setDatasetPreview('ZIP file data not available')
                          }
                        }}
                        className={`w-full rounded px-2 py-1 text-left text-xs transition ${
                          selectedDataset === dataset
                            ? 'bg-[#4285F4] text-white'
                            : 'border border-[#E5E7EB] bg-white text-[#202124] hover:bg-[#F0F0F0]'
                        }`}
                      >
                        {dataset}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="rounded-lg border border-[#E5E7EB] bg-white p-3 shadow">
                <div className="flex items-center justify-between">
                  <h2 className="text-xs font-semibold text-[#202124]">
                    {selectedDataset ? `Preview: ${selectedDataset}` : 'Dataset Preview'}
                  </h2>
                  <span className="rounded-full bg-[#E8F0FE] px-2 py-0.5 text-xs font-medium text-[#4285F4]">
                    {selectedDataset ? 'PREVIEW' : 'READY'}
                  </span>
                </div>
                <pre className="mt-3 max-h-64 overflow-auto rounded bg-gray-900 p-2 text-xs text-green-300">
                  {selectedDataset
                    ? datasetPreview
                    : JSON.stringify(previewPayload, null, 2)}
                </pre>
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
              <h2 className="text-sm font-semibold text-[#202124]">Conversation Turns</h2>
              <p className="mt-1 text-xs text-[#5F6368]">Configure conversation turn range for generated datasets.</p>
              <div className="mt-4 space-y-3">
                <div>
                  <label className="text-xs font-medium text-[#202124]">Minimum Turns</label>
                  <input
                    type="number"
                    min="3"
                    max="15"
                    value={minTurns}
                    onChange={(e) => {
                      const val = Math.max(3, Math.min(15, parseInt(e.target.value, 10)))
                      setMinTurns(val)
                      localStorage.setItem('eval_min_turns', val.toString())
                    }}
                    className="mt-1 w-full rounded border border-[#E5E7EB] bg-white p-2 text-sm"
                  />
                  <p className="mt-1 text-xs text-[#5F6368]">Current: {minTurns} turns (3-15)</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-[#202124]">Maximum Turns</label>
                  <input
                    type="number"
                    min="3"
                    max="15"
                    value={maxTurns}
                    onChange={(e) => {
                      const val = Math.max(3, Math.min(15, parseInt(e.target.value, 10)))
                      setMaxTurns(val)
                      localStorage.setItem('eval_max_turns', val.toString())
                    }}
                    className="mt-1 w-full rounded border border-[#E5E7EB] bg-white p-2 text-sm"
                  />
                  <p className="mt-1 text-xs text-[#5F6368]">Current: {maxTurns} turns (3-15)</p>
                </div>
                {minTurns > maxTurns && (
                  <p className="text-xs text-[#EA4335]">⚠ Min turns cannot exceed max turns</p>
                )}
              </div>
            </div>
          </div>
        )}

        {activePage === 'Settings' && (
          <div className="mt-4 grid gap-4 md:grid-cols-1">
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
