'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient, ModelVersion } from '@/lib/api';

export default function ModelsPage() {
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchModels() {
      try {
        const data = await apiClient.getModels(filter || undefined);
        setModels(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load models');
      } finally {
        setLoading(false);
      }
    }

    fetchModels();
  }, [filter]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading models...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'bg-green-100 text-green-800';
      case 'TRAINED':
        return 'bg-yellow-100 text-yellow-800';
      case 'DEPRECATED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-6"
        >
          <svg className="mr-2 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back to Dashboard
        </Link>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Model Registry</h1>
          <p className="mt-2 text-gray-600">
            Manage and track machine learning models for ESG scoring
          </p>
        </div>

        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Models</h2>
              <div className="flex gap-2">
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="block rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value="APPROVED">Approved</option>
                  <option value="TRAINED">Trained</option>
                  <option value="DEPRECATED">Deprecated</option>
                </select>
              </div>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              {models.length} model{models.length !== 1 ? 's' : ''} total
            </p>
          </div>

          <div className="overflow-x-auto">
            {models.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500">
                No models found. Train a model to get started.
              </div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Model Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Algorithm
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Val R²
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Val MAE
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {models.map((model) => (
                    <tr key={model.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{model.model_name}</div>
                        {model.description && (
                          <div className="text-sm text-gray-500">{model.description}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{model.algorithm}</div>
                        <div className="text-xs text-gray-500">
                          {Object.keys(model.hyperparameters || {}).length} params
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 text-xs font-semibold rounded-full ${getStatusColor(
                            model.status
                          )}`}
                        >
                          {model.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {model.val_metrics?.r2?.toFixed(4) || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {model.val_metrics?.mae?.toFixed(4) || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(model.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="mt-6 bg-white shadow-sm rounded-lg overflow-hidden p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Model Statistics</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm font-medium text-green-800">Approved Models</div>
              <div className="mt-1 text-2xl font-semibold text-green-900">
                {models.filter((m) => m.status === 'APPROVED').length}
              </div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="text-sm font-medium text-yellow-800">Trained Models</div>
              <div className="mt-1 text-2xl font-semibold text-yellow-900">
                {models.filter((m) => m.status === 'TRAINED').length}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm font-medium text-gray-800">Total Models</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">{models.length}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
