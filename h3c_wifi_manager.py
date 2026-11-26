#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华三AP WiFi管理工具
支持SSH远程连接、获取WiFi信息、修改SSID等配置
"""


import paramiko,time,re,logging
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor,as_completed
from threading import Lock
from settings_load import settings
# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class H3CAPManager:
    def __init__(self, num):
        """
        初始化华三AP管理器
        
        Args:
            num: AP编号，用于构建IP地址
        """
        self.host = settings.AP_HOST_TEMPLATE.format(aid=num)
        self.username = settings.AP_USERNAME
        self.password = settings.AP_PASSWORD
        self.port = settings.AP_PORT  # 华三设备可能使用非标准端口
        self.ssh = None
        self.shell = None
        self.aid = num
        self.output = ''  # 终端输出
        self._radio_count = None  # 缓存 radio 数量，避免重复 display
        self.radio_type_dict = {}    
        self.physical_port_list = []  

    def connect(self) -> bool:
        """
        建立SSH连接
        
        Returns:
            bool: 连接是否成功
        """
        try:

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logger.info(f"正在连接 {self.host}:{self.port}...")
            # 尝试不同的SSH配置
            ssh_configs = {
                    'hostname': self.host,
                    'port': self.port,
                    'username': self.username,
                    'password': self.password,
                    'timeout': 3,  # 增加超时时间
                    'allow_agent': False,
                    'look_for_keys': False,
                    'banner_timeout': 5,  # 增加banner超时
                    'auth_timeout': 5,
                    'compress': True,  # 启用压缩
                    'disabled_algorithms': {'pubkeys': []}}
            self.ssh.connect(**ssh_configs)
            transport=self.ssh.get_transport()
            if transport:
                transport.set_keepalive(30)
                self.shell = self.ssh.invoke_shell()
                time.sleep(0.2)
                while self.shell.recv_ready():
                    self.output += self.shell.recv(4096).decode('utf-8', errors='ignore')
                logger.info(f"{self.host}-------连接成功: {self.output.strip()}")
                return True
            else:
                logger.error(f"SSH连接异常: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"连接失败: {str(e)}")
            return False

    def disconnect(self):
        """断开SSH连接"""
        try:
            if self.shell:
                self.shell.close()
            if self.ssh:
                self.ssh.close()
            self._radio_count = None
            logger.info("连接已断开")
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")

    def shell_command(self, command: str, wait_time: float = 0.3, timeout: int = 5,is_output:bool=True) -> str:
        """
        执行命令并动态等待结果全部输出
        
        Args:
            command: 要执行的命令
            wait_time: 初始等待时间（秒）
            timeout: 最大超时时间（秒）
            
        Returns:
            str: 命令执行结果
        """
        if not self.shell:
            raise Exception("未建立SSH连接")
        
        try:
            logger.info(f"执行命令: {command}")
            
            # 清空输出缓冲区和SSH接收缓冲区
            self.output = ""
            self._clear_ssh_buffer()
            
            # 发送命令
            self.shell.send(command + '\n')
            
            if not is_output:
                return True
            # 动态等待命令执行完成
            start_time = time.time()
            last_output_time = start_time
            # consecutive_empty_reads = 0
            # max_empty_reads = 3  # 减少连续空读取次数
            command_completed = False
            i=0
            while time.time() - start_time < timeout and not command_completed:
                if self.shell.recv_ready():
                    time.sleep(0.1)
                    chunk = self.shell.recv(65535).decode('utf-8', errors='ignore')
                    # print(f"chunk: {chunk}")
                    if chunk:
                        i+=1
                        self.output += chunk
                        # consecutive_empty_reads = 0
                        # logger.info(f"command:{command} ,chunk{i}: {chunk}")
                        # 检查是否出现命令提示符，表示命令执行完成
                        if self._is_command_completed(self.output, command):
                            logger.info("检测到命令执行完成")
                            command_completed = True
                            break
                else:
                    # 如果没有数据可读，等待一下
                    time.sleep(0.1)
                    logger.info(f"等待{time.time() - start_time}秒")
                    # 如果超过一定时间没有新输出，检查是否完成
                    if time.time() - start_time > wait_time:
                        # 再次检查是否有数据可读
                        if not self.shell.recv_ready():
                            logger.info("已超过指定等待时间且无新数据，命令可能已完成")
                            break
            cleaned_output = self.output.replace('\r', '').replace('\x00', '')
            # logger.info(f'self.output:{self.output}')
            logger.info(f"命令执行完成，输出长度: {len(cleaned_output)}")         
            return cleaned_output
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"执行命令失败: {error_msg}")

            # 如果是socket连接问题，标记连接为无效
            if "closed" in error_msg.lower() or "socket" in error_msg.lower():
                logger.error("检测到socket连接已关闭，连接可能已失效")
                # 可以在这里设置一个标志，但由于连接池会检查，这里主要记录日志

            return ""
    
    def exec_command(self, command: str,timeout: int = 5) -> str:
        try:
            stdin,stdout,stderr = self.ssh.exec_command(command, timeout=timeout)
            out=stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore').strip()
            logger.info(f"out:{out},err:{err}")
            if out:
                return out
            if err:
                return err
            return ""
        except Exception as e:
            logger.error(f"执行命令失败: {str(e)}")
            return ""

    def _clear_ssh_buffer(self):
        """
        清空SSH接收缓冲区，避免上次命令的残留数据
        """
        try:
            while self.shell.recv_ready():
                self.shell.recv(4096)
        except Exception as e:
            logger.debug(f"清空SSH缓冲区时出错: {e}")
    
    def _is_command_completed(self, chunk: str, command: str) -> bool:
        """
        检查命令是否执行完成
        Args:
            chunk: 最新接收的输出块
            command: 执行的命令
        Returns:
            bool: 命令是否完成
        """
        # 华三设备常见的命令提示符模式
        prompt_patterns = [
            # r'<[^>]+>\s*$',       # <H3C> 在行尾
            r'\[[^\]]+\]$',    # [H3C] 在行尾
            r'[^>]+>\s*$',        # 任何以>结尾的提示符在行尾
            r'[^#]+#\s*$',        # 任何以#结尾的提示符在行尾
            r'[^$]+\$\s*$',       # 任何以$结尾的提示符在行尾
        ]
        # 检查是否包含提示符（更严格的匹配）
        for pattern in prompt_patterns:
            if re.search(pattern, chunk, re.MULTILINE):
                logger.info(f'命令已完成')
                return True     
        return False
    
    def _clean_command_output(self, command: str) -> str:
        """
        清理命令输出，移除命令本身和提示符
        
        Args:
            command: 执行的命令
            
        Returns:
            str: 清理后的输出
        """
        if not self.output:
            return ""
        lines = self.output.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # 跳过空行
            if not line:
                continue            
           # 跳过命令本身
            if line == command.strip():
                continue           
            # 跳过命令提示符行
            if re.match(r'^[<\[][^>\]]*[>\]]', line):
                continue           
            # 跳过分页提示
            if 'More' in line or 'Press any key' in line:
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
            
    
    def get_allwifi_info(self,wifi_list:List) -> Dict:
        """
        获取WiFi详细信息
        wifi_list:[1,2,3]
        Returns:
            Dict: WiFi信息字典
        """
        wifi_info_list = {}
        radio_bind_wifiall = {} # radio_bind_wifiall[wid] = [radio1,radio2,radio3]
        wifi_info = {}
        try:
            # 获取SSID列表
            search_dict={
                'SSID': r'SSID\s*:\s*(.+)',
                'SSID-hide': r'SSID-hide\s*:\s*(.+)',
                'User-isolation': r'User-isolation\s*:\s*(.+)',
                'Service': r'Service template status\s*:\s*(.+)',
                'wid': r'Service template name\s*:\s*(.+)',
            }
            h3c_to_wifi_dict={
                'SSID': 'ssid',
                'SSID-hide': 'ssid_hide',
                'User-isolation': 'user_isolation',
                'Service': 'status',
                'wid': 'wid',
            }
            print(f"=== 获取AP {self.aid} WiFi的SSID列表 ===")
            self.shell_command("system-view")
            out = self.shell_command(f"display wlan service-template ver",timeout=20)
            wifi_result_cut=re.split(r'\n\n', out)
            # def _get_wifi_info(wifi_result):
            #     if not re.search(r'Service template name\s*:\s*(.+)', wifi_result):
            #         return None,None
            #     wifi_info = {}
            #     for key, pattern in search_dict.items():
            #         match = re.search(pattern, wifi_result)
            #         if key == 'wid':
            #             wid=match.group(1) if match else 'Unknown'
            #         if match:
            #             wifi_info[h3c_to_wifi_dict[key]] = match.group(1)
            #         else:
            #             wifi_info[h3c_to_wifi_dict[key]] = "Unknown"
            #     logger.info(f'---------------wifi_info:{wifi_info}')
            #     wifi_info.update({
            #         "aid": self.aid,
            #         'wifipassword': '',
            #         'vlan':False if int(wid) > 200 else True
            #     })
            #     return wifi_info,wid
            # with ThreadPoolExecutor(max_workers=len(wifi_result_cut)) as executor:
            #     futures = [executor.submit(_get_wifi_info, wifi_result) for wifi_result in wifi_result_cut]
            #     for future in as_completed(futures):
            #         wifi_info,wid = future.result()
            #         logger.info(f'线程结果；wifi_info:{wifi_info},wid:{wid}')
            #         if wifi_info and wid:
            #             wifi_info_list[wid] = wifi_info
            #             radio_bind_wifiall[wid] = []
            for wifi_result in wifi_result_cut:
                wifi_info = {}
                # logger.info(f"wifi_result:{wifi_result}")
                if not re.search(r'Service template name\s*:\s*(.+)', wifi_result):
                    continue
                for key, pattern in search_dict.items():
                    match = re.search(pattern, wifi_result)
                    if key == 'wid':
                        wid=int(match.group(1)) if match else 0
                    if match:
                        wifi_info[h3c_to_wifi_dict[key]] = match.group(1)
                    else:
                        wifi_info[h3c_to_wifi_dict[key]] = "Unknown"
                    # logging.info(f"{key}: {wifi_info[h3c_to_wifi_dict[key]]}")
                # 构建WiFi信息，如果匹配失败则使用"Unknown"
                logger.info(f'---------------wifi_info:{wifi_info}')
                wifi_info.update({
                    "aid": self.aid,
                    'wifipassword': '',
                    'vlan':False if int(wid) > 200 else True
                })
                wifi_info_list[wid] = wifi_info
                # logger.info(f'---------------wifi_info_list:{wifi_info_list}')
                radio_bind_wifiall[wid] = []
            # time2=time.time()
            # logger.info(f'time1:{time1},time2:{time2},time2-time1:{time2-time1}')
            # 获取Radio绑定信息
            # logging.info(f"AP {self.aid} WiFi-LIST:{wifi_list},wifi_info_list:{wifi_info_list}")
            result = self.shell_command("display current-configuration interface WLAN-Radio",wait_time=0.5)
            radiocunt = len(re.findall(r'interface WLAN-Radio', result))
            for i in range(1, radiocunt):
                result = self.shell_command(f"display current-configuration interface WLAN-Radio 1/0/{i}",wait_time=0.3)
                st_pattern = r'service-template (\d+)'
                st_matches = re.findall(st_pattern, result)
                # logger.info(f'self.radio_type_dict:{self.radio_type_dict}')
                radio_type = self.radio_type_dict.get(str(i), "Unknown")
                for st_match in st_matches:
                    logger.info(f'WlanRadio{i} service-template: {st_match}')
                    for wid in wifi_list:
                        if int(st_match) == int(wid):
                            radio_bind_wifiall[int(wid)].append(radio_type + f'({i})')
            for wid in wifi_list:
                wifi_info_list[int(wid)]['radio_bind']=radio_bind_wifiall[int(wid)]
            logger.info(f"AP {self.aid} WiFi {wifi_list} 最终信息: {[wifi_info for wifi_info in wifi_info_list.values()]}")
            wifi_info_list=list(wifi_info_list.values())
            return wifi_info_list
            
        except Exception as e:
            logger.error(f"AP {self.aid} WiFi {wifi_list} 获取WiFi信息失败: {str(e)}")
            return []
    

    def get_radio_info(self,count:int)->List[Dict]:
        try:
        
            radio_info=[]
            # 获取Radio信息
            search_dict={
                'State': r'State\s+:(.+)',
                'Type': r'Type\s+:.+\((.+)\)',
                'Channe': r'Channel bandwidth\s+:(.+)',
                'Channel': r'Channel\s+:(.+)',
                'Max': r'Max power\s+:(.+)',
            }
            h3c_to_radio_dict={
                'State': 'state',
                'Type': 'type',
                'Channe': 'channel_bandwidth',
                'Channel': 'channel',
                'Max': 'max_power',
            }
            for i in range(1,count+1):
                print(f"=== 获取Radio{i}信息 ===")
                cmds=['system-view']
                # 为每个radio创建一个字典
                radio_data = {
                    "aid": self.aid,
                    "rid": i,
                    "type": "Unknown",
                    "state": "Unknown", 
                    "channel_bandwidth": "Unknown",
                    "channel": "Unknown",
                    "max_power": "Unknown",
                }
                cmds.append(f"display wlan radio {i}")
                result = self.shell_command('\n'.join(cmds)+'\n',wait_time=0.2 )
                for key, pattern in search_dict.items():
                    match = re.search(pattern, result)
                    if match:
                        radio_data[h3c_to_radio_dict[key]] = match.group(1).strip()
                    else:
                        radio_data[h3c_to_radio_dict[key]] = "Unknown"
                radio_info.append(radio_data)
            print('radio info:',radio_info)
            return radio_info
        except Exception as e :
            print(f"获取射频信息失败: {str(e)}")
            return radio_info
    
    def get_radio_type(self,radiocount:int)->str:
        try:
            for rid in range(1,radiocount+1):
                result = self.shell_command(f"display wlan radio {rid} | include Type",wait_time=0.3)
                radio_type_matches = re.findall(r'Type\s*:\s*(.+)', result)
                if radio_type_matches:
                    radio_type = radio_type_matches[0]
                    self.radio_type_dict[str(rid)] = radio_type
                    logger.info(f'WlanRadio{rid} type: {radio_type}')
        except Exception as e:
            logger.error(f"获取射频对应类型失败: {str(e)}")
        
    def set_ap(self,config:Dict,action:str):
        try:
            if action == 'add':
                cmds=[
                    'system-view',
                    f'vlan {str(1600+int(config["wid"]))}',
                    f'wlan service-template {config["wid"]}',
                    'undo service-template enable',
                    f'vlan {str(1600+int(config["wid"]))}',
                ]
            else:
                cmds=[
                    'system-view',
                    f'wlan service-template {config["wid"]}',
                    'undo service-template enable'
                ]
            if config.get("ssid"):
                cmds.append(f"ssid {config['ssid']}")

            if config.get("ssid_hide"):
                if config['ssid_hide'] == "Enabled":
                    cmds.append(f"beacon ssid-hide")
                else:
                    cmds.append(f"undo beacon ssid-hide")

            if config.get('user_isolation'):
                if config['user_isolation'] == "Enabled":
                    cmds.append(f"user-isolation enable")
                else:
                    cmds.append(f"undo user-isolation enable")

            if config.get('wifipassword'):
                if config['wifipassword'] != "":
                    cmds.append(f"akm mode psk")
                    cmds.append(f"preshared-key pass-phrase simple {config['wifipassword']}")
                    cmds.append(f"cipher-suite ccmp")
                    cmds.append(f"security-ie rsn")
            cmds.append('service-template enable')
            cmds.append('quit')
            if config.get('radio_bind') and len(config['radio_bind']) > 0:
                radio_bind=config['radio_bind'][0]
                radio_rid=radio_bind.split('(')[1].split(')')[0]
                cmds.append(f'interface WLAN-Radio 1/0/{radio_rid}')
                cmds.append(f'service-template {config["wid"]}')
                cmds.append('undo shutdown')
            self.shell.send('\n'.join(cmds)+'\n')
            logger.info(f'cmds:{cmds}')
            return {'success':True,'msg':f'WIFI-{config["wid"]}-{action}成功'}
        except Exception as e:
            return {'success':False,'msg':f'WIFI-{config["wid"]}-{action}失败: {str(e)}'}

    def del_wifi(self,wifi_list:List):
        try:
            radio_count=self.get_radio_count(use_cache=False)
            cmds=['system-view']
            for i in range(1,radio_count+1):
                cmds.append(f'interface WLAN-Radio 1/0/{i}')
                for wifi in wifi_list:
                    cmds.append(f'undo service-template {wifi}')
            cmds.append('exit')
            # self.shell.send('\n'.join(cmds)+'\n')
            # self.shell_command('exit',wait_time=0.2)
            for wifi in wifi_list:
                cmds.append(
                    f"undo wlan service-template {wifi}",
                )
                if int(wifi) < 200:
                    cmds.append(f'undo vlan {str(1600+int(wifi))}')
            self.shell.send('\n'.join(cmds)+'\n')
            exist_wifi=self.get_wifi_count()
            logger.info(f"del_wifi-----cmds:{cmds}")
            union_wifi=[x for x in wifi_list if x in exist_wifi] 
            if len(union_wifi) > 0:
                return {'success':False,'msg':f'删除WIFI失败,仍存在未删除的WIFI:{union_wifi}','union_wifi':union_wifi,'exit_wifi':exist_wifi}
            else:
                return {'success':True,'msg':f'删除WIFI{wifi_list}成功'}
        except Exception as e:
            logger.error(f"删除WIFI失败: {str(e)}")
            return {'success':False,'msg':f'删除WIFI失败: {str(e)}'}

    def set_vlan_tagged(self):
        try:
            cmds=[
                'system-view'
            ]
            wifi_list=self.get_wifi_count()
            vlan_max=max([int(x) for x in wifi_list if int(x) < 200])+1600
            logger.info(f"vlan_max:{vlan_max}")
            for port in self.physical_port_list:
                cmds.append(f'interface {port}')
                cmds.append('undo shutdown')
                cmds.append('undo port link-type')
                cmds.append('port link-type hybrid')
                cmds.append(f'port hybrid vlan 1601 to {vlan_max} tagged')
            # logger.info(f"set_vlan_tagged cmds:{cmds}")
            self.shell_command('\n'.join(cmds)+'\n')
            # logger.info(f"result:{result}")
            return {'success':True,'msg':f'设置物理端口为tagged成功'}
        except Exception as e:
            logger.error(f"设置物理端口为tagged失败: {str(e)}")
            return {'success':False,'msg':f'设置物理端口为tagged失败: {str(e)}'}

    def get_physical_port(self):
        try:
            self.shell_command("system-view")
            out = self.shell_command("display interface brief description",wait_time=1)
            regx=r'(?:XGE|SGE|GE)\d+\/\d+\/\d+'
            physical_port_list = re.findall(regx, out)
            logger.info(f"physical_port_list:{physical_port_list}")
            self.physical_port_list = physical_port_list
            return self.physical_port_list
        except Exception as e:
            logger.error(f"获取物理端口失败: {str(e)}")
            return []

    def get_wifi_count(self):
        """
        通过查看当前配置来获取WiFi数量（备用方法）
        """
        try:
            result = self.shell_command("display wlan service-template ver | include name",wait_time=4)
            # logger.info(f"=== display wlan service-template ver | include name 输出===")
            # logger.info(result)
            # logger.info("=" * 50)
            # 查找所有wlan service-template配置
            template_pattern = r'Service template name\W+(\d+)'
            template_matches = re.findall(template_pattern, result)
            logger.info(f"找到的service-template: {sorted(template_matches)}")
            # logger.info(f"WiFi数量: {len(template_matches)}")
            return template_matches
        except Exception as e:
            logger.info(f"获取WiFi数量失败: {str(e)}")
            return 0

    def get_radio_count(self, use_cache: bool = True):
        try:
            if use_cache and self._radio_count:
                logging.info(f'use cache radio count:{self._radio_count}')
                return self._radio_count
            self.shell_command("system-view")
            result = self.shell_command(
                "display current-configuration interface WLAN-Radio",
                wait_time=1,
            )
            count = re.findall(r'interface WLAN-Radio(.+)', result)
            logging.info(f'radio count:{count},len:{len(count)}')
            self._radio_count = len(count)
            return self._radio_count
        except Exception as e:
            logging.error(f"获取Radio数量失败: {str(e)}")
            return 0
        
    def set_radio_manage(self,rid:int,wid:list,wifi_count:list):
        def cmd(rid,wid:list):
            cmds=['system-view',f'interface WLAN-Radio 1/0/{rid}']
            wid=[int(w) for w in wid]
            for w in wifi_count:
                if int(w) not in wid:
                    cmds.append(f'undo service-template {w}')
                else:
                    cmds.append(f'service-template {w}')
            cmds.append('quit')
            return cmds
        try:
            shell_cmd=cmd(rid,wid)
            logger.info(f'set_radio_manage cmds:{shell_cmd}')
            self.shell.send('\n'.join(shell_cmd)+'\n')
            return {'success':True,'rid':rid,'action':'bind','msg':f'绑定wifi{wid}成功！'}
        except Exception as e:
            return {'success':False,'rid':rid,'msg':f"绑定wifi{wid}失败: {str(e)}","action":"bind"}

    def get_channel_bandwidth_info(self,rid:int):
        try:
            cmds=[
                'system-view',
                f'interface WLAN-Radio 1/0/{rid}',
            ]
            self.shell.send('\n'.join(cmds)+'\n')
            result = self.shell_command("channel ?",wait_time=0.2)
            channel_list=re.findall(r'(\s\d{1,})', result)
            channel_list=[i.strip(' ') for i in channel_list]
            print('channel_list:',channel_list)
            result = self.shell_command("channel band-width ?",wait_time=0.2)
            bandwidth_list = re.findall(r'(\s\d{1,}\sMHz)', result)
            print('bandwidth_list:',bandwidth_list)
            self.shell_command('quit',is_output=False)
            channel_list.append('auto')
            return channel_list,bandwidth_list
        except Exception as e:
            print(f"获取信道信息失败: {str(e)}")
            return []

    def get_all_channel_bandwidth(self):
        try:
            rid_count=self.get_radio_count(use_cache=False)
            info_list=[]
            for i in range(1,rid_count+1):
                result=self.shell_command(f'dis wlan radio {i} | include Type',wait_time=0.4)
                type_rid=re.findall(r'Type\s+:.+\((.+)\)',result)[0]
                logger.info(f'type_rid:{type_rid}')
                result=self.get_channel_bandwidth_info(i)
                rid_dict={
                    'rid':i,
                    'type':type_rid,
                    'channel':result[0],
                    'bandwidth':result[1]
                }
                info_list.append(rid_dict)
            return {'success':True,'msg':info_list}
        except Exception as e:
            print(f'获取全部信道带宽出错:{e}')
            return {'success':False,'msg':f'获取带宽信道信息出错：{e}'}

    
    def set_channel(self,rid:int,channel:str):
        try:
            # if channel == 'auto':
            #     pass
            # else:
            #     channel=channel
            cmds=[
                'system-view',
                f'interface WLAN-Radio 1/0/{rid}',
                f'channel {channel}',
                'quit',
            ]
            result=self.shell.send('\n'.join(cmds)+'\n')
            logger.info(f'result:{result}')
            if result:
                return {'success':True,'msg':f'设置信道{channel}成功！'}
            else:
                return {'success':False,'msg':f'设置信道{channel}失败！'}
            # result=self.shell_command(f'display wlan radio {rid} | include Channel',wait_time=0.6)
            # rematch=re.findall(r'Channel\s+:.(\d*)',result)[0]
            # logger.info(f'rematch:{rematch}')
            # if rematch == channel:
            #     return {'success':True,'msg':f'设置信道{channel}成功！'}
            # else:
            #     return {'success':False,'msg':f'设置信道{channel}失败！'}   
        except Exception as e:
            return {'success':False,'msg':f'设置射频{rid}信道出错：{e}'}

    def set_bandwidth(self,rid:int,bandwidth:int):
        try:
            cmds=[
                'system-view',
                f'interface WLAN-Radio 1/0/{rid}',
                f'channel band-width {bandwidth}',
                'y',
                'quit',
            ]
            self.shell.send('\n'.join(cmds)+'\n')
            return {'success':True,'msg':'设置带宽成功！'}
        except Exception as e:
            return {'success':False,'msg':e}

    def set_radio_status(self,rid:int,status:int):
        try:
            status_dict={
                1: 'Up',
                0: 'Down',
            }
            cmds=[
                'system-view',
                f'interface WLAN-Radio 1/0/{rid}',
                'undo shutdown' if status == 1 else 'shutdown',
                'quit',
            ]
            self.shell.send('\n'.join(cmds)+'\n')
            # time.sleep(0.3)
            # result=self.shell_command(f'display wlan radio {rid} | include State',wait_time=0.4)
            # logger.info(f'result:{result}')
            # rematch=re.findall(r'State\s+:.(\w*)',result)[0]
            # if rematch == status_dict[status]:
            return {'success':True,'rid':rid,'action':'status','msg':f'设置射频{status_dict[status]}状态成功！'}
        except Exception as e:
            return {'success':False,'rid':rid,'msg':f'设置射频{status_dict[status]}状态出错：{e}','action':'status'}

    def set_max_power(self,rid:int,power:int):
        try:
            cmds=[
                'system-view',
                f'interface WLAN-Radio 1/0/{rid}',
                f'max-power {power}',
                'quit',
            ]
            self.shell.send('\n'.join(cmds)+'\n')
            return {'success':True,'msg':f'设置频率{rid}最大功率{power}成功！'}
        except Exception as e:
            return {'success':False,'msg':f'设置频率{rid}最大功率{power}出错：{e}'}

if __name__ == "__main__":
# #     search_dict={
# #     'SSID': r'SSID\s*:\s*(.+)',
# #     'SSID-hide': r'SSID-hide\s*:\s*(.+)',
# #     'User-isolation': r'User-isolation\s*:\s*(.+)',
# #     'Service': r'Service template status\s*:\s*(.+)',
# # }
    ap_manager = H3CAPManager(1)
# #     con=ap_manager.connect()
# #     if con:
# #         cmds=[
# #             f"display wlan service-template 1 ver | include {key}" for key in search_dict.keys() 
# #         ]
# #         ap_manager.shell.send('\n'.join(cmds)+'\n')
# #         chunk = ap_manager.shell.recv(8192).decode("utf-8", errors="ignore")
# #         print(chunk)
# #     else:
# #         print('连接失败')
    ap_manager.connect()
#     physical_port_list = ap_manager.get_physical_port()
#     ap_manager.set_vlan_tagged(physical_port_list)
# #     print(f"physical_port_list:{physical_port_list}")
    wifi_count=ap_manager.get_wifi_count()
    # logger.info(f"wifi_count:{wifi_count}")
    wifi_info_list=ap_manager.get_allwifi_info(wifi_count)
    # logger.info(f"wifi_info_list:{wifi_info_list}")
    ap_manager.disconnect()