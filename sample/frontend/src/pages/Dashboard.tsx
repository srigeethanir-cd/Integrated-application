import React from 'react';
import {
  HeroBanner,
  MetricCards,
  EpicsOverview,
  RecentActivity,
} from '@/components/dashboard';
import { useWebSocket } from '@/hooks/useWebSocket';
import { usePipelineStatus } from '@/hooks/useDashboard';

/**
 * Main Dashboard page — purely presentational.
 * All data is fetched by child components through their own hooks.
 * WebSocket connection provides real-time push updates.
 */
const Dashboard: React.FC = () => {
  // Establish WebSocket for real-time pipeline updates
  const { connected } = useWebSocket('/pipeline', true);
  const { refetch: refetchPipeline } = usePipelineStatus();

  // When WS sends an update, trigger a manual refetch of pipeline status
  React.useEffect(() => {
    if (connected) {
      // Refetch once on WS connect
      refetchPipeline();
    }
  }, [connected, refetchPipeline]);

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Row 1: Hero banner */}
      <HeroBanner />

      {/* Row 2: 6 metric cards */}
      <MetricCards />

      {/* Row 3: Epics overview */}
      <EpicsOverview />

      {/* Row 4: Recent activity */}
      <RecentActivity />
    </div>
  );
};

export default Dashboard;
