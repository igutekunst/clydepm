import { useEffect, useState } from 'react';
import { getPackageDetails } from '@/api/client';
import type { DependencyNode, DependencyWarning } from '@/api/client';

interface DependencyDetailsProps {
  packageId: string | null;
}

const formatBytes = (bytes: number): string => {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
};

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const DependencyDetails: React.FC<DependencyDetailsProps> = ({ packageId }) => {
  const [details, setDetails] = useState<DependencyNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!packageId) {
      setDetails(null);
      return;
    }

    const fetchDetails = async () => {
      try {
        setLoading(true);
        const data = await getPackageDetails(packageId);
        setDetails(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load package details');
        setDetails(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [packageId]);

  if (!packageId) {
    return <div>Select a package to view details</div>;
  }

  if (loading) {
    return <div>Loading package details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!details) {
    return null;
  }

  return (
    <div className="dependency-details">
      <h2>
        {details.name}@{details.version}
        {details.is_dev_dep && <span className="dev-badge">dev</span>}
      </h2>

      <div className="metrics">
        <div className="metric">
          <label>Size</label>
          <span className="value">{formatBytes(details.size)}</span>
        </div>
        <div className="metric">
          <label>Direct Dependencies</label>
          <span className="value">{details.direct_deps.length}</span>
        </div>
        <div className="metric">
          <label>Total Dependencies</label>
          <span className="value">{details.all_deps.length}</span>
        </div>
        <div className="metric">
          <label>Last Used</label>
          <span className="value">{formatDate(details.last_used)}</span>
        </div>
      </div>

      {details.has_warnings && (
        <div className="warnings">
          <h3>⚠️ Warnings</h3>
          <ul>
            {details.warnings?.map((warning: DependencyWarning) => (
              <li key={warning.id} className={`warning-${warning.level}`}>
                {warning.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="dependencies">
        <h3>Direct Dependencies</h3>
        <ul>
          {details.direct_deps.map((dep) => (
            <li key={dep}>{dep}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}; 