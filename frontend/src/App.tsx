import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { CameraView } from './pages/CameraView';

export function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/camera/:id" element={<CameraView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
