import type { AxiosInstance } from 'axios';

export const axiosInstance: AxiosInstance;

export default function request<T = any>(
  url: string,
  method?: string,
  params?: Record<string, any>,
  data?: Record<string, any>
): Promise<T>;

// Support imports that include the .js extension
declare module '../store/messageaxios.js' {
  import type { AxiosInstance } from 'axios';
  export const axiosInstance: AxiosInstance;
  const request: <T = any>(
    url: string,
    method?: string,
    params?: Record<string, any>,
    data?: Record<string, any>
  ) => Promise<T>;
  export default request;
}
