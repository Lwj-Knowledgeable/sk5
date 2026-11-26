
from __future__ import annotations
from typing import List, Dict, Optional, Any, Union
import json,re,yaml,subprocess,requests,sys,os,logging
from ros import mikrotik_connection
from contextlib import contextmanager
from datetime import datetime
from flask import current_app, has_app_context
from settings_load import settings
# # 配置 logging 格式
# # 检查是否已经配置过 logging
# if not logging.root.handlers:
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
#         datefmt='%Y-%m-%d %H:%M:%S',
#         handlers=[
#             logging.StreamHandler(sys.stdout)
#         ]
#     )
# else:
#     # 如果已经配置过，更新格式
#     formatter = logging.Formatter(
#         fmt='%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
#         datefmt='%Y-%m-%d %H:%M:%S'
#     )
#     for handler in logging.root.handlers:
#         handler.setFormatter(formatter)
#     logging.root.setLevel(logging.INFO)

# # 创建标准 logger 作为后备
# _standard_logger = logging.getLogger(__name__)
# alipay_domains = ['alipay.com', 'alipayobjects.com','api.mch.weixin.qq.com','api2.mch.weixin.qq.com']
# def get_logger():
#     """
#     安全地获取 logger，支持在 Flask 应用外部使用
#     如果在 Flask 应用上下文中，使用 current_app.logger
#     否则使用标准库的 logging
#     """
#     if has_app_context():
#         try:
#             return current_app.logger
            
#         except RuntimeError:
#             return _standard_logger
#     return _standard_logger

logger=logging.getLogger(__name__)
path = "/root/.config/config.yaml"
if os.path.exists(path):
    pass
else:
    path=settings.CLASH_CONFIG_PATH
# reader_city = geoip2.database.Reader('GeoLite2-City.mmdb')
ip='10.0.0.254'
def restartOpenclash(data=None):
    try:

        headers = {
            'Authorization': 'Bearer Rc3lFJSt',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        params = {
            'force': 'true',
        }

        data = '{"path": "/root/.config/config.yaml", "payload": ""}'

        response = requests.put('http://10.0.0.254:9090/configs', params=params, headers=headers, data=data)
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        if response.status_code == 204:
            return True
        else:
            return False
    except:
        return False



def stopOpenclash():
    subprocess.Popen(
        "/etc/init.d/openclash stop",
        shell=True,
        executable="/bin/sh",  # OpenWrt 默认使用 sh

    )

def openclash_status():
    # 使用 systemctl 检查 OpenClash 状态
    result = subprocess.run(['service', 'openclash', 'status'],
                            stdout=subprocess.PIPE,  # 捕获标准输出
                            stderr=subprocess.PIPE,  # 捕获标准错误
                            text=True # 以文本形式返回输出
) # 检查命令是否成功执行)
    output = result.stdout
    return output


def get_ip_info(ip_address):
    try:
        if ip_address == '1.1.1.1':
            return '无效地址'
        # 调用ip-api.com查询
        url = f"http://opendata.baidu.com/api.php?query={ip_address}&co=&resource_id=6006&t={datetime.now().timestamp()}&ie=utf8&oe=utf-8&format=json"
        # print(url)
        response = requests.get(url)
        data = response.json()
        print(data['data'][0]['location'])
        if data["status"] == '0':
            return data['data'][0]['location']
        else:
            print({"error": data.get("message", "查询失败")})
            return "失败"
    except Exception as e:
        print({"error": str(e)})
        return "失败"

class RuleImportError(Exception):
    pass


class Rule:
    mode: str
    add: str
    path: str
    string: str

    def __init__(self, rule):
        parts = rule.split(",")
        if len(parts) < 3:
            # Handle cases where rule has fewer than 3 parts
            self.mode = parts[0] if len(parts) > 0 else ""
            self.add = parts[1] if len(parts) > 1 else ""
            self.path = parts[2] if len(parts) > 2 else ""
        else:
            self.mode, self.add, self.path = parts[:3]


class IPRule(Rule):
    def __init__(self, rule: str, proxies: list["Proxy"]):
        try:
            super().__init__(rule)
            assert self.mode == "SRC-IP-CIDR"
            # 支持两种格式：
            # 1. 单网段格式：10.0.0.x/32
            # 2. 多网段格式：10.2.x.0/24
            assert (self.add.startswith("10.0.0.") and self.add.endswith("/32")) or \
                   (self.add.startswith("10.0.") and self.add.endswith("/24"))
            assert self.path.startswith("Name")
            self.proxy = self.findProxy(proxies)
            # 检测并存储网段类型
            self.is_single_segment = self.add.endswith("/32")
        except Exception as e:
            print(f"IPRule出错{e}")
            raise RuleImportError

    def findProxy(self, proxies: list["Proxy"]):
        targetId = self.id
        for proxy in proxies:
            if proxy.id == targetId:
                return proxy
        return None

    @property
    def dict(self):
        data = {
            "id": self.id,
            "localAddr": self.add,
            "api": "",  # TODO
            "api_status":False,
        }
        if self.proxy:
            data.update({
                "proxyType": self.proxy.type,
                "address": self.proxy.address,
                "port": self.proxy.port,
                "user": self.proxy.user,
                "pass": self.proxy.passwd,
                "vmessId": self.proxy.alterId,
                "sslType": self.proxy.cipher,
                "area": self.proxy.area,
                "delay": self.proxy.delay,
            })
        return data

    @property
    def id(self):
        parts = self.add.split(".")
        if '/32' in parts[3]:
            return int(parts[3].split("/")[0])
        else:
            return int(parts[2])

    @property
    def string(self):
        if self.is_single_segment:
            # 单网段格式：10.0.0.x/32
            return f"SRC-IP-CIDR,10.0.0.{self.id}/32,Name{self.id}"
        else:
            # 多网段格式：10.0.x.0/24
            return f"SRC-IP-CIDR,10.0.{self.id}.0/24,Name{self.id}"

    def __str__(self):
        if self.is_single_segment:
            # 单网段格式：10.0.0.x/32
            return f"SRC-IP-CIDR,10.0.0.{self.id}/32,Name{self.id}"
        else:
            # 多网段格式：10.0.x.0/24
            return f"SRC-IP-CIDR,10.0.{self.id}.0/24,Name{self.id}"


class OtherRules(Rule):
    def __init__(self, rule: str):
        super().__init__(rule)

    @property
    def string(self):
        return ",".join([
            self.mode,
            self.add,
            self.path
        ])


class Proxy:
    name: str  # Name12
    id: int  # 12
    type: str  # socket5
    address: str  # "1.1.1.1"
    port: int  # 1080
    user: str  # ""
    passwd: str  # ""
    udp: bool  # True
    uuid: str  # ""
    delay: int  # 0
    alterId: str  # ""
    cipher: str  # ""
    area: str  # "" 地区
    # 定义属性与字典键的映射 + 类型转换逻辑
    _FIELDS = {
        "name": ("name", str),
        "type": ("type", str),
        "address": ("server", str),
        "port": ("port", int),
        "user": ("username", str),
        "passwd": ("password", str),
        "udp": ("udp", bool),
        "uuid": ("uuid", str),
        "delay": ("delay", int),
        "alterId": ("alterId", str),
        "cipher": ("cipher", str),
        "area": ("address", str),
    }

    def __init__(self, proxy: dict):
        self._proxy = proxy  # 直接保存引用
        self._cached_id = None  # 新增缓存字段

        # 必填字段检查（排除 id）
        required_keys = {v[0] for v in self._FIELDS.values() if v[0] != "id"}
        missing = required_keys - proxy.keys()
        if missing:
            raise ValueError(f"Missing keys: {missing}")

        # 代理类型验证
        if proxy["type"] not in ["socks5", "http", "ss", "vmess"]:
            raise ValueError("Invalid proxy type")

    @property
    def id(self) -> int:
        """高频访问属性单独用 property 优化"""
        if self._cached_id is None:
            self._cached_id = int(self._proxy["name"][4:])
        return self._cached_id

    def __getattr__(self, name):
        if name in self._FIELDS:
            key, cast = self._FIELDS[name]
            return cast(self._proxy[key])
        raise AttributeError(f"No attribute: {name}")

    def __setattr__(self, name, value):
        if name == "_proxy" or name == "_cached_id":
            super().__setattr__(name, value)
        elif name == "name":
            new_name = str(value)
            # 更新缓存 id
            self._cached_id = int(new_name[4:])
            # 修改原始数据
            self._proxy["name"] = new_name
        elif name == "id":
            # 通过修改 name 来间接改变 id
            new_id = int(value)
            self._cached_id = new_id
            self._proxy["name"] = f"Name{new_id}"
        elif name in self._FIELDS:
            key, cast = self._FIELDS[name]
            self._proxy[key] = cast(value)
            # 特殊字段校验
            if name == "type" and self._proxy[key] not in ["socks5", "http", "ss", "vmess"]:
                raise ValueError("Invalid proxy type")
        else:
            super().__setattr__(name, value)


class RulesManager:
    def __init__(self, yamlData):
        self.yamlData = yamlData
        # 利用 proxies 生成 Proxy 对象列表
        self.proxies = [Proxy(p) for p in self.yamlData['proxies']]
        self.ipRules: list[IPRule] = []
        self.otherRules: list[OtherRules] = []
        for rule_str in self.yamlData['rules']:
            try:
                # Skip empty or malformed rules
                if not rule_str or not isinstance(rule_str, str) or rule_str.strip() == "":
                    continue
                    
                if rule_str.startswith("SRC-IP-CIDR"):
                    self.ipRules.append(IPRule(rule_str, self.proxies))
                else:
                    self.otherRules.append(OtherRules(rule_str))
            except RuleImportError:
                continue
            except Exception as e:
                print(f"跳过无效规则 '{rule_str}': {e}")
                continue

    def getRules(self):
        return [r.dict for r in self.ipRules]

    def generate_rule_str(self, updated_item: dict) -> str:
        """
        根据更新项生成新的规则字符串
        更新项中必须包含 'id' 与 'localAddr' 字段
        """
        pid = updated_item.get("id")
        localAddr = updated_item.get("localAddr")
        return f"SRC-IP-CIDR,{localAddr},Name{pid}"

    def getYamlData(self):
        # 将 otherRules 放在前面，确保域名规则优先匹配
        self.yamlData["rules"] = [rule.string for rule in self.otherRules + self.ipRules]
        return self.yamlData

    def resetAllProxy(self):
        for proxy in self.proxies:
            proxy.type = "socks5"
            proxy.address = "1.1.1.1"
            proxy.port = 1080
            proxy.user = ""
            proxy.passwd = ""
            proxy.udp = True
            proxy.uuid = ""
            proxy.delay = 0
            proxy.alterId = ""
            proxy.cipher = ""
            proxy.area = ""

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller创建临时文件夹,将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 如果不是PyInstaller打包的环境，使用当前文件所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

class ConfigManager:
    config_path: str
    rulesManager: RulesManager

    def __init__(self):
        # 获取可执行文件所在目录
        # 配置文件路径
        self.config_path = path
        # self.mikrotik_connection = mikrotik_connection()
        try:
            yaml_data = self.readYaml()
            if not yaml_data or 'proxies' not in yaml_data or 'rules' not in yaml_data:
                print("警告：配置文件为空或格式不正确")
                yaml_data = {'proxies': [], 'rules': []}
            self.rulesManager = RulesManager(yaml_data)
            
        except Exception as e:
            print(f"初始化配置管理器失败: {e}")
            self.rulesManager = RulesManager({'proxies': [], 'rules': []})

    def readYaml(self) -> dict:
        try:
            if not os.path.exists(self.config_path):
                print(f"配置文件不存在: {self.config_path}")
                return {'proxies': [], 'rules': []}
                
            with open(self.config_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                if not data:
                    print("配置文件为空")
                    return {'proxies': [], 'rules': []}
                return data
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            print(f"配置文件路径: {self.config_path}")
            return {'proxies': [], 'rules': []}

    def writeYaml(self) -> bool:
        try:
            # 获取当前序列化的数据
            data = self.rulesManager.getYamlData()
            rules = data.get("rules", []) or []
            # 将所有 IP 规则 (SRC-IP-CIDR) 提前，保持相对顺序不变
            ip_rules = [r for r in rules if isinstance(r, str) and r.startswith("SRC-IP-CIDR")]
            other_rules = [r for r in rules if not (isinstance(r, str) and r.startswith("SRC-IP-CIDR"))]
            new_rules = ip_rules + other_rules
            if new_rules != rules:
                data = dict(data)
                data["rules"] = new_rules

            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)
            logger.info(f"写入YAML文件成功: {self.config_path}")
            result=restartOpenclash(data)
            logger.info(f"重启OpenClash成功: {result}")
            return True
        except Exception as err:
            logger.error(f"写入 YAML 文件失败:{err}")
            logger.error(f"重启OpenClash失败: {err}")
            return False

    def getList(self):
        try:
            self.__init__()
            data = self.rulesManager.getRules()
            if not data:
                print("警告：没有找到规则数据")
            return data
        except Exception as e:
            print(f"获取列表失败: {e}")
            return []

    # 将前端更新后的数据写入yaml文件，不重启openclash
    def reloadyaml(self,newdata):
        with open(path, 'r', encoding='utf-8') as file:
            configfile = yaml.safe_load(file)
        
        # 匹配并修改proxies列表中的字典
        for newproxy in newdata:
            for proxy in configfile['proxies']:
                nameid='Name'+str(newproxy['id'])
                if proxy['name'] == nameid:
                    proxy.update({
                        'type':newproxy.get('proxyType',''),
                        'server':newproxy.get('address',''),  # 注意：YAML中是server字段
                        'port':newproxy.get('port',''),
                        'username':newproxy.get('user',''),  # 注意：YAML中是username字段
                        'password':newproxy.get('pass',''),  # 注意：YAML中是password字段
                        'alterId':newproxy.get('vmessId',''),
                        'delay':newproxy.get('delay',0),
                        'address':newproxy.get('area', ''),  # 地区信息
                        'cipher':newproxy.get('sslType',''),
                    })
                    break
        print(f'proxy:{proxy}')
        with open(path, 'w', encoding='utf-8') as file:
            yaml.dump(configfile, file, allow_unicode=True)
        
        # 重新初始化 RulesManager
        self.rulesManager = RulesManager(configfile)
        

    def update(self, updated_items: list[dict]) -> bool:
        """
        根据前端传入的更新数据，仅更新 YAML 文件中 proxies 与 rules 部分
        更新项中每个 dict 需要包含以下字段（可选字段有默认保留原值）：
          - id, localAddr, proxyType, address, port, user, pass, delay, vmessId, sslType, area
        """
        if not updated_items:
            return False

        # 构建 id -> 更新项 的映射
        updated_map = {item["id"]: item for item in updated_items}

        # --- 更新 proxies ---
        for proxy in self.rulesManager.proxies:
            if proxy.id in updated_map:
                item = updated_map[proxy.id]
                proxy.type = item.get("proxyType", proxy.type)
                proxy.address = item.get("address", proxy.address)
                proxy.port = item.get("port", proxy.port)
                proxy.user = item.get("user", proxy.user)
                proxy.passwd = item.get("pass", proxy.passwd)
                proxy.delay = item.get("delay", proxy.delay)
                proxy.alterId = item.get("vmessId", proxy.alterId)
                proxy.cipher = item.get("sslType", proxy.cipher)
                proxy.area = item.get("area", proxy.area)
                logger.info(f"{proxy.name}--{proxy.address}-延迟：{proxy.delay}")
        # 写回 YAML 文件，其他部分不变
        
        return self.writeYaml()

    def reset_factory_settings(self):  # 原方法名：恢复出厂设置
        try:
            self.rulesManager.resetAllProxy()
            self.writeYaml()
            return True
        except Exception as e:
            print("恢复出厂设置出错", e)
            return False

    def updateCityDelay(self,data):
        try:
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Authorization': 'Bearer Rc3lFJSt',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Referer': f'http://{ip}:9090/ui/yacd/?hostname={ip}&port=9090&secret=Rc3lFJSt',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            }
            params = {
                'url': 'http://www.baidu.com',
                'timeout': '1000',
            }
            req = requests.get(f'http://{ip}:9090/group/GLOBAL/delay', params=params, headers=headers, verify=False)
            req.raise_for_status()
            print('延迟检测结果：',req.json())
            for proxy in data:
                proxy['delay']=0
            for k, v in req.json().items():
                if 'Name' in k:
                    for proxy in data:
                        # print(re.match(r'Name(\d{1,})',k).group(1))
                        kid=re.match(r'Name(\d{1,})',k).group(1)
                        if int(kid) == proxy['id']:
                            proxy['delay'] = v
                            print(f'Name{kid}--delay:{v}')
                            break
            # proxies = {'proxies': data}
            # # 写入YAML文件
            # with open('config.yaml', 'w', encoding='utf-8') as f:
            #     yaml.safe_dump(proxies, f, allow_unicode=True, sort_keys=False)
            
            self.update(data)
            return {'success': True,'data':data}
        except Exception as e:
            print('延迟检测',e)
            return False

    def updatearea(self,data):
        try:
            for proxy in data:
                # print(proxy)
                proxy['area'] = get_ip_info(proxy['address'])
                # print(proxy['area'])
            # proxies={'proxies': data}
            # # 写入YAML文件
            # with open('config.yaml', 'w', encoding='utf-8') as f:
            #     yaml.safe_dump(proxies, f, allow_unicode=True, sort_keys=False)
            self.update(data)
            return {'success':True,'data':data}
        except Exception as e:
            print('地区检测出错',e)
            return {'success':False}


    # 连接mikrotik运行修改MAC地址脚本
    def run_script(self,script_name: str) -> dict:
        """
        执行预存脚本并获取结果
        :param script_name: 脚本名称
        :return: API响应数据
        """
        try:
            conn=mikrotik_connection()
            params = {'number': script_name}

            # 核心API调用
            result = conn(
                cmd='/system/script/run',
                **params
            )
            resultjson=json.dumps(list(result),indent=4)
            print('runscript：',resultjson)
            return {'success': True,'data':resultjson}
        except Exception as e:
            if 'timed out' in str(e):
                return {'success':True}
            else:
                return {'success': False, 'error': str(e)}


    # def ishmpb(self):
    #     try:
    #         yamldata=self.readYaml()
    #         rules=yamldata['rules']
    #         for i in rules:
    #             if re.match(r'DOMAIH-SUFFIX',i):
    #                 print('true')
    #                 return True
    #                 break
    #         print('false')
    #         return False
    #     except Exception as e:
    #         print(e)

    # def qxhmpb(self):
    #     try:
    #         yamldata = self.readYaml()
    #         rules = yamldata['rules']
    #         newrules=[item for item in rules if 'DOMAIH-SUFFIX' not in item]
    #         yamldata['rules']=newrules
    #         with open(self.config_path, 'w', encoding='utf-8') as file:
    #             yaml.safe_dump(yamldata, file, allow_unicode=True, sort_keys=False)
    #         restartOpenclash()
    #         return True
    #     except Exception as e:
    #         print(e)
    #         return False

    #修改yaml文件添加rules（DOMAIH-SUFFIX, douyinedn.com, REJECTD）实现画面屏闭
    # def screen_block(self, pbstr: list):  # 原方法名：画面屏蔽
    #     try:
    #         yamldata = self.readYaml()
    #         for i in pbstr:
    #             yamldata['rules'].insert(0, i)
    #         with open(self.config_path, 'w', encoding='utf-8') as file:
    #             yaml.safe_dump(yamldata, file, allow_unicode=True, sort_keys=False)
    #         restartOpenclash()
    #         return True
    #     except Exception as e:
    #         print("写入 YAML 文件失败:", e)
    #         return False

    # 修改IP地址切回本地Ip（通过修改yaml文件的rules）
    def changipaddr(self,ipdict:dict):
        try:
            #数据以字典列表传递过来
            ipadds=ipdict['ipdict']
            #判断是否存在需要绑定的本地ip，获取本地网关，线路名写入yaml
            if len(ipadds) >= 1:
                yamldata = self.readYaml()

                for a in ipadds:
                    localip=a[0]
                    ipname=a[1]
                    if f"SRC-IP-CIDR,{localip},{ipname}" in yamldata:
                        pass
                    else:
                        yamldata['rules'].append(f"SRC-IP-CIDR,{localip},{ipname}")
                # with open(self.config_path, 'w', encoding='utf-8') as file:
                #     yaml.safe_dump(yamldata, file, allow_unicode=True, sort_keys=False)
                # restartOpenclash()
                return True
        except Exception as e:
                print("写入 YAML 文件失败:", e)
                return False

    def stopclash(self):
        try:
            stopOpenclash()
            return True
        except Exception as e:
            print('停用clash',e)
            return False

    def startclash(self):
        try:
            result=restartOpenclash()
            # [MOCK-修改] 由 result['success']==True 改为直接判断 result
            #   原因：restartOpenclash() 返回的是布尔值而非字典，
            #         原写法会抛 TypeError('bool' object is not subscriptable)，
            #         导致 /api/startclash 恒返回失败（真实模式下同样有此 bug）。
            if result:
                return True
            else:
                return False
        except Exception as e:
            print('重启clsh',e)
            return False
    def localaddr(self):
        try:
            idlist=[]
            yamldata=self.readYaml()
            localaddrlist=[i for i in yamldata['rules'] if 'SRC-IP-CIDR' in i]
            for i in localaddrlist:
                localaddrid=int(re.search(r'Name(\d{1,})',i).group(1))
                idlist.append(localaddrid)
            return {'succcess':True,'data':idlist}
        except Exception as e:
            print('获取localaddr失败:',e)
            return {'success':False,'data':e}

    def check_openclash_status(self):
        try:
            # 使用 systemctl 检查 OpenClash 状态
            output=openclash_status()
            print(output)
            # 检查是否在运行
            if 'running' in output:
                return {'success': True, 'data': True}
            else:
                print("OpenClash is not running")
                return {'success': True, 'data': False}
        except FileNotFoundError:
            print("systemctl command not found")
            return {'success': False, 'data': False}

    def add_aliwc_direct_rules(self):
        """
        添加支付宝域名直连规则到 config.yaml 的 rules 列表开头
        使以下域名走直连：
        - alipay.com 及其所有子域名（包括 @.alipay.com, *.alipay.com）
        - alipayobjects.com 及其所有子域名（包括 @.alipayobjects.com, *.alipayobjects.com）
        """
        try:
            # 需要添加的域名规则列表（使用 DOMAIN-SUFFIX 可以匹配所有子域名）
            
            # 需要添加的规则（使用 DOMAIN-SUFFIX 匹配域名及其所有子域名）
            new_rules_str = [f"DOMAIN-SUFFIX,{domain},DIRECT" for domain in alipay_domains]
            
            # 检查现有规则，避免重复添加
            existing_rules_str = [rule.string for rule in self.rulesManager.otherRules]
            existing_rules_str.extend([rule.string for rule in self.rulesManager.ipRules])
            
            # 过滤出需要添加的规则（避免重复）
            rules_to_add = []
            for rule_str in new_rules_str:
                if rule_str not in existing_rules_str:
                    rules_to_add.append(OtherRules(rule_str))
            
            if not rules_to_add:
                logger.info("支付宝域名规则已存在，无需重复添加")
                return {'success': True, 'message': '规则已存在，无需重复添加'}
            
            # 将新规则添加到 otherRules 列表的开头（确保优先匹配）
            self.rulesManager.otherRules = rules_to_add + self.rulesManager.otherRules
            
            # 写入 YAML 文件并重启 OpenClash
            if self.writeYaml():
                added_rules = [rule.string for rule in rules_to_add]
                logger.info(f"成功添加支付宝域名直连规则: {added_rules}")
                return {'success': True, 'message': f'成功添加 {len(rules_to_add)} 条规则', 'rules': added_rules}
            else:
                return {'success': False, 'message': '写入配置文件失败'}
                
        except Exception as e:
            logger.error(f"添加支付宝域名规则失败: {e}")
            return {'success': False, 'message': f'添加规则失败: {str(e)}'}

    def remove_aliwc_direct_rules(self):
        try:
            # 需要删除的规则（使用 DOMAIN-SUFFIX 匹配域名及其所有子域名）
            new_rules_str = [f"DOMAIN-SUFFIX,{domain},DIRECT" for domain in alipay_domains]
            old_rules_str = [rule.string for rule in self.rulesManager.otherRules]
            logger.info(f"old_rules_str: {old_rules_str}")
            logger.info(f"new_rules_str: {new_rules_str}")
            
            # 收集要删除的规则对象
            rules_to_remove = []
            for rule_obj in self.rulesManager.otherRules:
                if rule_obj.string in new_rules_str:
                    rules_to_remove.append(rule_obj)
            
            # 删除规则对象
            for rule_obj in rules_to_remove:
                self.rulesManager.otherRules.remove(rule_obj)
            
            if self.writeYaml():
                removed_rules = [rule_obj.string for rule_obj in rules_to_remove]
                logger.info(f"成功删除支付宝域名直连规则: {removed_rules}")
                return {'success': True, 'message': f'成功删除 {len(removed_rules)} 条规则', 'rules': removed_rules}
            else:
                logger.info('写入配置文件失败')
                return {'success': False, 'message': '写入配置文件失败'}
        except Exception as e:
            logger.error(f"删除支付宝域名规则失败: {e}")
            return {'success': False, 'message': f'删除规则失败: {str(e)}', 'rules': []}

    def get_aliwc_status(self):
        try:
            existing_rules_str = [rule.string for rule in self.rulesManager.otherRules]
            # 检查所有 alipay_domains 是否都在 otherRules 中
            if all(f'DOMAIN-SUFFIX,{domain},DIRECT' in existing_rules_str for domain in alipay_domains):
                return {'success': True, 'data': 'd'}
            else:
                return {'success': True, 'data': 'p'}
        except Exception as e:
            return {'success': False, 'message': f'获取支付宝微信直连状态失败: {str(e)}'}

class OpenClashMonitor:
    def __init__(self, api_port:int=9090):
        self.api_url = f"http://{ip}:{api_port}"
        self.upload_kb = 0  # 示例属性
        self.download_kb = 0
        self.proxy_ip = ""
        self.get_data()

    def get_data(self):
        try:
            # 优先使用API
            params = {'token': 'Rc3lFJSt'}
            traffic = requests.get(f"{self.api_url}/traffic", params=params).json()
            proxies = requests.get(f"{self.api_url}/proxies", params=params).json()
            current = proxies["proxies"]["GLOBAL"]["now"]
            self.upload_kb= traffic["up"] / 1024,
            self.download_kb= traffic["down"] / 1024,
            self.proxy_ip=proxies["proxies"][current]["history"][-1]["server"]
            print(proxies["proxies"][current]["history"][-1])

        except:
            # API失败时回退到日志分析
            return False

    def to_dict(self):
        """将对象转换为可序列化的字典"""
        return {
            "upload_kb": self.upload_kb,
            "download_kb": self.download_kb,
            "proxy_ip": self.proxy_ip
        }

    # def _parse_log(self):
    #     with open("/tmp/openclash.log", "r") as f:
    #         lines = f.readlines()[-10:]  # 读取最后10行
    #         for line in reversed(lines):
    #             ip = re.search(r"server=([\d.]+)", line)
    #             traffic = re.search(r"up=([\d.]+)(MB|KB).*down=([\d.]+)(MB|KB)", line)
    #             if ip and traffic:
    #                 return {
    #                     "proxy_ip": ip.group(1),
    #                     "upload_kb": float(traffic.group(1)) * (1024 if traffic.group(2) == "MB" else 1),
    #                     "download_kb": float(traffic.group(3)) * (1024 if traffic.group(4) == "MB" else 1)
    #                 }
    #     return {"error": "No data found"}

# def updateconfig(data):
#     with open('/root/.config/config.yaml', 'w') as f:
#         yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
#     restartOpenclash()


# if __name__ == '__main__':

    
    # print(get_ip_info("114.114.114.114"))
    # cn = ConfigManager()
    # cn.remove_alipay_direct_rules()
#     with open('config.yaml', 'r', encoding='utf-8') as file:
#         data = yaml.safe_load(file)
#     result=restartOpenclash({"address":"大洋洲-澳大利亚-*-*-*",
#   "alterId": "",
#   "cipher": "",
#   "delay": 0,
#   "name": "Name126",
#   "password": "pass",
#   "port": 1080,
#   "server": "1.1.1.1",
#   "type": "socks5",
#   "udp": False,
#   "url": "",
#   "username": "user",
#   "uuid": ""})
#     print(result)
    # print(data)
    # cn.localaddr()
    # print(get_ip_info("c501.ips5.vip"))
    # print(get_ip_info("1.1.1.1"))