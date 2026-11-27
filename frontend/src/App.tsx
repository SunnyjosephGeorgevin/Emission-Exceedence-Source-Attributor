import { Route, Routes } from 'react-router-dom'
import Layout from './layouts/Layout'
import Overview from './pages/Overview'
import Investigations from './pages/Investigations'
import NewInvestigation from './pages/NewInvestigation'
import Details from './pages/Details'
import Approvals from './pages/Approvals'
import System from './pages/System'
import { Picker, Settings } from './pages/Misc'
export default function App() {
  return (<Routes><Route element={<Layout />}>
    <Route index element={<Overview />} /><Route path="investigations" element={<Investigations />} />
    <Route path="investigations/:id" element={<Details />} /><Route path="new" element={<NewInvestigation />} />
    <Route path="air-quality" element={<Picker title="Air Quality Monitoring" />} /><Route path="facilities" element={<Picker title="Facility Analysis" />} />
    <Route path="approvals" element={<Approvals />} /><Route path="system" element={<System />} /><Route path="settings" element={<Settings />} />
  </Route></Routes>)
}
