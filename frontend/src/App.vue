<script setup lang="ts">
// import HelloWorld from './components/HelloWorld.vue'
import DataTable from './pages/DataTable.vue'
// import ApiTag from './pages/ApiTag.vue';
import BalanceTag from './pages/BalanceTag.vue';
import ScriptsTag from './pages/ScriptsTag.vue';
import L2tpTag from './pages/L2tpTag.vue';
import { ref } from "vue";
import { useSocketioStore } from './store/socketioStore';
import { onMounted,onUnmounted } from 'vue';
const socketio = useSocketioStore();
onMounted(() => {
  socketio.connect();
})
onUnmounted(() => {
  socketio.disconnect();
})
const activeTab = ref("list"); // 默认选中第一个Tab
</script>

<!--<template>-->
<!--  <DataTable />-->
<!--</template>-->

<template>
  <el-tabs v-model="activeTab" class="tag-container">
    <el-tab-pane label="sk5列表" name="list">
      <DataTable />
    </el-tab-pane>

    <el-tab-pane label="L2TP列表" name="l2tp">
      <L2tpTag />
    </el-tab-pane>

    <!-- <el-tab-pane label="设置API代理" name="api">
      <ApiTag />
    </el-tab-pane> -->

    <el-tab-pane label="AP管理" name="wifi" path="/ap">
      <!-- <el-button type="primary">点击跳转</el-button> -->
      <router-view />
    </el-tab-pane>

    
    <el-tab-pane label="负载均衡" name="balance">
      <!-- <el-button type="primary">点击跳转</el-button> -->
       <BalanceTag />
    </el-tab-pane>

    <el-tab-pane label="系统脚本" name="scripts">
      <ScriptsTag />
    </el-tab-pane>
  </el-tabs>
  
</template>

<style>

</style>

