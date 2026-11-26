import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import DataTable from '../pages/DataTable.vue';
import ApTag from '../pages/ApTag.vue';
import WifiTag from '../pages/WifiTag.vue';
import ApiTag from '../pages/ApiTag.vue';
import ApManage from '../pages/ApManage.vue';
import { useAuthStore } from '../store/authStore';

const routes: Array<RouteRecordRaw> = [
    { path: '/',  redirect: '/ap' },
    { path: '/data', component: DataTable },
    { path: '/ap', component: ApTag },
    { path: '/api', component: ApiTag },
    { path: '/wifi/:aid', name: 'WifiTag', component: WifiTag, props: true },
    { path: '/apManage/:aid', name: 'ApManage', component: ApManage, props: true },
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

// 路由守卫：在访问路由时自动认证
router.beforeEach(async (to, _from, next) => {
    const authStore = useAuthStore();

    console.log('路由守卫检查 - 目标路由:', to.path);
    console.log('当前认证状态:', {
        token: !!authStore.token,
        isAuthenticated: authStore.isAuthenticated,
        isAuthenticating: authStore.isAuthenticating
    });

    // 如果还没有 token 或未认证，执行认证
    if (!authStore.token || !authStore.isAuthenticated) {
        console.log('检测到未认证，开始自动认证...');

        try {
            const authenticated = await authStore.authenticate();

            if (authenticated) {
                console.log('自动认证成功，继续访问路由');
                next();
            } else {
                console.error('自动认证失败，阻止路由跳转');
                // 认证失败时，跳转到首页而不是阻止跳转
                // 这样用户至少能看到应用而不是空白页面
                console.log('认证失败，跳转到首页');
                next('/');
            }
        } catch (error) {
            console.error('认证过程出错:', error);
            // 认证出错时也跳转到首页
            next('/');
        }
    } else {
        // 已有 token，直接通过
        console.log('已有认证信息，继续访问路由');
        next();
    }
});

export default router;