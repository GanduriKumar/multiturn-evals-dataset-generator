function App() {
  return (
    <div className="min-h-screen bg-gray-100 text-slate-900">
      <div className="mx-auto max-w-3xl p-8">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
          <h1 className="text-2xl font-semibold text-blue-700">
            Tailwind is wired ✅
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            If this card has spacing, border, and colors, Tailwind is compiling.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700">
              Tailwind Button
            </button>
            <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
              Visual check
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
