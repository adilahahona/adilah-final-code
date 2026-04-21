'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  apiClient,
  Organization,
  ReportingPeriod,
  CoverageResponse,
  Prediction,
} from '@/lib/api';

export default function PeriodDetailPage() {
  const params = useParams();
  const orgId = Number(params.id);
  const periodId = Number(params.periodId);

  const [organization, setOrganization] = useState<Organization | null>(null);
  const [period, setPeriod] = useState<ReportingPeriod | null>(null);
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [org, periods, cov, featureVectors] = await Promise.all([
          apiClient.getOrganization(orgId),
          apiClient.getOrganizationPeriods(orgId),
          apiClient.getCoverage(orgId, periodId),
          apiClient.getFeatureVectors(orgId, periodId),
        ]);

        setOrganization(org);
        const currentPeriod = periods.find((p) => p.id === periodId);
        setPeriod(currentPeriod || null);
        setCoverage(cov);

        // Fetch predictions for feature vectors
        if (featureVectors.length > 0) {
          const preds = await apiClient.getPredictions(featureVectors[0].id);
          setPredictions(preds);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [orgId, periodId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error || !organization || !period) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">Error: {error || 'Period not found'}</div>
      </div>
    );
  }

  const latestPrediction = predictions[0];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link
          href={`/organizations/${orgId}`}
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-6"
        >
          <svg className="mr-2 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back to {organization.name}
        </Link>

        <div className="bg-white shadow-sm rounded-lg overflow-hidden mb-8">
          <div className="px-6 py-6">
            <h1 className="text-2xl font-bold text-gray-900">
              {new Date(period.period_start).toLocaleDateString()} - {new Date(period.period_end).toLocaleDateString()}
            </h1>
            <p className="mt-1 text-sm text-gray-500 capitalize">{period.period_type} reporting period</p>
          </div>
        </div>

        {/* ESG Scores */}
        {latestPrediction && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            <div className="bg-white overflow-hidden shadow-sm rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">Composite Score</dt>
                <dd className="mt-1 text-3xl font-semibold text-gray-900">
                  {latestPrediction.composite_score.toFixed(1)}
                </dd>
              </div>
            </div>
            <div className="bg-green-50 overflow-hidden shadow-sm rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-green-800 truncate">Environmental</dt>
                <dd className="mt-1 text-3xl font-semibold text-green-900">
                  {latestPrediction.e_score?.toFixed(1) || 'N/A'}
                </dd>
              </div>
            </div>
            <div className="bg-blue-50 overflow-hidden shadow-sm rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-blue-800 truncate">Social</dt>
                <dd className="mt-1 text-3xl font-semibold text-blue-900">
                  {latestPrediction.s_score?.toFixed(1) || 'N/A'}
                </dd>
              </div>
            </div>
            <div className="bg-purple-50 overflow-hidden shadow-sm rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-purple-800 truncate">Governance</dt>
                <dd className="mt-1 text-3xl font-semibold text-purple-900">
                  {latestPrediction.g_score?.toFixed(1) || 'N/A'}
                </dd>
              </div>
            </div>
          </div>
        )}

        {/* Coverage */}
        {coverage && (
          <div className="bg-white shadow-sm rounded-lg overflow-hidden mb-8">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Data Coverage</h2>
            </div>
            <div className="px-6 py-6">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Overall Coverage</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {(coverage.overall_coverage * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${coverage.overall_coverage * 100}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-green-700">Environmental</span>
                    <span className="text-sm font-semibold text-green-900">
                      {(coverage.coverage_by_pillar.E * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${coverage.coverage_by_pillar.E * 100}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-blue-700">Social</span>
                    <span className="text-sm font-semibold text-blue-900">
                      {(coverage.coverage_by_pillar.S * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${coverage.coverage_by_pillar.S * 100}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-purple-700">Governance</span>
                    <span className="text-sm font-semibold text-purple-900">
                      {(coverage.coverage_by_pillar.G * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full"
                      style={{ width: `${coverage.coverage_by_pillar.G * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Prediction Drivers */}
        {latestPrediction && latestPrediction.drivers.length > 0 && (
          <div className="bg-white shadow-sm rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Top Score Drivers</h2>
              <p className="mt-1 text-sm text-gray-500">
                Features contributing most to the composite score
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Feature
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contribution
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Direction
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {latestPrediction.drivers.map((driver) => (
                    <tr key={driver.rank}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {driver.rank}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                        {driver.feature_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {driver.contribution.toFixed(4)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 text-xs font-semibold rounded-full ${
                            driver.direction === 'positive'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {driver.direction}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
