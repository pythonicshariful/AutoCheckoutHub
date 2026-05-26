"use client";

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ShoppingCart, Activity, Target, Settings, Play, Square, Plus, Users, Trash2, Loader2 } from 'lucide-react';

export default function Dashboard() {
  const [skus, setSkus] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [newSku, setNewSku] = useState("");
  const [selectedSite, setSelectedSite] = useState("target");
  const [quantity, setQuantity] = useState(1);
  const [chromeVersion, setChromeVersion] = useState("auto");
  const [detectedChromeVersion, setDetectedChromeVersion] = useState<any>(null);

  const fetchDashboardData = async () => {
    try {
      const skusRes = await fetch("http://localhost:8000/skus");
      if (skusRes.ok) setSkus(await skusRes.json());
      
      const tasksRes = await fetch("http://localhost:8000/tasks");
      if (tasksRes.ok) setTasks(await tasksRes.json());
      
      const logsRes = await fetch("http://localhost:8000/logs");
      if (logsRes.ok) setLogs(await logsRes.json());
    } catch (err) {
      console.error("Failed to connect to backend", err);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchSystemChromeVersion = async () => {
      try {
        const res = await fetch("http://localhost:8000/system/chrome-version");
        if (res.ok) {
          const data = await res.json();
          if (data.status === "success" && data.major_version) {
            setDetectedChromeVersion(data.major_version);
          }
        }
      } catch (err) {
        console.error("Failed to fetch system Chrome version", err);
      }
    };
    fetchSystemChromeVersion();
  }, []);

  const handleAddSku = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSku) return;
    
    try {
      const resolvedVersion = selectedSite === 'walmart' ? 'auto' : chromeVersion;
      await fetch(`http://localhost:8000/skus?sku_id=${newSku}&site=${selectedSite}&quantity=${quantity}&chrome_version=${resolvedVersion}`, {
        method: 'POST'
      });
      setNewSku("");
      fetchDashboardData();
    } catch (err) {
      console.error("Failed to add SKU", err);
    }
  };

  const handleRunTask = async (sku_id: any) => {
    try {
      const res = await fetch(`http://localhost:8000/tasks/run/${sku_id}`, { method: 'POST' });
      if (!res.ok) {
        const errData = await res.json();
        alert(`Failed to run: ${errData.detail || 'Unknown error'}`);
      }
      fetchDashboardData();
    } catch (err) {
      alert("Failed to reach backend to run task");
      console.error("Failed to run task", err);
    }
  };

  const handleResumeTask = async (task_id: any) => {
    try {
      const res = await fetch(`http://localhost:8000/tasks/${task_id}/input?input_text=enter`, { method: 'POST' });
      if (!res.ok) {
        const errData = await res.json();
        alert(`Failed to resume: ${errData.detail || 'Unknown error'}`);
      }
      fetchDashboardData();
    } catch (err) {
      alert("Failed to reach backend to resume task");
      console.error("Failed to resume task", err);
    }
  };

  const handleDeleteSku = async (id: any) => {
    if (!confirm("Are you sure you want to delete this SKU?")) return;
    try {
      const res = await fetch(`http://localhost:8000/skus/${id}`, { method: 'DELETE' });
      if (!res.ok) alert("Failed to delete SKU");
      fetchDashboardData();
    } catch (err) {
      console.error("Failed to delete SKU", err);
    }
  };

  const handleStopTask = async (task_id: any) => {
    try {
      const res = await fetch(`http://localhost:8000/tasks/${task_id}/stop`, { method: 'POST' });
      if (!res.ok) {
        const errData = await res.json();
        alert(`Failed to stop: ${errData.detail || 'Unknown error'}`);
      }
      fetchDashboardData();
    } catch (err) {
      alert("Failed to reach backend to stop task");
      console.error("Failed to stop task", err);
    }
  };

  const handleClearHistory = async () => {
    if (!confirm("Are you sure you want to clear all tasks and logs?")) return;
    try {
      const res = await fetch("http://localhost:8000/tasks/clear", { method: 'POST' });
      if (res.ok) {
        fetchDashboardData();
      } else {
        alert("Failed to clear tasks history");
      }
    } catch (err) {
      alert("Failed to reach backend");
      console.error(err);
    }
  };

  const activeCount = tasks.filter(t => t.status === 'running' || t.status === 'paused').length;
  const successCount = tasks.filter(t => t.status === 'completed').length;
  const failedCount = tasks.filter(t => t.status === 'failed').length;

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-gray-100 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex justify-between items-center glass-panel p-6 rounded-2xl shadow-lg border border-neutral-800">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent flex items-center gap-3">
              <ShoppingCart className="w-8 h-8 text-blue-500" />
              AutoCheckout Hub
            </h1>
            <p className="text-gray-400 mt-1">Unified management for Target, Walmart, BestBuy & Topps</p>
          </div>
          <div className="flex gap-4">
            <button 
              onClick={handleClearHistory} 
              title="Clear Tasks & Logs History" 
              className="p-3 bg-red-950/20 hover:bg-red-900/30 border border-red-900/30 rounded-xl transition-colors text-red-400 flex items-center gap-2"
            >
              <Trash2 className="w-5 h-5" />
              <span className="text-xs font-semibold hidden md:inline">Clear Feed</span>
            </button>
            <button className="p-3 bg-neutral-800 hover:bg-neutral-700 rounded-xl transition-colors">
              <Users className="w-5 h-5 text-gray-300" />
            </button>
            <button className="p-3 bg-neutral-800 hover:bg-neutral-700 rounded-xl transition-colors">
              <Settings className="w-5 h-5 text-gray-300" />
            </button>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { label: "Active Tasks", value: activeCount, icon: Activity, color: "text-blue-500" },
            { label: "Successful Checkouts", value: successCount, icon: ShoppingCart, color: "text-green-500" },
            { label: "Failed Attempts", value: failedCount, icon: Target, color: "text-red-500" },
            { label: "Monitored SKUs", value: skus.length, icon: BoxIcon, color: "text-purple-500" },
          ].map((stat, i) => (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              key={i} 
              className="glass-panel p-6 rounded-2xl flex items-center justify-between glow-effect"
            >
              <div>
                <p className="text-gray-400 text-sm font-medium uppercase tracking-wider">{stat.label}</p>
                <p className="text-3xl font-bold mt-2">{stat.value}</p>
              </div>
              <div className={`p-4 bg-neutral-800/50 rounded-xl ${stat.color}`}>
                <stat.icon className="w-6 h-6" />
              </div>
            </motion.div>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* SKU Management */}
          <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-neutral-800">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-400" /> Monitored SKUs
            </h2>
            
            <form onSubmit={handleAddSku} className="flex gap-4 mb-8 bg-neutral-900/50 p-4 rounded-xl border border-neutral-800">
              <input 
                type="text" 
                placeholder="Enter SKU..." 
                className="bg-neutral-800 border-none rounded-lg px-4 py-2 flex-1 focus:ring-2 focus:ring-blue-500 outline-none"
                value={newSku}
                onChange={(e) => setNewSku(e.target.value)}
              />
              <select 
                className="bg-neutral-800 border-none rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                value={selectedSite}
                onChange={(e) => {
                  const site = e.target.value;
                  setSelectedSite(site);
                  if (site === 'walmart') {
                    setChromeVersion('auto');
                  }
                }}
              >
                <option value="target">Target</option>
                <option value="walmart">Walmart</option>
                <option value="bestbuy">BestBuy</option>
                <option value="topps">Topps</option>
              </select>
              <input 
                type="number" 
                min="1" max="10"
                className="bg-neutral-800 border-none rounded-lg px-4 py-2 w-20 focus:ring-2 focus:ring-blue-500 outline-none"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value))}
              />
              <select 
                className={`bg-neutral-800 border-none rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none ${selectedSite === 'walmart' ? 'opacity-50 cursor-not-allowed text-gray-500' : ''}`}
                value={chromeVersion}
                onChange={(e) => setChromeVersion(e.target.value)}
                disabled={selectedSite === 'walmart'}
              >
                {selectedSite === 'walmart' ? (
                  <option value="auto">Auto (Playwright)</option>
                ) : (
                  <>
                    <option value="auto">Auto {detectedChromeVersion ? `(${detectedChromeVersion})` : ""}</option>
                    <option value="149">v149</option>
                    <option value="148">v148</option>
                    <option value="147">v147</option>
                    <option value="146">v146</option>
                    <option value="145">v145</option>
                  </>
                )}
              </select>
              <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors font-medium">
                <Plus className="w-4 h-4" /> Add
              </button>
            </form>

            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-gray-400 border-b border-neutral-800">
                    <th className="pb-3 font-medium">SKU</th>
                    <th className="pb-3 font-medium">Site</th>
                    <th className="pb-3 font-medium">Quantity</th>
                    <th className="pb-3 font-medium">Chrome</th>
                    <th className="pb-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {skus.map((sku) => {
                    const isRunning = tasks.some(t => t.sku_id === sku.id && (t.status === 'running' || t.status === 'paused'));
                    return (
                    <motion.tr 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      key={sku.id} 
                      className="border-b border-neutral-800/50 hover:bg-neutral-800/20 transition-colors"
                    >
                      <td className="py-4 font-mono">{sku.sku_id}</td>
                      <td className="py-4 capitalize">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          sku.site === 'target' ? 'bg-red-500/20 text-red-400' :
                          sku.site === 'walmart' ? 'bg-blue-500/20 text-blue-400' :
                          sku.site === 'bestbuy' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-indigo-500/20 text-indigo-400'
                        }`}>
                          {sku.site}
                        </span>
                      </td>
                      <td className="py-4">{sku.quantity}</td>
                      <td className="py-4 font-mono text-sm">
                        {sku.site === 'walmart' ? (
                          <span className="text-gray-500 text-xs">Playwright</span>
                        ) : sku.chrome_version === 'auto' ? (
                          <span className="text-blue-400 text-xs flex items-center gap-1">
                            <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                            Auto {detectedChromeVersion ? `(${detectedChromeVersion})` : ""}
                          </span>
                        ) : (
                          <span className="text-purple-400 text-xs bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20 font-medium">
                            v{sku.chrome_version}
                          </span>
                        )}
                      </td>
                      <td className="py-4 flex justify-end gap-2">
                        {isRunning ? (
                          <>
                            <button disabled title="Task is running" className="p-2 bg-blue-500/10 text-blue-500 rounded-lg cursor-not-allowed">
                              <Loader2 className="w-4 h-4 animate-spin" />
                            </button>
                            <button onClick={() => {
                              const activeTask = tasks.find(t => t.sku_id === sku.id && (t.status === 'running' || t.status === 'paused'));
                              if (activeTask) handleStopTask(activeTask.id);
                            }} title="Stop Task" className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg transition-colors">
                              <Square className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <>
                            <button onClick={() => handleRunTask(sku.id)} title="Run Task" className="p-2 bg-green-500/10 hover:bg-green-500/20 text-green-500 rounded-lg transition-colors">
                              <Play className="w-4 h-4" />
                            </button>
                            <button onClick={() => handleDeleteSku(sku.id)} title="Delete SKU" className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg transition-colors">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </td>
                    </motion.tr>
                  )})}
                </tbody>
              </table>
            </div>
          </div>

          {/* Active Tasks Feed */}
          <div className="glass-panel p-6 rounded-2xl border border-neutral-800">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-400" /> Active Tasks
            </h2>
            <div className="space-y-4">
              {tasks.map((task) => (
                <div key={task.id} className="p-4 bg-neutral-900/50 rounded-xl border border-neutral-800">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-mono text-sm">{task.sku_id}</span>
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                      task.status === 'running' ? 'bg-blue-500/20 text-blue-400 animate-pulse' :
                      task.status === 'paused' ? 'bg-orange-500/20 text-orange-400' :
                      task.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {task.status}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <p className="text-xs text-gray-400 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-500 inline-block"></span>
                      Monitoring {task.site}...
                    </p>
                    {task.status === 'paused' && (
                      <button 
                        onClick={() => handleResumeTask(task.id)}
                        className="text-xs bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded-lg transition-colors"
                      >
                        Resume
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* System Logs */}
            <h2 className="text-xl font-semibold mb-6 mt-10 flex items-center gap-2">
              <Activity className="w-5 h-5 text-green-400" /> System Logs
            </h2>
            <div className="space-y-3 h-64 overflow-y-auto pr-2">
              {logs.map((log) => (
                <div key={log.id} className="p-3 bg-neutral-900/80 rounded-lg border border-neutral-800 text-xs font-mono">
                  <div className="flex justify-between text-gray-500 mb-1">
                    <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                    <span className={
                      log.level === 'error' ? 'text-red-400' : 
                      log.level === 'success' ? 'text-green-400' : 'text-blue-400'
                    }>[{log.level.toUpperCase()}]</span>
                  </div>
                  <p className="text-gray-300">{log.message}</p>
                </div>
              ))}
              {logs.length === 0 && <p className="text-gray-500 text-sm">No logs yet.</p>}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

function BoxIcon(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
      <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
      <line x1="12" y1="22.08" x2="12" y2="12"></line>
    </svg>
  );
}
