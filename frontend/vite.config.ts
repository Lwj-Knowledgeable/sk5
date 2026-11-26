import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  build: {
    // 输出目录，默认是 'dist'
    outDir: 'dist',
    // 生成静态资源的目录，默认是 'assets'
    assetsDir: 'assets',
    // 输出文件名称哈希化，默认 true
    rollupOptions: {
      output: {
        // 自定义输出文件名
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'css/[name]-[hash][extname]';
          }
          return '[ext]/[name]-[hash][extname]';
        },
      },
    },
  },
  server: {
    host: '0.0.0.0', // 允许外部访问
    proxy: {
      '/api': {
        target: 'http://0.0.0.0:8080',
        changeOrigin: true,
        rewrite: (path) => path
      },
      '/auth': {
        target: 'http://0.0.0.0:8080',
        changeOrigin: true,
        rewrite: (path) => path
      },
      '/socket.io':{
        target:'http://0.0.0.0:8080',
        changeOrigin: true,
        ws: true,  
      }
    }
  },
});
