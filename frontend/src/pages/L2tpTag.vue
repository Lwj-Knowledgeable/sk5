<template>
    <div style="margin-bottom: 10px;margin-left: 10px;">  
        <el-button type="primary" @click="handleEdit">选择编辑</el-button>
        <el-button type="primary" @click="handleRestore">还原L2TP配置</el-button>
        
    </div>
    <el-table 
      :data="paginatedData" border 
      style="width:100%;" 
      row-key="id"
      @selection-change="handleSelectionChange"
      ref="inputTableRef"
      >
        <el-table-column 
          type="selection" 
          width="50px" 
          align="left"
          reserve-selection
          
        ></el-table-column>
        <el-table-column label="线路" prop="id" width="60" align="center">
        </el-table-column>
        <el-table-column prop="name" label="名称" width="100" align="center"/>
        <el-table-column prop="connect_to" label="连接" width="200"/>
        <el-table-column prop="user" label="用户名" width="300"/>
        <el-table-column prop="password" label="密码" width="300"/>
        <el-table-column prop="running" label="运行状态" width="100" align="center">
          <template #default="scope">
          <el-tag :type="scope.row.running ? 'success' : 'danger'">{{ scope.row.running ? '连接中' : '离线' }}</el-tag>
         </template>
        </el-table-column>
        <el-table-column prop="rx" label="上行流量" width="200">
          <template #default="scope">
            <span>{{ formatBps(trafficMap.get(scope.row.name)?.rx) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="tx" label="下行流量" width="200">
          <template #default="scope"> 
            <span>{{ formatBps(trafficMap.get(scope.row.name)?.tx) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.status"
              @change="handleStatusChange(scope.row)"
              :active-value="true"
              :inactive-value="false"
            />
          </template>
        </el-table-column>
    </el-table>    
    <el-pagination
        background
        layout="sizes, prev, pager, next, total"
        :total="l2tp_data.length"
        :page-size="pageSize"
        :current-page="page"
        :page-sizes="pageSizes"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; text-align: right;"
    />

    <el-dialog v-model="dialogVisible" title="添加L2TP" width="50%" >
      <div>
        <el-row>
          <el-input
            v-model="manualInputIds"
            placeholder="请输入ID，多个ID用逗号分隔,1-5表示添加id为1到5的路线"
            style="margin-bottom: 10px;width: 60%;"  
          >
          </el-input>
          <el-button @click="addL2TPIds('edit')" style="color: #409EFF;">添加</el-button>
          <el-button @click="addL2TPIds('delete')" style="color: #409EFF;margin-left: 0px;">清除</el-button>
        </el-row>
        <div style="margin-top: 10px;height: 170px;border: 1px solid #ccc;">
          <span style="width: 100%;">已选择ID：</span>
          <span v-for="i in selectedRows" :key="i.id" style="margin-right: 8px;font-size: 20px;color: blue;;">{{ i.id }}</span>
        </div>
        <el-row style="margin-bottom: 10px;">
        <p style="padding: 2px 2px;margin: 4px 4px;">当前选中 <strong style="font-size: 20px;">{{ selectedRows.length }}</strong> 项</p>
        <p style="padding: 2px 2px;margin: 4px 100px;">当前输入 <strong style="font-size: 20px;">{{userInput.split('\n').length}}</strong> 行</p>
        </el-row>
        <el-row style="padding: 10px 6px;"><el-text style="font-size: 14px;color:darkmagenta;">L2TP信息格式为：1.1.1.1|账号|密码|日期</el-text></el-row>
        <el-form :model="{ userInput }">
          <el-form-item label="输入L2TP信息">
          <el-input
            type="textarea"
            :autosize="{minRows: 3, maxRows: 10}"
            @input="handleInputChange"
            v-model="userInput"
            placeholder="请输入代理信息，每行一个代理"
            style="max-height: 50vh;height: 20vh;"
          ></el-input>
        </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addL2TPData">提交</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { ref, onMounted,computed,onUnmounted } from 'vue';
import { axiosInstance } from '../store/messageaxios';
import { ElMessage,ElMessageBox } from 'element-plus';
import { L2TPStore } from '../store/dataStore';
import { useSocketioStore } from '../store/socketioStore';
const socketioStore = useSocketioStore();
const l2tpTrafficList = computed(() => socketioStore.l2tpTrafficList);
const l2tpStore = L2TPStore();
const l2tp_data = computed(() => l2tpStore.l2tpItems);
const page=ref(1);
const pageSize=ref(20); 
const pageSizes=[10, 20, 50, 100];
const total=ref(0);
const manualInputIds = ref('');
// 根据当前页和每页数量对数据进行分页处理
const paginatedData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  const end = start + pageSize.value
  return l2tp_data.value.slice(start, end)
})
const handleSizeChange = (val) => {
  pageSize.value = val
  page.value = 1
}
const handleCurrentChange = (val) => {
  page.value = val
}

const selectedRows = ref([]);
const userInput = ref('');
const inputLines = ref(0);
const dialogVisible = ref(false);
const inputTableRef = ref(null);
const handleEdit = () => {
  console.log('handleEdit');
  dialogVisible.value = true;
}
const handleSelectionChange = (rows) => {
  // console.log('handleSelectionChange',rows,);
  selectedRows.value = [...rows];
}
const addL2TPIds = (type) => {
  let ids=[];
  if (type == 'delete'){
    selectedRows.value=[];
    inputTableRef.value.clearSelection();
    console.log('del:','selectedRows',selectedRows.value);
  }
  else if(type == 'edit'){
    console.log('addL2TPIds-edit:','manualInputIds',manualInputIds.value);
    const regex=/(^([1-9]\d{0,}[，,-])+[1-9]\d{0,}$)|^[1-9]\d{0,}$/;
    console.log('regex',regex.test(manualInputIds.value));
    if (!regex.test(manualInputIds.value) ) {
      ElMessage.error('输入的格式不正确,请输入正确格式');
      return;
    }
    ids = manualInputIds.value.split(/[,，]/);
    console.log('split-ids',ids,ids.length);
    ids.forEach(item => {
      if (item.includes('-')) {
        console.log('item',item);
        const [start,end] = item.split('-');
        console.log('filter-ids',ids,ids.length);
        if(parseInt(start) > parseInt(end)) {
          for (let i = parseInt(start); i >= parseInt(end); i--) {
            ids.push(i.toString());
          }
          console.log('start > end',ids);
        }else{
          for (let i = parseInt(start); i <= parseInt(end); i++) {
          ids.push(i.toString());
        }}
      }
    });
    console.log('ids',ids,ids.length);
    const inputdata = l2tp_data.value.filter(item => ids.includes(item.id.toString()));
    console.log('inputdata',inputdata,inputdata.length);
    selectedRows.value = [...new Set([...selectedRows.value, ...inputdata])];
    console.log('first-selectedRows',selectedRows.value,selectedRows.value.length);
    selectedRows.value.forEach(item => {
      inputTableRef.value.toggleRowSelection(item,true);
    });
    console.log('selectedRows',selectedRows.value,selectedRows.value.length);
  }
  manualInputIds.value = '';
}
const addL2TPData = async () => {
  console.log('addL2TPData',selectedRows.value);
  // 验证输入的代理信息
  const inputdata = userInput.value.split('\n');
  if (inputdata.length !== selectedRows.value.length) {
    ElMessage.error('输入的代理信息与选中的路线数量不一致,请输入相同数目代理');
    return;
  }
  const data = inputdata.map(item => {
    const splitdata= item.split('|');
    if (splitdata.length !== 4) {
      ElMessage.error('输入的代理信息格式不正确,请输入正确格式');
      return;
    }
    if (!isValidIPv4(splitdata[0])) {
      ElMessage.error('输入的IP地址格式不正确,请输入正确格式');
      return;
    }

    const [connect_to, user, password, date] = splitdata;
    return { connect_to, user, password, date };
  });
  selectedRows.value.forEach((item,index) => {
    data.forEach((dataItem,dataIndex) => {
      if (dataIndex === index) {
        dataItem.name = item.name;
        dataItem.status = item.status;
        dataItem.id = item.id;
      }
    });
  });  
  console.log('data',data);
  ElMessageBox.confirm('确定添加吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    console.log('确定添加');
    const result=await l2tpStore.setL2TP(data);
    if (result.success) {
      ElMessage.success('添加成功');
    } else {
      ElMessage.error(result.msg);
      return;
    }
    dialogVisible.value = false;
    await l2tpStore.getL2TP();
    selectedRows.value = [];
    userInput.value = '';
    manualInputIds.value = '';
    inputTableRef.value.clearSelection();
  }).catch(() => {
    console.log('取消添加');
  });
}
const isValidIPv4 = (ip) => {
    const regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return regex.test(ip);
};
const handleStatusChange = async (row) => {
  console.log('handleStatusChange',row);
  await l2tpStore.setL2TPStatus(row);
  await l2tpStore.getL2TP();
} 
const restore_id=computed(() => selectedRows.value.map(item => item.id));
const handleRestore = async () => {
  console.log('handleRestore',selectedRows.value,restore_id.value);
  if (restore_id.value.length === 0) {
    ElMessage.error('请选择要还原的路线');
    return;
  }
  ElMessageBox.confirm('确定还原路线,'+restore_id.value.join(',')+'吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    console.log('确定还原');
    const data = selectedRows.value.map(item => 
      {
        return {
          id: item.id,
          name: item.name,
          connect_to: '1.1.1.1',
          user: '888888',
          password:'',
        }
      }
    )
    console.log('data',data);
    await l2tpStore.setL2TP(data);
    await l2tpStore.getL2TP();
  }).catch(() => {
    console.log('取消还原');
  });
}
const formatBps = (bps) => {
  const v = Number(bps);
  if (!Number.isFinite(v) || v <= 0) return '0 bps';
  const units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps'];
  const i = Math.min(Math.floor(Math.log(v) / Math.log(1000)), units.length - 1);
  return `${(v / Math.pow(1000, i)).toFixed(i === 0 ? 0 : 2)} ${units[i]}`;
};
const trafficMap = computed(() => {
  const m = new Map();
  for (const item of l2tpTrafficList.value || []) {
    m.set(item.name, item);
  }
  return m;
});
onMounted(async () => {
   await l2tpStore.getL2TP();
})
</script>
<style scoped>
  /* 设置 el-table 多选框边框颜色和粗细 */
  ::v-deep .el-checkbox__inner {
  border: 1px solid #d4d0d0 !important;   /* 2px粗黑色边框 */
  border-radius: 4px;                  /* 可选：圆角 */
}
    /* 放大 el-table 的多选框（checkbox） */
  ::v-deep .el-table__header .el-checkbox,
  ::v-deep .el-table__body .el-checkbox {
    transform: scale(1.5);   /* 2倍放大，可根据需要调整 */
    margin-right: 8px;
    /* 让checkbox居中对齐 */
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>