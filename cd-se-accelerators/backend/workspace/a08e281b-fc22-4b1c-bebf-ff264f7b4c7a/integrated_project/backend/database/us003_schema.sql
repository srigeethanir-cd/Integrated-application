-- Database Migration for US003: View Dashboard

CREATE TABLE IF NOT EXISTS tbl_dashboard_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_key VARCHAR(100) NOT NULL,
    metric_value NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    category VARCHAR(100) DEFAULT 'system',
    details JSONB DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tbl_dashboard_metrics_metric_key ON tbl_dashboard_metrics(metric_key);
