import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Server, Monitor, Shield, AlertCircle, CheckCircle, XCircle, Search } from 'lucide-react';
import { format } from 'date-fns';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1';

interface Host {
  id: number;
  hostname: string;
  ip_address: string | null;
  status: string;
  os_type: string | null;
  cloud_provider: string | null;
  last_seen: string;
  created_at: string;
}

export default function Hosts() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const queryClient = useQueryClient();

  const { data: hosts, isLoading } = useQuery<Host[]>({
    queryKey: ['hosts', statusFilter],
    queryFn: async () => {
      let url = `${API_URL}/hosts?`;
      if (statusFilter !== 'all') url += `status=${statusFilter}&`;
      const response = await axios.get(url);
      return response.data;
    },
  });

  const quarantineMutation = useMutation({
    mutationFn: async (hostId: number) => {
      await axios.post(`${API_URL}/hosts/${hostId}/quarantine`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hosts'] });
    },
  });

  const releaseMutation = useMutation({
    mutationFn: async (hostId: number) => {
      await axios.post(`${API_URL}/hosts/${hostId}/release`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hosts'] });
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'quarantined': return <XCircle className="h-5 w-5 text-red-500" />;
      case 'offline': return <Monitor className="h-5 w-5 text-gray-500" />;
      case 'compromised': return <AlertCircle className="h-5 w-5 text-red-500" />;
      default: return <Server className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-900 text-green-300';
      case 'quarantined': return 'bg-red-900 text-red-300';
      case 'offline': return 'bg-gray-700 text-gray-300';
      case 'compromised': return 'bg-red-900 text-red-300';
      default: return 'bg-gray-700 text-gray-300';
    }
  };

  const filteredHosts = hosts?.filter(host =>
    host.hostname.toLowerCase().includes(searchQuery.toLowerCase()) ||
    host.ip_address?.includes(searchQuery)
  ) || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Protected Hosts</h1>
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search hosts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          >
            <option value="all">All Status</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="quarantined">Quarantined</option>
            <option value="compromised">Compromised</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          <div className="col-span-full text-center py-8 text-gray-400">Loading hosts...</div>
        ) : filteredHosts.length === 0 ? (
          <div className="col-span-full text-center py-8 text-gray-400">No hosts found</div>
        ) : (
          filteredHosts.map((host) => (
            <div key={host.id} className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(host.status)}
                  <div>
                    <h3 className="text-white font-semibold">{host.hostname}</h3>
                    <p className="text-gray-400 text-sm">{host.ip_address || 'No IP'}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(host.status)}`}>
                  {host.status}
                </span>
              </div>

              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">OS:</span>
                  <span className="text-white">{host.os_type || 'Unknown'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Cloud:</span>
                  <span className="text-white">{host.cloud_provider || 'On-Premise'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Last Seen:</span>
                  <span className="text-white">{format(new Date(host.last_seen), 'MMM d, HH:mm')}</span>
                </div>
              </div>

              <div className="mt-4 flex space-x-2">
                {host.status === 'quarantined' ? (
                  <button
                    onClick={() => releaseMutation.mutate(host.id)}
                    className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Release
                  </button>
                ) : (
                  <button
                    onClick={() => quarantineMutation.mutate(host.id)}
                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Quarantine
                  </button>
                )}
                <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm font-medium transition-colors">
                  Details
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
