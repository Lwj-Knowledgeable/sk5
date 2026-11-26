<template>
  <el-row :gutter="10" style="padding-left: 20px;height: 50px;margin-top: 30px;">
    <el-col :span="2">api链接：</el-col>
    <el-col :span="9">
      <el-input v-model="apiUrl" placeholder="请输入API链接" style="width: 100%;height: 30px;" />
    </el-col>
    <el-col :span="2" style="padding-left: 10px;">
      <el-button size="small" @click="openPwdDialog">添加</el-button>
    </el-col>
  </el-row>
  <el-dialog v-model="pwdDialogVisible" title="请输入密码" width="300px" :close-on-click-modal="false">
    <el-input v-model="inputPwd" type="password" placeholder="请输入密码" @keyup.enter="verifyPwd" />
    <template #footer>
      <el-button @click="pwdDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="verifyPwd" :loading="pwdLoading">验证</el-button>
    </template>
  </el-dialog>
  <div>
    <el-table :data="dataStore.apiProxies" style="width: 60%; margin-top: 20px;margin-left: 40px;">
        <el-table-column prop="address" label="地址" />
        <el-table-column prop="port" label="端口" />
        <el-table-column prop="pass" label="密码" />
        <el-table-column prop="user" label="用户" />
        <el-table-column prop="date" label="日期" />
        <el-table-column prop="id" label="线路" />
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { axiosInstance } from '../store/messageaxios'
import { useDataStore } from '../store/dataStore'

const dataStore = useDataStore()
const apiUrl = ref('')
const pwdDialogVisible = ref(false)
const inputPwd = ref('')
const pwdLoading = ref(false)
const api_proxies=ref([])
// const apiProxies = computed(() => )
const openPwdDialog = () => {
  if (!apiUrl.value.trim()) {
    ElMessage.warning('请输入API链接')
    return
  }
  pwdDialogVisible.value = true
  inputPwd.value = ''
}

const verifyPwd = async () => {
  if (!inputPwd.value) {
    ElMessage.warning('请输入密码')
    return
  }
  pwdLoading.value = true
  try {
    // 1. 先将密码发给后端校验
    const res = await axiosInstance.post('/api/verify_pwd', { password: inputPwd.value,menu:'api' })
    if (res.data && res.data.success) {
      // 2. 校验成功后再发链接
      const api_res=await axiosInstance.post('/api/add_api_url', { url: apiUrl.value })
      if (api_res.data && api_res.data.success){
        ElMessage.success('添加成功')
        const api_result=api_res.data.msg
        api_proxies.value = api_result.map(item => {
            return {
                address: item.ip || '',
                port: item.port || '',
                pass: item.pass || '',
                user: item.user || '',
                date: item.stoptime || '',
                id:''
            }
        })
        dataStore.setproxyApi(api_proxies.value)
        pwdDialogVisible.value = false
        apiUrl.value = ''
      }else{
        ElMessage.error(api_res.data.msg)
      }
      
      
    } else {
      ElMessage.error(res.data && res.data.msg ? res.data.msg : '密码错误')
    }
  } catch (e) {
    ElMessage.error('请求失败')
  } finally {
    pwdLoading.value = false
  }
}
</script>