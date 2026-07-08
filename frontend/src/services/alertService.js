import api from './api';

export const alertService = {
  async getAlerts(params = {}) {
    const response = await api.get('/alerts', { params });
    return response.data;
  },

  async markAsRead(id) {
    const response = await api.put(`/alerts/${id}/read`);
    return response.data;
  },

  async markAllAsRead() {
    const response = await api.put('/alerts/read-all');
    return response.data;
  },

  async getAlertStats() {
    const response = await api.get('/alerts/stats');
    return response.data;
  },
};

export default alertService;
