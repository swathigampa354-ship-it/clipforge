# ClipForge API Reference

Base URL: `/api/v1`

## Authentication

### POST `/auth/register`
Create a new account.
- Request: `UserCreate` (email, username, password)
- Response: `ApiResponse` with user data

### POST `/auth/login`
Login with email and password.
- Request: `LoginRequest` (email, password)
- Response: `ApiResponse` with token

### GET `/auth/me`
Get current user.
- Headers: `Authorization: Bearer <token>`
- Response: `ApiResponse` with user data

### POST `/auth/logout`
Logout (stub — no token invalidation).

### POST `/auth/refresh`
Refresh token (stub).

### POST `/auth/forgot-password`
Send password reset email (stub).

### POST `/auth/oauth/start`
Initiate OAuth flow (stub).

### POST `/auth/oauth/callback`
Handle OAuth callback (stub).

---

## Projects

### POST `/projects`
Create a project.
- Request: `ProjectCreate` (name, description, source_type)
- Response: `ApiResponse` with `ProjectResponse`

### GET `/projects`
List projects for current user.
- Query: `status_filter`, `limit`, `offset`
- Response: `ApiResponse` with `[ProjectResponse]`

### GET `/projects/{project_id}`
Get a project.
- Response: `ApiResponse` with `ProjectResponse`

### PUT `/projects/{project_id}`
Update a project.
- Request: `ProjectUpdate`
- Response: `ApiResponse` with `ProjectResponse`

### DELETE `/projects/{project_id}`
Delete a project.
- Response: `ApiResponse` with message

### GET `/projects/{project_id}/videos`
List videos in a project.
- Response: `ApiResponse` with `[VideoResponse]`

---

## Videos

### POST `/videos/upload`
Upload a video file.
- Request: `multipart/form-data` with `file`
- Response: `ApiResponse` with video data

### POST `/videos/import`
Import video from URL.
- Request: `url` (YouTube/Vimeo/Twitch/Kick)
- Response: `ApiResponse` with video data

### GET `/videos/{video_id}`
Get video details.
- Response: `ApiResponse` with video data

### POST `/videos/{video_id}/analyze`
Start processing a video.
- Response: `ApiResponse` with job_id (note: processing not yet working)

### GET `/videos/{video_id}/status`
Get processing status.
- Response: `ApiResponse` with status (progress is hardcoded to 0)

### GET `/videos/{video_id}/clips`
List clips for a video.
- Response: `ApiResponse` with clip list (returns `[]` — stub)

### DELETE `/videos/{video_id}`
Delete a video (stub — no-op).

### POST `/videos/{video_id}/thumbnail`
Generate thumbnail (stub — returns placeholder URL).

### GET `/videos/{video_id}/transcript`
Get transcript (stub — returns empty data).

---

## Clips

### POST `/clips`
Create a clip.
- Request: `clip_data` dict (no Pydantic validation)
- Response: `ApiResponse` with clip data

### GET `/clips`
List clips.
- **WARNING**: No user isolation — returns ALL clips to any authenticated user

### GET `/clips/{clip_id}`
Get a clip by ID.
- **WARNING**: No ownership verification

### PUT `/clips/{clip_id}`
Update a clip.
- **WARNING**: No ownership verification, no field validation

### POST `/clips/{clip_id}/render`
Trigger rendering for a clip.
- Creates a `RenderJob` record in DB
- Response: `ApiResponse` with render job data

### POST `/clips/{clip_id}/select`
Select a clip for rendering.
- Sets status to "rendering" (no ownership verification)

### POST `/clips/{clip_id}/deselect`
Deselect a clip.
- Sets status to "draft" (no ownership verification)

### POST `/clips/{clip_id}/edit`
Edit a clip.
- **BROKEN**: Calls non-existent `service.edit_clip()` method

### DELETE `/clips/{clip_id}`
Delete a clip.
- **WARNING**: No ownership verification

---

## AI Analysis

### POST `/ai/analyze`
Run complete AI analysis on a video.
- Response: `ApiResponse` with candidates, topics, processing time

### GET `/ai/candidates/{video_id}`
Get clip candidates for a video.
- Response: `ApiResponse` with candidate list

### POST `/ai/select/{candidate_id}`
Select a clip candidate.
- Response: `ApiResponse` with message

### POST `/ai/segment`
Segment a transcript.
- Response: `ApiResponse` with segments

### POST `/ai/transcribe/{video_id}`
Trigger transcription for a video.
- Response: `ApiResponse` with result

### GET `/ai/status/{video_id}`
Get AI analysis status.
- Response: `ApiResponse` with stats

### GET `/ai/ollama/health`
Check if Ollama is running.
- Response: `ApiResponse` with health status and models

### GET `/ai/ollama/models`
List available Ollama models.
- Response: `ApiResponse` with model list

### POST `/ai/ollama/generate`
Generate text using Ollama.
- Request: `prompt`, `system` (optional)
- Response: `ApiResponse` with generated text

### POST `/ai/ollama/summarize`
Summarize text using Ollama.
- Request: `text`, `max_length`
- Response: `ApiResponse` with summary

### POST `/ai/ollama/analyze`
Analyze a transcript segment using Ollama.
- Request: `transcript`
- Response: `ApiResponse` with analysis

---

## Captions

### GET `/caption-styles`
List all caption styles.
- Response: `ApiResponse` with styles object

### POST `/caption-styles`
Create a custom caption style.
- Request: style data
- Response: `ApiResponse` with created style

### PUT `/caption-styles/{style_id}`
Update a caption style.
- Note: Actually calls `create_style` again (not update)

### POST `/captions/generate`
Generate captions for a video.
- Request: `video_id`, `language`, `style_id`
- Response: `ApiResponse` with segments and analysis

### POST `/captions/{clip_id}/apply`
Apply captions to a clip.
- Request: `style_id`, `format`, `language`
- Response: `ApiResponse` with captions

### POST `/captions/{clip_id}/preview`
Preview caption rendering.
- Response: `ApiResponse` with preview URL (placeholder)

### POST `/captions/{clip_id}/export`
Export captions in specified format.
- Response: `ApiResponse` with status

### POST `/captions/analyze`
Analyze caption quality.
- Request: `segments_data`
- Response: `ApiResponse` with readability analysis

---

## Reframe

### POST `/reframe/{video_id}/generate`
Generate reframe path for a video.
- Request: `mode`, `aspect_ratio`
- Response: `ApiResponse` with camera path

### GET `/reframe/{video_id}/path`
Get the generated camera path for a video.
- Response: `ApiResponse` with keyframes

### POST `/reframe/{clip_id}/reframe`
Reframe a specific clip.
- Response: `ApiResponse` with output path

### POST `/reframe/detect/{video_id}`
Detect faces and speakers in a video.
- Response: `ApiResponse` with detection data

### GET `/reframe/speakers/{video_id}`
Get speaker tracking data for a video.
- Response: `ApiResponse` with speaker data

### POST `/reframe/preview/{video_id}`
Preview reframe at a specific time.
- Response: `ApiResponse` with preview URL

---

## Renders

### GET `/renders/{render_id}`
Get render status.
- **STUB**: Returns hardcoded `{"status": "queued"}`

### GET `/renders/{render_id}/download`
Download render output.
- **STUB**: Returns `{"url": "/placeholder/download"}`

### POST `/renders`
Create a render job.
- **STUB**: No DB persistence

### GET `/renders`
List render jobs.
- **STUB**: Returns `[]`

### GET `/renders/{render_id}/progress`
Get render progress.
- **STUB**: Returns `{"progress": 0.0}`

### DELETE `/renders/{render_id}`
Delete a render.
- **STUB**: No DB deletion

---

## Usage & Billing

### GET `/usage`
Get usage statistics.
- **STUB**: Returns hardcoded credits

### GET `/usage/overview`
Get usage overview.
- **STUB**: Returns hardcoded monthly data

### GET `/usage/history`
Get usage history.
- **STUB**: Returns `[]`

### GET `/subscriptions`
Get subscription.
- **STUB**: Returns hardcoded plan data

### POST `/subscriptions/checkout`
Create Stripe checkout.
- **STUB**: Returns placeholder URL

### GET `/subscriptions/portal`
Get Stripe billing portal.
- **STUB**: Returns placeholder URL

### POST `/subscriptions/webhook`
Handle Stripe webhook.
- **STUB**: No signature verification

---

## API Keys

### POST `/api-keys`
Create an API key.
- **STUB**: Returns `{"key": "ck_live_placeholder"}`

### GET `/api-keys`
List API keys.
- **STUB**: Returns `[]`

### DELETE `/api-keys/{key_id}`
Delete an API key.
- **STUB**: No DB deletion

### GET `/api-keys/{key_id}/usage`
Get API key usage.
- **STUB**: Returns hardcoded data

---

## Scheduled Posts

### GET `/scheduled-posts`
List scheduled posts.
- Response: `ApiResponse` with posts list

### POST `/scheduled-posts`
Schedule a new post.
- Request: `platform`, `scheduled_for`, `content`

### POST `/scheduled-posts/{postId}/publish`
Publish a scheduled post.
- **STUB**: No actual publishing

---

## Error Responses

All endpoints return `ApiResponse`:
```json
{
  "success": true,
  "data": null,
  "message": "string",
  "error": "string"
}
```

### ErrorResponse
```json
{
  "success": false,
  "error": "string",
  "details": [],
  "code": "string"
}
```

---

## Rate Limiting

Applied to:
- Auth endpoints: `5/minute`, `10/minute`
- Video upload: `5/minute`

Most other endpoints have **no rate limiting**.

---

*Last updated: September 24, 2026*