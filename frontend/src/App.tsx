import { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import GraphView from './pages/GraphView';
import { motion, AnimatePresence } from 'framer-motion';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="h-full"
        >
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'graph' && <GraphView />}
          {activeTab === 'anomalies' && <div className="p-8 text-center text-gray-500">Anomalies Module (Coming Soon)</div>}
          {activeTab === 'evidence' && <div className="p-8 text-center text-gray-500">Evidence Module (Coming Soon)</div>}
        </motion.div>
      </AnimatePresence>
    </Layout>
  );
}
