import api from './api';

export const fileService = {
  async uploadFile(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  async getFiles(params = {}) {
    const response = await api.get('/files', { params });
    return response.data;
  },

  async getFile(id) {
    const response = await api.get(`/files/${id}`);
    return response.data;
  },

  async deleteFile(id) {
    const response = await api.delete(`/files/${id}`);
    return response.data;
  },

  async downloadFile(id) {
    const response = await api.get(`/files/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

export default fileService;
