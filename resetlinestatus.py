from librouteros.types import ReplyDict
from librouteros.exceptions import ConnectionClosed, TrapError, FatalError
import json,re,time,threading
from ros import mikrotik_connection
import logging
logger = logging.getLogger(__name__)
def API():
    api = mikrotik_connection()
    return api

def find_rule_by_comment(api,path):
    """根据注释查找规则"""
    nat_rules = api.path(path)
    rules = nat_rules.select('comment','.id','action','src-address')
    return rules

def toggle_rule(api, path, comment, action_type,srcaddr,enable):
    """启用或禁用规则"""
    rules = find_rule_by_comment(api, path)
    if not rules:
        print(f"未找到注释为'{comment}'的规则")
        return False

    filter_rules=[
            rule for rule in rules
            if all(key in rule for key in ('comment', 'action', 'src-address'))
        ]
    # print(filter_rules)
    for rule in filter_rules:
        # print(rule)
        # print(action_type)
        if rule['action'] == action_type and rule['src-address'] == srcaddr and rule['comment'] == comment:
            rule_id = rule['.id']
            print(rule_id)
            action = 'enable' if enable else 'disable'
            result=api(cmd=f'{path}/{action}', **{'.id': rule_id})
            # result=api.path(path).call('set',{'id':rule_id,'disabled':action})
            # print(json.dumps(list(result),indent=4))
            status = "启用" if enable else "禁用"
            logger.info(f"{status}规则 ID: {rule_id}, Comment: {comment},action:{action_type},result:{json.dumps(list(result),indent=4)}") #result必须用print不然命令在winbox没有实现
    
            

def localstatus(id):
    # 连接到MikroTik
    try:
        api = API()
        # 启用或禁用NAT规则
        toggle_rule(api, '/ip/firewall/nat', id,'src-nat',f'10.2.{id}.0/24', enable=False)
        # 启用或禁用Mangle规则
        toggle_rule(api, '/ip/firewall/mangle', id,'mark-routing',f'10.2.{id}.0/24', enable=False)
        return True
    except Exception as e:
        logger.error('切换本地出错',e)
        return False
    finally:
        if api:
            api.close()
            logger.info("已断开与MikroTik路由器的连接")

def proxystatus(id):
    # 连接到MikroTik
    try:
        api = API()
        # 启用或禁用NAT规则
        toggle_rule(api, '/ip/firewall/nat', id,'src-nat',f'10.2.{id}.0/24', enable=True)
        # 启用或禁用Mangle规则
        toggle_rule(api, '/ip/firewall/mangle', id,'mark-routing',f'10.2.{id}.0/24', enable=True)
        return True
    except Exception as e:
        logger.error('切换代理出错',e)
        return False


def setStatus(data):
    try:
        api = API()
        nat_rules = getstatus(api, '/ip/firewall/nat')
        mangle_rules = getstatus(api, '/ip/firewall/mangle')
        # 构建 comment 到 nat_rule 的映射
        nat_comment_map = {str(rule['comment']): rule for rule in nat_rules if 'comment' in rule}
        logger.info('nat_comment_map',nat_comment_map)
        for i in data:
            id = i['id']
            # 如果id和comment相等，则赋值
            if str(id) in nat_comment_map:
                try:
                    i['api'] = nat_comment_map[str(id)]['disabled']
                except Exception as e:
                    # print('设置状态出错',e)
                    i['api'] = False
        return data 
    except Exception as e:
        logger.error('设置状态出错',e)
        return data
    finally:
        if api:
            api.close()

def setlineproxy(data):
    for i in data:
        id=i['id']
        proxystatus(id)

def setlinelocal(data):
    for i in data:
        id=i['id']
        localstatus(id)

def getstatus(api,path):
    # 立即验证修改
    updated_rule = api.path(path).select(
        '.id','disabled','comment'
    )
    updated_rule=[rule for rule in updated_rule]
    # print(updated_rule)
    # print(f"当前状态: {'已启用' if updated_rule == False else '未生效'}")
    return updated_rule

def hmpb(enable):
    try:
        api=API()
        rules = api.path('/ip/firewall/filter').select('.id', 'comment','chain')
        # 找到所有 comment 为 lanjie 的规则
        lanjie_ids = [r['.id'] for r in rules if r.get('chain') == 'lanjie' and 'zhibo' in r.get('comment')]
        action = 'enable' if enable else 'disable'
        for rule_id in lanjie_ids:
            result=api(cmd=f'/ip/firewall/filter/{action}', **{'.id': rule_id})
            logger.info(f"{'启用' if enable else '禁用'}了 {rule_id} comment=lanjie 的规则,result:{json.dumps(list(result),indent=4)}")
        logger.info(f"{'启用' if enable else '禁用'}了 {len(lanjie_ids)} 条 comment=lanjie 的规则")
        return True
    except Exception as e:
        logger.error('画面屏蔽',e)
        return False

def hmpb_status():
    try:
        api=API()
        rules = api.path('/ip/firewall/filter').select('.id', 'comment','chain','disabled')
        # 找到所有 comment 为 lanjie 的规则
        # print(rules)
        # lanjie_ids = [r for r in rules if r.get('chain') == 'lanjie' and 'zhibo' in r.get('comment')]
        # print('lanjie',lanjie_ids)
        # count=sum(1 for item in lanjie_ids if item.get('disabled') is False)
        # print()
        lanjie_id=[r for r in rules if r.get('chain') == 'forward' and 'lanjie' in r.get('comment')]
        if lanjie_id[0]['disabled']:
            return False
        else:
            return True
    except Exception as e:
        logger.error('画面屏蔽状态',e)
        return False


class RouteAP:
    def __init__(self):
        self.lock=threading.Lock()
    # def route_ap(self):
    #     try:
    #         ip=[]
    #         result = self.api(cmd='/ip/firewall/connection/print')
    #         for i in result:
    #             if ('src-address' in i and i['src-address'].startswith('192.168.88.24')) or ('dst-address' in i and i['dst-address'].startswith('192.168.88.24')):
    #                 ap=i['src-address'] if '192.168.88.24' in i['src-address'] else i['dst-address']
    #                 ap=ap.split(':')[0]
    #                 aid=int(re.search(r'192.168.88.24(\d+)', ap).group(1))
    #                 ip.append(aid)
    #         ip=list(set(ip))
    #         print(ip)
    #         return ip
    #     except Exception as e:
    #         print('路由AP',e)
    #         return '获取AP设备列表失败'

    def ping_single(self, ip, api, reachable_devices=None,thread=True):
        """每线程独立 API 连接，真正并行 ping，避免共享连接锁串行化。"""
        try:
            # count=1 + 短 interval，不可达时尽快返回
            ping_args = {
                'address': f'192.168.88.24{ip}',
                'count': '1',
                'interval': '100ms',
            }
            with self.lock:
                result = list(api(cmd='/ping', **ping_args))
            for item in result:
                # logger.info(item)
                if int(item.get('packet-loss', 100)) == 0:
                    # logger.info(f"✓ {ip} 可达")
                    with self.lock:
                        if thread:
                            reachable_devices.append(ip)
                    return True
                # logger.info(f"✗ {ip} 不可达")
                return False
            # logger.info(f"✗ {ip} 不可达")
            return False
        except Exception as e:
            logger.error(f"✗ {ip} 测试失败: {e}")
            return False

    def ping_all_thread(self):
        try:
            api=API()
            start_time = time.time()
            reachable_devices = []
            threads = []
            for i in range(1, 10):
                thread = threading.Thread(
                    target=self.ping_single,
                    args=(i, api, reachable_devices,True),
                )
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            for device in sorted(reachable_devices):
                logger.info(f"AP-PING成功-----------> {device}")
            end_time = time.time()
            logger.info(f"总耗时：{end_time - start_time}秒")
            return reachable_devices
        except Exception as e:
            logger.error('ping_all_thread出错', e)
            return []
        finally:
            if api:
                try:
                    api.close()
                except Exception:
                    pass    
    

class WinScript:
    scriptdescription={
        '01-yijian-BangDing-IP/MAC':
            {
                'description':'一次性绑定所有已连接的设备MAC和IP，无需手动一个个加入静态绑定了',
                'parentid': 1,
                'paramIs':False,
                'name':'一键静态绑定所有设备MAC及IP'
             },
        '02-yijian-zhuanhuan-L2TP':
            {
                'description':'请确认自己IP是否支持L2TP协议,并提前保存好代理线路',
                'parentid':2,
                'paramIs':False,
                'name':'一键转换为L2TP协议'
            },
        '03-yijian-zhuanhuan-PPTP':
            {
                'description':'请确认自己IP是否支持PPTP协议,并提前保存好代理线路',
                'parentid':3,
                'paramIs':False,
                'name':'一键转换为PPTP协议'
            },
        '04-yijian-zou-bendi-kai':
            {
                'description':'所有代理IP线路失效,强制走本地网,请慎重使用此功能,如不明白请咨询技术',
                'parentid':3,
                'paramIs':False,
                'name':'一键切换所有设备使用本地网络'
            },
        '05-yijian-zou-bendi-Guan':
            {
                'description':'切回代理使用IP线路,如不明白请咨询技术',
                'parentid':4,
                'paramIs':False,
                'name':'一键切回代理线路'
            },
        '06-Douyin-Shiping-PingBi':
            {
                'description':'抖音/快手等视频画面屏蔽,不影响点赞,评论,减少网络流量,提升整体网速',
                'parentid':5,
                'paramIs':False,
                'name':'一键抖音/快手等视频画面屏蔽(开)'
            },
        '07-Douyin-Shiping-ZhengChang':
            {
                'description':'恢复正常抖音/快手视频画面',
                'parentid':5,
                
                'paramIs':False,
                'name':'一键关闭抖音/快手视频屏蔽(关)'
            },
        '08-Douyin-Zhibo-HeiPing':
            {
                'description':'抖音/快手等直播画面屏蔽,节约流量提升带机量,不影响点赞,关注,评论,互动,在线数等功能',
                'parentid':6,
                
                'paramIs':False,
                'name':'一键抖音/快手等直播画面屏蔽(开)'
            },
        '09-Douyin-Zhibo-ZhengChang':
            {
                'description':'恢复正常抖音/快手等直播画面',
                'parentid':6,
                
                'paramIs':False,
                'name':'一键关闭抖音/快手等直播画面屏蔽(关)'
            },
        '10-yijian-Huan-IP':
            {
                'description':'一次性重拨所有代理线路(适用于L2TP/PPTP协议)',
                'parentid':7,
                
                'paramIs':False,
                'name':'一键重拨所有L2TP或PPTP代理线路'
            },
        '11-VPN-xianlu-QiYong':
            {
                'description':'一次性启用所有代理线路(适用于L2TP/PPTP协议)',
                'parentid':8,
                
                'paramIs':False,
                'name':'一键启用所有L2TP或PPTP代理线路'
            },
        '12-VPN-xianlu-TingYong':
            {
                'description':'一次性停用所有代理线路(适用于L2TP/PPTP协议)',
                'parentid':9,
                
                'paramIs':False,
                'name':'一键停用所有L2TP或PPTP代理线路'
            },
        '13-Douyin-fenLiu-zoubeidi-Guan':
            {
                'description':'只针对使用代理IP线路生效,智能识别视频直播流量走本地宽带,降低对IP线路的要求',
                'parentid':9,
                
                'paramIs':False,
                'name':'一键切换抖音快手流量走本地'
            },
        '13-Douyin-fenLiu-zoubeidi-Kai':
            {
                'description':'切换抖音快手视频直播流量走回到代理线路',
                'parentid':10,
                
                'paramIs':False,
                'name':'一键切回抖音快手流量走代理'
            },
        '14-L2TP/PPTP-yijian-DaoRu1.4.1':
            {
                'description':'L2TP与PPTP账号批量导入,需搭配脚本参数使用,使用方法需设置脚本参数,不懂请咨询技术(需加一个确认选项}',
                'parentid':11,
                
                'paramIs':True,
                'name':'一键批量导入L2TP与PPTP账号密码'
            },
        '88-yituoN-SD1.5':
            {
                'description':'手动分配代理线路支持L2TP和SK5协议共用,支持AP和交换机链接方式,支持手机和电脑及主板机',
                'parentid':88,
                
                'paramIs':False,
                'name':'手动分配代理线路(一拖几)'
            },
        '98-L2TP-yituoN-ZD1.6':
            {
                'description':'支持设置一拖几自动分配L2TP线路,支持AP和交换机链接如:一个IP带1台输1,带2台输2',
                'parentid':98,
                
                'paramIs':True,
                'name':'自动分配L2TP协议(一拖几)'
            },
        '99-SK5-yituoN-ZD1.6':
            {
                'description':'支持设置一拖几自动分配SK5线路,支持AP和交换机链接方如:一个IP带1台输1,带2台输2',
                'parentid':99,
                
                'paramIs':True,
                'name':'自动分配SK5协议(一拖几)'
            },
    }
    def __init__(self):
        self.lock=threading.Lock()

    def get_script(self):
        try:
            api=API()
            result=api(cmd='/system/script/print')
            result=[i for i in result]
            count=14
            scriptlist=[]
            for i in range(len(result)):
                isNull=self.scriptdescription.get(result[i]['name'],'')
                logger.info(f"{result[i]['name']} isNull:{isNull}")
                if isNull != '':
                    scriptlist.append({
                    'id':result[i]['name'],
                    'name':self.scriptdescription[result[i]['name']].get('name','Null'),
                    'description':self.scriptdescription[result[i]['name']].get('description','Null'),
                    'parentid':self.scriptdescription[result[i]['name']].get('parentid',0),
                    'paramIs':self.scriptdescription[result[i]['name']].get('paramIs',False)
                })
                    
            sorted_scriptlist=sorted(scriptlist,key=lambda x: x['parentid'])
            return {'success':True,'data':sorted_scriptlist}
        except Exception as e:
            logger.error('获取脚本失败',e)
            return {'success':False,'msg':str(e)}
        finally:
            if api:
                api.close()

    def run_script(self,rejson):
        try:
            api=API()
            isparam=rejson['isparam']
            id=rejson['id']
            param=rejson['param'][0]
            logger.info(f'isparam：{isparam},id：{id},param；{param}')
            if isparam:
                logger.info(f'执行脚本参数：{rejson["param"][0]}')
                self.set_note(param,api)
                result=api(cmd=f'/system/script/run', **{'number': id,})
                time.sleep(3)
                logger.info(f'执行脚本结果：{list(result)}')
                return {'success':True,'data':list(result)}
            else:
                logger.info(f'执行脚本没有参数')
                result=api(cmd=f'/system/script/run', **{'number': id})
                time.sleep(1)
                return {'success':True,'data':list(result)}
        except Exception as e:
            logger.error('执行脚本失败',e)
            return {'success':False,'msg':str(e)}
        finally:
            if api:
                api.close()

    def set_note(self,param,api):
        try:
            noteresult=api(cmd='/system/note/set',**{'note':param,})
            time.sleep(0.3)
            logger.info(f'修改note结果：{list(noteresult)}')
        except Exception as e:
            logger.error(f'修改NOTE参数出错：{e}')
        
    def import_script_on_router(self,filename: str):
        """在路由器上导入指定脚本文件 (.rsc)。
        Returns: True/False
        """
        conn = API()
        try:
            conn('/import', **{'file-name': filename})
            return True
        except (TrapError, FatalError, ConnectionClosed) as e:
            raise RuntimeError(f"导入脚本失败: {str(e)}") from e
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def fetch_file_to_router(self,url,dst):
        try:
            api=API()
            result=api(cmd=f'/tool/fetch', **{'url': url,'dst': dst})
            return {'success':True,'data':list(result)}
        except Exception as e:
            logger.error('获取脚本失败',e)
            return {'success':False,'msg':str(e)}
        finally:
            if api:
                api.close()

class L2TP:
    def __init__(self):
        self.l2tp_list=[]

    def get_l2tp_data(self):
        self.l2tp_list=[]
        try:
            api=API()
            result=api(cmd='/interface/l2tp-client/print')
            result=list(result)
            j=0
            # logger.info(f'result:{result}')
            for i in result:
                j+=1
                self.l2tp_list.append({
                    'id':j,
                    'name':i['name'],
                    'user':i['user'],
                    'password':i['password'],
                    'status': True if not i['disabled'] else False,
                    'connect_to':i['connect-to'],
                    'running':i['running'],
                        })
            # logger.info(f'self.l2tp_list:{self.l2tp_list}')
            return {'success':True,'data':self.l2tp_list}
        except Exception as e:
            # print('获取L2TP数据失败',e)
            return {'success':False,'msg':str(e)}
        finally:
            if api:
                api.close()

    def get_l2tp_traffic(self):
        """
        获取 L2TP 客户端接口的实时流量（实时速率）
        使用 RouterOS 的 /interface/monitor-traffic（once 模式）逐个接口采样
        返回: {'success': bool, 'data': [{'interface','running','rx_speed','tx_speed'}], 'msg': str}
        """
        api=API()
        def _get_l2tp_traffic(interface,api):
            try:
                stream = api(cmd='/interface/monitor-traffic',
                                        **{'interface': interface,'once': ''})
                
                for response in stream:
                    # print(f'response:{response}')
                    # response 字典中通常包含 rx-bits-per-second 和 tx-bits-per-second
                    rx_speed = response.get('rx-bits-per-second',None)
                    tx_speed = response.get('tx-bits-per-second',None)
                if rx_speed is not None:
                    return {'success': True, 'data': {'rx_speed': rx_speed, 'tx_speed': tx_speed ,'running': True}}
                else:
                    return {'success': False, 'msg': '获取L2TP流量失败', 'data': {'rx_speed': rx_speed, 'tx_speed': tx_speed ,'running': True}}
            except Exception as e:
                logger.error(f'获取L2TP流量失败: {e}')
                return {'success': False, 'msg': str(e), 'data': []}
        try:
            
            l2tp_list=[]
            l2tp=self.get_l2tp_data()
            # print(f'l2tp:{l2tp}')
            if l2tp['success']:
                for i in l2tp['data']:
                    if i['running']:
                        l2tp_list.append(i['name'])
            else:
                return {'success': False, 'msg': l2tp['msg'], 'data': []}
            # print(f'l2tp_list:{l2tp_list}')
            l2tp_traffic_list=[]
            for interface in l2tp_list:
                result=_get_l2tp_traffic(interface,api)
                if result['success']:
                    l2tp_traffic_list.append({'running': result['data']['running'],'rx_speed': result['data']['rx_speed'], 'tx_speed': result['data']['tx_speed'],'interface':interface})
                else:
                    l2tp_traffic_list.append({'running': True,'rx_speed': 0, 'tx_speed': 0,'interface':interface})

            return {'success': True, 'data': l2tp_traffic_list}

        except Exception as e:
            logger.error(f'获取L2TP流量失败: {e}')
            return {'success': False, 'msg': str(e), 'data': []}
        finally:
            if api:
                try:
                    api.close()
                except Exception:
                    pass


    def set_l2tp(self,config):
        try:
            api=API()
            id=api(cmd='/interface/l2tp-client/print')
            id_=[i for i in id if i['name'] == config['name']][0]['.id']
            logger.info(f'设置L2TP ID：{id_},name：{config["name"]}')
            result=api(cmd='/interface/l2tp-client/set',
                        **{'.id':id_,
                        'user':config['user'],
                        'password':config['password'],
                        'connect-to':config['connect_to']}
            )
            if config['connect_to']!='1.1.1.1':
                config['status']=True
            else:
                config['status']=False
            result1=self.set_l2tp_status(config)
            if result and result1:
                logger.info(f'设置L2TP结果：{list(result)}')
                return True
            else:
                logger.info(f'设置L2TP结果：{list(result)}')
                return False
        except Exception as e:
            logger.error('设置L2TP失败',e)
            return {'success':False,'msg':str(e)}
        finally:
            if api:
                api.close()

    def _get_l2tp_id(self,name):
        try:
            api=API()
            id=api(cmd='/interface/l2tp-client/print')
            id=[i for i in id if i['name'] == name][0]['.id']
            return id
        except Exception as e:
            logger.error('获取L2TP ID失败',e)
            return None
        finally:
            if api:
                api.close()

    def set_l2tp_status(self,config):
        try:
            api=API()
            id=api(cmd='/interface/l2tp-client/print')
            id=[i for i in id if i['name'] == config['name']][0]['.id']
            if config['status']:
                result=api(cmd='/interface/l2tp-client/enable',
                        **{'.id':id}
                )
            else:
                result=api(cmd='/interface/l2tp-client/disable',
                        **{'.id':id})
            result=list(result)
            logger.info(f'result:{result}')
            if result==[]:
                # logging.info(f'设置L2TP状态成功:{list(result)}')
                return True
            else:
                # logging.info(f'设置L2TP状态失败:{list(result)}')
                return False
        except Exception as e:
            logging.error(f'设置L2TP状态失败:{str(e)}')
            return False
        finally:
            if api:
                api.close()
    
if __name__ == '__main__':
# # #     ws=WinScript()
# # #     data={
# # #     "id": "99-SK5-yituoN-ZD1.6",
# # #     "param": ["15"],
# # #     "isparam": True
# # # }
# #     # print(ws.get_script())
# #     # print(ws.run_script(data))
# #     # nb=NetBalance()
# #     # data={
# #     #     'interface':'ether4',
# #     # }
# #     # nb.set_DHCP(data)
# #     # ra=RouteAP()
# #     # ra.ping_all_thread()
    l2tp=L2TP()
#     # data={
#     #     'name':'IP-001',
#     #     'status':False
#     # }
#     # l2tp.set_l2tp_status(data)
#     # data={
#     #     'name':'IP-001',
#     #     'user':'test',
#     #     'password':'test',
#     #     'connect_to':'192.168.1.1'
#     # }
#     # l2tp.set_l2tp(data)
    print(l2tp.get_l2tp_traffic())