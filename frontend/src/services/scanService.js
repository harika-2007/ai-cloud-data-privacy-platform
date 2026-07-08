import api from './api';

export const scanService = {
  async startScan(fileId) {
    const response = await api.post(`/scans/start/${fileId}`);
    return response.data;
  },

  async getScanResults(fileId) {
    const response = await api.get(`/scans/file/${fileId}`);
    return response.data;
  },

  async getRiskAssessment(fileId) {
    const response = await api.get(`/scans/risk/file/${fileId}`);
    return response.data;
  },

  async getScans(params = {}) {
    const response = await api.get('/scans', { params });
    return response.data;
  },
};

export default scanService;
