// Update App.tsx with all routes including AI Analysis, Reframe, and Scheduled Posts
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/queryClient'
import Layout from './components/Layout'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import Editor from './pages/Editor'
import Settings from './pages/Settings'
import Billing from './pages/Billing'
import NotFound from './pages/NotFound'
import AIAnalysis from './pages/AIAnalysis'
import Reframe from './pages/Reframe'
import Scheduled from './pages/Scheduled'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <NotFound />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'projects', element: <Projects /> },
      { path: 'projects/:id', element: <ProjectDetail /> },
      { path: 'projects/:id/ai', element: <AIAnalysis /> },
      { path: 'editor/:clipId', element: <Editor /> },
      { path: 'reframe/:clipId', element: <Reframe /> },
      { path: 'settings', element: <Settings /> },
      { path: 'billing', element: <Billing /> },
      { path: 'scheduled', element: <Scheduled /> },
    ],
  },
  {
    path: '/login', element: <Login />,
  },
  {
    path: '/signup', element: <Signup />,
  },
])

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}

export default App