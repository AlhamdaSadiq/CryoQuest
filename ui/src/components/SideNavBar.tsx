import React from 'react';
import { SystemTab } from '../types';

interface SideNavBarProps {
  activeTab: SystemTab;
  setActiveTab: (tab: SystemTab) => void;
  onInitiateAscent: () => void;
  onOpenSettings: () => void;
  hazardCount: number;
}

export const SideNavBar: React.FC<SideNavBarProps> = ({
  activeTab,
  setActiveTab,
  onInitiateAscent,
  onOpenSettings,
  hazardCount,
}) => {
  const navItems: { id: SystemTab; label: string; icon: string; badge?: number }[] = [
    { id: 'mission_control', label: 'Mission Control', icon: 'dashboard' },
    { id: 'telemetry', label: 'Telemetry', icon: 'monitor_heart' },
    { id: 'trajectory', label: 'Trajectory', icon: 'route' },
    { id: 'navigation', label: 'Navigation', icon: 'explore' },
    { id: 'diagnostics', label: 'Diagnostics', icon: 'settings_suggest', badge: hazardCount > 0 ? hazardCount : undefined },
  ];

  return (
    <aside className="w-[280px] h-screen fixed left-0 top-0 border-r border-[#1F1F1F] bg-[#0A0A0A] flex flex-col py-6 px-4 z-50 select-none">
      {/* Header Logo */}
      <div className="px-2 mb-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-[#3B82F6] flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
          <span
            className="material-symbols-outlined text-xl"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            rocket_launch
          </span>
        </div>
        <div>
          <h1 className="font-['Space_Grotesk'] text-sm text-[#E5E5E5] font-bold tracking-tight">
            LUNAR COMMAND
          </h1>
          <p className="font-['JetBrains_Mono'] text-[11px] text-[#737373]">
            BENTO SECTOR-7
          </p>
        </div>
      </div>

      {/* Navigation Group */}
      <nav className="flex-1 flex flex-col gap-1.5">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[#737373] px-3 mb-2 block">
          Core Workspaces
        </span>

        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center justify-between px-3.5 py-3 rounded-xl transition-all duration-150 group cursor-pointer ${
                isActive
                  ? 'bg-[#1A1A1A] text-white font-semibold border border-[#2A2A2A] shadow-sm'
                  : 'text-[#A3A3A3] hover:bg-[#141414] hover:text-white'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                    isActive
                      ? 'bg-[#3B82F6] text-white glow-active'
                      : 'bg-[#161616] text-[#737373] group-hover:text-white group-hover:bg-[#222222]'
                  }`}
                >
                  <span className="material-symbols-outlined text-lg">{item.icon}</span>
                </div>
                <span className="text-xs font-medium tracking-wide">{item.label}</span>
              </div>

              {item.badge && (
                <span className="text-[10px] bg-[#EF4444]/20 text-[#EF4444] border border-[#EF4444]/40 px-2 py-0.5 rounded-full font-mono font-bold">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Actions */}
      <div className="pt-4 border-t border-[#1A1A1A] flex flex-col gap-3">
        <button
          onClick={onInitiateAscent}
          className="w-full bg-[#3B82F6] hover:bg-[#2563EB] text-white text-xs font-semibold rounded-xl py-3 px-4 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20 cursor-pointer active:scale-[0.98]"
        >
          <span className="material-symbols-outlined text-base">rocket</span>
          INITIATE ASCENT
        </button>

        <div className="flex justify-between items-center px-2 pt-1">
          <button
            onClick={onOpenSettings}
            className="text-[#737373] hover:text-white transition-colors flex items-center gap-1.5 text-xs cursor-pointer"
          >
            <span className="material-symbols-outlined text-base">settings</span> Settings
          </button>
          <button
            onClick={() => setActiveTab('diagnostics')}
            className="text-[#737373] hover:text-white transition-colors flex items-center gap-1.5 text-xs cursor-pointer"
          >
            <span className="material-symbols-outlined text-base">help</span> Help
          </button>
        </div>
      </div>
    </aside>
  );
};
