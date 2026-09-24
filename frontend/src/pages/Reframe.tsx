import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useAuth } from '../hooks/useAuth'

export default function Reframe() {
  const { clipId } = useParams<{ clipId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [aspectRatio, setAspectRatio] = useState('9:16')
  const [mode, setMode] = useState('auto')
  const [comfortMode, setComfortMode] = useState(true)

  const { data: reframePath, isLoading } = useQuery({
    queryKey: ['reframe-path', clipId],
    queryFn: () => api.get(`/reframe/${clipId}/path`).then(r => r.data),
    enabled: !!clipId,
  })

  const reframeMutation = useMutation({
    mutationFn: () => api.post(`/reframe/${clipId}/generate`, { mode, aspect_ratio: aspectRatio }),
    onSuccess: () => {
      // Refetch path
    },
  })

  const renderMutation = useMutation({
    mutationFn: () => api.post(`/reframe/${clipId}/render`, { aspect_ratio: aspectRatio }),
  })

  const generatePath = () => {
    reframeMutation.mutate()
  }

  const renderClip = () => {
    renderMutation.mutate()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Smart Reframe</h1>
        <p className="text-gray-400">AI-powered camera path generation</p>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Reframe Settings</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-gray-400">Aspect Ratio</label>
            <select
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value)}
              className="w-full bg-gray-800 rounded p-2 mt-1"
            >
              <option value="9:16">9:16 (Vertical)</option>
              <option value="1:1">1:1 (Square)</option>
              <option value="16:9">16:9 (Horizontal)</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400">Mode</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="w-full bg-gray-800 rounded p-2 mt-1"
            >
              <option value="auto">Auto</option>
              <option value="track">Track</option>
              <option value="wide">Wide</option>
              <option value="center">Center</option>
            </select>
          </div>
          <div>
            <label className="flex items-center gap-2 mt-4">
              <input
                type="checkbox"
                checked={comfortMode}
                onChange={(e) => setComfortMode(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">Comfort Mode</span>
            </label>
          </div>
        </div>
        <button className="btn-primary mt-4" onClick={generatePath} disabled={reframeMutation.isPending}>
          {reframeMutation.isPending ? 'Generating...' : '🔍 Generate Path'}
        </button>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Camera Path Preview</h2>
        {isLoading ? (
          <div className="animate-spin text-4xl">⏳</div>
        ) : reframePath ? (
          <div className="space-y-3">
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-400">Keyframes:</span>
              <span className="text-green-400">{reframePath.keyframes?.length || 0}</span>
            </div>
            <div className="h-4 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full bg-indigo-600 rounded-full" style={{ width: '75%' }} />
            </div>
            <div className="grid grid-cols-4 gap-2 text-xs">
              {reframePath.keyframes?.slice(0, 4).map((kf: any, i: number) => (
                <div key={i} className="bg-gray-800 rounded p-2 text-center">
                  <p>{kf.time}s</p>
                  <p className="text-gray-400">{kf.strategy}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-gray-400">Generate a path to see preview</p>
        )}
      </div>

      <div className="flex gap-4">
        <button className="btn-primary" onClick={renderClip} disabled={renderMutation.isPending}>
          {renderMutation.isPending ? 'Rendering...' : '🎬 Render Reframed Clip'}
        </button>
        <button className="btn-secondary" onClick={() => navigate(-1)}>
          Back
        </button>
      </div>
    </div>
  )
}