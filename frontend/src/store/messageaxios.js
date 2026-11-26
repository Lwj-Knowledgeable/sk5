import axios from 'axios';

// 配置axios默认设置，支持Cookie认证
axios.defaults.withCredentials = true; // 重要：允许发送Cookie

// 创建axios实例
const axiosInstance = axios.create({
  withCredentials: true, // 允许发送Cookie
  timeout: 100000, // 30秒超时
});

// 全局认证状态管理，避免并发认证
let authPromise = null;

// 请求拦截器
axiosInstance.interceptors.request.use(
  async (config) => {
    // 确保每次请求都发送Cookie
    config.withCredentials = true;

    // 非 /auth 请求需要确保具备 token
    if (config.url !== '/auth') {
      let token = localStorage.getItem('auth_token');

      // 若无 token，尝试自动认证
      if (!token) {
        // 如果正在认证中，等待认证完成
        if (authPromise) {
          console.log('等待认证完成...');
          await authPromise;
          // 重新获取 token
          token = localStorage.getItem('auth_token');
        } else {
          // 开始新的认证
          try {
            console.log('开始自动认证...');
            const { useAuthStore } = await import('./authStore');
            const authStore = useAuthStore();

            // 创建认证 Promise
            authPromise = authStore.authenticate();

            const ok = await authPromise;
            if (ok) {
              token = authStore.token;
              console.log('自动认证成功');
            } else {
              console.error('自动认证失败');
              // 认证失败，抛出错误阻止请求
              throw new Error('认证失败，无法发送请求');
            }
          } catch (e) {
            console.error('认证过程出错:', e);
            throw e;
          } finally {
            // 清除认证 Promise
            authPromise = null;
          }
        }
      }

      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
        console.log(`添加认证头到请求: ${config.url}`);
      } else {
        console.warn(`没有 token，请求可能失败: ${config.url}`);
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // 处理401未授权错误
    if (error.response && error.response.status === 401) {
      console.error('认证失败，请重新登录:', error.response.data?.msg || '未授权');

      // 清除token
      localStorage.removeItem('auth_token');

      // 清除全局认证状态
      authPromise = null;

      // 清除认证状态
      try {
        const { useAuthStore } = await import('./authStore');
        const authStore = useAuthStore();
        authStore.clearAuth();
      } catch (e) {
        console.error('清除认证状态失败:', e);
      }
      
      // 如果不是 /auth 接口，尝试重新认证
      const config = error.config;
      if (config.url !== '/auth' && !config._retry) {
        config._retry = true;
        
        // 尝试重新认证
        try {
          // 动态导入 authStore 避免循环依赖
          const { useAuthStore } = await import('./authStore');
          const authStore = useAuthStore();
          const authenticated = await authStore.authenticate();
          
          if (authenticated && authStore.token) {
            // 重新设置 token 并重试请求
            config.headers.Authorization = `Bearer ${authStore.token}`;
            return axiosInstance(config);
          }
        } catch (authError) {
          console.error('重新认证失败:', authError);
        }
      }
      
      // 可以在这里添加跳转到登录页的逻辑
      // 例如：window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * 通用 API 请求函数
 * @param {string} url - API 地址
 * @param {string} method - HTTP 方法（GET、POST 等）
 * @param {Object} [params] - 请求参数（可选，用于 GET 请求）
 * @param {Object} [data] - 请求体数据（可选，用于 POST、PUT 等请求）
 * @returns {Promise} - 返回 API 响应数据
 */
const request = async (url, method = 'GET', params = {}, data = {}) => {
  try {
    const response = await axiosInstance({
      url,
      method,
      params, // GET 请求的参数
      data,   // POST、PUT 等请求的请求体
      withCredentials: true, // 确保发送Cookie
    });
    return response.data; // 返回 API 响应数据
  } catch (error) {
    console.error('API 请求失败:', error);
    throw error; // 抛出错误以便调用方处理
  }
};

// 导出axios实例，方便直接使用
export { axiosInstance };
export default request;