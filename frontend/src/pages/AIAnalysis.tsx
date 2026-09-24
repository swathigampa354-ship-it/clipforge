import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../lib/api'
import { useAuth } from '../hooks/useAuth'

export default function AIAnalysis() {
  const { clipId } = useParams<{ clipId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()

  const { data: analysis, isLoading } = useQuery({
    queryKey: ['ai-analysis', clipId],
    queryFn: () => api.get(`/ai/analyze/${clipId}`).then(r => r.data),
    enabled: !!clipId,
  })

  const { data: clips } = useQuery({
    queryKey: ['clips', clipId],
    queryFn: () => api.get(`/clips/${clipId}`).then(r => r.data),
    enabled: !!clipId,
  })

  if (isLoading) return <div className="animate-spin text-4xl">⏳</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Analysis</h1>
        <p className="text-gray-400">ClipForge AI insights and clip detection</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-gray-400 text-sm">Clips Found</p>
          <p className="text-3xl font-bold text-green-400">{analysis?.clip_count || 0}</p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm">Avg Score</p>
          <p className="text-3xl font-bold">{analysis?.avg_score || 0}/100</p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm">Confidence</p>
          <p className="text-3xl font-bold">{analysis?.confidence || 0}%</p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm">Duration</p>
          <p className="text-3xl font-bold">{analysis?.total_duration || 0}s</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Detection Strategies</h2>
          <div className="space-y-3">
            {(analysis?.strategies || []).map((strategy: any, i: number) => (
              <div key={i} className="flex items-center justify-between bg-gray-800 rounded p-3">
                <span className="text-sm">{strategy.name}</span>
                <span className="text-green-400 text-sm">{strategy.count} clips</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Top Clips</h2>
          <div className="space-y-3">
            {clips?.data?.map((clip: any, i: number) => (
              <div key={i} className="flex items-center justify-between bg-gray-800 rounded p-3 cursor-pointer hover:bg-gray-750"
                onClick={() => navigate(`/editor/${clip.id}`)}>
                <div>
                  <p className="text-sm font-medium">{clip.title || `Clip ${i + 1}`}</p>
                  <p className="text-xs text-gray-400">{clip.start_time}s - {clip.end_time}s</p>
                </div>
                <span className="bg-green-900 text-green-300 px-2 py-1 rounded text-xs">
                  {clip.score}/100
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Scoring Breakdown</h2>
        <div className="space-y-4">
          {(analysis?.score_breakdown || []).map((item: any, i: number) => (
            <div key={i} className="flex items-center gap-4">
              <span className="text-sm w-40">{item.name}</span>
              <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-600 rounded-full" style={{ width: `${item.score}%` }} />
              </div>
              <span className="text-sm w-12 text-right">{item.score}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}