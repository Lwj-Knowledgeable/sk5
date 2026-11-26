<template >
    <el-button type="success" plain circle :icon="Refresh" :loading="refreshLoading" @click="refreshBalance"></el-button>
    <el-button :type="schedulerStatus ? 'primary' : 'warning'" plain :icon="Setting" :loading="settingLoading" @click="BalanceScheduler">
        {{ schedulerStatus ? '关闭负载均衡' : '开启负载均衡' }}
    </el-button>

    <!-- 加载状态 -->
    <div v-if="isLoading" style="text-align: center; margin-top: 50px;">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>正在加载数据...</p>
    </div>
    
    <!-- 无数据状态 -->
    <div v-else-if="balanceItems.length === 0" style="text-align: center; margin-top: 50px;">
        <el-empty description="暂无数据" />
    </div>
    
    
    <!-- 数据展示 -->
    <div v-else style="margin-left: 10%;margin-top: 30px;overflow: hidden;">
            <el-divider/>
            <span style="font-size: 18px;display: block;margin-bottom: 20px;"><span style="padding-right: 10px;display: inline;font-size: 30px;color: rgb(222 118 96);">{{ wanItems.length }}</span>外网网口</span>
            <div style="margin-left: 20px; width: 250px; display: inline-block; " v-for="item in  wanItems" :key="item.id">
                <div style="justify-content: center;align-items: center;">
                    <el-button style="width: 60px; height: 60px; border-radius: 10%;" disabled>
                    <!-- <el-button style="width: 60px; height: 60px; border-radius: 10%;" @click="EtherDisabledChange(item.interface,!item.disabled)"> -->
                        <el-icon style="width: 60px; height: 60px;">
                            <img v-if="item.running==false" src="../public/portdown.png" style="width: 60px; height: 60px;"></img>
                            <img v-else src="../public/portup.png" style="width: 60px; height: 60px;"></img>
                        </el-icon>
                    </el-button>
                    <el-row style="margin-top: 10px;">接口：<el-col :style="{ color: getTypeColor(item) }" :span="12">{{item.interface}}</el-col></el-row>
                    <el-row>类型：<el-col :style="{ color: getTypeColor(item) }" :span="12">{{item.type}}</el-col></el-row>
                    <el-row>状态：<el-col :style="{ color: getTypeColor(item) }" :span="12">{{item.running==true ? '连通' : '离线'}}</el-col></el-row>
                    <el-row v-if="item.balance===true" type="flex">接入方式：
                        <el-col :span="12" v-if="item.dhcp.status==='enabled'" :style="{ color: getTypeColor(item) }">DHCP-自动获取</el-col>
                        <el-col :span="12" v-if="item.static_ip.status==='enabled'" :style="{ color: getTypeColor(item) }">静态IP-手动设置</el-col>
                        <el-col :span="12" v-if="item.ppoe.status==='enabled'" :style="{ color: getTypeColor(item) }">ADSL-拨号方式</el-col>
                        <el-button type="primary" size="small" @click="OpenEtherTypeDialog(form,item)" :icon="Edit" style="" link></el-button>
                    </el-row>
                    <el-row v-if="item.balance===false">
                        接入方式：
                        <el-col :span="12" :style="{ color: getTypeColor(item) }">无</el-col>
                    </el-row>
                    <!-- <el-row>上传：<el-col :span="12">{{formatBytes(item.up)}}</el-col></el-row>
                    <el-row>下载：<el-col :span="12">{{formatBytes(item.down)}}</el-col></el-row> -->
                    <el-row>负载均衡状态：
                        <el-col :span="8">
                            <el-switch
                                :id="`switch-${item.interface}`"
                                aria-disabled="true"
                                v-model="item.balance"
                                style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
                                @change="handleBalanceChange(item, $event)"
                                active-text="开启"
                                inactive-text="关闭"
                                inline-prompt
                                :loading="balanceLoading"
                            >
                        </el-switch>
                        </el-col>
                    </el-row>
                </div>
            </div>
            <el-divider />
            <span style="font-size: 18px;display: block;margin-bottom: 20px;"><span style="padding-right: 10px;display: inline;font-size: 30px;color: rgb(222 118 96);">{{ lanItems.length }}</span>内网网口</span>
            <div style="margin-left: 20px; width: 250px;display:inline-block;" v-for="item in  lanItems" :key="item.id">
                <div style="justify-content: center;align-items: center;">
                    <el-button style="width: 60px; height: 60px; border-radius: 10%;" disabled>
                    <!-- <el-button style="width: 60px; height: 60px; border-radius: 10%;" @click="EtherDisabledChange(item.interface,!item.disabled)"> -->
                        <el-icon style="width: 60px; height: 60px;">
                            <img v-if="item.running==false" src="../public/portdown.png" style="width: 60px; height: 60px;"></img>
                            <img v-else src="../public/portup.png" style="width: 60px; height: 60px;"></img>
                        </el-icon>
                    </el-button>
                    <el-row  style="margin-top: 10px;">接口：<el-col :style="{ color: getTypeColor(item) }" :span="12">{{item.interface}}</el-col></el-row>
                    <el-row >类型：<el-col :style="{ color: getTypeColor(item) }" :span="12">{{item.type}}</el-col></el-row>
                    <el-row >状态：<el-col :style="{ color: getTypeColor(item,state) }" :span="12">{{item.running==true ? '连通' : '离线'}}</el-col></el-row>
                    <el-row v-if="item.balance===true" type="flex">接入方式：
                        <el-col :span="12" :style="{ color: getTypeColor(item) }">无</el-col>
                        <!-- <el-col :span="12" v-if="item.static_ip.status==='enabled'" :style="{ color: getTypeColor(item) }">静态IP-手动设置</el-col>
                        <el-col :span="12" v-if="item.ppoe.status==='enabled'" :style="{ color: getTypeColor(item) }">ADSL-拨号方式</el-col>
                        <el-button type="primary" size="small" @click="OpenEtherTypeDialog(form,item)" :icon="Edit" style="" link></el-button> -->
                    </el-row>
                    <el-row v-if="item.balance===false">
                        接入方式：
                        <el-col :span="12" :style="{ color: getTypeColor(item) }">无</el-col>
                    </el-row>
                    <!-- <el-row>上传：<el-col :span="12">{{formatBytes(item.up)}}</el-col></el-row>
                    <el-row>下载：<el-col :span="12">{{formatBytes(item.down)}}</el-col></el-row> -->
                    <el-row>负载均衡状态：
                        <el-col :span="8">
                            <el-switch
                                :id="`switch-${item.interface}`"
                                aria-disabled="true"
                                v-model="item.balance"
                                style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
                                @change="handleBalanceChange(item, $event)"
                                active-text="开启"
                                inactive-text="关闭"
                                inline-prompt
                                :loading="balanceLoading"
                            >
                        </el-switch>
                        </el-col>
                    </el-row>
                </div>
            </div>
    </div>
    <el-dialog v-model="dialogVisible" width="60%" >
        <el-tag type="warning" size="large" effect="dark" style="font-size:20px">当前配置端口：{{ dialogInterface }}</el-tag>
        <el-form :model="form" label-width="120px"  :rules="formRules" ref="formRef" width="20px" style="margin:30px 40px 40px 0">
            <el-form-item label="接入方式" prop="accessType">
                <el-select v-model="form.accessType" placeholder="请选择接入方式">
                    <el-option label="DHCP(动态获取)" value="dhcp"></el-option>
                    <el-option label="静态IP-手动设置" value="ip"></el-option>
                    <el-option label="ADSL-拨号方式" value="ppoe"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="状态">
                    <span v-if="currentAccessInfo.status === 'enabled'" style="color: #13ce66;font-size: 18px;font-weight: bold;">已连接</span>
                    <span v-else style="color: #ff4949;font-size: 18px;font-weight: bold;">已断开</span>
            </el-form-item>
            <el-form-item label="提示">
                <span :style="{ color: currentMsgInfo.danger ? '#ff4949' : '#13ce66', fontSize: '18px', fontWeight: 'bold' }">{{currentMsgInfo.text}}</span>
            </el-form-item>
            <el-form-item label="数量">
                <span style="color: blue;font-size: 18px;font-weight: bold;"> {{form.accessType}}数量：{{currentAccessInfo.len}}</span>
            </el-form-item>
            <!-- 静态IP -->
            <el-form-item label="IP地址"  v-if="form.accessType=='ip'" prop="ipAddress">
                <el-input v-model="form.ipAddress" placeholder="请输入IP地址,例如：192.168.1.100" ></el-input>
            </el-form-item>
            <el-form-item label="网关" v-if="form.accessType=='ip'" prop="gateway">
                <el-input v-model="form.gateway" placeholder="请输入网关"></el-input>
            </el-form-item>
            <el-form-item label="首选DNS" v-if="form.accessType=='ip'" prop="firstDns">
                <el-input v-model="form.firstDns" placeholder="请输入首选DNS"></el-input>
            </el-form-item>
            <el-form-item label="备选DNS" v-if="form.accessType=='ip'" prop="secondDns">
                <el-input v-model="form.secondDns" placeholder="请输入备选DNS"></el-input>
            </el-form-item>
            <!-- PPOE -->
            <el-form-item label="ppoe账号" v-if="form.accessType=='ppoe'" prop="ppoe_user">
                <el-input v-model="form.ppoe_user" placeholder="请输入ppoe账号"></el-input>
            </el-form-item>
            <el-form-item label="ppoe密码" v-if="form.accessType=='ppoe'" prop="ppoe_pd">
                <el-input v-model="form.ppoe_pd" placeholder="请输入ppoe密码"></el-input>
            </el-form-item>

        </el-form>
        <template #footer>
            <el-button type="primary" @click="InterfaceSubmit(form)" :loading="etherSubmitLoading">确定</el-button>
            <el-button @click="dialogVisible = false" :loading="etherSubmitLoading">取消</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';
import { useBalanceStore } from '../store/dataStore';
import { onMounted } from 'vue';
import { Refresh, Loading, Setting,Edit } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { axiosInstance } from '../store/messageaxios';
import { createEmitAndSemanticDiagnosticsBuilderProgram } from 'typescript';

const balanceStore = useBalanceStore();
const dialogVisible = ref(false);
const dialogInterface=ref();
const form = ref({
    interface:'',
    accessType: '',
    ipAddress: '',
    firstDns: '',
    secondDns: '',
    ppoe_user:'',
    ppoe_pd:'',
    gateway:'',
});
// 表单组件实例 ref，用于调用 el-form 自带的 validate 校验方法
const formRef = ref(null);

const formRules = ref({
    accessType: [
        { required: true, message: '请选择接入方式', trigger: 'change' },
    ],
    ipAddress: [
        { required: true, message: 'IP地址不为空', trigger: 'blur' },
        {type: 'string', pattern: /^((2(5[0-5]|[0-4]\d)|1\d{1,2}|\d{1,2})\.){3}(2(5[0-5]|[0-4]\d)|1\d{1,2}|\d{1,2})$/, message: 'IP地址格式不正确', trigger: 'blur' },
    ],
    ppoe_user: [
        { required: true, message: 'ppoe账号不为空', trigger: 'blur' },
    ],
    ppoe_pd: [
        { required: true, message: 'ppoe密码不为空', trigger: 'blur' },
    ],
    gateway: [
        { required: true, message: '网关不为空', trigger: 'blur' },
        {type: 'string', pattern: /^((2(5[0-5]|[0-4]\d)|1\d{1,2}|\d{1,2})\.){3}(2(5[0-5]|[0-4]\d)|1\d{1,2}|\d{1,2})$/, message: '网关格式不正确', trigger: 'blur' },
    ],
});
// 加载状态
const isLoading = ref(false);
const refreshLoading = ref(false);
const settingLoading = ref(false);
const balanceLoading = ref(false);
const etherSubmitLoading = ref(false);

// 负载均衡调度器状态
const schedulerStatus = ref(false);

// 使用计算属性来获取 store 中的数据，这样会自动响应数据变化
const balanceItems = computed(() => balanceStore.balanceItems);
const lanItems = computed(() => balanceItems.value.filter(item => item.type === 'LAN'));
const wanItems = computed(() => balanceItems.value.filter(item => item.type === 'WAN'));
// 当前弹窗选中的端口原始数据（含 dhcp / static_ip / ppoe 三种接入方式的 msg）
const selectedItem = ref(null);

// 接入方式 -> 该方式在接口返回里的字段名
const ACCESS_MSG_FIELD = {
    dhcp: 'dhcp',
    ip: 'static_ip',
    ppoe: 'ppoe',
};

// 接入方式 -> 需要参与校验的字段（只校验与当前接入方式相关的数据）
const ACCESS_VALIDATE_FIELDS = {
    dhcp: ['accessType'],
    ip: ['accessType', 'ipAddress', 'gateway'],
    ppoe: ['accessType', 'ppoe_user', 'ppoe_pd'],
};

// 根据当前选择的接入方式动态取出对应的 msg 与 status
const currentAccessInfo = computed(() => {
    const field = ACCESS_MSG_FIELD[form.value.accessType];
    const info = field && selectedItem.value ? selectedItem.value[field] : null;
    return {
        status: info?.status ?? '',
        msg: info?.msg ?? '',
        success: info?.success ?? null,
        len: info?.len ?? 0,
    };
});

// 表单里“提示”这一行显示的内容：跟随接入方式变化，红字代表异常
const currentMsgInfo = computed(() => {
    const { msg, success } = currentAccessInfo.value;
    if (!msg) return { text: '', danger: true };
    return { text: msg, danger: success === false };
});

// 格式化字节数的函数
const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 根据类型返回行文本颜色，WAN 使用开关开启色
const getTypeColor = (item,state=false) => {
    return item?.type=='WAN' ?  'rgb(121 222 38)':'rgb(223 156 79)'
};

const EtherDisabledChange = async (interfaceName,disabled)=>{
    console.log('before',balanceItems.value,lanItems.value,wanItems.value)
    const status= disabled? 'disable':'enable';
    const res=await axiosInstance.post('/api/set_ether_status',{interface:interfaceName,status:status})
    if(res.data.success){
        ElMessage.success(res.data.msg)
    }else{
        ElMessage.error(res.data.msg)
    }
    // console.log('after_res',balanceItems.value,lanItems.value,wanItems.value,balanceStore.balanceItems)
    await balanceStore.balanceData()
    console.log('after_store',balanceItems.value,lanItems.value,wanItems.value)
}
const OpenEtherTypeDialog = async (formel,item)=>{
    if(item.type=='WAN'){
        // 重置上一次的残留，避免切换端口后还保留旧的接入方式
        formel.accessType = '';
        dialogVisible.value = true;
        dialogInterface.value=item.interface
        selectedItem.value = item
        formel.interface=item.interface
        formel.gateway=item.static_ip.gateway
        formel.ipAddress=item.static_ip.ip
        formel.ppoe_user=item.ppoe.user
        formel.ppoe_pd=item.ppoe.pd
    }
    else{
        return
    }
}

// 获取负载均衡调度器状态
const fetchSchedulerStatus = async () => {
    try {
        const res = await axiosInstance.get('/api/balance_scheduler_status');
        console.log('获取状态响应:', res.data);
        if (res.data && res.data.success && res.data.data !== undefined) {
            // data 字段返回的是 disabled 状态，需要取反：disabled=false 表示开启
            schedulerStatus.value = !res.data.data;
            console.log('更新状态为:', schedulerStatus.value);
        } else if (res.data && res.data.status !== undefined) {
            schedulerStatus.value = res.data.status;
            console.log('更新状态为:', schedulerStatus.value);
        } else if (res.data && res.data.success === true && res.data.data === undefined) {
            // 如果成功但没有data字段，可能需要从其他字段获取
            console.warn('状态响应格式异常:', res.data);
        }
    } catch (error) {
        console.error('获取负载均衡调度器状态失败:', error);
        ElMessage.error('获取状态失败');
    }
}

// 切换负载均衡调度器状态
const BalanceScheduler = async () => {
    settingLoading.value = true;
    try {
        // 将布尔值转换为 1 或 0：false -> 1 (开启), true -> 0 (关闭)
        const statusValue = schedulerStatus.value ? 0 : 1;
        const res = await axiosInstance.post('/api/balance_scheduler', { status: statusValue });
        if (res.data && res.data.success) {
            // 立即更新本地状态，确保按钮立即刷新
            schedulerStatus.value = !schedulerStatus.value;
            ElMessage.success('操作成功');
            // 从服务器重新获取最新状态进行确认
            await fetchSchedulerStatus();
        } else {
            ElMessage.error('操作失败');
        }
    } catch (error) {
        console.error('切换负载均衡调度器状态失败:', error);
        ElMessage.error('操作失败，请重试');
    } finally {
        settingLoading.value = false;
    }
}

// 处理开关变化，显示确认弹窗
const handleBalanceChange = async (item, event) => {
    const action = item.balance ? '开启' : '关闭';
    const interfaceName = item.interface;
    
    // 滚动到触发元素位置
    await nextTick();
    const switchId = `switch-${interfaceName}`;
    const switchElement = document.getElementById(switchId);
    if (switchElement) {
        const rect = switchElement.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const targetY = rect.top + scrollTop - 100; // 100px 偏移，让元素上方留出空间
        
        window.scrollTo({
            top: targetY,
            behavior: 'smooth'
        });
        
        // 等待滚动完成后再显示弹窗
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    try {
        await ElMessageBox.confirm(
            `确定要${action}接口 "${interfaceName}" 的负载均衡吗？`,
            '确认操作',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
                closeOnClickModal: false,
                closeOnPressEscape: false,
                showClose: false,
            }
        );
        // 输入密码
        const { value: password, action: promptAction } = await ElMessageBox.prompt(
            '请输入管理密码以继续操作',
            '密码验证',
            {
                confirmButtonText: '验证',
                cancelButtonText: '取消',
                inputType: 'password',
                inputPlaceholder: '请输入密码',
                inputValidator: (val) => {
                    if (!val) return '密码不能为空';
                    return true;
                }
            }
        ).catch(err => {
            // 取消输入
            return { value: null, action: 'cancel' };
        });

        if (promptAction === 'cancel' || !password) {
            item.balance = !item.balance;
            ElMessage.info('已取消操作');
            return;
        }

        // 先验证密码（指向指定端口的 /api/verify_pwd）
        const verifyRes = await axiosInstance.post('/api/verify_pwd', { 'password':password,'menu':'balance' });
        if (!(verifyRes.data && verifyRes.data.success)) {
            item.balance = !item.balance;
            ElMessage.error(verifyRes.data && verifyRes.data.msg ? verifyRes.data.msg : '密码错误');
            return;
        }

        // 验证通过，执行设置
        console.log(item.interface,item.balance)
        balanceLoading.value=true;
        const req=await axiosInstance.post('/api/setbalance',{interface:item.interface,balance:item.balance})
        console.log(req.data,lanItems,wanItems)
        if(req.data.success){
            ElMessage.success(req.data.msg)
            // API调用成功，保持开关状态不变
        }else{
            ElMessage.success(req.data.msg)
        }
    } catch (error) {
        // 用户点击取消或网络错误，恢复开关状态
        // item.balance = !item.balance;
        if (error === 'cancel') {
            ElMessage.info('已取消操作');
        } else {
            ElMessage.error('操作失败，请重试');
        }
    }
    await balanceStore.balanceData();
    balanceLoading.value=false;
}
    
const refreshBalance = async () => {
    refreshLoading.value = true;
    try {
        await balanceStore.balanceData();
    } finally {
        refreshLoading.value = false;
    }
}

const InterfaceSubmit = async (formel) => {
    console.log("formel:", formel);
    etherSubmitLoading.value=true;
    // el-form 实例不存在时直接退出，避免报错
    if (!formRef.value) {
        console.warn('未获取到 el-form 实例');
        etherSubmitLoading.value=false;
        return;
    }

    // 根据当前接入方式取出需要校验的字段（没选接入方式时只校验接入方式本身）
    const fields = ACCESS_VALIDATE_FIELDS[formel.accessType] || ['accessType'];

    // 清掉上一次校验留下的红色提示，避免残留
    formRef.value.clearValidate();

    // 只校验与当前接入方式相关的字段：
    // validateField 在校验失败时会 reject 一个 { 字段名: [{message}] } 结构
    try {
        await formRef.value.validateField(fields);
    } catch (invalidFields) {
        console.log('表单校验未通过:', invalidFields);

        // 把所有报错信息收集起来，用弹窗提示
        const messages = Object.values(invalidFields)
            .flat()
            .map((item) => item.message);

        await ElMessageBox.alert(
            messages.join('<br/>'),
            '校验未通过',
            {
                confirmButtonText: '知道了',
                type: 'warning',
                dangerouslyUseHTMLString: true,
            }
        ).catch(() => {});
        etherSubmitLoading.value=false;
        return;
    }
    if(selectedItem.value.ppoe.len != 1 || selectedItem.value.static_ip.len != 1 || selectedItem.value.dhcp.len != 1){
        const mes=[
            selectedItem.value.ppoe.len != 1 ? 'ppoe数量不正确' : null,
            selectedItem.value.static_ip.len != 1 ? 'static_ip数量不正确' : null,
            selectedItem.value.dhcp.len != 1 ? 'dhcp数量不正确' : null,
        ]
        ElMessageBox.alert(selectedItem.value.interface+'的'+mes.filter(item => item !== null).join('<br/>')+'<br/>请检查winboxs配置 或 修改后重新提交', '提示', {
            confirmButtonText: '知道了',
            type: 'warning',
            dangerouslyUseHTMLString: true,
        }).catch(() => {});
        etherSubmitLoading.value=false;
        return;
    }
    
    // 根据接入方式组装要提交的数据（必须在 if/else 外部声明，
    // 否则块级作用域会让下面的 axios 调用拿不到 sendData）
    let sendData = {};
    if(formel.accessType=='ip'){
        sendData={
            accessType:formel.accessType,
            interface:formel.interface,
            ip:formel.ipAddress,
            gateway:formel.gateway,
            firstDns:formel.firstDns,
            secondDns:formel.secondDns,
        }
        console.log('IP sendData:', sendData);
    }
    else if(formel.accessType=='ppoe'){
        sendData={
            accessType:formel.accessType,
            interface:formel.interface,
            ppoe_user:formel.ppoe_user,
            ppoe_pd:formel.ppoe_pd
        }
        console.log('PPOE sendData:', sendData);
    }
    else if(formel.accessType=='dhcp'){
        sendData={
            accessType:formel.accessType,
            interface:formel.interface
        }
        console.log('DHCP sendData:', sendData);
    }
    const res=await axiosInstance.post('/api/set_ether_type',sendData)
    if(res.data.success){
        ElMessage.success(res.data.msg)
    }else{
        ElMessage.error(res.data.msg)
    }
    // 校验通过
    console.log('校验通过，提交数据:', formel);
    await balanceStore.balanceData();
    // TODO: 调用后端接口提交配置
    etherSubmitLoading.value=false;
    selectedItem.value=balanceItems.value.filter(item => item.interface == formel.interface)[0];
}

onMounted(async () => {
    console.log('BalanceTag mounted, 开始获取数据...');
    isLoading.value = true;
    try {
        // 等待数据获取完成
        await balanceStore.balanceData();
        // 获取负载均衡调度器状态
        await fetchSchedulerStatus();
        console.log('Balance items:', balanceItems.value);
        console.log('Balance items length:', balanceItems.value.length);
    } catch (error) {
        console.error('获取数据失败:', error);
    } finally {
        isLoading.value = false;
    }
})


</script>

<style scoped>
.el-row{
    width: 100%;
    padding:2px 2px;
    margin:2px 2px;
    border: 1px dashed #74d117;
    
}   
.el-col{
    text-align: center;
    font-size: 17px;
    font-weight: bold;
    color: #d1173f;
}
</style>