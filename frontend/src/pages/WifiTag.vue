<template>
    <el-breadcrumb separator="/" style="margin-bottom: 30px;margin-top: 10px;">
        <el-breadcrumb-item :to="{ path: '/ap' }">返回</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/wifi/' + aid }">AP{{ aid }}</el-breadcrumb-item>
    </el-breadcrumb>
    <div style="margin-bottom: 20px;">
        <el-button type="success" style="margin-left: 10px;" plain size="middle" @click="openAddNoVlanWifi">添加SSID</el-button>
        <el-button type="primary" style="margin-left: 10px;" plain size="middle" @click="openBatchAddWifi">批量添加SSID</el-button>
        <el-button type="primary" style="margin-left: 10px;" plain size="middle" @click="openBatchDelWifi">批量删除SSID</el-button>
    </div>
    <!-- <div v-loading="isLoading">
        <span style="   font-weight: bold;
                        font-size:18px;
                        color: #b435f4f5;
                        margin-left:10px;
                        margin-bottom: 20px;"
                        >
                        射频设置
                        
                    </span>
            <el-button type="primary" style="position: absolute;margin-left: 20px;" plain circle :icon="Check" size="small" @click="wifiStore.resetRadioInfo(radioItems)"></el-button>
            <el-row class="rowsetting">
                <el-col >
                        信道2.4GHz：
                        <el-radio-group v-model="radioItems.state_24">
                            <el-radio label="开启" value="Up"></el-radio>
                            <el-radio label="关闭" value="Down"></el-radio>
                        </el-radio-group>
                        <div class="secdiv">
                            <el-row style="margin-left: 20px;padding-bottom: 3px">
                                <el-col :span="8">
                                    带宽：
                                    <el-select v-model="radioItems.channel_bandwidth_24" placeholder="请选择" size="small" style="width: 120px;">
                                        <el-option label="20MHz" value="20MHz"></el-option>
                                        <el-option label="40MHz" value="40MHz"></el-option>
                                    </el-select>
                                </el-col>
                                <el-col :span="8">
                                    配置信道：
                                    <el-select v-model="radioItems.channel_24" placeholder="请选择" size="small" style="width: 120px;">
                                        <el-option v-for="v in channel24list" :label="v" :value="v"></el-option>
                                    </el-select>
                                </el-col>
                                <el-col :span="8">
                                    最大功率：
                                    <el-input v-model="radioItems.max_power_24" size="small" style="width: 120px;"></el-input>
                                    dbm(1-20)
                                </el-col>
                            </el-row>

                        </div>
                </el-col>
            </el-row>
            <el-row class="rowsetting" style="margin-bottom: 20px;">
                
                <el-col>
                        信道5GHz：
                        <el-radio-group v-model="radioItems.state_5">
                            <el-radio label="开启" value="Up"></el-radio>
                            <el-radio label="关闭" value="Down"></el-radio>
                        </el-radio-group>
                        <div class="secdiv">
                            <el-row style="margin-left: 20px;padding-bottom: 3px">
                                <el-col :span="8">
                                    带宽：
                                    <el-select v-model="radioItems.channel_bandwidth_5" placeholder="请选择" size="small" style="width: 120px;">
                                        <el-option label="20MHz" value="20MHz"></el-option>
                                        <el-option label="40MHz" value="40MHz"></el-option>
                                        <el-option label="80MHz" value="80MHz"></el-option>
                                        <el-option label="160MHz" value="160MHz"></el-option>
                                        <el-option label="80+80MHz" value="80+80MHz"></el-option>
                                    </el-select>
                                </el-col>
                                <el-col :span="8">
                                    配置信道：
                                    <el-select v-model="radioItems.channel_5" placeholder="请选择" size="small" style="width: 120px;">
                                        <el-option v-for="v in channel5list" :label="v" :value="v"></el-option>
                                    </el-select>
                                </el-col>
                                <el-col :span="8">
                                    最大功率：
                                    <el-input v-model="radioItems.max_power_5" size="small" style="width: 120px;"></el-input>
                                    dBm(1-20)
                                </el-col>
                            </el-row>

                        </div>
                </el-col>
            </el-row>
    </div> -->
    <div v-for="(v, index) in wifiItems" :key="v.wid" style="border:1px dashed #000000;height: 80px;position: relative;">
        <div style="position: relative;top:5px;height: 80px;">
            <span class="settting-span">WIFI设置 (AP{{ v.aid }}-{{ v.vlan ? 'VLAN' : '无VLAN' }})</span>
            <el-row class="rowsetting" :gutter="10">
                <el-col :span="5" class="setttingcol">
                    SSID：
                    <el-input v-model="v.ssid" size="small" style="width: 200px;"></el-input>
                </el-col>
                <el-col :span="8" class="setttingcol">
                    <el-switch v-model="v.is_pwd" size="small" style="margin-bottom: 4px;"></el-switch>
                    密码：
                    <el-input v-model="v.wifipassword" size="small" style="width: 200px;" placeholder="密码长度设定在8-16位数" :disabled="!v.is_pwd"></el-input>
                    <span style="font-size: 12px;color: red;">密码长度设定在8-16位数</span>
                </el-col>
                <el-col :span="5" class="setttingcol">
                    隐藏SSID：
                    <el-radio-group v-model="v.ssid_hide">
                        <el-radio label="隐藏" value="Enabled"></el-radio>
                        <el-radio label="显示" value="Disabled"></el-radio>
                    </el-radio-group>
                </el-col>
                <el-col :span="5" class="setttingcol">
                    二层隔离：
                    <el-radio-group v-model="v.user_isolation">
                        <el-radio label="开启" value="Enabled"></el-radio>
                        <el-radio label="关闭" value="Disabled"></el-radio>
                    </el-radio-group>
                </el-col>

            </el-row>

        </div>
        <!-- <el-button type="primary" style="position: absolute;top: 10px;right: 10px;" plain round :icon="Setting" size="small"></el-button> -->
        <!-- 修改确定按钮，添加禁用状态和加载状态 -->
        <el-button 
            type="primary" 
            style="position: absolute;top:10px;right: 10px;width: 70px;" 
            round 
            :icon="Check" 
            size="middle" 
            :disabled="isUpdatingWifi[v.wid] || isLoading"
            :loading="isUpdatingWifi[v.wid]"
            @click="handleWifiUpdate(v, index)"
        >
            {{ isUpdatingWifi[v.wid] ? '更新中...' : '确定' }}
        </el-button>
    </div>
    <el-dialog v-model="batchAddWifiDialog" title="批量添加wifi" width="60%">
        <el-form :model="batchAddWifiForm" label-width="120px">
            <el-form-item label="要添加的wifi个数">
                <el-input-number v-model="batchAddWifiForm.wifiCount" placeholder="请输入要添加的wifi个数" :min="1" :max="16"><span style="color: red;">最多16个wifi</span></el-input-number>
            </el-form-item>
            <el-form-item label="SSID前缀">
                <el-input v-model="batchAddWifiForm.ssidPrefix" placeholder="请输入SSID前缀" style="width: 400px;"></el-input>
            </el-form-item>
            <el-form-item label="密码前缀">
                <el-input v-model="batchAddWifiForm.passwordPrefix" placeholder="请输入密码前缀" style="width: 400px;"></el-input>
            </el-form-item>
        </el-form>
        <div v-for="(v, index) in batchWifiList" style="display: flex;">
            <p style="width: 80px;text-align: center;font-size: 16px;font-weight: bold;margin:10px 8px;">wifi-{{ index + 1 }}</p>
            <el-descriptions :column="3" border  :key="index" style="">
                <el-descriptions-item label="SSID" label-class-name="batch-label" class-name="batch-content">
                    {{ batchAddWifiForm.ssidPrefix }}{{ index + 1 }}
                </el-descriptions-item>
                <el-descriptions-item label="密码" label-class-name="batch-label" class-name="batch-content">
                    {{ batchAddWifiForm.passwordPrefix }}
                </el-descriptions-item>
            </el-descriptions>
        </div>
        <template #footer>
            <el-button type="primary" @click="batchAddWifi" :loading="isLoading">确定</el-button>
            <el-button @click="batchAddWifiDialog = false" :loading="isLoading">取消</el-button>
        </template>

    </el-dialog>
    <el-dialog v-model="batchDelWifiDialog" title="批量删除wifi" width="60%">
        <el-form :model="batchDelWifiForm" label-width="120px">
            <el-form-item label="要删除的wifi个数">
                <el-input-number v-model="batchDelWifiForm.wifiCount" placeholder="请输入要删除的wifi个数" :min="1" :max="20"><span style="color: red;">最多20个wifi</span></el-input-number>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="batchDelWifi" :loading="isLoading">确定</el-button>
            <el-button @click="batchDelWifiDialog = false" :loading="isLoading">取消</el-button>
        </template>
    </el-dialog>
    <el-dialog v-model="addNoVlanWifiDialog" title="添加wifi（无VLAN）" width="60%">
        <el-form :model="addNoVlanWifiForm" label-width="120px" :rules="addNoVlanWifiRules" ref="addNoVlanWifiFormRef">
            <el-form-item label="SSID" prop="ssid">
                <el-input v-model="addNoVlanWifiForm.ssid" placeholder="请输入SSID" style="width: 400px;"></el-input>
            </el-form-item>
            <el-form-item label="密码" prop="password">
                <el-input v-model="addNoVlanWifiForm.password" placeholder="请输入密码" style="width: 400px;"></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="addNoVlanWifi" :loading="isLoading">确定</el-button>
            <el-button @click="addNoVlanWifiDialog = false" :loading="isLoading">取消</el-button> 
        </template>
    </el-dialog>
    <!-- 密码验证对话框 -->
    <el-dialog
            v-model="verifyPwdDialog"
            title="管理权限验证"
            width="400px"
            :close-on-click-modal="false"
            :close-on-press-escape="false"
        >
            <div style="text-align: center;">
                <el-icon size="48" color="#409EFF" style="margin-bottom: 16px;">
                    <Lock />
                </el-icon>
                <p style="margin-bottom: 20px; color: #606266;">请输入管理密码以访问功能</p>
                
                <el-form :model="verifyPwdForm" ref="verifyPwdRef" @submit.prevent>
                    <el-form-item prop="password" :rules="[{ required: true, message: '请输入管理密码', trigger: 'blur' },{ min: 1, message: '密码不能为空', trigger: 'blur' }]">
                        <el-input
                            v-model="verifyPwdForm.password"
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
                    <el-button @click="verifyPwdDialog = false" size="large">取消</el-button>
                    <el-button 
                        type="primary" 
                        @click="verifyPassword()" 
                        :loading="verifyPwdLoading"
                        size="large"
                    >
                        {{ verifyPwdLoading ? '验证中...' : '确认' }}
                    </el-button>
                </div>
            </template>
        </el-dialog>
</template>

<script setup>
import { ref,onMounted,computed, reactive } from 'vue';
import { Setting,Check, Lock } from '@element-plus/icons-vue';
import { useWifiStore } from '../store/dataStore.ts';
import { useRouter } from 'vue-router';
import { ElDescriptions, ElMessage, ElMessageBox } from 'element-plus';
import { axiosInstance } from '../store/messageaxios';
// const channel5list=ref([36,40,44,48,52,56,60,64,149,153,157,161,155,"auto"]);
// const channel24list=ref(['auto',1,2,3,4,5,6,7,8,9,10,11,12,13])

const wifiStore = useWifiStore();
const wifiItems = computed(() => wifiStore.wifiItems.filter(item => item.aid === aid.value));
const radioItems = computed(() => wifiStore.radioItems);
const isLoading = computed(() => wifiStore.isLoading);
const router = useRouter();
const aid = computed(() => Number(router.currentRoute.value.params.aid));
const verifyPwdType=ref('');
const verifyPwdForm=ref({
    password: '',
});
const verifyPwdRef=ref(null);
const verifyPwdDialog = ref(false);
const verifyPwdLoading = ref(false);
const verifyPassword=async(type)=>{
    try {
        await verifyPwdRef.value.validate();
    } catch (e) {
        // 校验失败时 validate 会 reject，这里吞掉异常，避免 Uncaught (in promise)
        ElMessage.error('请输入管理密码！');
        return;
    }
    verifyPwdLoading.value = true;
    try {
        const res = await axiosInstance.post('/api/verify_pwd', {
            password: verifyPwdForm.value.password,
            menu: 'wifi'
        });
        if(res.data.success){
            ElMessage.success('密码验证成功！');
            verifyPwdDialog.value = false;
            if(verifyPwdType.value === 'batchadd'){
                batchAddWifiDialog.value = true;
            }else if(verifyPwdType.value === 'delete'){
                batchDelWifiDialog.value = true;
            }else if(verifyPwdType.value === 'addNoVlan'){
                addNoVlanWifiDialog.value = true;
            }
        }else{
            ElMessage.error('密码验证失败！');
        }
    } catch (error) {
        console.error('密码验证失败:', error);
    } finally {
        verifyPwdLoading.value = false;
        verifyPwdForm.value.password = '';
    }
}
const batchAddWifiDialog = ref(false);
const batchAddWifiForm = ref({
    wifiCount: 1,
    ssidPrefix: 'test',
    passwordPrefix: 'test'
});
const batchDelWifiForm = ref({
    wifiCount: 1,
});
// 为每个WiFi项添加独立的更新状态，使用 wid 作为key
const isUpdatingWifi = ref({});

// 根据aid获取对应的射频绑定列表
const getRadioBindList = (currentAid) => {
    const radioList = [];
    for (let radio of radioItems.value) {
        if (radio.aid === currentAid) {
            const tag = radio.type + '(' + radio.rid + ')';
            radioList.push(tag);
        }
    }
    return radioList;
};

// 处理WiFi更新的方法
const handleWifiUpdate = async (wifiItem, index) => {
    console.log('wifistore的wifiItems:', wifiStore.wifiItems);
    console.log('wifiItems:', wifiItems.value);
    console.log('更新WiFi项:', wifiItem);
    console.log('aid:', wifiItem.aid, 'wid:', wifiItem.wid);

    // 密码长度校验：8-16位
    if (wifiItem.is_pwd) {
    const pwd = wifiItem.wifipassword || '';
    if (pwd.length < 8 || pwd.length > 16) {
        console.warn('密码长度不符合要求:', pwd.length);
        alert('密码长度需控制在8-16位数，请检查输入！');
        return;
    }}
    // 设置当前项的更新状态
    isUpdatingWifi.value[wifiItem.wid] = true;
    
    try {
        // 调用store的更新方法，传递正确的aid和wid
        await wifiStore.resetWifiInfo(wifiItem.aid, wifiItem.wid,undefined,'update');
    } catch (error) {
        console.error('WiFi更新失败:', error);
    } finally {
        // 无论成功失败，都要重置更新状态
        isUpdatingWifi.value[wifiItem.wid] = false;
    }
};
const batchList = ref([]);
const radio_bind_default=computed(() => {
    return radioItems.value[0]['type']+'('+radioItems.value[0]['rid']+')';
});
const batchWifiList = computed(() => {
    const batchWifiTemp = [];
    for(let i = 1; i <= batchAddWifiForm.value.wifiCount; i++) {
        batchWifiTemp.push({
            ssid: batchAddWifiForm.value.ssidPrefix + i,
            wifipassword: batchAddWifiForm.value.passwordPrefix,
            status: "Enabled",
            aid: aid.value,
            wid: i+wifiItems.value.filter(item => item.aid === aid.value && item.vlan).length,
            radio_bind:[radio_bind_default.value],
            ssid_hide: "Disabled",
            user_isolation: "Disabled",
            vlan: true
        });
    }
    console.log('batchWifiList:', batchWifiTemp);
    batchList.value = batchWifiTemp;
    return batchWifiTemp;
});

const openBatchAddWifi=()=>{
    if(wifiItems.value.length + batchAddWifiForm.value.wifiCount > 16){
        ElMessage.error('最多16个wifi！');
        return;
    }
    console.log('批量添加wifi');
    verifyPwdDialog.value = true;
    verifyPwdType.value = 'batchadd';
}

const batchAddWifi=async()=>{
    console.log('batchList:', batchList.value);
    if(batchList.value.length+wifiItems.value.length > 16){
        ElMessage.error('最多16个wifi！');
        return;
    }
    for(let item of batchList.value){
        if(item.wifipassword.length  < 8 || item.wifipassword.length > 16){
            console.warn('密码长度不符合要求:', item.wifipassword.length);
            alert('密码长度需控制在8-16位数，请检查输入！');
            return;
        }
        const isSameWifi = wifiItems.value.some(wifi => wifi.ssid === item.ssid && wifi.aid === aid.value);
        if(isSameWifi){
            console.warn('SSID已存在:', item.ssid);
            alert('SSID已存在，请检查输入！');
            return;
        }
    }
    
    await wifiStore.resetWifiInfo(undefined, undefined, batchList.value,'add');
    batchAddWifiDialog.value = false;
}
const batchDelWifiDialog = ref(false);
const openBatchDelWifi=()=>{
    console.log('批量删除wifi');

    verifyPwdDialog.value = true;
    verifyPwdType.value = 'delete';
}
const batchDelWifi=async()=>{
    console.log('batchDelWifiForm:', batchDelWifiForm.value);
    if(batchDelWifiForm.value.wifiCount > wifiItems.value.filter(item => item.aid === aid.value).length){
        ElMessage.error('要删除的wifi个数不能大于当前wifi个数！');
        return;
    }
    const delWifiList = wifiItems.value.filter(item => item.aid === aid.value).slice(wifiItems.value.length - batchDelWifiForm.value.wifiCount, wifiItems.value.length).map(item => item.wid);
    console.log('delWifiList:', delWifiList,wifiItems);
    await wifiStore.batchDelWifi(delWifiList,aid.value);
    batchDelWifiDialog.value = false;
}
const addNoVlanWifiDialog = ref(false);
const addNoVlanWifiForm = ref({
    ssid: '',
    password: '',
});
const addNoVlanWifiFormRef = ref(null);
const addNoVlanWifiRules = ref({
    ssid: [
        { required: true, message: '请输入SSID', trigger: 'blur' },
    ],
    password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 8, max: 16, message: '密码长度需控制在8-16位数', trigger: 'blur' },
    ],
});
const openAddNoVlanWifi=()=>{
    if(wifiItems.value.length + 1 > 16){
        ElMessage.error('最多16个wifi！');
        return;
    }
    console.log('添加wifi（无VLAN）');
    verifyPwdDialog.value = true;
    verifyPwdType.value = 'addNoVlan';
}
const addNoVlanWifi=async()=>{
    console.log('addNoVlanWifiForm:', addNoVlanWifiForm.value);

    const addNoVlanWifiList = {
        ssid: addNoVlanWifiForm.value.ssid,
        wifipassword: addNoVlanWifiForm.value.password,
        status: "Enabled",
        aid: aid.value,
        wid: wifiItems.value.filter(item => item.aid === aid.value && !item.vlan).length + 1 +200,
        radio_bind:[radio_bind_default.value],
        vlan: false,
        user_isolation: "Disabled",
        ssid_hide: "Disabled",
    }
    await wifiStore.resetWifiInfo(undefined, undefined, [addNoVlanWifiList],'addNoVlan');
    addNoVlanWifiDialog.value = false;
}
onMounted(async () => {
    // 确保数据已加载
    await wifiStore.initializeData();
    console.log('当前AP ID:', aid.value);
    console.log('WiFi项:', wifiItems.value);
})
</script>

<style scoped>
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
.rowsetting{
    /* font-size:17px;
    color: #190ae7; */
    width: 100%;
    margin-left: 30px;
    margin-top: 15px;
}
 .settting-span{
    font-weight: bold;
    font-size:18px;
    color: #b435f4f5;
    margin-left:10px;
    margin-bottom: 20px;

}
.setttingcol{
    margin-bottom: 40px;
    margin-left:10px;
}
.secdiv{
    margin-top: 10px;
    margin-left: 10px;
    background-color: #e4fcf0f5;
}
:deep(.batch-content){
    color: #cf129394 !important;
    font-size: 18px !important;
    font-weight: bold !important;
    background-color: #d0f4d094 !important;
    
}

:deep(.batch-label){
    background-color:  #a1e5a294!important;
    font-size: 18px !important;
    font-weight: bold !important;
    width:70px !important;
}
</style>