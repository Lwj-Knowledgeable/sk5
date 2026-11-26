<template>
    <el-button @click="startScanAp" :loading="isLoading" type="primary" style="margin-bottom: 10px;">开始扫描AP</el-button>
    <div v-loading="isLoading">
        <el-table :data="processedRadioData">
            <el-table-column prop="aid" label="id" width="200">
                <template #default="{ row }">
                    <div style="width: 13%;height: auto;float:left">
                        <el-button class="icon-button" style="height: 70px; width: 80px;border-radius: 10%;display: flex;align-items: center;justify-content: center;" @click="wifiStore.refreshWifiStatus(row.aid)">
                            <el-icon class="status-icon" v-if="apdata.find(item=>item.aid===row.aid)?.status == '离线'"></el-icon>
                            <el-icon class="enabled_status-icon" v-if="apdata.find(item=>item.aid===row.aid)?.status == '在线'"></el-icon>
                            <el-icon><img src="../public/wifi.png" alt="wifi" class="button-icon"/></el-icon>
                        </el-button>
                    </div>
                    <div style="float: left;">
                        <el-row style="margin-left: 100px;margin-top: 20px;">AP{{ row.aid }}</el-row>
                    </div>
                </template>
            </el-table-column>
            <el-table-column label="状态" width="150">
                <template #default="{ row }">
                    <el-tag type="success">{{ apdata.find(item=>item.aid===row.aid)?.status || '未知' }}</el-tag>
                </template>
            </el-table-column>
            <el-table-column label="信道" width="800">
                <template #default="{ row }">
                    <!-- 显示该AP的所有射频信息 -->
                    <div v-for="radio in row.radioInfo" :key="radio.type" style="float: left;width: 30%;">
                        <el-row>
                            <el-tag>{{ radio.type }}</el-tag>
                            <el-col>信道：{{ radio.channel }}</el-col>
                            <el-col>状态：{{ radio.state }}</el-col>
                            <el-col>频宽：{{ radio.channel_bandwidth }}</el-col>
                        </el-row>
                    </div>
                </template>
            </el-table-column>
            <el-table-column label="操作" >
                <template #default="{row}">
                    <el-button type="primary" @click="editWifi(row.aid)">编辑</el-button>
                    <el-button type="warning" @click="showPasswordDialog(row.aid)" :icon="User" size="mini" circle></el-button>
                </template>
            </el-table-column>
        </el-table>

        <!-- 密码验证对话框 -->
        <el-dialog
            v-model="passwordDialogVisible"
            title="管理权限验证"
            width="400px"
            :close-on-click-modal="false"
            :close-on-press-escape="false"
        >
            <div style="text-align: center;">
                <el-icon size="48" color="#409EFF" style="margin-bottom: 16px;">
                    <Lock />
                </el-icon>
                <p style="margin-bottom: 20px; color: #606266;">请输入管理密码以访问AP管理功能</p>
                
                <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" @submit.prevent>
                    <el-form-item prop="password">
                        <el-input
                            v-model="passwordForm.password"
                            type="password"
                            placeholder="请输入管理密码"
                            show-password
                            size="large"
                            @keyup.enter.prevent="verifyPassword"
                        >
                            <template #prefix>
                                <el-icon><Lock /></el-icon>
                            </template>
                        </el-input>
                    </el-form-item>
                </el-form>
            </div>
            
            <template #footer>
                <div style="text-align: center;">
                    <el-button @click="cancelPasswordDialog" size="large">取消</el-button>
                    <el-button 
                        type="primary" 
                        @click="verifyPassword" 
                        :loading="passwordVerifying"
                        size="large"
                    >
                        {{ passwordVerifying ? '验证中...' : '确认' }}
                    </el-button>
                </div>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeMount } from 'vue';
import { useWifiStore } from '../store/dataStore';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Lock,User } from '@element-plus/icons-vue';
import { axiosInstance } from '../store/messageaxios';

const router = useRouter();
const wifiStore = useWifiStore();

// 密码验证相关状态
const passwordDialogVisible = ref(false);
const passwordVerifying = ref(false);
const currentAid = ref(null);
const passwordForm = ref({
    password: ''
});
const passwordFormRef = ref(null);

// 密码验证规则
const passwordRules = {
    password: [
        { required: true, message: '请输入管理密码', trigger: 'blur' },
        { min: 1, message: '密码不能为空', trigger: 'blur' }
    ]
};

// 使用计算属性来获取响应式数据
const wifidata = computed(() => wifiStore.wifiItems);
const radiodata = computed(() => wifiStore.radioItems);
const apdata = computed(() => wifiStore.apItems);
const isLoading = computed(() => wifiStore.isLoading);

// 计算属性：处理radiodata的aid并形成列表
const processedRadioData = computed(() => {
    console.log('radiodata.value:', radiodata.value);
    console.log('radiodata length:', radiodata.value?.length);
    
    if (!radiodata.value || radiodata.value.length === 0) {
        console.log('radiodata is empty or undefined');
        return [];
    }
    
    // 按aid分组射频数据
    const groupedByAid = {};
    
    radiodata.value.forEach(radio => {
        console.log('processing radio:', radio);
        if (radio && radio.aid) {
            if (!groupedByAid[radio.aid]) {
                groupedByAid[radio.aid] = {
                    aid: radio.aid,
                    radioInfo: []
                };
            }
            
            // 添加射频信息到对应的aid组
            groupedByAid[radio.aid].radioInfo.push({
                type: radio.type || '未知',
                channel: radio.channel || '未知',
                state: radio.state || '未知',
                channel_bandwidth: radio.channel_bandwidth || '未知'
            });
        }
    });
    
    console.log('groupedByAid:', groupedByAid);
    // 转换为数组格式
    const result = Object.values(groupedByAid);
    console.log('processedRadioData result:', result);
    return result;
});

// 显示密码验证对话框
const showPasswordDialog = (aid) => {
    currentAid.value = aid;
    passwordForm.value.password = '';
    passwordDialogVisible.value = true;
    
    // 清除之前的验证状态
    if (passwordFormRef.value) {
        passwordFormRef.value.clearValidate();
    }
};

// 取消密码验证
const cancelPasswordDialog = () => {
    passwordDialogVisible.value = false;
    passwordForm.value.password = '';
    currentAid.value = null;
    passwordVerifying.value = false;
};

// 验证密码
const verifyPassword = async () => {
    if (!passwordFormRef.value) return;
    
    try {
        // 验证表单
        await passwordFormRef.value.validate();
        
        passwordVerifying.value = true;
        
        // 调用后端API验证密码
        const response = await axiosInstance.post('/api/verify_pwd', {
            password: passwordForm.value.password,
            menu: 'sk5'
        });
        
        if (response.data.success) {
            console.log('密码验证成功，准备跳转。currentAid:', currentAid.value);
            ElMessage.success('密码验证成功！');
            passwordDialogVisible.value = false;

            // 跳转到管理页面
            manageWifi(currentAid.value);
        } else {
            ElMessage.error('密码错误，请重新输入！');
        }
        
    } catch (error) {
        console.error('密码验证失败:', error);
        if (error.response && error.response.data && !error.response.data.success) {
            ElMessage.error('密码错误，请重新输入！');
        } else {
            ElMessage.error('验证失败，请重试！');
        }
    } finally {
        passwordVerifying.value = false;
    }
};

const defaultdata = {
    'aid': 1,
    'status': 'Disabled',
    'channel_5': 'string',
    'state_5': 'string',
    'max_power_5': 'string',
    'channel_bandwidth_5': 'string',
    'type_5': 'string',
    'channel_24': 'string',
    'state_24': 'string',
    'max_power_24': 'string',
    'channel_bandwidth_24': 'string',
    'type_24': 'string',
}

const getApdata = (aid) => {
    return wifiStore.apItems.find(item => item.aid == aid)
}

const editWifi = (aid) => {
    // 跳转到WiFi编辑页面，传递aid参数
    router.push({
        name: 'WifiTag', // 或者使用 path: '/wifi/' + aid
        params: { aid: aid }
    });
};

// 管理WiFi - 跳转到WiFi管理页面
const manageWifi = (aid) => {
    console.log('准备跳转到AP管理页面，AID:', aid);
    console.log('当前路由:', router.currentRoute.value.path);
    console.log('路由对象:', router);

    if (!aid) {
        console.error('AID为空，无法跳转');
        ElMessage.error('AP ID为空，无法跳转到管理页面');
        return;
    }

    try {
        // 使用path而不是name，避免路由名称匹配问题
        router.push({
        name: 'ApManage', // 或者使用 path: '/apManage/' + aid
        params: { aid: aid }
    });

    } catch (error) {
        console.error('路由跳转失败:', error);
        ElMessage.error('跳转到管理页面失败: ' + error.message);
    }
};

// 其他跳转方法示例
const goToHome = () => {
    router.push('/')
}

const goToApList = () => {
    router.push('/ap')
}

const radioSocket = () => {
    const radioWs = new WebSocket('ws://127.0.0.1:5000/socket.io/?EIO=4&transport=websocket')
    radioWs.onmessage = (event) => {
        console.log(event.data)
        try {
            const data = JSON.parse(event.data)
            console.log(data)
        } catch (error) {
            console.log(error)
        }
    }
    radioWs.onopen = () => {
        console.log("radioWs opened")
    }
    radioWs.onclose = () => {
        console.log("radioWs closed")
    }
}

const ManageAp = () => {
    
}
const startScanAp = async () => {
    try {
        await wifiStore.initializeData(true);
        ElMessage.success('扫描AP成功');
    } catch (error) {
        console.error('扫描AP失败:', error)
    }
}
</script>

<style scoped>
.el-table {
    width: 100%;
}
.icon-button {
    padding: 0;
    border-radius: 10%;
    display: flex;
    align-items: center;
    justify-content: center;;
}
.status-icon {
    width: 10px;
    height: 10px;
    object-fit: contain;
    border-radius: 50%;
    display: flex;
    background-color: rgb(248, 74, 10);
    position: relative;
    right: 13px;
    bottom: 20px;
    z-index: 2;
}
.enabled_status-icon{
    width: 10px;
    height: 10px;
    object-fit: contain;
    border-radius: 50%;
    display: flex;
    background-color: rgb(38, 188, 38);
    position: relative;
    right: 13px;
    bottom: 20px;
    z-index: 2;
}
.button-icon {
    width: 80px;
    height: 60px;
    object-fit: contain;
    border-radius: 4px;
    z-index: 1;
    position: absolute;
}

/* 悬停效果 */
.icon-button:hover {
    transform: scale(1.1);
    transition: transform 0.2s ease;
}

/* 密码对话框样式 */
:deep(.el-dialog__body) {
    padding: 20px 30px;
}

:deep(.el-form-item) {
    margin-bottom: 20px;
}

:deep(.el-input__wrapper) {
    border-radius: 8px;
}
</style>