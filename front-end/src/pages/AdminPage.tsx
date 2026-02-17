import PipelineControl from '../components/admin/PipelineControl';
import MetricsCards from '../components/admin/MetricsCards';
import DriftMonitor from '../components/admin/DriftMonitor';
import DatabaseStats from '../components/admin/DatabaseStats';
import CustomerExplorer from '../components/admin/CustomerExplorer';

export default function AdminPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-metro-gray-900">Admin ML Dashboard</h2>
        <p className="text-sm text-metro-gray-500 mt-1">
          Control pipeline, monitorizare drift, si metrici model
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Pipeline + Metrics */}
        <div className="lg:col-span-2 space-y-6">
          <PipelineControl />
          <MetricsCards />
          <DriftMonitor />
        </div>

        {/* Right column: Stats */}
        <div className="space-y-6">
          <DatabaseStats />
        </div>
      </div>

      {/* Customer Explorer - full width */}
      <div className="mt-6">
        <CustomerExplorer />
      </div>
    </div>
  );
}
