import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Shield, AlertTriangle, Server, Activity, Clock, CheckCircle } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

interface DashboardStats {
  total_hosts: number;
  online_hosts: number;
  quarantined_hosts: number;
  total_alerts: number;
  critical_alerts: number;
  high_risk_events: number;
  protection_status: string;
}

interface ThreatTrend {
  date: string;
  count: number;
  avg_risk_score: number;
}

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/dashboard/stats`);
      return response.data;
    },
  });

  const { data: trends, isLoading: trendsLoading } = useQuery<ThreatTrend[]>({
    queryKey: ['threat-trends'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/dashboard/trends?days=7`);
      return response.data;
    },
  });

  const { data: protectionStatus } = useQuery({
    queryKey: ['protection-status'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/dashboard/protection-status`);
      return response.data;
    },
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Security Dashboard</h1>
        <div className="flex items-center space-x-2">
          <span className="text-gray-400">Last updated:</span>
          <span className="text-white">{new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Protected Hosts"
          value={stats?.total_hosts || 0}
          icon={<Server className="h-8 w-8 text-blue-500" />}
          subtitle={`${stats?.online_hosts || 0} online`}
        />
        <StatCard
          title="Active Alerts"
          value={stats?.total_alerts || 0}
          icon={<AlertTriangle className="h-8 w-8 text-yellow-500" />}
          subtitle={`${stats?.critical_alerts || 0} critical`}
          highlight={stats?.critical_alerts > 0}
        />
        <StatCard
          title="High Risk Events"
          value={stats?.high_risk_events || 0}
          icon={<Activity className="h-8 w-8 text-red-500" />}
          subtitle="Last 24 hours"
          highlight={(stats?.high_risk_events || 0) > 0}
        />
        <StatCard
          title="Protection Status"
          value={stats?.protection_status || 'Unknown'}
          icon={<Shield className="h-8 w-8 text-green-500" />}
          subtitle={protectionStatus?.agents_online ? `${protectionStatus.agents_online} agents online` : ''}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Threat Trends (7 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
              <Line type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6' }} />
              <Line type="monotone" dataKey="avg_risk_score" stroke="#EF4444" strokeWidth={2} dot={{ fill: '#EF4444' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Protection System Status</h2>
          <div className="space-y-4">
            <StatusItem
              name="ML Models"
              status={protectionStatus?.ml_models_loaded ? 'active' : 'inactive'}
              icon={<CheckCircle className="h-5 w-5" />}
            />
            <StatusItem
              name="Real-time Protection"
              status={protectionStatus?.real_time_protection ? 'active' : 'inactive'}
              icon={<CheckCircle className="h-5 w-5" />}
            />
            <StatusItem
              name="Auto-Response"
              status={protectionStatus?.auto_response_enabled ? 'active' : 'inactive'}
              icon={<CheckCircle className="h-5 w-5" />}
            />
            <StatusItem
              name="Agents Connected"
              status={protectionStatus?.agents_online > 0 ? 'active' : 'inactive'}
              details={`${protectionStatus?.agents_online || 0} of ${protectionStatus?.agents_total || 0}`}
            />
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <Clock className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-white font-medium">Security scan completed</p>
                  <p className="text-gray-400 text-sm">Host srv-{i.toString().padStart(3, '0')}</p>
                </div>
              </div>
              <span className="text-gray-400 text-sm">{i * 5} min ago</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  subtitle,
  highlight = false,
}: {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  subtitle: string;
  highlight?: boolean;
}) {
  return (
    <div className={`bg-gray-800 rounded-lg p-6 ${highlight ? 'ring-2 ring-red-500' : ''}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className={`text-3xl font-bold mt-2 ${highlight ? 'text-red-400' : 'text-white'}`}>
            {value}
          </p>
          <p className="text-gray-500 text-sm mt-1">{subtitle}</p>
        </div>
        {icon}
      </div>
    </div>
  );
}

function StatusItem({
  name,
  status,
  icon,
  details,
}: {
  name: string;
  status: 'active' | 'inactive';
  icon?: React.ReactNode;
  details?: string;
}) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
      <div className="flex items-center space-x-3">
        {icon}
        <span className="text-white">{name}</span>
      </div>
      <div className="flex items-center space-x-2">
        {details && <span className="text-gray-400 text-sm">{details}</span>}
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            status === 'active'
              ? 'bg-green-900 text-green-300'
              : 'bg-red-900 text-red-300'
          }`}
        >
          {status}
        </span>
      </div>
    </div>
  );
}
