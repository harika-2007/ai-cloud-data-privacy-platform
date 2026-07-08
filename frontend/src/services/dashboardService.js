import api from './api';

export const dashboardService = {
  async getStats() {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  async getTrends(days = 30) {
    const response = await api.get('/dashboard/trends', {
      params: { days },
    });
    return response.data;
  },

  async getDistribution() {
    const response = await api.get('/dashboard/distribution');
    return response.data;
  },

  async getCompliance() {
    const response = await api.get('/dashboard/compliance');
    return response.data;
  },

  async getFull() {
    const response = await api.get('/dashboard/full');
    return response.data;
  },
};

export default dashboardService;
