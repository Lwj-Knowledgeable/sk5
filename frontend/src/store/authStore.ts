import { defineStore } from 'pinia';
import { axiosInstance } from '../store/messageaxios.js';
import { buildEncryptedPayload } from '../utils/encrypt';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  isAuthenticating: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: localStorage.getItem('auth_token') || null,
    isAuthenticated: false,
    isAuthenticating: false,
  }),

  getters: {
    hasToken: (state) => !!state.token,
  },

  actions: {
    /**
     * 执行认证，获取 token
     * @param secretString 要加密的字符串，默认为 'abdaeeifoajn'
     */
    async authenticate(secretString: string = 'abdaeeifoajn'): Promise<boolean> {
      // 如果正在认证中，避免重复请求
      if (this.isAuthenticating) {
        return false;
      }

      // 如果已有有效 token，直接返回
      if (this.token && this.isAuthenticated) {
        return true;
      }

      this.isAuthenticating = true;

      try {
        // 加密字符串
        const encryptedToken = buildEncryptedPayload(secretString);

        // 发送认证请求
        const response = await axiosInstance.post('/auth', {
          token: encryptedToken, // 后端期望的字段名是 'token'
        });

        if (response.data.success && response.data.token) {
          // 保存 token
          this.token = response.data.token;
          this.isAuthenticated = true;
          localStorage.setItem('auth_token', this.token as string);
          console.log('认证成功，token 已保存');
          return true;
        } else {
          console.error('认证失败:', response.data.msg || '未知错误');
          this.clearAuth();
          return false;
        }
      } catch (error: any) {
        console.error('认证请求失败:', error);
        this.clearAuth();
        return false;
      } finally {
        this.isAuthenticating = false;
      }
    },

    /**
     * 清除认证信息
     */
    clearAuth() {
      this.token = null;
      this.isAuthenticated = false;
      localStorage.removeItem('auth_token');
    },

    /**
     * 设置 token（用于从外部设置）
     */
    setToken(token: string) {
      this.token = token;
      this.isAuthenticated = true;
      localStorage.setItem('auth_token', token);
    },
  },
});
