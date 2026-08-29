import { Home, Share2, AlertCircle, FileText, Settings } from 'lucide-react';
import { motion } from 'framer-motion';

const navItems = [
  { icon: Home, label: 'Dashboard', id: 'dashboard' },
  { icon: Share2, label: 'Knowledge Graph', id: 'graph' },
  { icon: AlertCircle, label: 'Anomalies', id: 'anomalies' },
  { icon: FileText, label: 'Evidence', id: 'evidence' },
];

export default function Sidebar({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (id: string) => void }) {
  return (
    <aside className="w-64 relative z-20 flex flex-col h-full glass-panel dark:glass-panel-dark border-r border-gray-200 dark:border-gray-800">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold">
            CIP
          </div>
          <span className="font-semibold text-lg tracking-tight">Intelligence</span>
        </div>
        
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.id === activeTab;
            
            return (
              <motion.button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                whileHover={{ scale: 0.98 }}
                whileTap={{ scale: 0.95 }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive 
                    ? 'bg-blue-600 text-white shadow-sm' 
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100/50 dark:hover:bg-gray-800/50'
                }`}
              >
                <Icon size={18} />
                {item.label}
              </motion.button>
            );
          })}
        </nav>
      </div>
      
      <div className="mt-auto p-6">
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 transition-colors">
          <Settings size={18} />
          Settings
        </button>
      </div>
    </aside>
  );
}
