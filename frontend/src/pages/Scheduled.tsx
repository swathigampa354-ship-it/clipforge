import React from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'

export default function Scheduled() {
  const navigate = useNavigate()

  const { data: scheduled, isLoading } = useQuery({
    queryKey: ['scheduled-posts'],
    queryFn: () => api.get('/scheduled-posts').then(r => r.data),
  })

  const scheduleMutation = useMutation({
    mutationFn: (data: any) => api.post('/scheduled-posts', data),
  })

  const publishMutation = useMutation({
    mutationFn: (postId: string) => api.post(`/scheduled-posts/${postId}/publish`),
  })

  const schedulePost = () => {
    scheduleMutation.mutate({
      clipId: 'sample',
      platform: 'tiktok',
      scheduledFor: new Date().toISOString(),
      content: { caption: 'Check out this clip!', hashtags: ['#trending'] },
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Scheduled Posts</h1>
        <p className="text-gray-400">Auto-publish clips to social media</p>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Platform Settings</h2>
          <button className="btn-primary" onClick={schedulePost}>
            {scheduleMutation.isPending ? 'Scheduling...' : '+ Schedule Post'}
          </button>
        </div>

        <div className="space-y-3">
          {[
            { platform: 'tiktok', color: '#000000', icon: '🎵' },
            { platform: 'instagram', color: '#E1306C', icon: '📸' },
            { platform: 'youtube', color: '#FF0000', icon: '▶️' },
            { platform: 'twitter', color: '#1DA1F2', icon: '🐦' },
          ].map((p, i) => (
            <div key={i} className="flex items-center justify-between bg-gray-800 rounded p-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{p.icon}</span>
                <div>
                  <p className="font-medium">{p.platform.charAt(0).toUpperCase() + p.platform.slice(1)}</p>
                  <p className="text-xs text-gray-400">Auto-publish enabled</p>
                </div>
              </div>
              <button className="btn-secondary text-xs">Configure</button>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Scheduled Posts</h2>
        {isLoading ? (
          <div className="animate-spin text-4xl">⏳</div>
        ) : (
          <div className="space-y-3">
            {(scheduled?.data || []).map((post: any, i: number) => (
              <div key={i} className="flex items-center justify-between bg-gray-800 rounded p-3">
                <div>
                  <p className="font-medium">{post.platform}</p>
                  <p className="text-sm text-gray-400">{post.scheduled_for}</p>
                  <p className="text-xs text-gray-500">{post.status}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    className="btn-primary text-xs"
                    onClick={() => publishMutation.mutate(post.id)}
                    disabled={publishMutation.isPending}
                  >
                    Publish Now
                  </button>
                  <button className="btn-secondary text-xs">Cancel</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Quick Schedule</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {['TikTok', 'Instagram', 'YouTube', 'Twitter'].map((platform, i) => (
            <button key={i} className="btn-secondary" onClick={() => navigate('/scheduled')}>
              {platform}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}