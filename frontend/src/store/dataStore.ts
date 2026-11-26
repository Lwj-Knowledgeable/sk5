import { defineStore } from 'pinia';
import { ref } from "vue";
import { axiosInstance } from '../store/messageaxios.js';
import { ElMessage } from 'element-plus';

interface L2TPTable{
    id:number;
    name:string;
    connect_to:string;
    user:string;
    password:string;
    status:boolean;
};

interface TableRow {
    id: number; // ID
    proxyType: string; // 代理类型
    address: string; // 代理ip
    port: number; // 端口
    user: string; // 账号
    pass: string; // 密码
    vmessId: string; // vmessID
    sslType: string; // ssl加密方式
    area: string; // 地区
    delay: number; // 延迟
    localAddr: string; // 内网绑定
    api: string; // 代理状态
    api_status: string;//api
};
interface ApiTable{
    id:number;
    user:string;
    pass:string;
    port:number;
    address:string;
    date:string;
};

interface WifiTable{
    aid:number;
    wid:number; 
    ssid:string;
    wifipassword:string;
    status:string;
    ssid_hide:string;
    user_isolation:string;
    radio_bind:string[];
    vlan:boolean;
};
interface RadioTable{
    aid:number;
    rid:number;
    type:string;
    state:string;
    channel_bandwidth:string;
    channel:string;
};
interface BalanceTable{
    id:number;
    mid:string;
    interface:string;
    status:boolean;
    disabled:boolean;
    up:number;
    down:number;
    type:string;
    balance:boolean;
    ppoe:{};
    dhcp:{};
    static_ip:{};
};
interface ApTable{
    aid:number;
    status:string;
};
interface ScriptTable{
    id:string;
    name:string;
    description:string;
    parentid:number;
    alter:string;
    paramIs:boolean;
};

export const useDataStore = defineStore('data', {
    state: () => ({
        items: [] as TableRow[],
        isUpdating: false,  // 用于控制上传中状态（页面可根据此状态添加灰色遮罩及禁用保存按钮）
		isHmpb: false,
		apiProxies:[] as ApiTable[]
    }),
    actions: {
        async fetchData() {
            const { data } = await axiosInstance.get('/api/data');
            this.items = data;			
        },
        async update() {
            // 开始更新时，设置 isUpdating 为 true，页面上可显示灰色遮罩和禁用保存按钮
            this.isUpdating = true;
            try {
                // 将当前数据发送到后端进行更新
                // 此处假设后端接口需要整个数据数组作为请求体
                console.log('dataStore更新',this.items)
                await axiosInstance.post('/api/update', { items: this.items });
                // 更新成功，提示保存成功
                ElMessage.success("保存成功");
            } catch (error) {
                console.error("更新数据失败：", error);
                // 更新失败，提示保存失败
                ElMessage.error("保存失败，请重试");
                // 可根据需要抛出错误
                throw error;
            } finally {
                // 不论成功或失败，都将 isUpdating 重置为 false
                this.isUpdating = false;
            }
        },
        async city_delay(ipdata:[]) {
            this.isUpdating = true;
            try {
                // 将当前数据发送到后端进行更新
                // 此处假设后端接口需要整个数据数组作为请求体
                // await axios.post('/api/city_delay');
                // 更新成功，提示保存成功
                // ElMessage.success("保存成功");
				this.items = ipdata;
            } catch (error) {
                console.error("更新数据失败：", error);
                // 更新失败，提示保存失败
                // ElMessage.error("保存失败，请重试");
                // 可根据需要抛出错误
                throw error;
            } finally {
                // 不论成功或失败，都将 isUpdating 重置为 false
                this.isUpdating = false;
            }
        },
        // 更新本地数据函数
        updateLocalData(list: { id: number, [key: string]: any }[]) {
            list.forEach(updateItem => {
                const index = this.items.findIndex(item => item.id === updateItem.id);
                if (index !== -1) {
                    // 更新数据，只更新有值的字段
                    this.items[index] = { ...this.items[index], ...updateItem };
                }
            });
        },
        setproxyApi(list:ApiTable[]){
            this.apiProxies=list
        }
    }
});

export const useWifiStore = defineStore('wifi', {
    state: () => ({
        wifiItems: ref<WifiTable[]>([]),
        radioItems: ref<RadioTable[]>([]),
        // 保存原始数据用于对比
        originalWifiItems: ref<WifiTable[]>([]),
        originalRadioItems: ref<RadioTable[]>([]),
        isLoading: ref<boolean>(false),
        apItems: ref<ApTable[]>([]),
        // 添加数据加载状态标记
        dataLoaded: ref<boolean>(false),
        lastLoadTime: ref<number>(0),
    }),
    actions: {
        async wifidata(forceRefresh = false) {
            // 如果数据已加载且不是强制刷新，则跳过
            if (this.dataLoaded && !forceRefresh) {
                return;
            }
            try {
                const response = await axiosInstance.get('/api/getAP');
                if (response.data.success) {
                    this.wifiItems = response.data.data;
                    // 保存原始数据的深拷贝
                    this.originalWifiItems = JSON.parse(JSON.stringify(response.data.data));
                }
            } catch (error) {
                console.error('获取 WiFi 信息失败:', error);
                ElMessage.error('获取 WiFi 信息失败');
            }
        },

        async radiodata(forceRefresh = false) {
            // 如果数据已加载且不是强制刷新，则跳过
            if (this.dataLoaded && !forceRefresh) {
                return;
            }
            try {
                const response = await axiosInstance.get('/api/getRadio');
                if (response.data.success) {
                    const data=response.data.data;

                    this.radioItems = data;
                    // 保存原始数据的深拷贝
                    this.originalRadioItems = JSON.parse(JSON.stringify(response.data.data));
                    this.radioItems.forEach(item=>{
                        this.apItems.push({aid:item.aid,status:'离线'})
                        this.refreshWifiStatus(item.aid);
                    })
                }
            } catch (error) {
                console.error('获取射频信息失败:', error);
                ElMessage.error('获取射频信息失败');    
            }
        },

        // 新增：初始化数据方法
        async initializeData(forceRefresh = false) {
            if (this.dataLoaded && !forceRefresh) {
                return;
            }
            this.isLoading = true;
            try {
                console.log('开始加载数据...')
                
                // 并行请求数据（更快）
                await Promise.all([
                    this.radiodata(forceRefresh),
                    this.wifidata(forceRefresh)
                ])
                
                this.dataLoaded = true;
                this.lastLoadTime = Date.now();
                console.log('数据加载完成:')
                console.log('radiodata:', this.radioItems)
                console.log('wifidata:', this.wifiItems)
                console.log('apdata:', this.apItems)
                
            } catch (error) {
                console.error('数据加载失败:', error)
            } finally {
                this.isLoading = false;
            }
        },

        // 新增：重置数据加载状态（当需要重新加载时调用）
        resetDataLoaded() {
            this.dataLoaded = false;
            this.lastLoadTime = 0;
        },

        // 检查数据是否发生变化
        hasWifiChanges(): boolean {
            return JSON.stringify(this.wifiItems) !== JSON.stringify(this.originalWifiItems);
        },

        hasRadioChanges(): boolean {
            return JSON.stringify(this.radioItems) !== JSON.stringify(this.originalRadioItems);
        },

        // 获取变化的 WiFi 数据
        getChangedWifiItems(aid?: number, wid?: number): Partial<WifiTable> | null {
            const currentItem = this.wifiItems.find(item => item.aid === aid && item.wid === wid);
            const originalItem = this.originalWifiItems.find(item => item.aid === aid && item.wid === wid);
            
            if (!currentItem) return null;
            if (!originalItem) {
                // 新增的项目，全部字段返回
                return { ...currentItem };
            }

            // 逐字段比较，只提取变化的字段
            const wifichange: Partial<WifiTable> = {
                aid: currentItem.aid,
                wid: currentItem.wid,
            };
            let hasChanges = false;

            if (currentItem.ssid !== originalItem.ssid) {
                wifichange.ssid = currentItem.ssid;
                hasChanges = true;
            }
            if (currentItem.wifipassword !== originalItem.wifipassword) {
                wifichange.wifipassword = currentItem.wifipassword;
                hasChanges = true;
            }
            if (currentItem.ssid_hide !== originalItem.ssid_hide) {
                wifichange.ssid_hide = currentItem.ssid_hide;
                hasChanges = true;
            }
            if (currentItem.user_isolation !== originalItem.user_isolation) {
                wifichange.user_isolation = currentItem.user_isolation;
                hasChanges = true;
            }
            if (currentItem.status !== originalItem.status) {
                wifichange.status = currentItem.status;
                hasChanges = true;
            }
            if (JSON.stringify(currentItem.radio_bind) !== JSON.stringify(originalItem.radio_bind)) {
                wifichange.radio_bind = currentItem.radio_bind;
                hasChanges = true;
            }

            console.log('检查变化:', {
                'currentItem:':currentItem,
                'originalItem:':originalItem,
                'hasChanges:':hasChanges,
                'wifichange:':wifichange
            });

            return hasChanges ? wifichange : null;
        },


        // 获取变化的射频数据
        // getChangedRadioItems(): RadioTable[] {
        //     return this.radioItems.filter((item, index) => {
        //         const original = this.originalRadioItems[index];
        //         if (!original) return true; // 新增的项目
                
        //         // 比较关键字段
        //         return null;
        //     });
        // },

        // 重置 WiFi 信息到原始状态
        resetWifiToOriginal() {
            this.wifiItems = JSON.parse(JSON.stringify(this.originalWifiItems));
            this.radioItems = JSON.parse(JSON.stringify(this.originalRadioItems));
        },
        // 主要方法：过滤变化的数据并发送到API
        async resetWifiInfo( aid: number | undefined,wid:number | undefined,wifi_data:WifiTable[] | undefined,action:string) {
            try {
                console.log('resetWifiInfo:', aid, wid, wifi_data,action);
                this.isLoading = true;
                if(wifi_data && wifi_data.length > 0){
                    console.log('批量设置WiFi信息:', wifi_data);
                    const response = await axiosInstance.post('/api/setAP', {'wifi_data':wifi_data,'action':action});
                    if (response.data.success) {
                        ElMessage.success('WiFi设置更新成功');
                        this.wifiItems.push(...wifi_data);
                        this.originalWifiItems=JSON.parse(JSON.stringify(this.wifiItems));
                    } else {
                        ElMessage.error(response.data.message || '更新失败');
                    }
                }else{
                    const changed = this.getChangedWifiItems(aid, wid);
                    // 检查是否有变化
                    if (!changed) {
                        ElMessage.info('没有检测到数据变化');
                        return;
                    }
                    console.log('单个WiFi项变化:', changed);
                    const response = await axiosInstance.post('/api/setAP', {'wifi_data':[changed],'action':action});
                    if (response.data.success) {
                        // 更新 wifiItems 中对应项的变化字段，保持其他字段不变
                           const wifiIndex = this.wifiItems.findIndex(item => item.aid === aid && item.wid === wid);
                           if (wifiIndex !== -1) {
                               Object.assign(this.wifiItems[wifiIndex], changed);
                           }
                           this.originalWifiItems=JSON.parse(JSON.stringify(this.wifiItems))
                           ElMessage.success('WiFi设置更新成功');
                       } else {
                           ElMessage.error(response.data.message || '更新失败');
                       }
                }
                

                
            } catch (error) {
                console.error('更新WiFi信息失败:', error);
                ElMessage.error('更新失败，请重试');
            } finally {
                this.isLoading = false;
            }
        },
        async refreshWifiStatus(aid:number){
            const response = await axiosInstance.post('/api/getAPstatus', {aid:aid})
            if(response.data.success){
                this.apItems.filter(item=>item.aid==aid)[0].status=response.data.msg;
                ElMessage.success('更新成功');
            }else{
                ElMessage.error('更新失败');
            }
        },
        // async setRadioManage(radio_data:RadioTable[]){
        //     const response = await axiosInstance.post('/api/setRadioManage', {radio_data:radio_data})
        //     if(response.data.success){
        //         ElMessage.success('设置成功');
        //     }else{
        //         ElMessage.error('设置失败');
        //     }
        // }
        async batchDelWifi(wifi_list:number[],aid:number){
            this.isLoading = true;
            const response = await axiosInstance.post('/api/delwifi', {wifi_list:wifi_list,aid:aid})
            if(response.data.success){
                this.wifiItems = this.wifiItems.filter(item => !wifi_list.includes(item.wid as number) && item.aid==aid);
                console.log('this.wifiItems:',this.wifiItems);
                this.originalWifiItems = JSON.parse(JSON.stringify(this.wifiItems));
                ElMessage.success('删除成功');
            }else{
                if(response.data.exit_wifi){
                    this.wifiItems = this.wifiItems.filter(item => response.data.exit_wifi.includes(item.wid) && item.aid==aid);
                    this.originalWifiItems = JSON.parse(JSON.stringify(this.wifiItems));
                }
                ElMessage.error(response.data.msg);

            }
            this.isLoading = false;
        }
    },
    
    // async getApdata() {
    //     const response = await axios.get('/api/getApcount');
    //     if (response.data.success) {
    //         this.apItems = response.data.data;
    //     }else{
    //         ElMessage.error(response.data.message);
    //     }
    // }

});


export const useBalanceStore = defineStore('balance', {
    state: () => ({
        balanceItems: ref<BalanceTable[]>([]),
    }),
    actions: {
        async balanceData(){
            const response = await axiosInstance.get('/api/balance_port');
    if (response.data.success) {
        this.balanceItems = response.data.data;
    } else {
        ElMessage.error(response.data.msg);
    }
        }
    }
});

export const useScriptStore = defineStore('script', {
    state: () => ({
        scriptItems: ref<ScriptTable[]>([]),
    }),
    actions: {
        async getScript(){
            const response = await axiosInstance.get('/api/getScript');
            if(response.data.success){
                this.scriptItems = response.data.data;
                console.log('scriptItems:',this.scriptItems)
                ElMessage.success('获取脚本成功');
            }else{
                ElMessage.error(response.data.msg);
            }
        },
        async runScript(id:string,param:any,isparam:boolean=false){

            const response = await axiosInstance.post('/api/runScript', {id:id,param:param,isparam:isparam});
            if(response.data.success){
                ElMessage.success('执行脚本成功');
            }else{
                ElMessage.error(response.data.msg);
            }
        },
        async uploadScript(file: File, opts: { importOnRouter?: boolean; dstName?: string } = {}){
            const form = new FormData();
            form.append('file', file);
            if (opts.dstName) form.append('dst', opts.dstName);
            if (typeof opts.importOnRouter !== 'undefined') form.append('import', String(!!opts.importOnRouter));
            const res = await axiosInstance.post('/api/upload_script', form, { headers: { 'Content-Type': 'multipart/form-data' } });
            if(res.data.success){
                ElMessage.success('已上传并推送到路由器');
            }else{
                ElMessage.error(res.data.msg || '上传/推送失败');
            }
        }
    }
});

export const L2TPStore = defineStore('l2tp', {
    state: () => ({
        l2tpItems: ref<L2TPTable[]>([]),
    }),
    actions: {
        async getL2TP(){
            const response = await axiosInstance.get('/api/l2tp');
            if (response.data.success) {
                this.l2tpItems = response.data.data;
            }else{
                ElMessage.error(response.data.msg);
            }
        },

        async setL2TP(editL2tp:L2TPTable[]){
            const response = await axiosInstance.post('/api/set_l2tp', editL2tp);
            return response.data;
        },
        async setL2TPStatus(row:L2TPTable){
            const response = await axiosInstance.post('/api/set_l2tp_status', row);
            if(response.data.success){
                this.l2tpItems.forEach(item => {
                    if (item.id === row.id) {
                        item.status = !item.status;
                    }
                });
                ElMessage.success('设置成功');
            }else{
                ElMessage.error(response.data.msg);
            }
        }
    }
});