import api from './api';

const AI_TIMEOUT = 15000; // 15 seconds

export const aiService = {
  async getRecommendations(fileId, timeout = AI_TIMEOUT) {
    const response = await api.post(`/ai/recommend/${fileId}`, null, {
      timeout,
    });
    return response.data;
  },

  async getSummary(fileId, timeout = AI_TIMEOUT) {
    const response = await api.post(`/ai/summary/${fileId}`, null, {
      timeout,
    });
    return response.data;
  },

  async chat(message, conversationHistory = [], timeout = AI_TIMEOUT) {
    const response = await api.post('/ai/chat', {
      message,
      conversation_history: conversationHistory,
    }, { timeout });
    return response.data;
  },
};

export default aiService;
