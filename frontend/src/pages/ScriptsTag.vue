<template>
    <el-button :type="aliwcStatus?'warning':'success'" @click="setALIWC_d_or_p(!aliwcStatus)" :loading="aliwcLoading">{{aliwcStatus?'关闭支付宝微信直连':'开启支付宝微信直连'}}</el-button>
    <div style="margin-top: 10px;width: 80%;margin-left: 10%;">
        
        <el-table 
        :data="scriptStore.scriptItems" 
        v-loading="isLoading" 
        style="width: 100%;"
        :row-class-name="getRowClassName"
        :span-method="spanMethod"
        border
    >
        <el-table-column prop="parentid" label="ID" width="60" class-name="bold-column"/>
        <el-table-column prop="name" label="脚本名称" width="300" class-name="bold-column" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <!-- <el-table-column prop="alter" label="类型" width="100" /> -->
        <el-table-column prop="paramIs" label="参数" width="380">
            <template #default="scope">
                <div v-if="scope.row.paramIs">
                    <!-- 参数输入区域 -->
                    <div style="margin-bottom: 8px;">
                        <div 
                            v-for="(param, index) in scope.row.parameters" 
                            :key="index" 
                            style="margin-bottom: 8px; display: flex; align-items: center; gap: 8px;"
                        >
                            <el-input 
                                v-model="param.value" 
                                :placeholder="`参数值 ${index + 1}`"
                                size="small"
                                style="max-width: 200px;"
                                autosize
                                type="textarea"
                            />
                            <el-tooltip content="需设置脚本参数,不懂请咨询技术">
                                <el-icon ><warning/></el-icon>
                            </el-tooltip>                     
                            
                        </div>
                    </div>
                    
                    <!-- 添加参数按钮 -->

                </div>
                <span v-else style="color: #999;"></span>
            </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
            <template #default="scope">
                <el-button 
                    type="primary" 
                    @click="handleRun(scope.row)"
                >
                    执行
                </el-button>
                <!-- <el-button type="danger" @click="handleDelete(scope.row)">删除</el-button> -->
            </template>
        </el-table-column>
    </el-table></div>
    
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import { useScriptStore } from '../store/dataStore';
import { ElMessage } from 'element-plus';
import { CirclePlus,Warning } from '@element-plus/icons-vue';
import { axiosInstance } from '../store/messageaxios';

const scriptStore = useScriptStore();
const isLoading = ref(false);

const rowspanArr = ref([]);

const buildRowspan = () => {
    const data = scriptStore.scriptItems || [];
    const arr = new Array(data.length).fill(1);
    let i = 0;
    while (i < data.length) {
        const currentParent = data[i]?.parentid;
        let span = 1;
        let j = i + 1;
        while (j < data.length && data[j]?.parentid === currentParent) {
            span++;
            j++;
        }
        // i 是该连续块首行
        arr[i] = span;       // 首行显示合并
        for (let k = i + 1; k < j; k++) {
            arr[k] = 0;      // 其余行隐藏该列
        }
        i = j;               // 跳到下一个块
    }
    rowspanArr.value = arr;
};

// 初始化参数数组
const initializeParameters = () => {
    if (scriptStore.scriptItems) {
        scriptStore.scriptItems.forEach(item => {
            if (item.paramIs && !item.parameters) {
                item.parameters = [{ value: '' }];
            }
        });
    }
};

// 数据变化时重建（含首次）
watch(() => scriptStore.scriptItems, () => {
    buildRowspan();
    initializeParameters();
}, { deep: true, immediate: true });

// 合并单元格方法
const spanMethod = ({ rowIndex, columnIndex }) => {
    if (columnIndex === 0) {
        return {
            rowspan: rowspanArr.value[rowIndex] ?? 1,
            colspan: 1
        };
    }
    return { rowspan: 1, colspan: 1 };
};

// 添加行样式类名函数
const getRowClassName = ({ row }) => {
    if (row.alter === 'System') {
        return 'system-row';
    }
    return '';
};

// 上传脚本：选择文件 -> 上传后端 -> 推送到 RouterOS
const handleUpload = async () => {
    try {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.rsc,.txt,.script,.sh,.py';
        input.onchange = async () => {
            const file = input.files && input.files[0];
            if (!file) return;
            await scriptStore.uploadScript(file, { importOnRouter: true });
        };
        input.click();
    } catch (e) {
        ElMessage.error('上传失败');
    }
};

// 添加参数（只允许添加一个参数输入框）
const addParameter = (row) => {
    if (!row.parameters) {
        row.parameters =[];
    }
    // 只允许添加一个参数输入框
    if (row.parameters.length === 0) {
        row.parameters.push({ value: '' });
    }
};

// 删除参数
const removeParameter = (row, index) => {
    row.parameters.splice(index, 1);
};
const aliwcLoading=ref(false)
const aliwcStatus=ref(false)
const getaliwcStatus=async () => {
    const res=await axiosInstance.get('/api/get_ALIWC_status')
    if(res.data.success){
        if(res.data.data=='d'){
            aliwcStatus.value = true;
        }else{
            aliwcStatus.value = false;
        }
    }
}
const setALIWC_d_or_p = async (status) => {
    const aliwc=ref('')
    aliwcLoading.value = true;
    if(status){
        aliwc.value='d';
    }else{
        aliwc.value='p'
    }
    const req=await axiosInstance.post('/api/set_ALIWC_d_or_p',{status:aliwc.value})
    if(req.data.success){
        ElMessage.success(req.data.msg)
        await getaliwcStatus()
    }else{
        ElMessage.error(req.data.msg)
    }
    aliwcLoading.value = false;
}
onMounted(async () => {
    isLoading.value = true;
    await scriptStore.getScript();
    // 在获取数据后初始化参数
    initializeParameters();
    await getaliwcStatus();
    isLoading.value = false;
});

const handleRun = (row) => {
    // 如果该行需要参数，检查参数是否为空
    if (row.paramIs) {
        // 检查是否有参数输入框
        if (!row.parameters || row.parameters.length === 0) {
            ElMessage.warning('请先添加参数');
            return;
        }
        
        // 检查参数值是否为空
        const emptyParams = row.parameters.filter(p => !p.value || p.value.trim() === '');
        if (emptyParams.length > 0) {
            ElMessage.warning('请填写所有参数值');
            return;
        }
        
        // 将参数转换为执行格式
        const paramValues = row.parameters.map(p => p.value.trim());
        scriptStore.runScript(row.id, paramValues, true);
    } else {
        scriptStore.runScript(row.id, 'Null', false);
    }
};
</script>

<style scoped>
/* 为system类型的行添加淡粉色背景 */
:deep(.system-row) {
    background-color: #e0f9e0 !important;
}

/* 可选：为system类型的行添加悬停效果 */
:deep(.system-row:hover) {
    background-color: #f8bbd9 !important;
}

/* 为指定列添加加粗样式 */
:deep(.bold-column .cell) {
    font-weight: bold;
}
</style>