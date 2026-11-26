<template>
  <div>
    <div class="listButs">

      <el-button type="primary" round  @click="openDialog" style="background-color: blue;">选中编辑</el-button>
<!--      <el-button type="primary" round>地区检测</el-button>-->
      <el-button type="primary" round @click="delayClick" :loading="delayLoading">延迟检测</el-button>
	  <el-button type="primary" round @click="locationClick" :loading="locationLoading">地区检测</el-button>
      <span class="butsm"/>
      <el-button type="primary" round @click="hmpbClick" :class="{'active-btn':hmpbbtn,'unactive-btn':!hmpbbtn}" :loading="hmpbloading">{{hmpbtext}}</el-button>
	  <!-- <el-button type="primary" round  @click="qhbdMessage" :class="{'active-btn':!qhbdbtn,'unactive-btn':qhbdbtn}" :loading="qhbdLoading">{{qhbdtext}}</el-button> -->
	  <el-button type="primary" round @click="openLocalSwitchDialog" >切换本地</el-button>
	  <el-button type="primary" round @click="openProxySwitchDialog" >切换代理</el-button>
    <el-button type="primary" round  @click="changeMac" :loading="macLoading">修改MAC</el-button>
    <el-button type="primary" round @click="apiEnabled = !apiEnabled">API开关</el-button>
    <el-button type="warning" round @click="clearSelectedProxyData">清除代理数据</el-button>
      <span class="butsm"/>
	  <el-button
	      v-if="editingMode"
	      type="success"
	      round
	      @click="saveData"
	  >
	    保存
	  </el-button>
      <el-button type="success" round @click="copyData">复制数据</el-button>

    <div style="float:right;width: 140px;">
    <!-- <el-switch v-model="showImport" style="position: absolute;"/> -->
    <el-row style="display: flex; align-items: center;">
        <el-button
          :type="untnNetExists ? 'success' : 'danger'"
          round
          @click="checkUntnNet"
          :loading="untnNetLoading"
          :icon="Refresh"
          style="float: left;"
        >
          {{ untnNetExists ? '已授权' : '未授权' }}
        </el-button>
		    <span :class="untnNetExists ? 'untn-net-green' : 'untn-net-red'" style="font-size: 16px;">●</span>
		</el-row>
    <!-- <el-button type="danger" :icon="Refresh" @click="IsRestartServer" size="small" :loading="restartserverLoading" style="float:right;margin-top: 40px;">重启服务</el-button> -->
    </div>
    <el-button v-if="showImport" :icon="FolderOpened" size="small" circle  style="float:right;margin-right: 10px;margin-left:5px" @click="handleRestoreClick" />
    <el-button v-if="showImport" type="primary" round style="float:right;" @click="resetyamlfile" :disabled="!resetbutton" size="small">恢复配置</el-button>

    <input ref="fileInput" type="file" accept=".yaml" style="display: none;" @change="handleFileChange" />
    <!-- 密码弹窗 -->
    <el-dialog v-model="passwordDialogVisible" title="请输入密码" width="300px" :close-on-click-modal="false">
      <el-input v-model="restorePassword" type="password" placeholder="请输入密码" @keyup.enter="confirmRestorePassword" />
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRestorePassword">确定</el-button>
      </template>
    </el-dialog>
	
    <el-row style="padding-bottom: 5px;" :gutter="10">
		  <el-col :span="3">上传：{{formatSize(trafficData_up)}} /s</el-col>
		  <el-col :span="3">下载：{{formatSize(trafficData_down)}} /s</el-col>
		  <el-col :span="3">上传总量：{{formatSize(total_up)}}</el-col>
		  <el-col :span="5">下载总量：{{formatSize(total_down)}}</el-col>
	  </el-row>
    </div>
    <el-table
        :data="paginatedData"
		    :row-style="tableRowClassName"
        :cell-style="{ padding: '1px 1px' }"
        border
        style="width: 100%"
        height="100%"
        row-key="id"
        @selection-change="handleSelectionChange"
        ref="tableRef"
    >
      <!-- 多选列 -->
      <el-table-column 
          type="selection" 
          width="50px" 
          align="left"
          :selectable="row => row.id !== undefined"
          reserve-selection
      ></el-table-column>
      <!-- 示例：ID 列 -->
      <el-table-column prop="id" width="54" algin="center" label="线路"/>

      <!-- 代理类型 -->
      <el-table-column prop="proxyType" width="80" algin="center" label="代理类型">
        <template #default="{ row }">
          <template v-if="editingMode">
            <el-select v-model="row.proxyType" size="small" placeholder="请选择代理类型">
              <el-option label="socks5" value="socks5"></el-option>
              <el-option label="http" value="http"></el-option>
              <el-option label="ss" value="ss"></el-option>
              <el-option label="vmess" value="vmess"></el-option>
            </el-select>
          </template>
          <template v-else>
            {{ row.proxyType }}
          </template>
        </template>
      </el-table-column>

      <!-- 代理IP -->
      <el-table-column prop="address" width="200" label="代理IP">
        <template #default="{ row }">
          <template v-if="editingMode">
            <el-form :model="row" :rules="validationRules" ref="form">
              <el-form-item prop="address">
                <el-input v-model="row.address" size="small" />
              </el-form-item>
            </el-form>
          </template>
          <template v-else>
            {{ row.address }}
          </template>
        </template>
      </el-table-column>

      <!-- 端口 -->
      <el-table-column prop="port" width="70" label="端口">
        <template #default="{ row }">
          <template v-if="editingMode">
            <el-input v-model="row.port" size="small" />
          </template>
          <template v-else>
            {{ row.port }}
          </template>
        </template>
      </el-table-column>

      <!-- 账号 -->
      <el-table-column prop="user" min-width="80" label="账号">
        <template #default="{ row }">
          <template v-if="editingMode">
            <el-input v-model="row.user" size="small" />
          </template>
          <template v-else>
            {{ row.user }}
          </template>
        </template>
      </el-table-column>

      <!-- 密码 -->
      <el-table-column prop="pass" min-width="80" label="密码">
        <template #default="{ row }">
          <template v-if="editingMode">
            <el-input v-model="row.pass" size="small" />
          </template>
          <template v-else>
            {{ row.pass }}
          </template>
        </template>
      </el-table-column>

      <!-- vmessID -->
      <el-table-column prop="vmessId" width="90" label="vmessID">
        <template #default="{ row }">
          <template v-if="editingMode">
            <el-input v-model="row.vmessId" size="small" />
          </template>
          <template v-else>
            {{ row.vmessId }}
          </template>
        </template>
      </el-table-column>

      <!-- SSL加密方式 -->
      <el-table-column prop="sslType" width="80" label="SSL加密">
        <template #default="{ row }">
          <template v-if="editingMode">
            <el-input v-model="row.sslType" size="small" />
          </template>
          <template v-else>
            {{ row.sslType }}
          </template>
        </template>
      </el-table-column>

      <!-- 地区 -->
      <el-table-column prop="area" min-width="190" label="地区"/>

      <!-- 延迟 -->
	  <el-table-column prop="delay" min-width="50" label="延迟">
		  <template #default="{row}">
			<span v-if="row.delay === 0" class="red-circle">●</span>
			<span v-else class="green-circle">●</span>
			{{row.delay}}
		  </template>
	  </el-table-column>

      <!-- 内网绑定 -->
      <el-table-column prop="localAddr" width="120" label="内网绑定">
        <template #default="{ row }">
          <template v-if="editingMode">
            <el-input v-model="row.localAddr" size="small" />
          </template>
          <template v-else>
            {{ row.localAddr }}
          </template>
        </template>
      </el-table-column>

      <!-- API -->
      <el-table-column prop="api" label="代理状态" width="80" align="center">
        <template #default="{ row }">
          <span v-if="row.api===false" class="status_green">代理</span>
          <span  v-if="row.api===true" class="status_red">本地</span>
          <span v-if="row.api===''" class="status_yellow">线路配置不存在</span>
        </template>
      </el-table-column>
      <!-- <el-table-column label="API" width="70" align="center">
      <template #default="{ row }">
        <el-switch v-model="row.api_status" :disabled="!apiEnabled" size="small" @change="onApiSwitchChange(row)"/>
        <el-tooltip placement="top" v-if="row.api_status">
          <template #content> {{getApiProxyInfo(row)}} </template>
          <el-icon><InfoFilled /></el-icon>
        </el-tooltip>
      </template>
      </el-table-column> -->
    </el-table>
    <el-pagination
        background
        layout="sizes, prev, pager, next, total"
        :total="dataStore.items.length"
        :page-size="pageSize"
        :current-page="currentPage"
        :page-sizes="pageSizes"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; text-align: right;"
    />
  </div>

  <!-- 弹窗部分 -->
  <el-dialog
    v-model="dialogVisible"
    title="选中编辑"
    :before-close="handleClose"
    width="50%"
    top="10px"
  >
  <div style="height: 180px;overflow-y: auto;overflow-x: hidden;">
    <!-- <el-checkbox
      :indeterminate="EditisIndeterminate"
      v-model="EditcheckAll"
      @change="EdithandleCheckAllChange"
      style="margin-bottom: 10px;"
    >全选</el-checkbox> -->
    <el-row>
    <el-input
      v-model="manualInputIds"
      placeholder="请输入ID，多个ID用逗号分隔,1-5表示添加id为1到5的路线"
      style="margin-bottom: 10px;width: 70%;"
      @keyup.enter="addManualIds"
    >
    </el-input>
    <el-button @click="addManualIds('add')" style="color: #409EFF;">添加</el-button>
    <el-button @click="addManualIds('delete')" style="color: #409EFF;margin-left: 0px;">清除</el-button>
    </el-row>
    <div style="margin: 8px 0;">
      <span>已选ID：</span>
      <span v-for="item in selectedRows" :key="item" style="margin-right: 8px; color: #409EFF; font-weight: bold;">
        {{ item }}
      </span>
    </div>
    <!-- <el-checkbox-group v-model="selectedRows" @change="EdithandleCheckedChange">
      <el-row :gutter="10">
        <el-col
          v-for="id in editAllIds"
          :key="id"
          :span="1.2"
        >
          <el-checkbox :label="id">{{ id }}</el-checkbox>
        </el-col>
      </el-row>
    </el-checkbox-group> -->
  </div>
  <el-divider style="width: 90%;"/>
    <div>
      <el-row style="margin-bottom: 10px;">
        <p style="padding: 2px 2px;margin: 4px 4px;">当前选中 <strong style="font-size: 20px;">{{ selectedRows.length }}</strong> 项</p>
        <p style="padding: 2px 2px;margin: 4px 100px;">当前输入 <strong style="font-size: 20px;">{{ inputLines }}</strong> 行</p>
      </el-row>
      
      <el-form :model="{ userInput }">
		<el-radio-group v-model="apivalue" style="padding:2px;margin-bottom: 10px;">
		      <el-radio label="socks5" border>socks5</el-radio>
		      <el-radio label="http" border>http</el-radio>
		      <el-radio label="ss" border>ss</el-radio>
			    <el-radio label="vmess" border>vmess</el-radio>
		</el-radio-group>
		<el-row style="padding: 2px 4px;"><el-text style="font-size: 14px;color:darkmagenta;">sk5/http代理格式为：1.1.1.1|端口|账号|密码</el-text></el-row>
		<el-row style="padding: 2px 4px;"><el-text style="font-size: 14px;color: darkmagenta;">ss代理格式为：1.1.1.1|端口|加密方式|密码</el-text></el-row>
		<el-row style="padding: 2px 4px 4px 4px;"><el-text style="font-size: 14px;color: darkmagenta;margin-bottom: 10px;">vm代理格式为：1.1.1.1|端口|uuid|alterId|加密方式</el-text></el-row>
        
        <el-form-item label="输入内容">
          <el-input
            type="textarea"
            :autosize="{minRows: 3, maxRows: 10}"
            @input="handleInputChange"
            v-model="userInput"
            placeholder="请输入代理信息，每行一个代理"
            style="max-height: 30vh;"
          ></el-input>
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitDialog">提交</el-button>
    </template>
  </el-dialog>

  <div>
    <!-- 切换本地对话框 -->
    <el-dialog
  v-model="dialogVisible1"
  :title="dialogMode === 'local' ? '选择要切换本地的ID' : '选择要切换代理的ID'"
  width="60%"
  :style="{ height: '70%' }"
>
  <div style="height: 280px;overflow-y: auto;overflow-x: hidden;">
    <el-checkbox
      :indeterminate="isIndeterminate"
      v-model="checkAll"
      @change="handleCheckAllChange"
      style="margin-bottom: 10px;"
    >全选</el-checkbox>
    <el-row>
      <el-input
        v-model="manualInputIds"
        placeholder="请输入ID，多个ID用逗号分隔"
        style="margin-bottom: 10px;width: 70%;"
        @keyup.enter="addManualIds"
        
      >
      </el-input>
  
      <el-button @click="addManualIds('edit')" style="color: #409EFF;">添加</el-button>
      <el-button @click="addManualIds('delete')" style="color: #409EFF;margin-left:0px;">清除</el-button>
    </el-row>
    <el-checkbox-group v-model="selectedIds" @change="handleCheckedChange">
      <!-- <el-row :gutter="10"> -->
        <!-- <el-col
          v-for="id in LocalProxyListIds"
          :key="id"
          :span="1.2"
        > -->
          <el-checkbox :label="id" v-for="id in LocalProxyListIds" :value="id">{{ id }}</el-checkbox>
        <!-- </el-col>
      </el-row> -->
    </el-checkbox-group>
  </div>
  <div style="margin-top: 10px;height: 70px;border: 1px solid #ccc;">
    <span>已选择ID：</span>
    <span v-for="id in selectedIds" :key="id" style="margin-right: 8px;">{{ id }}</span>
  </div>
  <template #footer>
    <el-button @click="dialogVisible1 = false">取消</el-button>
    <el-button type="primary" @click="submitLocalSwitch">提交</el-button>
  </template>
</el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {useDataStore} from '../store/dataStore.js'
import { axiosInstance } from '../store/messageaxios';
import { ElMessageBox } from 'element-plus';
import jsonp from 'jsonp';
import { watch } from 'vue'
import { InfoFilled,FolderOpened,Refresh} from '@element-plus/icons-vue'
import { TableCell } from 'element-plus/es/components/table-v2/src/components/index.mjs';


// 使用 Pinia 数据仓库
const dataStore = useDataStore()
//代理选择
const apivalue=ref('socks5')

//地区检测
const locationLoading=ref(false)
const locationClick=async()=>{
	try{
		locationLoading.value=true
		const postdata=get_address(dataStore.items)
    console.log('地区检测',postdata)
		const req=await axiosInstance.post('/api/location',postdata)
		console.log('地区检测',req.data)
		if(req.data.success){
			dataStore.updateLocalData(req.data.data)
			ElMessage.success('地区检测成功')
		}else{
			ElMessage.error('地区检测失败')
		}
		locationLoading.value=false
	}catch (error){
		console.log('地区检测出错',error)
	}
}

const get_address=(datatable)=>{
	return datatable.filter(item => item.address !== '1.1.1.1')
}

//延迟检查按钮事件
const delayLoading=ref(false)
const delaybtn=ref(false)
const delayClick=async()=>{
	delayLoading.value=true
	// await dataStore.updateLocalData()
	const req = await(await axiosInstance.post('/api/city_delay',dataStore.items)).data
	if(req.data.success){
		dataStore.updateLocalData(req.data.data)
		ElMessage.success('延迟检测成功')
	}else{
		ElMessage.error('延迟检测失败')
	}
	delayLoading.value=false
	
}
// 画面屏蔽按钮事件
const hmpbbtn=ref()
const hmpbloading=ref(false)
const getIshmpb= async ()=>{
	try{
    const req=await axiosInstance.get('/api/ishmpb')
		const hmreq=req.data
		hmpbbtn.value=hmreq.data
		if(hmpbbtn.value){
			hmpbtext.value="画面屏蔽中"
		}else{
			hmpbtext.value="画面屏蔽"
		}
		console.log("获取画面屏蔽状态",req,hmreq)
	} catch (error) {
		console.error("更新数据失败：", error);
		// 更新失败，提示保存失败
		// ElMessage.error("保存失败，请重试");
		// 可根据需要抛出错误
		throw error;
	}
	
}
const hmpbtext=ref()
const hmpbClick=async ()=>{
	try{
		hmpbloading.value=true
		if(!hmpbbtn.value){
			const req=await axiosInstance.get('/api/hmpb')
			const hmreq=req.data
			if(req.data){
				ElMessage.success('画面屏蔽成功')
			}else{
				ElMessage.error('画面屏蔽失败')
			}
			getIshmpb()
		}else{
			const req=await axiosInstance.get('/api/cancelhmpb')
			const hmreq=req.data
			if(req.data){
				ElMessage.success('取消画面屏蔽成功')
			}else{
				ElMessage.error('取消画面屏蔽失败')
			}
			getIshmpb()
		}

	} catch (error) {
		ElMessage.error('画面屏蔽失败')
		console.error("更新数据失败：", error);
		// 更新失败，提示保存失败
		// ElMessage.error("保存失败，请重试");
		// 可根据需要抛出错误
		throw error;
	}
	hmpbloading.value=false
}


// 选中的ID
const dialogMode = ref('') // 'local' 或 'proxy'
const dialogVisible1 = ref(false)
//本地或者代理编辑框中可选择的ID列表
const LocalProxyListIds = computed(() => {
  // 根据模式返回不同的ID列表
  if (dialogMode.value === 'local') {
    return dataStore.items
      .filter(item => item.api=== false)
      .map(item => item.id)
  } else {
    return dataStore.items
      .filter(item =>  item.api===true)
      .map(item => item.id)
  }
})
const selectedIds = ref([])

const checkAll = ref(false)
const isIndeterminate = ref(false)

const handleCheckAllChange = (val) => {
  selectedIds.value = val ? [...LocalProxyListIds.value] : []
  isIndeterminate.value = false
}
const handleCheckedChange = (value) => {
  const checkedCount = value.length
  checkAll.value = checkedCount === LocalProxyListIds.value.length
  isIndeterminate.value = checkedCount > 0 && checkedCount < LocalProxyListIds.value.length
  console.log('checkedCount:',checkedCount,'checkAll:',checkAll.value,'isIndeterminate:',isIndeterminate.value)
  console.log('selectedIds',value)
}
// 打开切换代理弹窗
const openProxySwitchDialog = () => {
  tableRef.value.clearSelection();
  dialogMode.value = 'proxy'
  selectedIds.value = []
  checkAll.value = false
  isIndeterminate.value = false
  dialogVisible1.value = true
  console.log('当前窗口',dialogMode.value)
}
// 打开切换本地弹窗
const openLocalSwitchDialog = () => {
  tableRef.value.clearSelection();
  dialogMode.value = 'local'
  selectedIds.value = []
  checkAll.value = false
  isIndeterminate.value = false
  dialogVisible1.value = true
  console.log('当前窗口',dialogMode.value)
}
const api=ref()
// 提交选择
const submitLocalSwitch = async() => {
  if(dialogMode.value==='local'){
    api.value='/api/setlinelocal'
  }else{
    api.value='/api/setlineproxy'
  }
  console.log('api',api.value)
  if (!selectedIds.value || selectedIds.value.length === 0) {
    ElMessage.warning('请先选择一个ID')
    return
  }
  // 获取已选中的完整字典对象
  const selectedItems = dataStore.items.filter(item => selectedIds.value.includes(item.id))
  const req=await axiosInstance.post(api.value,selectedItems)
  dataStore.updateLocalData(req.data)
  console.log('切换本地',req.data)
  console.log('提交的ID:', selectedIds.value)
  ElMessage.success('提交成功')
  dialogVisible1.value = false
}
// 切换本地址按钮事件
// const qhbdLoading=ref(false)
// const qhbdbtn=ref()
// const getIsqhbd=async()=>{
// 	const req=await(await axios.get('/api/check_openclash')).data
// 	console.log(`openclash运行状态${req.data}`,req)
// 	if(req.success){
// 		qhbdbtn.value=req.data
// 		if(req.data){
// 			qhbdtext.value='切换本地'
// 		}else{
// 			qhbdtext.value='切换代理'
// 		}
// 	}else{
// 		qhbdtext.value='无法判断服务器连接'
// 	}
	
// }

// const qhbdtext=ref()
// const qhbdClick=async ()=>{
// 	  if(!qhbdbtn.value){
// 		const req=await(await axios.get('/api/startclash')).data
// 		console.log("切换代理（重启clash）",req.data)
// 		setTimeout(() => {
// 		        if(req.data){
// 		        	ElMessage.success("切换代理成功！！")
// 		        }
// 		        else{
// 		        	ElMessage.error("切换代理失败！！")
// 		        }
// 				qhbdLoading.value=false
// 		        getIsqhbd()
				
// 				}, 3000); // 3000 毫秒 = 3 秒

// 	  }else{
// 		const req=await(await axios.get('/api/stopclash')).data
// 		console.log('切换本地',req)
// 		setTimeout(() => {
// 		          if(req.data){
// 		          	ElMessage.success("切换本地成功")
// 		          }else{
// 		          	ElMessage.error("切换本地失败")
// 		          }
// 				  qhbdLoading.value=false
// 		          getIsqhbd()
// 		        }, 3000); // 3000 毫秒 = 3 秒
		
// 	  }
	  
// 	// const selectrows=await selectedRows
// 	// console.log('选中行',selectedRows)

// }
// const qhbdMessage=()=>{
// 	qhbdLoading.value=true
// 	ElMessageBox.confirm(`确定要${qhbdtext.value}吗？`, '提示', {
// 	        confirmButtonText: '确定',
// 	        cancelButtonText: '取消',
// 	        type: 'warning', // 弹窗类型
// 	      })
// 	        .then(() => {
// 	          // 用户点击了"确定"，发送请求
// 	          qhbdClick();
			  
// 	        })
// 	        .catch(() => {
// 	          // 用户点击了"取消"
// 	          handleCancelAction();
// 			  qhbdLoading.value=false
// 	        });
	
// }


const handleCancelAction=()=> {
      // 取消后的操作
      console.log('用户点击了取消');
    }
// 修改MAC事件
const macLoading=ref(false)
const changeMac=async ()=>{
	macLoading.value=true
	const req=await axiosInstance.get('/api/mac')
	const macreq=req.data
	if(macreq.success){
		ElMessage.success("修改MAC成功")
	}else{
		ElMessage.error("修改MAC失败")
	}
	macLoading.value=false
	
}

const resetyamlLoading=ref(false)
// 恢复出厂设置按钮事件
const resetyaml=async ()=>{
	  const req=await axiosInstance.get('/api/resetyaml')
	  const macreq=req.data
	  if(macreq.data){
		ElMessage.success("恢复出厂设置成功")
	  }else{
		ElMessage.error("恢复出厂设置失败")
		
	  }
	  dataStore.fetchData()
}
const resetyamlMessage=()=>{
	resetyamlLoading.value=true
	ElMessageBox.confirm('确定要恢复出厂设置吗？', '提示', {
	        confirmButtonText: '确定',
	        cancelButtonText: '取消',
	        type: 'warning', // 弹窗类型
	      })
	        .then(() => {
	          // 用户点击了"确定"，发送请求
	          resetyaml();
			  this.$forceUpdate()
			  
	        })
	        .catch(() => {
	          // 用户点击了"取消"
	          handleCancelAction();
			  
	        });
	resetyamlLoading.value=false
}

// 分页相关
const currentPage = ref(1)
const pageSize = ref(100)
const pageSizes = [50, 100, 1000]
const proxyOptions = ["socks5", "http", "ss", "vmess"];
// 编辑模式状态
const editingMode = ref(false)
const validationRules = {
  // address: [
  //   { required: true, message: "请输入 IP 地址", trigger: "blur" },
  //   {
  //     pattern: /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  //     message: "请输入有效的 IP 地址", trigger: "blur"
  //   }
  // ],
  port: [
    { required: true, message: "请输入端口", trigger: "blur" },
    {
      pattern: /^[0-9]{1,5}$/,
      message: "端口必须是一个 1 到 5 位的数字",
      trigger: "blur"
    },
    {
      validator: (rule, value, callback) => {
        if (value < 1 || value > 65535) {
          callback(new Error("端口必须在 1 到 65535 之间"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
};
// 判断内网绑定Ip是否存在，是更换行样式
// const isIPAddress = (addr) => {
// 	const ipPattern = /^((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\/([1-3][0-9])$/;
// 	return ipPattern.test(addr);
//   };

// 根据条件返回行样式类名
const tableRowClassName = async({ row }) => {
	// const localaddrlist= await (await axios.get('/api/iprules')).data.data
	// console.log('localaddrlist',localaddrlist)
	// console.log('当前行数据:', row); // 打印当前行数据
	//   if (localaddrlist.includes(row.id)) {
	//     console.log('已开启本地模式，应用样式',row.id); // 打印调试信息
	//     return { backgroundColor: '#f0f9eb' };
	//   }
	//   return {};
};

// 根据当前页和每页数量对数据进行分页处理
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return dataStore.items.slice(start, end)
})

// 分页切换事件
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}
const handleCurrentChange = (val) => {
  currentPage.value = val
}

const editdata=ref(dataStore.items)

// 切换编辑模式
const toggleEdit = () => {
  editingMode.value = !editingMode.value
}

// 保存编辑内容，并调用 dataStore.update 方法
const saveData = async () => {
  // 这里假设 dataStore.update 方法接受整个数据数组
  await dataStore.update()
  editingMode.value = false
}

// 新增：管理弹窗显示和表单数据
const dialogVisible = ref(false)
const userInput = ref('')
const inputLines = ref(0)
// 用来保存当前表格选中的行数据
const selectedRows = ref([])
const editAllIds = computed(() => dataStore.items.map(item => item.id))

const EditcheckAll = ref(false)
const EditisIndeterminate = ref(false)

const EdithandleCheckAllChange = (val) => {
  selectedRows.value = val ? [...editAllIds.value] : []
  EditisIndeterminate.value = false
}
const EdithandleCheckedChange = (value) => {
  const checkedCount = value.length
  EditcheckAll.value = checkedCount === editAllIds.value.length
  EditisIndeterminate.value = checkedCount > 0 && checkedCount < editAllIds.value.length
  selectedRows.value=value.sort((a,b) => a - b);
}

// 表格选中事件（注意：element-plus 会自动解包 ref，所以 template 中可直接使用 selectedRows.length）
const handleSelectionChange = (rows) => {
  // // 当前页选中的id
  // const currentPageIds = rows.map(item => item.id)
  // // 当前页所有id
  // const currentPageAllIds = paginatedData.value.map(item => item.id)
  // // 先移除当前页的所有id
  // selectedRows.value = selectedRows.value.filter(id => !currentPageAllIds.includes(id))
  // // 再合并当前页新选中的id
  // selectedRows.value = [...selectedRows.value, ...currentPageIds]

}

// 点击"批量处理"按钮时，打开弹窗（若未选中任何数据，则给出提示）
const openDialog = () => {
  // if (selectedRows.value.length === 0) {
  //   ElMessage.warning('请先选择至少一行数据')
  //   return
  // }
  dialogVisible.value = true;
  console.log('Dialog visibility after:', dialogVisible.value); // 调试语句
}

// 点击弹窗"提交"按钮时，获取用户输入和选中项 ID 列表
const submitDialog = () => {
  // 获取选中行的 ID 列表
  // const selectedIds = selectedRows.value.map(item => item.id);
  console.log('用户输入内容:', userInput.value);
  console.log('选中 id 列表:', selectedRows.value);
  var error = false;
  // 格式化用户输入并拆分为每一行
  const inputList = userInput.value.split('\n').map((line, index) => {
    const fields = line.split('|').filter(field => field.trim() !== ""); // 去除空字段

    // 检查每行是否有 4 个字段
    if (fields.length !== 4 && fields.length !== 5) {
      ElMessage.error(`输入格式错误，第 ${index + 1} 行应包含 4/5 个字段`);
      error = true;
      return null;
    }
      // 检查是否有空格
    if (fields.some(field => field.includes(' '))) {
      ElMessage.error(`第 ${index + 1} 行存在空格，请去除空格后再提交`);
      error = true;
      return null;
    }
    const [address, port, user, pass] = fields;

    // 格式检查
    const errors = [];
    // if (!/^(\d{1,3}\.){3}\d{1,3}$/.test(address)) {
    //   errors.push(`第 ${index + 1} 行 IP 地址格式无效`);
    // }
    const parsedPort = parseInt(port);
    if (isNaN(parsedPort) || parsedPort < 1 || parsedPort > 65535) {
      errors.push(`第 ${index + 1} 行端口号无效，必须在 1 到 65535 之间`);
    }

    if (errors.length > 0) {
      errors.forEach(error => ElMessage.error(error));
      return null;
    }

    // 假设每行的数据应该对应一个选中的 ID
    const id = selectedRows.value[index];

    return {
      id,
      address,
      port: parsedPort,
      user,
      pass
    };
  }).filter(item => item !== null);
  if (error) return;
  console.log('格式化后的输入列表:', inputList);

  console.log('选择长度：',inputList.length,selectedRows.value.length)
  // 如果格式化后的数据行数与选中的 ID 数量匹配，进行更新
  if (inputList.length === selectedRows.value.length) {
    // 更新本地数据
    dataStore.updateLocalData(inputList);
    // 调用后端更新数据
    dataStore.update();
    saveOriginalData();
    // 关闭弹窗
    dialogVisible.value = false;

    // 清空用户输入（可选）
    userInput.value = '';
  } else {
    ElMessage.error("输入行数与选中的 ID 数量不匹配");
  }
};// 弹窗关闭前的钩子，可用于重置数据
const handleClose = (done) => {
  userInput.value = ''
  done()
}
// 处理输入框失焦事件
const handleInputChange = () => {
  // 计算有效行数（包含空行）
  const lines = userInput.value.split('\n')
  inputLines.value = lines.length

  // 如果只需要统计非空行，使用这个版本：
  // inputLines.value = lines.filter(line => line.trim() !== '').length
}
// const headers = ref({
// "accept": "*/*",
// "accept-language": "zh-CN,zh;q=0.9",
// "cache-control": "no-cache",
// "pragma": "no-cache",
// "sec-ch-ua-mobile": "?0",
// "sec-fetch-dest": "script",
// "sec-fetch-mode": "no-cors",
// "sec-fetch-site": "cross-site",
// "sec-fetch-storage-access": "active",
// "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
// })

// 发送 GET 请求
const proxy_ip=ref()
const proxy_location=ref()
const getproxy=async()=>{
	const url = 'https://whois.pconline.com.cn/ipJson.jsp?';
	      jsonp(url, null, (err, data) => {
	        if (err) {
	          console.error('请求失败:', err);
	        } else {
	          console.log('响应数据:', data);
			    // 3. 解析JSON数据
			    const ipInfo = data
			    // console.log('IP信息:',ipInfo)
			  // 处理响应数据
			  console.log('ip:',ipInfo.ip,ipInfo.addr);
			  proxy_ip.value=ipInfo.ip
			  proxy_location.value=ipInfo.addr
			  
	        }
	      });
} 
// const connectionStatus = ref('disconnected')
const trafficData_up = ref(null)
const trafficData_down = ref(null)
let socket = null

const initWebSocket = () => {
  // 使用动态检测的IP地址
  const wsUrl = 'ws://10.0.0.254:9090/traffic?token=Rc3lFJSt';
  socket = new WebSocket(wsUrl, [],{
  headers: {
    'Sec-WebSocket-Key': '+Hqdgt/X/68cJ3cKfc53MA=='}
  })

  // 手动设置请求头（浏览器环境部分头信息无法修改）
  socket.onopen = () => {
	console.log('traffic-WebSocket connected')
  }

  socket.onmessage = (event) => {
    // console.log('traffic-WebSocket message:', event.data)
    const trafficData = JSON.parse(event.data)
    trafficData_up.value=trafficData.up
    trafficData_down.value=trafficData.down
	// document.getElementById('traffic_upload').innerHTML = `上传: ${trafficData.upload_kb}KB/s`,
	// document.getElementById('traffic_download').innerHTML = ` 下载: ${trafficData.download_kb}KB/s`;
  }

  socket.onerror = (error) => {
	console.error('traffic-WebSocket error:', error)
  }

  socket.onclose = () => {
	console.log('traffic-WebSocket disconnetced')
  }
}

const total_down=ref()
const total_up=ref()
let socket_total=null
const totalWebSocket = () => {
  // 使用动态检测的IP地址
  const wsUrl = 'ws://10.0.0.254:9090/connections?token=Rc3lFJSt';
  socket_total = new WebSocket(wsUrl, [],{
  headers: {
      "Upgrade": "websocket",
      "Origin": 'http://${__LOCAL_IP__}:${__WS_PORT__}',
      "Cache-Control": "no-cache",
      "Accept-Language": "zh-CN,zh;q=0.9",
      "Pragma": "no-cache",
      "Connection": "Upgrade",
      "Sec-WebSocket-Key": "6Y3Bjd/xE0u2l67XaP1Peg==",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
      "Sec-WebSocket-Version": "13",
      "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits"}
  })

  // 手动设置请求头（浏览器环境部分头信息无法修改）
  socket_total.onopen = () => {
	console.log('connect_websockets connected')
  }

  socket_total.onmessage = (event) => {
	const trafficData = JSON.parse(event.data)
	total_up.value=trafficData.uploadTotal
	total_down.value=trafficData.downloadTotal
	// document.getElementById('traffic_upload').innerHTML = `上传: ${trafficData.upload_kb}KB/s`,
	// document.getElementById('traffic_download').innerHTML = ` 下载: ${trafficData.download_kb}KB/s`;
  }

  socket_total.onerror = (error) => {
	console.error('connect_websockets error:', error)
  }

  socket_total.onclose = () => {
	console.log('connect_websockets disconnetced')
  }
}

// 虚拟网卡检测相关
const untnNetExists = ref(false)

const formatSize=computed(()=>{
	return (bytes) => {
	  if (bytes === 0) return '0 B'
	  const k = 1024
	  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
	  const i = Math.floor(Math.log(bytes) / Math.log(k))
	  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
	}
})
// 组件挂载后获取数据
onMounted(() => {
  initWebSocket()
  dataStore.fetchData(),
  getIshmpb()
  // getIsqhbd()
  getproxy()
  totalWebSocket()
  isbp()
  saveOriginalData()
  checkUntnNet()
})


// 添加手动输入ID相关的变量和函数
const manualInputIds = ref('')
const tableRef = ref(null)
// 添加手动输入的ID
const addManualIds = (dialogIs) => {
  if (dialogIs == 'delete'){
    selectedRows.value=[];
    selectedIds.value=[];
    tableRef.value.clearSelection();
    return;
  }
  if (!manualInputIds.value.trim()) return
  let ids = []
  const regx= /(^([1-9]\d{0,}[，,-])+[1-9]\d{0,}$)|^[1-9]\d{0,}$/;
  if (!regx.test(manualInputIds.value)) {
    ElMessage.error('输入格式错误，请使用正确的格式')
    return
  }
  manualInputIds.value.split(/[,，]/).forEach(part => {
    part = part.trim()
    if (part.includes('-')) {
      // 区间格式
      const [start, end] = part.split('-').map(Number)
      if (!isNaN(start) && !isNaN(end) && start <= end) {
        for (let i = start; i <= end; i++) {
          ids.push(i)
        }
      }else if(start > end){
        for(let i = start; i >= end; i--) {
          ids.push(i)
        }
      }
    } else{
      ids.push(Number(part))
    }
  })
  console.log('ids:',ids)
    // 验证ID是否有效
  const validIds = ids.filter(id => {
    const numId = Number(id)
    if(dialogIs=='add'){
      return !isNaN(numId) && editAllIds.value.includes(numId)
    }else{
      return !isNaN(numId) && LocalProxyListIds.value.includes(numId)
    }
  })
  console.log('validIds:',validIds,validIds.length,selectedRows.value,selectedIds.value )
  if (dialogIs=='add'){
    validIds.forEach(id => {
      if (!selectedRows.value.includes(Number(id))) {
        selectedRows.value.push(Number(id))
        console.log('add-selectedRows.value:',selectedRows.value)
      }})
      const inputdata=editdata.value.filter(item => validIds.includes(item.id))
      console.log('add-inputdata:',inputdata)
      inputdata.forEach(item => {
        tableRef.value.toggleRowSelection(item,true)
      })
    // selectedRows.value=selectedRows.value.sort((a,b) => a.id - b.id);
    EdithandleCheckedChange(selectedRows.value)
  }else{
    // 添加有效的ID到selectedIds
    validIds.forEach(id => {
      if (!selectedIds.value.includes(Number(id))) {
        selectedIds.value.push(Number(id));
        console.log('edit-selectedIds.value:',selectedIds.value)
      }})
      const inputdata=editdata.value.filter(item => validIds.includes(item.id))
      console.log('edit-inputdata:',inputdata)
      inputdata.forEach(item => {
        tableRef.value.toggleRowSelection(item,true)
      })
      // 更新全选状态
    handleCheckedChange(selectedIds.value)
    
  }
  // 清空输入框
  manualInputIds.value = ''
 }
  const showImport=ref(false)
  const fileInput=ref(null)
  const triggerFileInput = () => {
      if (fileInput.value) fileInput.value.click()
    }

const handleFileChange = (event) => {
    const file = event.target.files[0]
    if (!file) return
    if (!file.name.endsWith('.yaml')) {
      ElMessage.error('只允许导入.yaml文件')
      event.target.value = ''
      return
    }
    const formData = new FormData()
    formData.append('file', file)
    // 这里假设你的API为 /api/upload_yaml
    axiosInstance.post('/api/uploadyaml', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => {
      ElMessage.success('上传成功')
      dataStore.fetchData()
    }).catch(err => {
      ElMessage.error('上传失败')
    })
    event.target.value = ''
    selectedRows.value=[]
  }
const passwordDialogVisible = ref(false)
const restorePassword = ref('')
const correctPassword = '6668' // 你可以自定义密码

const handleRestoreClick = () => {
    ElMessageBox.confirm(
      '导入配置文件，是否继续？',
      '警告',
      {
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      passwordDialogVisible.value = true
      restorePassword.value = ''
    }).catch(() => {})
  }

const resetyamlfile=()=>{
        ElMessageBox.confirm(
      '恢复配置文件会导致线路数据丢失，是否继续？',
      '警告',
      {
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      axiosInstance.get('/api/resetyamlfile', {
      }).then(res => {
        ElMessage.success('恢复配置文件成功')
        
      }).catch(err => {
        ElMessage.error('恢复配置文件失败')
      })
    }).catch(() => {})
    dataStore.fetchData()
  }
const confirmRestorePassword = () => {
    axiosInstance.post('/api/verify_pwd', {
     password: restorePassword.value,
     menu:'sk5'
    }).then(res => {
      if (res.data.success) {
        triggerFileInput()
        
      } else {
        ElMessage.error('密码错误，请重新输入！')}
   passwordDialogVisible.value=false})
   isbp()
  }

const resetbutton=ref(false)
const isbp=()=>{
    axiosInstance.get('/api/isbp').then(res => {
      resetbutton.value=res.data.success
    })
  }
const apiEnabled = ref(false)
const apiProxies = computed(() => dataStore.apiProxies)
const getApiProxyInfo = (row) => {
  // 只在 row.api 为 true 时展示
    // if (!row.api || !apiProxies.value.length) return null
    // 这里默认取 apiProxies 的第一条
    const proxy = apiProxies.value.find(p=>p.id===row.id)
    if (!proxy) return null
  // 你可以自定义展示哪些字段
    return `地址: ${proxy.address}  端口: ${proxy.port}  用户: ${proxy.user}  密码: ${proxy.pass}  日期: ${proxy.date}`
}
 const syncApiProxiesWithTable = () => {
  // 1. 获取所有 api_status 为 true 的行，按表格顺序
    const openedRows = dataStore.items.filter(row => row.api_status === true)
    // 2. 遍历 apiProxies，依次赋值 id
    apiProxies.value.forEach((proxy, idx) => {
      if (openedRows[idx]) {
        proxy.id = openedRows[idx].id
      } else {
        proxy.id = null // 或者清空
      }
    })

}
watch(
  () => dataStore.items.map(row => row.api_status),
  () => {
    syncApiProxiesWithTable()
  }
)// 记录原始数据到 localStorage
const saveOriginalData = () => {
  const originalData = {};
  dataStore.items.forEach(item => {
    originalData[item.id] = {
      address: item.address,
      port: item.port,
      user: item.user,
      pass: item.pass
    };
  });
  localStorage.setItem('proxy_original_data', JSON.stringify(originalData));
};

const saveApiData = (row) => {
  let apiData = JSON.parse(localStorage.getItem('proxy_api_data') || '{}');
  apiData[row.id] = {
    address: row.address,
    port: row.port,
    user: row.user,
    pass: row.pass
  };
  localStorage.setItem('proxy_api_data', JSON.stringify(apiData));
};

const onApiSwitchChange = async (row) => {
  if (row.api_status) {
    // 只在开关为 true 时发送
    // 获取所有已开启API的行（按表格顺序）
    const openedRows = dataStore.items.filter(item => item.api_status === true)
    // 找到当前行在已开启行中的索引
    const rowIndex = openedRows.findIndex(item => item.id === row.id)
    // 使用索引从 openedRows 中获取对应的数据
    const sourceRow = openedRows[rowIndex]
    
    console.log('当前开启的API路线索引为：', rowIndex, '线路ID为：', row.id, '源数据：', sourceRow)
    
    dataStore.updateLocalData([
      { 
        id: row.id,
        address: sourceRow.address,
        port: sourceRow.port,
        user: sourceRow.user,
        pass: sourceRow.pass,
      }
    ]);
    // 调用后端更新数据
    dataStore.update();
    saveApiData(row);
}else{
    // 读取原始数据
    const originalData = JSON.parse(localStorage.getItem('proxy_original_data') || '{}');
    const old = originalData[row.id];
    if (old) {
      dataStore.updateLocalData([
        { id: row.id, address: old.address, port: old.port, user: old.user, pass: old.pass }
      ]);
      dataStore.update();
    } else {
      // 没有原始数据，使用当前行数据
      dataStore.updateLocalData([
        { id: row.id, address: row.address, port: row.port, user: row.user, pass: row.pass }
      ]);
      dataStore.update();
    }
}
}
const restartserverLoading=ref(false)
const IsRestartServer=()=>{
  console.log('IsRestartServer')
  ElMessageBox.confirm(
    '重启服务会导致所有连接断开，是否继续？', 
    '警告', 
    {
    confirmButtonText: '立即重启',
    cancelButtonText: '稍后重启',
    type: 'warning',
  }).then(() => {
    restartserver()
  }).catch(() => {
    restartserverLoading.value=false
  })
}
const restartserver=async()=>{
  restartserverLoading.value=true
  await axiosInstance.get('/api/restartserver').then(res => {
    ElMessage.success('重启服务成功')
  })
  restartserverLoading.value=false
  dataStore.fetchData()
}
const copyData=()=>{
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要复制的数据')
    return
  }
  
  // 获取选中行的完整数据
  const selectedData = dataStore.items.filter(item => selectedRows.value.includes(item.id))
  
  // 格式化数据为指定格式
  const formattedData = selectedData.map(item => {
    return `${item.address}|${item.port}|${item.user || ''}|${item.pass || ''}`
  }).join('\n')
  
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(formattedData)
      .then(() => {
        // 复制成功
        ElMessage.success('已复制到剪贴板');
      })
      .catch(() => {
        fallbackCopyTextToClipboard(formattedData);
      });
  } else {
    fallbackCopyTextToClipboard(formattedData);
  }
}
const fallbackCopyTextToClipboard = (text) => {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  // 设置样式使 textarea 不可见且不影响页面滚动
  textArea.style.position = 'fixed';
  textArea.style.left = '-9999px';
  textArea.style.top = '-9999px';
  textArea.style.opacity = '0';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    document.execCommand('copy');
    ElMessage.success('已复制到剪贴板');
  } catch (err) {
    ElMessage.error('复制失败，请手动复制');
  }
  document.body.removeChild(textArea);
}
const clearSelectedProxyData = () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先在表格中勾选需要恢复的行')
    return
  }
  const originalData = {
    type: "socks5",
    address: "1.1.1.1",
    port: 1080,
    user: "",
    pass: "",
    udp:   true,
    uuid: "",
    delay: 0,
    alterId: "",
    cipher: "",
    area: ""

  }
  const updates = []
  selectedRows.value.forEach((id) => {
    updates.push({ id, address: originalData.address, port: originalData.port, user: originalData.user, pass: originalData.pass
      ,udp:originalData.udp,
      uuid:originalData.uuid,
      delay:originalData.delay,
      alterId:originalData.alterId,
      cipher:originalData.cipher,
      area:originalData.area
     })
  })
  if (!updates.length) {
    ElMessage.error('未找到可用的初始数据')
    return
  }
  dataStore.updateLocalData(updates)
  dataStore.update()
  ElMessage.success('已恢复选中行到初始数据')
}
const untnNetLoading=ref(false)
const checkUntnNet=()=>{
  untnNetLoading.value=true
  ElMessage.info('正在检测服务...')
  axiosInstance.get('/api/untn_net').then(res => {
    console.log(res.data)
    untnNetExists.value = res.data.exists
  }).finally(() => {
    untnNetLoading.value=false
    ElMessage.success('授权检测完成')
  })
}
</script>

<!-- /* <script>
const source = new EventSource('/stream_traffic');
source.onmessage = (e) => {
    const data = JSON.parse(e.data);
    document.getElementById('traffic_upload').innerHTML = `上传: ${data.upload_kb}KB/s`,
	document.getElementById('traffic_download').innerHTML = ` 下载: ${data.download_kb}KB/s`;
    document.getElementById('proxy_ip').innerHTML = `代理IP: ${data.proxy_ip}`;
	document.getElementById('proxy_location').innerHTML = `当前地区: ${data.location}`;
};
</script> */ -->


<style scoped>
	/* 激活状态样式 */
	.active-btn {
	    background-color: red;
	    color: white;
	    padding: 10px 20px;
	    border: none;
	    cursor: pointer;
	}
	.unactive-btn{
		  /* background-color: blue; */
		  color: white;
		  padding: 10px 20px;
		  border: none;
		  cursor: pointer;
	}
	/* 蓝色按钮样式 */
	.highlight-row {
	     background-color: #ffaa7f; /* 你可以自定义颜色 */
	}
	.el-table {
	    font-size: 13px; /* 设置表格文本大小 */
	}
	.el-table th {
		
		
		font-size: 14px; /* 设置表头文本大小 */
		font-weight: bold; /* 设置表头字体加粗 */
	}
	.el-col{
		text-align: center;
		font-size:13px
	}
	.listButs > button {
	    margin-bottom: 10px;
	}
	.el-dialog__wrapper {
	  display: flex;
	  justify-content: center;
	  align-items: center;
	}
	.red-circle {
	  color: red;
	  font-size: 16px;
	}
	.green-circle {
	  color: green;
	  font-size: 16px;
	}
	.status_green{
		color: green;
	}
	.status_red{
		color: red;
	}
	.status_yellow{
		color: #f7b911;
	}
	.untn-net-green {
	  color: #67c23a;
	  font-size: 16px;
	}
	.untn-net-red {
	  color: #f56c6c;
	  font-size: 16px;
	}
	.el-table__body-wrapper{
  overflow-x: hidden !important;
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
  /* 表格整体边框 */
  .el-table, .el-table__header-wrapper, .el-table__body-wrapper {
    border-color: #bbb7b7 !important;
  }

  /* 兼容 Element Plus 内部嵌套表格结构 */
  .el-table__row td, .el-table__header th {
    border: 1px solid #bbb7b7 !important;
    border-color: #bbb7b7 !important;
  }
  ::v-deep .el-table th,
  ::v-deep .el-table td,
  ::v-deep .el-table__row td,
  ::v-deep .el-table__header th {
    border: 1px solid rgba(214, 214, 219, 0.918) !important;
    border-color: rgba(214, 214, 219, 0.918) !important;
  }
  /* ::v-deep .el-table__body .el-table__row td{
  font-weight: bold;
  } */
  /* 设置 el-table 多选框边框颜色和粗细 */
::v-deep .el-checkbox__inner {
  border: 1px solid #d4d0d0 !important;   /* 2px粗黑色边框 */
  border-radius: 4px;                  /* 可选：圆角 */
}
/* 表头字体加粗（scoped模式下最保险） */
::v-deep .el-table__header th {
  font-family: "黑体", "楷体_GB2312", KaiTi, STKaiti, serif !important;
  font-weight: bold !important;
  color: #111111 !important;
  font-size: 13px;
}
</style>
