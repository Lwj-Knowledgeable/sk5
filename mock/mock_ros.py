"""模拟 mikrotik_connection，返回固定结构数据"""
import random

class MockMikrotikConnection:
    def __init__(self):
        self.hmpb=False

    def __call__(self, cmd=None, **kwargs):
        cmd = cmd or ''
        if 'bridge/port/print' in cmd:
            return iter([{'interface': 'ether1'}, {'interface': 'ether2'}])
        if 'interface/print' in cmd:
            return iter([
                {'name': 'ether1', 'type': 'ether', 'running': 'true', 'disabled': 'false',
                 'rx-byte': '1000', 'tx-byte': '2000', '.id': '*1'},
                {'name': 'ether2', 'type': 'ether', 'running': 'true', 'disabled': 'false',
                 'rx-byte': '3000', 'tx-byte': '4000', '.id': '*2'},
            ])
        if 'dhcp-client/print' in cmd:
            return iter([{'.id': '*1', 'interface': 'ether1', 'disabled': 'false'}])
        if 'address/print' in cmd:
            return iter([{'.id': '*1', 'interface': 'ether1', 'address': '192.168.1.2/24',
                          'network': '192.168.1.1', 'comment': 'ether1', 'disabled': 'false'}])
        if 'pppoe-client/print' in cmd:
            return iter([])
        if 'route/print' in cmd:
            return iter([{'.id': '*1', 'comment': 'ether1', 'gateway': '192.168.1.1'}])
        if 'scheduler/print' in cmd:
            return iter([{'name': 'pcc', 'disabled': 'false'}])
        if 'script/run' in cmd:
            return iter([{'status': 'ok'}])
        return iter([])


    def hmpb_status(self):
        return self.hmpb

    def set_hmpb_status(self,status):
        self.hmpb=status
        return True

    def qhbd(self):
        return True

    def city_delay(self,data):
        for proxy in data:
            proxy['delay'] = random.randint(30, 300)
        return data

    def get_iprule_proxy_status(self,data):
        for rule in data:
            rule['api']=False
        return data

    def set_iprule_proxy(self,data):
        for rule in data:
            rule['api']=False
        return data

    def set_iprule_local(self,data):
        for rule in data:
            rule['api']=True
        return data

    def balance_port(self):
        balance_port=[
    {
      "balance": True,
      "dhcp": {
        "len": 1,
        "msg": "dhcp获取成功",
        "status": "enabled",
        "success": True
      },
      "disabled": False,
      "down": 0,
      "id": 1,
      "interface": "ether1",
      "mid": "*2",
      "ppoe": {
        "interface": "ether1",
        "len": 1,
        "msg": "success",
        "pd": 1,
        "status": "disabled",
        "success": True,
        "user": 1
      },
      "running": False,
      "static_ip": {
        "gateway": "192.168.1.16",
        "ip": "192.168.1.18",
        "len": 1,
        "msg": "获取静态ip状态成功",
        "status": "disabled",
        "success": True
      },
      "type": "WAN",
      "up": 0
    },
    {
      "balance": True,
      "dhcp": {
        "len": 1,
        "msg": "dhcp获取成功",
        "status": "enabled",
        "success": True
      },
      "disabled": False,
      "down": 1582125,
      "id": 2,
      "interface": "ether2",
      "mid": "*3",
      "ppoe": {
        "interface": "ether2",
        "len": 1,
        "msg": "success",
        "pd": "",
        "status": "disabled",
        "success": True,
        "user": ""
      },
      "running": True,
      "static_ip": {
        "gateway": "",
        "ip": "",
        "len": 0,
        "msg": "获取静态ip状态失败，请检查函数是否正常",
        "status": "disabled",
        "success": False
      },
      "type": "WAN",
      "up": 1505642
    },
    {
      "balance": True,
      "dhcp": {
        "len": 0,
        "msg": "未找到对应的端口dhcp",
        "status": "disabled",
        "success": True
      },
      "disabled": False,
      "down": 0,
      "id": 3,
      "interface": "ether3",
      "mid": "*4",
      "ppoe": {
        "interface": "ether3",
        "len": 1,
        "msg": "success",
        "pd": 13,
        "status": "disabled",
        "success": True,
        "user": 21131313
      },
      "running": False,
      "static_ip": {
        "gateway": "192.168.33.254",
        "ip": "192.168.33.1",
        "len": 1,
        "msg": "获取静态ip状态成功",
        "status": "disabled",
        "success": True
      },
      "type": "WAN",
      "up": 0
    },
    {
      "balance": False,
      "disabled": False,
      "down": 11783888,
      "id": 4,
      "interface": "ether4",
      "mid": "*5",
      "running": True,
      "type": "LAN",
      "up": 3798402
    }
  ]
        return balance_port

    def mock_get_script(self):
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
        data=[]
        for key,value in scriptdescription.items():
            data.append({
                'id':key,
                'name':value['name'],
                'description':value['description'],
                'parentid':value['parentid'],
                'paramIs':value['paramIs']
            })
        return data
    def close(self):
        pass