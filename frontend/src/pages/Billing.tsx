import React from 'react'

export default function Billing() {
  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Billing & Credits</h1>
      <div className="card">
        <h2 className="font-semibold mb-4">Current Plan</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-2xl font-bold text-indigo-400">Free</p>
            <p className="text-sm text-gray-400">100 credits/month</p>
          </div>
          <button className="btn-primary">Upgrade</button>
        </div>
      </div>
      <div className="card">
        <h2 className="font-semibold mb-4">Usage</h2>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Processing minutes</span>
            <span>0 / 50</span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: '0%' }} />
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Rendering minutes</span>
            <span>0 / 20</span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: '0%' }} />
          </div>
        </div>
      </div>
      <div className="card">
        <h2 className="font-semibold mb-4">Pricing</h2>
        <div className="grid gap-3">
          {[
            { name: 'Pro', price: '$19/mo', credits: '500/mo' },
            { name: 'Enterprise', price: 'Custom', credits: 'Unlimited' },
          ].map(plan => (
            <div key={plan.name} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
              <div>
                <p className="font-semibold">{plan.name}</p>
                <p className="text-sm text-gray-400">{plan.credits} credits</p>
              </div>
              <p className="font-bold">{plan.price}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
