import React from 'react'
import { Outlet } from 'react-router-dom'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => api.get(`/projects/${id}`).then(r => r.data),
    enabled: !!id,
  })

  if (isLoading) return <div className="text-center py-20 text-gray-400">Loading...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{data?.data?.name}</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <h3 className="font-semibold mb-2">Upload</h3>
          <p className="text-sm text-gray-400 mb-2">Drop video file or click to browse</p>
          <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center text-gray-500">
            📁 Drop video here
          </div>
          <p className="text-xs text-gray-600 mt-2">Max 16GB. MP4, MOV, WebM</p>
        </div>
        <div className="card">
          <h3 className="font-semibold mb-2">Import URL</h3>
          <p className="text-sm text-gray-400">Paste a YouTube or video URL</p>
          <div className="flex gap-2 mt-2">
            <input type="text" placeholder="https://youtube.com/..." className="input flex-1" />
            <button className="btn-primary text-sm">Import</button>
          </div>
        </div>
        <div className="card">
          <h3 className="font-semibold mb-2">Processing</h3>
          <p className="text-sm text-gray-400">Jobs appear here</p>
          <div className="mt-2 space-y-1">
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 rounded-full bg-gray-600" />
              <span className="text-gray-400">Waiting</span>
            </div>
          </div>
        </div>
      </div>
      <Outlet />
    </div>
  )
}
