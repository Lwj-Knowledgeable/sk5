from ros import mikrotik_connection
import json
import time,logging,re
from flask import current_app
logger=logging.getLogger(__name__)
def API():
    api = mikrotik_connection()
    return api

def get_port_info():
    conn = mikrotik_connection()
    portdict=[]
    try:
        query = list(conn(cmd="/interface/print"))
        
        j=0
        for i in query:
            if i['type']=='ether':
                j+=1
                portdict.append({
                    "id":j,
                    "interface":i["name"],
                    "running":i["running"],
                    "disabled":i['disabled'],
                    "up":i['rx-byte'],
                    "down":i['tx-byte'],
                    "type":i['type'],
                    "mid":i['.id']
                })
        logger.info(portdict)
        return portdict
    except Exception as e:
        logger.error(f"获取端口信息失败: {str(e)}")
        return []
    finally:
        conn.close()

def set_port_status(name, status):
    conn = mikrotik_connection()
    try:
        # 先检查端口当前状态
        logger.info(f"=== 操作前检查端口 {name} 状态 ===")
        interfaces = list(conn(cmd="/interface/print"))
        target_interface = None
        for interface in interfaces:
            if interface['name'] == name:
                target_interface = interface
                logger.info(f"端口 {name} 当前状态: 运行={interface['running']}, 禁用={interface['disabled']}")
                break
        
        if not target_interface:
            logger.error(f"未找到端口 {name}")
            return {"success": False, "msg": f"未找到端口 {name}"}
        
        # 使用正确的 set 命令格式
        logger.info(f"\n=== 尝试{status}端口 ===")
        if status == "disable":
            set_cmd = f"/interface/disable"
        else:
            set_cmd=f"/interface/enable"

        logger.info(f"执行命令: {set_cmd}")
        result = list(conn(cmd=set_cmd,numbers=target_interface['name']))
        logger.info(f"命令结果: {result}")
        
        time.sleep(2)
        
        # 检查最终状态
        logger.info(f"\n=== 操作后检查端口 {name} 状态 ===")
        interfaces = list(conn(cmd="/interface/print"))
        for interface in interfaces:
            if interface['name'] == name:
                logger.info(f"端口 {name} 当前状态: 运行={interface['running']}, 禁用={interface['disabled']}")
                break
        
        return {"success": True, "msg": f"端口 {name} {status} 操作完成"}
        
    except Exception as e:
        logger.error(f"错误详情: {str(e)}")
        return {"success": False, "msg": f"设置端口状态失败: {str(e)}"}
    finally:
        conn.close()

class NetBalance():
        
    def get_netbalance(self):
        try:
            api=API()
            result=api(cmd=f'/interface/bridge/port/print')
            return {'success':True,'data':list(result)} 
        except Exception as e:
            logger.error(f'获取负载均衡失败: {e}')
            return {'success':False,'msg':str(e)}
        finally:
            if api:
                api.close()
    
    def add_bridge(self,data):
        """
        data={
            'bridge':'bridge',
            'interface':interface,
        }
        """
        try:
            api=API()
            data1={
                'interface':data['interface'],
                'bridge':'bridge',
            }
            result=list(api(cmd=f'/interface/bridge/port/add', **data1))
            return {'success':True,'msg':'网桥添加成功'}
        except Exception as e:
            logger.error(f'添加网桥失败：{e}')
            return {'success':False,'msg':f'添加网桥失败：{e}'}
        finally:
            if api:
                api.close()

    def rm_bridge(self,data):
        """
        data={
            '.id':id,
        }
        """
        try:
            api=API()
            interface_id_result=api('/interface/bridge/port/print')
            interface_id=[i['.id'] for i in list(interface_id_result) if i['interface'] == data['interface']][0]
            result=list(api(cmd=f'/interface/bridge/port/remove', **{'numbers':interface_id}))
            # print(f"接口 '{data1['interface']}' 已成功从网桥中移除")
            # print(f"result:{json.dumps(list(result),indent=4)}")
            return {'success':True,'msg':'网桥移除成功'}
        except Exception as e:
            logger.error(f'移除网桥失败：{e}')
            return {'success':False,'msg':f'移除网桥失败：{e}'}
        finally:
            if api:
                api.close()

    def add_DHCP(self,data):
        """
        data={
            'interface':interface,
            '.....':.....,
        }
        """
        try:
            api=API()
            data1={
                'interface':data['interface']
            }
            data1['comment']='pcc'
            data1['use-peer-dns']=False
            # result1=self.get_dhcp(data['interface'])
            # print(result1)
            # result1=[i for i in result1[0] if i.get('comment',None) == 'pcc']
            # if result1[1] and len(result1[0]) >= 1:
            #     return {'success':True,'msg':'DHCP已存在，无需创建'}
            # else:
            result=list(api(cmd=f'/ip/dhcp-client/add', **data1))
            return {'success':True,'msg':result}
        except Exception as e:
            logger.error(f'创建DHCP失败：{e}')
            return {'success':False,'msg':f'创建DHCP失败：{str(e)}'}
        finally:
            if api:
                api.close()
    
    def rm_DHCP(self,data):
        """
        data={
            'interface':interface,
        }
        """
        try:
            api=API()
            interface_id_result=api('/ip/dhcp-client/print')
            interface_id=[i['.id'] for i in list(interface_id_result) if i['interface'] == data['interface']][0]
            result=api(cmd='/ip/dhcp-client/remove', numbers=interface_id)
            # print(f"接口 '{data1['interface']}' 已成功移除DHCP")
            # print(f"result:{json.dumps(list(result),indent=4)}")
            return {'success':True,'msg':list(result)}
        except Exception as e:
            logger.error(f'移除DHCP失败：{e}')
            return {'success':False,'msg':f'移除DHCP失败：{str(e)}'}
        finally:
            if api:
                api.close()
    
    def set_netbalance(self,data):
        """
        data={
            'interface':interface,
        }
        """
        try:
            if data['balance']:
                bridge_result=self.rm_bridge(data)
                dhcp_add_result=self.add_DHCP(data)
                route_result=self.set_route_status(data['interface'],'disable')
                static_ip_result=self.set_static_ip_status(data['interface'],'disable')
                ppoe_result=self.set_ppoe_status(data['interface'],'disable')
                results=[('网桥删除',bridge_result)]
            else:
                bridge_result=self.add_bridge(data)
                dhcp_rm_result=self.rm_DHCP(data)
                route_result=self.set_route_status(data['interface'],'disable')
                ppoe_result=self.set_ppoe_status(data['interface'],'disable')
                static_ip_result=self.set_static_ip_status(data['interface'],'disable')
                results=[('网桥添加',bridge_result)]
            # 用 .get 取值，避免子结果缺少 success/msg 字段时抛 KeyError
            failed=[f'{name}失败：{res.get("msg","未知错误")}' for name,res in results if not res.get('success')]
            if not failed:
                return {'success':True,'msg':'开启成功' if data['balance'] else '关闭成功'}
            return {'success':False,'msg':','.join(failed)}
        except Exception as e:
            logger.error(f'设置负载均衡失败：{e}')
            return {'success':False,'msg':str(e)}

    def get_port_dhcp(self):
        try:
            api=API()
            result=api('/interface/bridge/port/print')
            portlist=[i['interface']for i in list(result)]
            port_dict=get_port_info()
            for i in port_dict:
                if i['interface'] not in portlist:
                    i['balance']=True
                    i['type']='WAN'
                    ppoe_result=self.get_ppoe(i['interface'])
                    if ppoe_result:
                        i['ppoe']=ppoe_result
                    else:
                        i['ppoe']={
                            'status':'disabled',
                            'user':'',
                            'pd':'',
                            'msg':'获取ppoe状态失败，请检查函数是否正常',
                            'success':False,
                            'len':0,
                        }
                    dhcp_result=self.get_dhcp(i['interface'])
                    # print(dhcp_result,len(dhcp_result))
                    if dhcp_result[1] and len(dhcp_result[0]) == 1:
                        i['dhcp']={
                            'status':'disabled' if dhcp_result[0][0]['disabled'] else 'enabled',
                            'msg':'获取成功',
                            'success':True,
                            'len':len(dhcp_result[0]),
                        }
                    elif dhcp_result[1] and len(dhcp_result[0]) > 1:
                        i['dhcp']={
                            'status':'disabled',
                            'msg':'该端口多条dhcp记录，请检查winboxs配置是否正确',
                            'success':False,
                            'len':len(dhcp_result[0]),
                        }
                    elif dhcp_result[1] and len(dhcp_result[0]) == 0:
                        i['dhcp']={
                            'status':'disabled',
                            'msg':'未找到对应端口的dhcp',
                            'success':False,
                            'len':len(dhcp_result[0]),
                        }
                    else:
                        i['dhcp']={
                            'msg':'获取dhcp状态失败，请检查函数是否正常',  
                            'status':'disabled',
                            'success':False,
                            'len':0,
                        }
                    static_ip_result=self.get_static_ip(i['interface'])
                    static_ip=[i for i in static_ip_result[0] if i.get('comment',None) == i['interface']]
                    if static_ip_result[1] and len(static_ip) == 1:
                        i['static_ip']={
                            'status':'disabled' if static_ip[0]['disabled'] else 'enabled',
                            'msg':'获取成功',
                            'success':True,
                            'ip':static_ip[0]['address'].split('/')[0],
                            'gateway':static_ip[0]['network'],
                            'len':len(static_ip),
                        }
                    elif static_ip_result[1] and len(static_ip_result[0]) > 1:
                        i['static_ip']={
                            'status':'disabled',
                            'msg':'该端口多条静态ip记录，请检查winboxs配置是否正确',
                            'success':False,
                            'ip':'',
                            'gateway':'',
                            'len':len(static_ip),
                        }
                    elif static_ip_result[1] and len(static_ip_result[0]) == 0:
                        i['static_ip']={
                            'status':'disabled',
                            'msg':'未找到对应端口的静态ip',
                            'success':False ,
                            'ip':'',
                            'gateway':'',
                            # 'network':'',
                            'len':len(static_ip),
                        }
                    else:
                        i['static_ip']={
                            'msg':'获取静态ip状态失败，请检查函数是否正常',
                            'status':'disabled',
                            'success':False,
                            'ip':'',
                            'gateway':'',
                            # 'network':'',
                            'len':0,
                        }
                else:
                    i['balance']=False
                    i['type']='LAN'
            return {'success':True,'data':port_dict}
        except Exception as e:
            logger.error(f'获取端口DHCP信息失败：{e}')
            return {'success':False,'msg':str(e)}
        finally:
            if api:
                api.close()

    def set_ether_status(self,config):
        try:
            api=API()
            result=list(api(cmd=f'/interface/{config["status"]}',**{'numbers':config["interface"]}))
            return {'success':True,'msg':'设置端口状态成功'}
        except Exception as e:
            return {'success':False,'msg':f'设置端口状态失败：{e}'}
        finally:
            if api:
                api.close()

    def run_scheduler(self,status):
        try:
            api=API()
            if status == 1:
                result1=api(cmd=f'/system/script/run', **{'number': 'duoxianfuzai',})
                logger.info(f'开启负载均衡脚本（duoxianfuzai）结果:{list(result1)}')
                time.sleep(1)
                result=list(api(cmd=f'/system/script/run', **{'number': 'pcc_up',}))
                logger.info(f'pcc_up:{type(result)}')
                return {'success':True,'msg':'负载均衡开启成功'}
            if status == 0:
                result=list(api(cmd=f'/system/script/run', **{'number': 'pcc_down',}))
                return {'success':True,'msg':'负载均衡关闭成功'}
            return {'success':False,'msg':'参数错误'}

        except Exception as e:
            logger.error(str(e))
            return {'success':False,'msg':str(e)}
        finally:
            if api:
                api.close() 

    def get_scheduler_status(self):
        try:
            api=API()
            result=api(cmd=f'/system/scheduler/print')
            status=[i['disabled'] for i in list(result) if i['name'] == 'pcc']
            if not status:
                return {'success':False,'msg':'未找到pcc调度器'}
            logger.info(f'status:{status[0]}')
            return {'success':True,'data':status[0]}
        except Exception as e:
            return {'success':False,'msg':f'负载均衡开启失败：{str(e)}'}
        finally:
            if api:
                api.close()

    def set_ppoe_status(self,interface,status):
        try:
            nums=re.findall(r'\d+',interface)
            if nums:
                number=nums[0]
                api=API()
                result=api(cmd=f'/interface/{status}',**{'numbers':f'pppoe-out{number}'})
                result=list(result)
                logger.info(f'设置ppoe状态成功：{result}')
                return {'success':True,'msg':'设置ppoe状态成功'}
            else:
                return {'success':False,'msg':'接口名格式错误'}
        except Exception as e:
            return {'success':False,'msg':f'开启ppoe失败：{e}'}
        finally:
            if api:
                api.close()

    def set_ppoe(self,config):
        '''
        config={
            'interface':interface,
            'ppoe_user':ppoe_user,
            'ppoe_pd':ppoe_pd,
        }
        '''
        try:
            nums=re.findall(r'\d+',config['interface'])
            if nums:
                number=nums[0]
                api=API()
                result=api(cmd='/interface/pppoe-client/set',**{'user':config['ppoe_user'],'password':config['ppoe_pd'],'numbers':f'pppoe-out{number}'})
                if list(result):
                    return {'success':True,'msg':'设置ppoe成功'}
                else:
                    return {'success':False,'msg':'设置ppoe失败'}
            else:
                return {'success':False,'msg':'接口名格式错误'}
        except Exception as e:
            return{'success':False,'msg':f'配置ppoe失败：{e}'}
        finally:
            if api:
                api.close()
    
    def add_ppoe(self,config):
        try:
            api=API()
            result=api(cmd='/interface/pppoe-client/add',**{'comment':'ADSL_PPOE-Bohao!!','name':config['name'],'interface':config['interface']})
            if list(result):
                return {'success':True,'msg':'添加ppoe成功'}
            else:
                return {'success':False,'msg':'添加ppoe失败'}
        except Exception as e:
            return {'success':False,'msg':f'添加ppoe失败：{e}'}
        finally:
            if api:
                api.close()

    def get_ppoe(self,interface):
        try:
            datadict={
                    'status':'disabled',
                    'user':'',
                    'pd':'',
                    "msg":''
                }
            api=API()
            result=api(cmd='/interface/pppoe-client/print')
            result=[i for i in list(result)]
            # print(f'result:{result}',len(result))
            # print(list(result)[0]['name'],list(result)[0]['interface'])
            rinterface=[i for i in list(result) if str(i['interface']) == str(interface)]
            # print(f'rinterface:{rinterface}')
            if len(rinterface) == 1:
                datadict={
                    'interface':interface,
                    'status':'disabled' if rinterface[0]['disabled'] else 'enabled',
                    'user':rinterface[0]['user'],
                    'pd':rinterface[0]['password'],
                    'msg':'success',
                    'success':True,
                    'len':len(rinterface),
                }
            elif len(rinterface) > 1:
                datadict={
                    'interface':interface,
                    'status':'disabled',
                    'user':'',
                    'pd':'',
                    'msg':'该端口多条ppoe记录，请检查winboxs配置是否正确',
                    'success':False,
                    'len':len(rinterface),
                }
            else:
                datadict={
                    'interface':interface,
                    'status':'disabled',
                    'user':'',
                    'pd':'',
                    'msg':'未找到对应端口的ppoe',
                    'success':False,
                    'len':len(rinterface),
                }
            return datadict
        except Exception as e:
            logger.error(f'获取ppoe状态失败：{e}')
            datadict['msg']=f'获取ppoe状态失败：{e}'
            datadict['success']=False
            datadict['len']=0
            return datadict
        finally:
            if api:
                api.close()

    def get_dhcp(self,interface):
        try:
            api=API()
            result=api(cmd=f'/ip/dhcp-client/print')
            result=[i for i in list(result)if i['interface'] == interface]
            return result,True
        except Exception as e:
            logger.error(f'获取dhcp状态失败：{e}')
            return [],False
        finally:
            if api:
                api.close()
    
    def get_static_ip(self,interface):
        try:
            api=API()
            result=api(cmd=f'/ip/address/print')
            result=[i for i in list(result) if i['interface'] == interface]
            return result,True
        except Exception as e:
            logger.error(f'获取ip地址失败：{e}')
            return [],False
        finally:
            if api:
                api.close()

    def set_static_ip_status(self,interface,status):
        try:
            api=API()
            result=self.get_static_ip(interface)[0]
            result=[i for i in result if i.get('comment',None) == interface]
            if len(result) == 0:
                return {'success':False,'msg':f'未找到对应端口{interface}的静态ip'}
            # print(result)
            logger.info('设置静态ip状态成功')
            result=list(api(cmd=f'/ip/address/{status}',numbers=result[0]['.id']))
            return {'success':True,'msg':'设置静态ip状态成功'}
        except Exception as e:
            logger.error(f'设置静态ip状态失败：{e}')
            return {'success':False,'msg':f'设置静态ip状态失败：{e}'}
        finally:
            if api:
                api.close()

    def set_static_ip(self,data):
        try:
            api=API()
            static_ip_result=self.get_static_ip(data['interface'])[0]
            static_ip_result=[i for i in static_ip_result if i.get('comment',None) == data['interface']][0]
            result=list(api(cmd=f'/ip/address/set',**{'interface':data['interface'],'address':data['ip'],'network':data['gateway'],'numbers':static_ip_result['.id']}))
            logger.info('设置静态ip成功')
            return True
        except Exception as e:
            logger.error(f'设置静态ip失败：{e}')
            return False
        finally:
            if api:
                api.close()

    def set_dhcp_status(self,interface,status):
        try:
            api=API()
            result=self.get_dhcp(interface)
            # print(result[0])
            if result[1] and len(result[0]) == 1:
                dhcp_id=result[0][0]['.id']
                # print(dhcp_id)
                result=list(api(cmd=f'/ip/dhcp-client/{status}',numbers=dhcp_id))
                logger.info('设置dhcp状态成功')
                return {'success':True,'msg':'设置dhcp状态成功'}
            else:
                return {'success':False,'msg':f'设置dhcp状态失败,{interface}端口dhcp配置不正确'}
        except Exception as e:
            logger.error(f'设置dhcp状态失败：{e}')
            return {'success':False,'msg':f'设置dhcp状态失败：{e}'}
        finally:
            if api:
                api.close()

    def get_route(slef):
        try:
            api=API()
            result=api(cmd=f'/ip/route/print')
            result=[i for i in list(result)]
            return result
        except Exception as e:
            logger.error(f'获取路由失败：{e}')
            return []
        finally:
            if api:
                api.close()

    def set_route_status(self,interface,status):
        try:
            api=API()
            result=self.get_route()
            ether_result=[i['.id'] for i in result if i.get('comment',None) == f'{interface}']
            if len(ether_result) == 0:
                return {'success':False,'msg':f'未找到对应端口{interface}的路由'}
            result=list(api(cmd=f'/ip/route/{status}',numbers=ether_result[0]))
            logger.info('设置路由状态成功')
            return {'success':True,'msg':'设置路由状态成功'}
        except Exception as e:
            logger.error(f'设置路由状态失败：{e}')
            return {'success':False,'msg':f'设置路由状态失败：{e}'}
        finally:
            if api:
                api.close()

    def set_route(self,data):
        """
        data={
            'interface':'ether1',
            'ip':'192.168.1.1/24',
            'gateway':'192.168.1.2',
        }
        """
        try:
            api=API()
            ether_result=self.get_route()
            ether_route=[i for i in ether_result if i.get('comment',None) == f'{data["interface"]}'][0]
            result=list(api(cmd=f'/ip/route/set',**{'gateway':data['gateway'],'numbers':ether_route['.id']}))
            return True
        except Exception as e:
            logger.error(f'设置路由失败：{e}')
            return False,e
    def set_ether_type(self,data):
        try:
            if data['accessType'] == 'dhcp':
                self.set_dhcp_status(data['interface'],'enable')
                self.set_ppoe_status(data['interface'],'disable')
                self.set_static_ip_status(data['interface'],'disable')
                self.set_route_status(data['interface'],'disable')
            elif data['accessType'] == 'ip':
                self.set_static_ip_status(data['interface'],'enable')
                self.set_route_status(data['interface'],'enable')
                self.set_route(data)
                self.set_static_ip(data)
                self.set_ppoe_status(data['interface'],'disable')
                self.set_dhcp_status(data['interface'],'disable')
            elif data['accessType'] == 'ppoe':
                self.set_ppoe_status(data['interface'],'enable')
                self.set_dhcp_status(data['interface'],'disable')
                self.set_static_ip_status(data['interface'],'disable')
                self.set_route_status(data['interface'],'disable')
                self.set_ppoe(data)
            else:
                return {'success':False,'msg':f'未知的接入方式：{data["accessType"]}'}
            return {'success':True,'msg':'设置端口接入方式成功'}
        except Exception as e:
            logger.error(f'设置ether类型失败：{e}')
            return {'success':False,'msg':f'设置ether类型失败：{e}'}

if __name__ == "__main__":
    netbalance=NetBalance()
# #     print(netbalance.get_scheduler_status())
# #     # 尝试禁用端口
# #     # set_port_status("ether1",'enable')
#     # netbalance=NetBalance()
#     # print(netbalance.run_scheduler(0))
# #     print(netbalance.get_port_dhcp())
#     # config={
#     #     'number':'pppoe-out1',
#     #     'status':'disable',
#     #     'user': 'test',
#     #     'pd':'test'
#     # }
    print(netbalance.add_DHCP({'interface':'ether1'}))








