const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

class ApiService {
  async request(endpoint, options = {}) {
    // Ensure we use the correct protocol
    let baseUrl = API_BASE_URL;
    
    // If we're on HTTPS and the base URL is HTTP, convert it to HTTPS
    if (window.location.protocol === 'https:' && baseUrl.startsWith('http:')) {
      baseUrl = baseUrl.replace('http:', 'https:');
    }
    
    const url = `${baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health check
  async healthCheck() {
    return this.request('/api/health');
  }

  // Categories
  async getCategories() {
    return this.request('/api/categories/super-rubrics');
  }

  async getSubCategories(superRubricId) {
    return this.request(`/api/categories/sub-rubrics?super_rubric_id=${superRubricId}`);
  }

  async getCities() {
    return this.request('/api/categories/cities');
  }

  async getCurrencies() {
    return this.request('/api/categories/currencies');
  }

  // Posts
  async getPosts(filters = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
        params.append(key, filters[key]);
      }
    });
    
    const queryString = params.toString();
    return this.request(`/api/posts${queryString ? '?' + queryString : ''}`);
  }

  async getPost(postId) {
    return this.request(`/api/posts/${postId}`);
  }

  async createJobPost(postData, authorId) {
    return this.request('/api/posts/jobs', {
      method: 'POST',
      body: postData,
      headers: {
        'X-Author-ID': authorId
      }
    });
  }

  async createServicePost(postData, authorId) {
    return this.request('/api/posts/services', {
      method: 'POST',
      body: postData,
      headers: {
        'X-Author-ID': authorId
      }
    });
  }

  async updatePost(postId, postData) {
    return this.request(`/api/posts/${postId}`, {
      method: 'PUT',
      body: postData,
    });
  }

  async deletePost(postId) {
    return this.request(`/api/posts/${postId}`, {
      method: 'DELETE',
    });
  }

  // Favorites
  async addToFavorites(userId, postId) {
    return this.request('/api/posts/favorites', {
      method: 'POST',
      body: { user_id: userId, post_id: postId },
    });
  }

  async removeFromFavorites(userId, postId) {
    return this.request('/api/posts/favorites', {
      method: 'DELETE',
      body: { user_id: userId, post_id: postId },
    });
  }

  async getUserFavorites(userId) {
    return this.request(`/api/posts/favorites/${userId}`);
  }

  // Users
  async createUser(userData) {
    return this.request('/api/users/', {
      method: 'POST',
      body: userData,
    });
  }

  async getUser(userId) {
    return this.request(`/api/users/${userId}`);
  }

  async getUserByTelegramId(telegramId) {
    return this.request(`/api/users/telegram/${telegramId}`);
  }

  async updateUser(userId, userData) {
    return this.request(`/api/users/${userId}`, {
      method: 'PUT',
      body: userData,
    });
  }

  // Packages
  async getPackages() {
    return this.request('/api/packages/');
  }

  async createPayment(paymentData, userId) {
    return this.request('/api/packages/payments', {
      method: 'POST',
      body: paymentData,
      headers: {
        'X-User-ID': userId
      }
    });
  }

  async getPayment(paymentId) {
    return this.request(`/api/packages/payments/${paymentId}`);
  }

  async completePayment(paymentId, telegramChargeId, providerChargeId) {
    return this.request(`/api/packages/payments/${paymentId}/complete`, {
      method: 'PUT',
      body: {
        telegram_charge_id: telegramChargeId,
        provider_charge_id: providerChargeId
      }
    });
  }
}

const apiService = new ApiService();

// Export individual functions for easier imports
export const healthCheck = () => apiService.healthCheck();
export const getCategories = () => apiService.getCategories();
export const getSubCategories = (superRubricId) => apiService.getSubCategories(superRubricId);
export const getCities = () => apiService.getCities();
export const getCurrencies = () => apiService.getCurrencies();
export const getPosts = (filters) => apiService.getPosts(filters);
export const getPost = (postId) => apiService.getPost(postId);
export const createJobPost = (postData, authorId) => apiService.createJobPost(postData, authorId);
export const createServicePost = (postData, authorId) => apiService.createServicePost(postData, authorId);
export const updatePost = (postId, postData) => apiService.updatePost(postId, postData);
export const deletePost = (postId) => apiService.deletePost(postId);
export const addToFavorites = (userId, postId) => apiService.addToFavorites(userId, postId);
export const removeFromFavorites = (userId, postId) => apiService.removeFromFavorites(userId, postId);
export const getUserFavorites = (userId) => apiService.getUserFavorites(userId);
export const createUser = (userData) => apiService.createUser(userData);
export const getUser = (userId) => apiService.getUser(userId);
export const getUserByTelegramId = (telegramId) => apiService.getUserByTelegramId(telegramId);
export const updateUser = (userId, userData) => apiService.updateUser(userId, userData);
export const getPackages = () => apiService.getPackages();
export const createPayment = (paymentData, userId) => apiService.createPayment(paymentData, userId);
export const getPayment = (paymentId) => apiService.getPayment(paymentId);
export const completePayment = (paymentId, telegramChargeId, providerChargeId) => apiService.completePayment(paymentId, telegramChargeId, providerChargeId);

export default apiService;