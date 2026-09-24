import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useAuth } from '../hooks/useAuth'

function LoadingSpinner() {
  return <div className="animate-spin text-4xl">⏳</div>
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { data: projects, isLoading, isError } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get('/projects').then(r => r.data),
    staleTime: 30000,
  })

  const { data: usage } = useQuery({
    queryKey: ['usage'],
    queryFn: () => api.get('/usage').then(r => r.data),
    staleTime: 60000,
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <div className="text-red-400">Failed to load dashboard</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">Welcome, {user?.name}</h1>
        <p className="text-gray-400">Manage your video clipping projects</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-gray-400 text-sm">Projects</p>
          <p className="text-3xl font-bold">{projects?.data?.length || 0}</p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm">Processing</p>
          <p className="text-3xl font-bold text-yellow-400">-</p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm">Credits Used</p>
          <p className="text-3xl font-bold">{usage?.data?.credits_used || 0}</p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm">Credits Remaining</p>
          <p className="text-3xl font-bold text-green-400">{usage?.data?.credits_balance || 0}</p>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="flex gap-4">
          <button
            onClick={() => navigate('/projects')}
            className="btn-primary"
          >
            📁 New Project
          </button>
          <button className="btn-secondary">📤 Upload Video</button>
          <button className="btn-secondary">🔗 Paste URL</button>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Recent Projects</h2>
        {projects?.data?.length === 0 && (
          <p className="text-gray-400">No projects yet. Create your first one!</p>
        )}
        {projects?.data?.map((project: any) => (
          <div key={project.id} className="flex items-center justify-between py-2 border-b border-gray-800">
            <div>
              <p className="font-medium">{project.name}</p>
              <p className="text-sm text-gray-400">{project.status}</p>
            </div>
            <button className="btn-secondary text-sm" onClick={() => navigate(`/projects/${project.id}`)}>
              Open
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
