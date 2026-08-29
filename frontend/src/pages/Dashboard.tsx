import { motion } from 'framer-motion';
import { Users, Phone, MapPin, AlertTriangle } from 'lucide-react';
import { useEffect, useRef } from 'react';
import gsap from 'gsap';

const stats = [
  { label: 'Entities Discovered', value: 438, icon: Users, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
  { label: 'Phones Extracted', value: 94, icon: Phone, color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-900/20' },
  { label: 'Locations', value: 31, icon: MapPin, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
  { label: 'High Anomalies', value: 12, icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20' },
];

function StatCard({ stat, index }: { stat: typeof stats[0], index: number }) {
  const Icon = stat.icon;
  const numRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!numRef.current) return;
    
    // GSAP animation for the number counter
    const obj = { val: 0 };
    gsap.to(obj, {
      val: stat.value,
      duration: 2,
      ease: 'power3.out',
      delay: index * 0.1,
      onUpdate: () => {
        if (numRef.current) {
          numRef.current.innerText = Math.floor(obj.val).toString();
        }
      }
    });
  }, [stat.value, index]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, type: 'spring', damping: 1, stiffness: 100 }}
      className="glass-panel dark:glass-panel-dark p-5 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 shadow-sm"
    >
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-xl ${stat.bg} ${stat.color}`}>
          <Icon size={24} />
        </div>
        <div>
          <div ref={numRef} className="text-3xl font-bold tracking-tight">0</div>
          <div className="text-sm text-gray-500 dark:text-gray-400 font-medium">{stat.label}</div>
        </div>
      </div>
    </motion.div>
  );
}

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="display-text font-bold mb-1">Overview</h2>
          <p className="text-gray-500 dark:text-gray-400">Network insights for active cases.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <StatCard key={stat.label} stat={stat} index={i} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4, type: 'spring' }}
          className="lg:col-span-2 flex flex-col glass-panel dark:glass-panel-dark rounded-2xl border border-gray-200/50 dark:border-gray-800/50 shadow-sm p-6 min-h-[300px]"
        >
          <h3 className="text-lg font-semibold mb-4">Network Growth (Temporal)</h3>
          <div className="flex-1 flex items-center justify-center text-gray-400 bg-white/30 dark:bg-black/20 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
            Chart visualization goes here
          </div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, type: 'spring' }}
          className="glass-panel dark:glass-panel-dark rounded-2xl border border-gray-200/50 dark:border-gray-800/50 shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold mb-4">Recent Uploads</h3>
          <div className="space-y-4">
            {['FIR_001.pdf', 'FIR_002.pdf', 'CDR_Jan.csv'].map((file, idx) => (
              <motion.div 
                key={file}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + (idx * 0.1), type: 'spring' }}
                className="flex items-center justify-between p-3 rounded-lg bg-white/40 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-800"
              >
                <span className="font-medium text-sm">{file}</span>
                <span className="text-xs px-2 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full font-medium">Processed</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
