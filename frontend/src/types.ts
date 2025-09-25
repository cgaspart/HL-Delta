export interface AccountInfo {
  address: string;
  total_value: number;
  margin_used: number | null;
  total_raw_usd: number | null;
}

export interface Position {
  coin: string;
  type: 'spot' | 'perp';
  size: number;
  value?: number;
  entry_price?: number;
  position_value?: number;
  unrealized_pnl?: number;
  leverage?: number;
  liquidation_price?: number;
  funding?: number;
  hold?: number;
}

export interface FundingRate {
  hourly: number;
  yearly: number | null;
}

export interface BotStatus {
  running: boolean;
  positions: Position[];
  funding_rates: Record<string, FundingRate>;
  account: AccountInfo;
  pending_orders: number;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data?: T;
}
