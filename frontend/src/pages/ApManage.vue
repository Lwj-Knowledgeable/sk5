<template>
    <div>
        <el-breadcrumb separator="/" style="margin-bottom: 30px;margin-top: 10px;">
            <el-breadcrumb-item :to="{ path: '/ap' }">返回</el-breadcrumb-item>
            <el-breadcrumb-item :to="{ path: '/apManage/' + aid }">AP{{ aid }}</el-breadcrumb-item>
        </el-breadcrumb>
        <h1>AP管理 - AP{{ aid }}</h1>
        <div v-for="item in channel_bandwidth">
        <el-card style="width: 60%;margin-bottom: 20px;height: 220px;margin-left: 40px;">
            <el-row style="margin-bottom:20px">
                <span>射频{{item.rid}}--{{ item.type }}</span>
                <span style="margin-left: 20px;color: red;" v-if="item.state === 'Down'">射频关闭</span>
                <span style="margin-left: 20px;color: green;" v-else-if="item.state === 'Up'">射频开启</span>
            </el-row>
            <el-row>
                <span class="settting-span">信道设置：</span>
                <el-select v-model="radioChannelValues[item.rid]" style="width:180px;margin-bottom: 20px;">
                    <el-option v-for="channelitem in item.channel" :label="channelitem" :value="channelitem"></el-option>
                </el-select>
                <el-button type="primary" @click="setChannel(item.rid,radioChannelValues[item.rid])" style="margin-left:10px" :loading="SubmitLoading">提交</el-button>
            </el-row>
            
            
            <el-row>
                <span class="settting-span">频率绑定：</span>
                <el-select v-model="radioBandwidthValues[item.rid]"  style="width:180px;margin-bottom: 20px;">
                    <el-option v-for="bandwidthitem in item.bandwidth" :label="bandwidthitem" :value="bandwidthitem"></el-option>
                </el-select>
                <el-button type="primary" @click="setBandwidth(item.rid,radioBandwidthValues[item.rid])" style="margin-left:10px" :loading="SubmitLoading">提交</el-button>
            </el-row>
            <el-row>
                <span class="settting-span">最大功率：</span>
                <el-input-number v-model="radioMaxPowerValues[item.rid]" :min="1" :max="20" style="width:180px;height: 30px;">
                    <template #suffix>
                        <span>dBm</span>
                    </template>
                </el-input-number>
                <el-button type="primary" @click="setMaxpower(item.rid,radioMaxPowerValues[item.rid])" style="margin-left:10px" :loading="SubmitLoading">提交</el-button>
            </el-row>
        </el-card>
        </div>


        <div v-if="currentWifiItem">
            <el-card style="width: 60%;margin-bottom: 20px;height: auto;margin-left:40px">
            <div v-for="item in currentWifiItem" :key="item.wid" style="margin-bottom: 20px;">
                <el-row>
                    <el-col :span="12" style="margin-left: 10px;margin-bottom: 20px;"><span class="settting-span">SSID：</span>{{ item.ssid }}</el-col>
                    <el-col :span="12" class="setttingcol">
                        <span class="settting-span">频率绑定：</span>
                        <el-select size="small" style="width: 300px;" multiple v-model="item.radio_bind">
                            <el-option v-for="radio in getRadioBindList(item.aid)" :label="radio" :value="radio"></el-option>
                        </el-select>
                    </el-col>
                </el-row>
            </div>
            <el-button style="margin-top: 20px;float:right;margin-bottom:20px;" @click="setRadioManage" :loading="SubmitLoading">确定</el-button>
            </el-card>
            
        </div>
        
        <div v-else>
            <p>正在加载WiFi配置...</p>
        </div>
        
        
        <!-- SSH连接状态 -->
        <!-- <div style="margin: 20px 0;">
            <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'">
                {{ connectionStatus === 'connected' ? '已连接' : '未连接' }}
            </el-tag>
        </div> -->
        
        <!-- 终端输出区域 -->
        <!-- <div style="margin: 20px 0;">
            <h3>终端输出</h3>
            <div 
                ref="terminalOutput" 
                class="terminal-output"
                v-html="terminalContent"
            ></div>
        </div> -->
        
        <!-- 命令输入区域 -->
        <!-- <div style="margin: 20px 0;">
            <el-input
                v-model="command"
                placeholder="输入命令..."
                @keyup.enter="sendCommand"
                :disabled="connectionStatus !== 'connected'"
            >
                <template #append>
                    <el-button 
                        @click="sendCommand" 
                        :disabled="connectionStatus !== 'connected'"
                    >
                        发送
                    </el-button>
                </template>
            </el-input>
        </div> -->
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed, reactive} from 'vue'
import { useRoute } from 'vue-router'
import { ElDialog, ElMessage } from 'element-plus'
import { io } from 'socket.io-client'
import { axiosInstance } from '../store/messageaxios'
import { useWifiStore } from '../store/dataStore.ts';
import { useRouter } from 'vue-router';
import axios from 'axios'

const wifiStore = useWifiStore();
const wifiItems = computed(() => wifiStore.wifiItems.filter(item => Number(item.aid) === aid.value));
const radioItems = computed(() => wifiStore.radioItems);
const isLoading = computed(() => wifiStore.isLoading);
const router = useRouter();
const aid = computed(() => Number(router.currentRoute.value.params.aid));
const SubmitLoading =ref(false);
const bandwidthSubmitLoading=ref(false);
// 当前WiFi项（用于安全访问）
const currentWifiItem = computed(() => {
    const items = reactive(JSON.parse(JSON.stringify(wifiItems.value)));
    console.log('wifiItems.value:', items);
    console.log('aid.value:', aid.value);
    console.log('items.length:', items?.length);

    if (items && items.length > 0) {
        // 返回第一个匹配的WiFi项
        console.log('返回第一个WiFi项:', items);
        return items;
    }

    console.log('没有找到匹配的WiFi项，返回null');
    return null;
});

// 添加调试信息
console.log('ApManage.vue 已加载，路由参数:', router.currentRoute.value.params);
console.log('AID值:', aid.value);
console.log('wifiItems:', wifiItems.value);
// Socket连接
const socket = ref(null)
const connectionStatus = ref('disconnected')
const isConnecting = ref(false)
const isDisconnecting = ref(false)

// 终端相关
const terminalOutput = ref(null)
const terminalContent = ref('')
const command = ref('')

// 信道带宽数据
const channel_bandwidth = ref([])

const SOCKET_BASE_URL = import.meta.env.VITE_SOCKET_BASE_URL || window.location.origin

// 初始化数据
onMounted(async () => {
    console.log('ApManage.vue onMounted 执行');
    try {
        // 确保数据已加载
        await wifiStore.initializeData();

        // 获取信道带宽信息（用于显示选项卡片）
        await getChannelBindwidth();

        // 初始化射频channel和带宽值 - 使用radioItems中的数据作为默认选中值
        radioItems.value.forEach(radio => {
            if (radio.aid === aid.value) {  // 只处理当前AP的radio
                const key = `${radio.aid}-${radio.rid}`;
                radioChannelValues.value[radio.rid] = radio.channel || '';
                radioBandwidthValues.value[radio.rid] = radio.channel_bandwidth || '';
                radioMaxPowerValues.value[radio.rid] = parseInt(radio.max_power) || 0;
                radioStateValues.value[radio.rid] = radio.state || '';
            }
        });

        console.log('ApManage.vue 数据初始化完成');
        console.log('当前AID:', aid.value);
        console.log('WiFi项:', wifiItems.value);
        console.log('信道带宽信息:', channel_bandwidth.value);
        console.log('带宽，信道值,最大功率:',radioChannelValues.value,radioBandwidthValues.value,radioMaxPowerValues.value)
    } catch (error) {
        console.error('ApManage.vue 初始化失败:', error);
        ElMessage.error('页面初始化失败: ' + error.message);
    }
});

// 初始化Socket连接
const initSocket = () => {
    socket.value = io(SOCKET_BASE_URL, {
        path: '/socket.io',
        withCredentials: true,
        transports: ['websocket', 'polling']
    })
    
    // 监听连接状态
    socket.value.on('connect', () => {
        console.log('Socket连接成功')
        connectionStatus.value = 'connected'
    })
    
    socket.value.on('disconnect', () => {
        console.log('Socket连接断开')
        connectionStatus.value = 'disconnected'
    })
    
    // 监听SSH连接状态
    socket.value.on('ssh_connection_status', (data) => {
        console.log('SSH连接状态:', data)
        if (data.status === 'connected') {
            ElMessage.success(data.message)
            connectionStatus.value = 'connected'
        } else if (data.status === 'error') {
            ElMessage.error(data.message)
            connectionStatus.value = 'disconnected'
        }
        isConnecting.value = false
    })
    
    // 监听SSH输出
    socket.value.on('ssh_output', (data) => {
        console.log('SSH输出:', data)
        terminalContent.value += data.data
        // 自动滚动到底部
        nextTick(() => {
            if (terminalOutput.value) {
                terminalOutput.value.scrollTop = terminalOutput.value.scrollHeight
            }
        })
    })

    socket.value.on('connect_error', (err) => {
        console.error('Socket连接错误:', err)
        ElMessage.error('Socket连接失败，请检查服务器')
        isConnecting.value = false
    })
}

// 连接AP
const openManageWifi = async () => {
    if (connectionStatus.value === 'connected') {
        ElMessage.warning('已经连接到AP')
        return
    }
    initSocket()
    isConnecting.value = true
    try {
        // 通过Socket发送连接请求
        socket.value.emit('apc', { aid: aid.value })
    } catch (error) {
        console.error('连接AP失败:', error)
        ElMessage.error('连接AP失败')
        isConnecting.value = false
    }
}
const getRadioBindList = computed(() => (currentAid) => {
    const radioList = [];
    for (let radio of radioItems.value) {
        if (radio.aid === currentAid) {
            const tag = radio.type + '(' + radio.rid + ')';
            radioList.push(tag);
        }
    }
    return radioList;
});

// 射频channel绑定状态
const radioChannelValues = ref({});
const radioMaxPowerValues = ref({});
const radioBandwidthValues = ref({});
const radioStateValues = ref({});
// 获取射频channel绑定值
// const getRadioChannelValue = (rid, aid) => {
//     const radio = radioItems.value.find(r => r.rid === rid && r.aid === aid);
//     return radio ? radio.channel : '';
// };



// // // 获取射频channel绑定值
// const getRadioBandwidthValue = (rid, aid) => {
//     const key = `${aid}-${rid}`;
//     if (!(key in radioBandwidthValues.value)) {
//         const radio = radioItems.value.find(r => r.rid === rid && r.aid === aid);
//         radioBandwidthValues.value[key] = radio ? radio.channel_bandwidth : '';
//     }
//     return radioBandwidthValues.value[key];
// };
//获取AP中各个频道的信道带宽设置范围
const getChannelBindwidth=async()=>{
    const req=await axiosInstance.post('/api/get_channel_bandwidth',{aid:aid.value})
    if(req.data.success){
        channel_bandwidth.value = req.data.msg
        ElMessage.success('获取信道带宽成功!!')
        console.log('channel:',channel_bandwidth.value)
    }else(
        ElMessage.error(req.data.msg)
    )
}

const setChannel=async(rid,channel)=>{
    try{
        SubmitLoading.value=true;
        const req=await axiosInstance.post('/api/setchannel',{aid:aid.value,rid:rid,channel:channel})
        if(req.data.success){
            ElMessage.success('设置信道成功！！')
            // 更新dataStore中对应radio的channel值
            const radioItem = radioItems.value.find(r => r.rid === rid && r.aid === aid.value);
            if (radioItem) {
                radioItem.channel = channel;
            }
        }else(
            ElMessage.error('设置信道失败！！',req.data.msg)
        )
    }catch(error){
        console.error('设置信道失败：',error)
        ElMessage.error('设置信道失败：',error)
    }finally{
        SubmitLoading.value=false
    }
}
const setBandwidth=async(rid,bandwidth)=>{
    try{
        SubmitLoading.value=true;
        const req=await axiosInstance.post('/api/setbandwidth',{aid:aid.value,rid:rid,bandwidth:bandwidth})
        if(req.data.success){
            ElMessage.success('设置带宽成功！！')
            // 更新dataStore中对应radio的channel_bandwidth值
            const radioItem = radioItems.value.find(r => r.rid === rid && r.aid === aid.value);
            if (radioItem) {
                radioItem.channel_bandwidth = bandwidth;
            }
        }else(
            ElMessage.error('设置带宽失败！！',req.data.msg)
        )
    }catch(error){
        console.error('设置带宽失败：',error)
        ElMessage.error('设置带宽失败：',error)
    }finally{
        SubmitLoading.value=false
    }
}

const setMaxpower=async(rid,power)=>{
    try{
        SubmitLoading.value=true;
        const req=await axiosInstance.post('/api/setMaxpower',{aid:aid.value,rid:rid,max_power:power})
        if(req.data.success){
            ElMessage.success('设置最大功率成功！！')
            // 更新dataStore中对应radio的max_power值
            const radioItem = radioItems.value.find(r => r.rid === rid && r.aid === aid.value);
            if (radioItem) {
                radioItem.max_power = power;
            }
        }else(
            ElMessage.error('设置最大功率失败！！',req.data.msg)
        )
        console.log('radioItems.value:',radioItems.value)
    }catch(error){
        console.error('设置最大功率失败：',error)
        ElMessage.error('设置最大功率失败：',error)
    }finally{
        SubmitLoading.value=false
}}
// 断开AP连接
const closeManageWifi = async () => {
    if (connectionStatus.value === 'disconnected') {
        ElMessage.warning('未连接到AP')
        return
    }
    
    isDisconnecting.value = true
    try {
        // 这里可以添加断开连接的逻辑
        connectionStatus.value = 'disconnected'
        terminalContent.value = ''
        ElMessage.success('已断开AP连接')
    } catch (error) {
        console.error('断开AP失败:', error)
        ElMessage.error('断开AP失败')
    } finally {
        isDisconnecting.value = false
    }
}

// 发送命令
const sendCommand = () => {
    if (!command.value.trim()) return
    
    if (connectionStatus.value !== 'connected') {
        ElMessage.warning('请先连接AP')
        return
    }
    
    // 在终端显示命令
    terminalContent.value += `<div class="command-line">$ ${command.value}</div>`
    
    // 通过Socket发送命令
    socket.value.emit('apcommand', { command: command.value })
    
    // 清空输入框
    command.value = ''
    
    // 自动滚动到底部
    nextTick(() => {
        if (terminalOutput.value) {
            terminalOutput.value.scrollTop = terminalOutput.value.scrollHeight
        }
    })
}
const setRadioManage=async()=>{
    try{
        SubmitLoading.value=true;
        const req=await axiosInstance.post('/api/setRadioManage',{radio_data:currentWifiItem.value})
        if(req.data.success){
            ElMessage.success('设置成功！！')
            // console.log('radioStateValues.value:',radioStateValues.value)
            // 更新dataStore中对应wifiItems的radio_bind值
            if (currentWifiItem.value) {
                currentWifiItem.value.forEach(wifi => {
                    const wifiItem = wifiStore.wifiItems.find(w => w.aid === wifi.aid && w.wid === wifi.wid);
                    if (wifiItem) {
                        wifiItem.radio_bind = [...wifi.radio_bind];
                    }
                });
            }

        }else(
            ElMessage.error('设置失败！！',req.data.msg)
        )
    }catch(error){
        console.error('设置失败：',error)
        ElMessage.error('设置失败：',error)
    }finally{
        SubmitLoading.value=false
        await wifiStore.radiodata(true);
        console.log('radioItems.value:',radioItems.value)
    }
}
onUnmounted(() => {
    if (socket.value) {
        socket.value.disconnect()
    }
})
</script>

<style scoped>
.terminal-output {
    background-color: #1e1e1e;
    color: #ffffff;
    padding: 15px;
    border-radius: 5px;
    height: 400px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.4;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.command-line {
    color: #4CAF50;
    font-weight: bold;
    margin: 5px 0;
}

.terminal-output::-webkit-scrollbar {
    width: 8px;
}

.terminal-output::-webkit-scrollbar-track {
    background: #2d2d2d;
}

.terminal-output::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 4px;
}

.terminal-output::-webkit-scrollbar-thumb:hover {
    background: #777;
}
</style>
