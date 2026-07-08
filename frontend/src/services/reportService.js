import api from './api';

export const reportService = {
  async generateReport(data) {
    const response = await api.post('/reports/generate', data);
    return response.data;
  },

  async getReports(params = {}) {
    const response = await api.get('/reports', { params });
    return response.data;
  },

  async getReport(id) {
    const response = await api.get(`/reports/${id}`);
    return response.data;
  },

  async downloadReport(id) {
    const response = await api.get(`/reports/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

export default reportService;
