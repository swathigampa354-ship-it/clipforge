// Hooks for clip operations
import { useQuery, useMutation } from '@tanstack/react-query'
import api from '../lib/api'

export function useClips(projectId?: string) {
  return useQuery({
    queryKey: ['clips', projectId],
    queryFn: () => api.get(`/clips${projectId ? `?project_id=${projectId}` : ''}`).then(r => r.data),
    enabled: !!projectId,
  })
}

export function useClip(clipId: string) {
  return useQuery({
    queryKey: ['clip', clipId],
    queryFn: () => api.get(`/clips/${clipId}`).then(r => r.data),
    enabled: !!clipId,
  })
}

export function useCreateClip() {
  return useMutation({
    mutationFn: (data: any) => api.post('/clips', data),
  })
}

export function useUpdateClip() {
  return useMutation({
    mutationFn: ({ clipId, data }: { clipId: string; data: any }) =>
      api.put(`/clips/${clipId}`, data),
  })
}

export function useGenerateClips() {
  return useMutation({
    mutationFn: (videoId: string) => api.post(`/ai/generate-clips/${videoId}`),
  })
}

export function useReframe() {
  return useMutation({
    mutationFn: ({ clipId, data }: { clipId: string; data: any }) =>
      api.post(`/reframe/${clipId}/generate`, data),
  })
}

export function useRenderClip() {
  return useMutation({
    mutationFn: (clipId: string) => api.post(`/renders/${clipId}/render`),
  })
}

export function useCaptionGeneration() {
  return useMutation({
    mutationFn: ({ clipId, data }: { clipId: string; data: any }) =>
      api.post(`/captions/generate`, { ...data, video_id: clipId }),
  })
}

export function useCaptionExport() {
  return useMutation({
    mutationFn: ({ clipId, format }: { clipId: string; format: string }) =>
      api.post(`/captions/${clipId}/export?format=${format}`),
  })
}

export function useTranscript(videoId: string) {
  return useQuery({
    queryKey: ['transcript', videoId],
    queryFn: () => api.get(`/videos/${videoId}/transcript`).then(r => r.data),
    enabled: !!videoId,
  })
}

export function useAnalytics() {
  return useQuery({
    queryKey: ['analytics'],
    queryFn: () => api.get('/usage').then(r => r.data),
  })
}