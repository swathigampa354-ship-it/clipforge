import React from 'react'

export default function Settings() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <div className="card space-y-4 max-w-lg">
        <h2 className="font-semibold">Profile</h2>
        <label className="block text-sm text-gray-400">Name</label>
        <input className="input" defaultValue="Creator" />
        <label className="block text-sm text-gray-400">Email</label>
        <input type="email" className="input" defaultValue="creator@example.com" />
        <button className="btn-primary">Save</button>
      </div>
      <div className="card space-y-4 max-w-lg">
        <h2 className="font-semibold">API Keys</h2>
        <p className="text-sm text-gray-400">Configure AI provider keys</p>
        <label className="block text-sm text-gray-400">Gemini API Key</label>
        <input type="password" className="input" placeholder="AIza..." />
        <label className="block text-sm text-gray-400">Deepgram API Key</label>
        <input type="password" className="input" placeholder="..." />
        <button className="btn-primary">Save Keys</button>
      </div>
    </div>
  )
}
