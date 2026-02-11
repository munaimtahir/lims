export interface AnalyticsParams {
    start_date?: string;
    end_date?: string; // YYYY-MM-DD
    include_cancelled?: boolean;
}

export interface OverviewData {
    meta: {
        start_date: string;
        end_date: string;
        include_cancelled: boolean;
    };
    summary: {
        patients_seen: number;
        total_orders: number;
        total_tests: number;
        gross_sales: number;
        total_discount: number;
        net_sales: number;
        total_collections: number;
        cash_collections: number;
        outstanding_for_orders: number;
        outstanding_period_net: number;
    };
}

export interface PatientRow {
    patient_id: number;
    name: string;
    age: string | number;
    gender: string;
    orders_count: number;
    revenue: number;
}

export interface TestRow {
    test_name: string;
    count: number;
    revenue: number;
    share_percent: number;
}

export interface ReferralRow {
    referrer: string;
    count: number;
    revenue: number;
}

export interface ReferralRows {
    volume: ReferralRow[];
    revenue: ReferralRow[];
}

export interface FinanceSummary {
    gross_sales: number;
    discount: number;
    net_sales: number;
    total_collected: number;
}

export interface CollectionRow {
    method: string;
    amount: number;
}

export interface ExportLogRow {
    id: number;
    user: string | null;
    report_key: string;
    filters_json: Record<string, unknown>;
    format: 'csv' | 'xlsx';
    generated_at: string;
    row_count: number;
    file_path: string | null;
}
