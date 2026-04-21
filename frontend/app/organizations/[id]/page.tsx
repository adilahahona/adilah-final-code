'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { apiClient, Organization, ReportingPeriod } from '@/lib/api';

export default function OrganizationDetailPage() {
  const params = useParams();
  const orgId = Number(params.id);

  const [organization, setOrganization] = useState<Organization | null>(null);
  const [periods, setPeriods] = useState<ReportingPeriod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [org, periodsList] = await Promise.all([
          apiClient.getOrganization(orgId),
          apiClient.getOrganizationPeriods(orgId),
        ]);
        setOrganization(org);
        setPeriods(periodsList);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [orgId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error || !organization) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">Error: {error || 'Organization not found'}</div>
      </div>
    );
  }

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
          Back to Organizations
        </Link>

        <div className="bg-white shadow-sm rounded-lg overflow-hidden mb-8">
          <div className="px-6 py-8">
            <h1 className="text-3xl font-bold text-gray-900">{organization.name}</h1>
            <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
              {organization.sector && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Sector</dt>
                  <dd className="mt-1 text-sm text-gray-900">{organization.sector}</dd>
                </div>
              )}
              {organization.country && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Country</dt>
                  <dd className="mt-1 text-sm text-gray-900">{organization.country}</dd>
                </div>
              )}
              {organization.external_id && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">External ID</dt>
                  <dd className="mt-1 text-sm font-mono text-gray-900">{organization.external_id}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-gray-500">Periods</dt>
                <dd className="mt-1 text-sm text-gray-900">{periods.length} reporting period{periods.length !== 1 ? 's' : ''}</dd>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Reporting Periods</h2>
          </div>

          <div className="divide-y divide-gray-200">
            {periods.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500">
                No reporting periods found for this organization.
              </div>
            ) : (
              periods.map((period) => (
                <Link
                  key={period.id}
                  href={`/organizations/${orgId}/periods/${period.id}`}
                  className="block px-6 py-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        {new Date(period.period_start).toLocaleDateString()} - {new Date(period.period_end).toLocaleDateString()}
                      </h3>
                      <p className="mt-1 text-sm text-gray-500 capitalize">{period.period_type}</p>
                    </div>
                    <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
