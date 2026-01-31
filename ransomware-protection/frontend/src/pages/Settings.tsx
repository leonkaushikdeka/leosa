import React, { useState } from 'react';
import { Shield, Cloud, Bell, Lock, Database, Save, RefreshCw } from 'lucide-react';

export default function Settings() {
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState({
    autoResponse: true,
    quarantineEnabled: true,
    notificationEmail: true,
    notificationSlack: false,
    detectionThreshold: 0.85,
    scanInterval: 60,
  });

  const tabs = [
    { id: 'general', label: 'General', icon: <Shield className="h-5 w-5" /> },
    { id: 'cloud', label: 'Cloud Providers', icon: <Cloud className="h-5 w-5" /> },
    { id: 'notifications', label: 'Notifications', icon: <Bell className="h-5 w-5" /> },
    { id: 'security', label: 'Security', icon: <Lock className="h-5 w-5" /> },
    { id: 'data', label: 'Data Retention', icon: <Database className="h-5 w-5" /> },
  ];

  const handleSave = () => {
    console.log('Saving settings...', settings);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <button
          onClick={handleSave}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
        >
          <Save className="h-5 w-5" />
          <span>Save Changes</span>
        </button>
      </div>

      <div className="flex space-x-6">
        <div className="w-64 space-y-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="flex-1 bg-gray-800 rounded-lg p-6">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">General Settings</h2>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">Auto-Response</p>
                    <p className="text-gray-400 text-sm">Automatically respond to detected threats</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.autoResponse}
                      onChange={(e) => setSettings({ ...settings, autoResponse: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">Quarantine Hosts</p>
                    <p className="text-gray-400 text-sm">Automatically quarantine compromised hosts</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.quarantineEnabled}
                      onChange={(e) => setSettings({ ...settings, quarantineEnabled: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div>
                  <p className="text-white font-medium mb-2">Detection Threshold</p>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={settings.detectionThreshold}
                    onChange={(e) => setSettings({ ...settings, detectionThreshold: parseFloat(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-gray-400 text-sm mt-1">
                    <span>Less Sensitive</span>
                    <span>{(settings.detectionThreshold * 100).toFixed(0)}%</span>
                    <span>More Sensitive</span>
                  </div>
                </div>

                <div>
                  <p className="text-white font-medium mb-2">Scan Interval (seconds)</p>
                  <input
                    type="number"
                    value={settings.scanInterval}
                    onChange={(e) => setSettings({ ...settings, scanInterval: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'cloud' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">Cloud Provider Configuration</h2>

              <div className="space-y-4">
                <div className="p-4 bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <Cloud className="h-6 w-6 text-orange-500" />
                      <span className="text-white font-medium">AWS</span>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  <div className="space-y-3">
                    <input
                      type="text"
                      placeholder="Region"
                      className="w-full px-4 py-2 bg-gray-600 border border-gray-500 rounded-lg text-white"
                    />
                    <input
                      type="password"
                      placeholder="Access Key"
                      className="w-full px-4 py-2 bg-gray-600 border border-gray-500 rounded-lg text-white"
                    />
                  </div>
                </div>

                <div className="p-4 bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <Cloud className="h-6 w-6 text-blue-500" />
                      <span className="text-white font-medium">Azure</span>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>

                <div className="p-4 bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <Cloud className="h-6 w-6 text-red-500" />
                      <span className="text-white font-medium">GCP</span>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">Notification Settings</h2>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-white font-medium">Email Notifications</p>
                    <p className="text-gray-400 text-sm">Receive alerts via email</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notificationEmail}
                      onChange={(e) => setSettings({ ...settings, notificationEmail: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-white font-medium">Slack Notifications</p>
                    <p className="text-gray-400 text-sm">Receive alerts in Slack</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notificationSlack}
                      onChange={(e) => setSettings({ ...settings, notificationSlack: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">Security Settings</h2>

              <div className="space-y-4">
                <div className="p-4 bg-gray-700 rounded-lg">
                  <h3 className="text-white font-medium mb-3">JWT Configuration</h3>
                  <div className="space-y-3">
                    <input
                      type="number"
                      defaultValue={30}
                      placeholder="Access Token Expiry (minutes)"
                      className="w-full px-4 py-2 bg-gray-600 border border-gray-500 rounded-lg text-white"
                    />
                    <input
                      type="number"
                      defaultValue={7}
                      placeholder="Refresh Token Expiry (days)"
                      className="w-full px-4 py-2 bg-gray-600 border border-gray-500 rounded-lg text-white"
                    />
                  </div>
                </div>

                <button className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg">
                  <RefreshCw className="h-5 w-5" />
                  <span>Rotate Encryption Keys</span>
                </button>
              </div>
            </div>
          )}

          {activeTab === 'data' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">Data Retention</h2>

              <div className="space-y-4">
                <div>
                  <p className="text-white font-medium mb-2">Audit Log Retention (days)</p>
                  <input
                    type="number"
                    defaultValue={365}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  />
                </div>

                <div>
                  <p className="text-white font-medium mb-2">Event Data Retention (days)</p>
                  <input
                    type="number"
                    defaultValue={90}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  />
                </div>

                <div>
                  <p className="text-white font-medium mb-2">Backup Retention (days)</p>
                  <input
                    type="number"
                    defaultValue={30}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
