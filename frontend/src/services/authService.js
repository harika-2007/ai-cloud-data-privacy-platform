import api from './api'

export const authService = {
  refresh: async (refreshToken) => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
}
