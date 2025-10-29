import React, { useState, useEffect } from 'react';
import { reserveStudiesApi, type ReserveStudy } from '../api/reserves';

const ReserveStudiesPage: React.FC = () => {
  const [studies, setStudies] = useState<ReserveStudy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStudies();
  }, []);

  const fetchStudies = async () => {
    try {
      setLoading(true);
      const data = await reserveStudiesApi.list();
      setStudies(data);
    } catch (err) {
      setError('Failed to load reserve studies');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Reserve Studies</h1>
        <p className="mt-2 text-gray-600">
          Plan for capital expenditures over 5-30 year horizons
        </p>
      </div>

      {studies.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500 mb-4">No reserve studies found</p>
          <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Create First Study
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {studies.map((study) => (
            <div
              key={study.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{study.name}</h3>
                  <p className="text-gray-600 mt-1">
                    Study Date: {new Date(study.study_date).toLocaleDateString()}
                  </p>
                  <p className="text-gray-600">
                    Horizon: {study.horizon_years} years | Inflation: {study.inflation_rate}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Reserve Balance</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${parseFloat(study.current_reserve_balance).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="mt-4 flex gap-2">
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                  {study.components?.length || 0} Components
                </span>
                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                  {study.scenarios?.length || 0} Scenarios
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReserveStudiesPage;
