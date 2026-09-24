import React from 'react'
import { Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

export default function Projects() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get('/projects').then(r => r.data),
    staleTime: 30000,
  })

  if (isLoading) return <div className="text-center py-20 text-gray-400">Loading projects...</div>
  if (isError) return <div className="text-red-400">Failed to load</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Projects</h1>
        <button className="btn-primary">+ New Project</button>
      </div>
      <div className="grid gap-4">
        {(data?.data || []).map((project: any) => (
          <div key={project.id} className="card flex items-center justify-between">
            <div>
              <h3 className="font-semibold">{project.name}</h3>
              <p className="text-sm text-gray-400">{project.status}</p>
            </div>
            <button className="btn-secondary text-sm">Open</button>
          </div>
        ))}
      </div>
      <Outlet />
    </div>
  )
}
