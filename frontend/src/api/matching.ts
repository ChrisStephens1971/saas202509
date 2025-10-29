/**
 * API client for auto-matching engine
 */

import apiClient from './apiClient';

export interface AutoMatchRule {
  id: string;
  rule_type: string;
  rule_type_display: string;
  pattern: any;
  confidence_score: number;
  times_used: number;
  times_correct: number;
  accuracy_rate: string;
  is_active: boolean;
  created_at: string;
}

export interface MatchResult {
  id: string;
  bank_transaction: string;
  bank_transaction_description: string;
  matched_entry: string;
  matched_entry_reference: string;
  confidence_score: number;
  match_explanation: string;
  was_accepted: boolean;
  created_at: string;
}

export interface MatchStatistics {
  id: string;
  period_start: string;
  period_end: string;
  total_transactions: number;
  auto_matched: number;
  manually_matched: number;
  unmatched: number;
  auto_match_rate: string;
  average_confidence: string;
  false_positive_rate: string;
  created_at: string;
}

export const getMatchRules = async (): Promise<AutoMatchRule[]> => {
  const response = await apiClient.get('/accounting/auto-match-rules/');
  return response.data;
};

export const getMatchResults = async (): Promise<MatchResult[]> => {
  const response = await apiClient.get('/accounting/match-results/');
  return response.data;
};

export const acceptMatch = async (id: string): Promise<MatchResult> => {
  const response = await apiClient.post(`/accounting/match-results/${id}/accept/`);
  return response.data;
};

export const getMatchStatistics = async (): Promise<MatchStatistics[]> => {
  const response = await apiClient.get('/accounting/match-statistics/');
  return response.data;
};
