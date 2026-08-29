import type { ReactNode } from 'react';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: ReactNode;
  activeTab: string;
  setActiveTab: (id: string) => void;
}

export default function Layout({ children, activeTab, setActiveTab }: LayoutProps) {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950 overflow-hidden text-gray-900 dark:text-gray-100">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-100/40 via-transparent to-transparent dark:from-blue-900/20 z-0"></div>
      
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 relative z-10 overflow-y-auto flex flex-col">
        <header className="sticky top-0 z-20 h-16 w-full glass-panel dark:glass-panel-dark flex items-center px-6 shadow-sm">
          <h1 className="text-xl font-semibold tracking-tight">Investigator UI</h1>
        </header>
        <div className="p-6 flex-1 flex flex-col">
          {children}
        </div>
      </main>
    </div>
  );
}
