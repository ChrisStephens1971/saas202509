import axios from 'axios';

const API_BASE_URL = 'http://localhost:8009/api/v1/accounting';

// Get auth token from localStorage
const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Type definitions
export interface ReserveStudy {
  id: string;
  name: string;
  study_date: string;
  horizon_years: number;
  inflation_rate: string;
  interest_rate: string;
  notes: string;
  components?: ReserveComponent[];
  scenarios?: ReserveScenario[];
  current_reserve_balance: string;
  created_at: string;
  updated_at: string;
}

export interface ReserveComponent {
  id: string;
  study: string;
  name: string;
  description: string;
  category: string;
  quantity: string;
  unit: string;
  useful_life_years: number;
  remaining_life_years: number;
  current_cost: string;
  inflated_cost: string;
  replacement_year: number;
  created_at: string;
  updated_at: string;
}

export interface ReserveScenario {
  id: string;
  study: string;
  name: string;
  description: string;
  monthly_contribution: string;
  one_time_contribution: string;
  contribution_increase_rate: string;
  is_baseline: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface FundingProjection {
  year: number;
  beginning_balance: string;
  contributions: string;
  expenditures: string;
  interest_earned: string;
  ending_balance: string;
  percent_funded: string;
}

export interface FundingAdequacy {
  current_balance: string;
  total_future_cost: string;
  percent_funded: string;
  status: 'WELL_FUNDED' | 'ADEQUATE' | 'UNDERFUNDED';
}

// Reserve Studies API
export const reserveStudiesApi = {
  list: async (): Promise<ReserveStudy[]> => {
    const response = await axios.get(`${API_BASE_URL}/reserve-studies/`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  get: async (id: string): Promise<ReserveStudy> => {
    const response = await axios.get(`${API_BASE_URL}/reserve-studies/${id}/`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  create: async (data: Partial<ReserveStudy>): Promise<ReserveStudy> => {
    const response = await axios.post(`${API_BASE_URL}/reserve-studies/`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  update: async (id: string, data: Partial<ReserveStudy>): Promise<ReserveStudy> => {
    const response = await axios.put(`${API_BASE_URL}/reserve-studies/${id}/`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/reserve-studies/${id}/`, {
      headers: getAuthHeader(),
    });
  },

  getFundingAdequacy: async (id: string): Promise<FundingAdequacy> => {
    const response = await axios.get(`${API_BASE_URL}/reserve-studies/${id}/funding_adequacy/`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },
};

// Reserve Components API
export const reserveComponentsApi = {
  list: async (studyId?: string): Promise<ReserveComponent[]> => {
    const params = studyId ? { study: studyId } : {};
    const response = await axios.get(`${API_BASE_URL}/reserve-components/`, {
      headers: getAuthHeader(),
      params,
    });
    return response.data;
  },

  create: async (data: Partial<ReserveComponent>): Promise<ReserveComponent> => {
    const response = await axios.post(`${API_BASE_URL}/reserve-components/`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  update: async (id: string, data: Partial<ReserveComponent>): Promise<ReserveComponent> => {
    const response = await axios.put(`${API_BASE_URL}/reserve-components/${id}/`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/reserve-components/${id}/`, {
      headers: getAuthHeader(),
    });
  },
};

// Reserve Scenarios API
export const reserveScenariosApi = {
  list: async (studyId?: string): Promise<ReserveScenario[]> => {
    const params = studyId ? { study: studyId } : {};
    const response = await axios.get(`${API_BASE_URL}/reserve-scenarios/`, {
      headers: getAuthHeader(),
      params,
    });
    return response.data;
  },

  create: async (data: Partial<ReserveScenario>): Promise<ReserveScenario> => {
    const response = await axios.post(`${API_BASE_URL}/reserve-scenarios/`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  update: async (id: string, data: Partial<ReserveScenario>): Promise<ReserveScenario> => {
    const response = await axios.put(`${API_BASE_URL}/reserve-scenarios/${id}/`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/reserve-scenarios/${id}/`, {
      headers: getAuthHeader(),
    });
  },

  getProjection: async (id: string): Promise<FundingProjection[]> => {
    const response = await axios.get(`${API_BASE_URL}/reserve-scenarios/${id}/projection/`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  compareScenarios: async (scenarioIds: string[]): Promise<any> => {
    const response = await axios.post(
      `${API_BASE_URL}/reserve-scenarios/compare/`,
      { scenario_ids: scenarioIds },
      { headers: getAuthHeader() }
    );
    return response.data;
  },
};
