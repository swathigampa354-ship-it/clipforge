import React from 'react'
import { useParams } from 'react-router-dom'

export default function Editor() {
  const { clipId } = useParams<{ clipId: string }>()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Editor</h1>
      <div className="grid grid-cols-3 gap-4" style={{ height: '70vh' }}>
        <div className="col-span-2 bg-gray-900 rounded-lg border border-gray-800 flex items-center justify-center">
          <div className="text-center text-gray-400">
            <p className="text-6xl mb-4">▶</p>
            <p>Video Preview</p>
            <p className="text-xs mt-2">9:16 · 1080×1920</p>
          </div>
        </div>
        <div className="space-y-4 overflow-auto">
          <div className="card">
            <h3 className="font-semibold text-sm mb-3">Captions</h3>
            <div className="space-y-2 text-sm">
              {['Word 1', 'Word 2', 'Word 3'].map((w, i) => (
                <div key={i} className="bg-gray-800 rounded px-3 py-1 text-center">{w}</div>
              ))}
            </div>
          </div>
          <div className="card">
            <h3 className="font-semibold text-sm mb-3">Crop</h3>
            <p className="text-gray-400 text-xs">Adjust framing</p>
          </div>
          <div className="card">
            <h3 className="font-semibold text-sm mb-3">Audio</h3>
            <p className="text-gray-400 text-xs">Volume, noise</p>
          </div>
          <div className="card">
            <h3 className="font-semibold text-sm mb-3">Text</h3>
            <p className="text-gray-400 text-xs">Overlays</p>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden flex-1 max-w-2xl">
          <div className="h-full bg-indigo-600 rounded-full" style={{ width: '30%' }} />
        </div>
        <button className="btn-primary">Export MP4</button>
      </div>
    </div>
  )
}
