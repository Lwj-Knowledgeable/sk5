"""模拟 H3CAPManager，返回固定结构数据，不建立 SSH 连接"""
import random
import time

class MockH3CAPManager:
    def __init__(self, num):
        self.aid = int(num)
        self.host = f'192.168.88.24{num}'
        self.radio_type_dict = {}
        self.physical_port_list = ['port1', 'port2']

    def connect(self):
        return True

    def disconnect(self):
        pass

    def is_alive(self):
        return True

    def get_radio_count(self, use_cache=False):
        return 2

    def get_radio_type(self, count):
        self.radio_type_dict = {i: '2.4G' if i == 1 else '5G' for i in range(1, count + 1)}
        return self.radio_type_dict

    def get_wifi_count(self):
        return 4

    def get_radio(self):
        result =[
                {
                "aid": self.aid,
                "channel": "40",
                "channel_bandwidth": "20/40/80MHz",
                "max_power": "19 dBm",
                "rid": 1,
                "state": "Down",
                "type": "5GHz"
                },
                {
                "aid": self.aid,
                "channel": "4",
                "channel_bandwidth": "20MHz",
                "max_power": "15 dBm",
                "rid": 2,
                "state": "Up",
                "type": "2.4GHz"
                }
            ]
        return result

    def get_ap(self):
        return [
    {
      "aid": self.aid,
      "radio_bind": [],
      "ssid": "test1",
      "ssid_hide": "Disabled",
      "status": "Enabled",
      "user_isolation": "Disabled",
      "vlan": True,
      "wid": "1",
      "wifipassword": ""
    },
    {
      "aid": self.aid,
      "radio_bind": [],
      "ssid": "test2",
      "ssid_hide": "Disabled",
      "status": "Enabled",
      "user_isolation": "Disabled",
      "vlan": True,
      "wid": "2",
      "wifipassword": ""
    },
    {
      "aid": self.aid,
      "radio_bind": [],
      "ssid": "test3",
      "ssid_hide": "Disabled",
      "status": "Enabled",
      "user_isolation": "Disabled",
      "vlan": True,
      "wid": "3",
      "wifipassword": ""
    },
    {
      "aid": self.aid,
      "radio_bind": [],
      "ssid": "test4",
      "ssid_hide": "Disabled",
      "status": "Enabled",
      "user_isolation": "Disabled",
      "vlan": True,
      "wid": "4",
      "wifipassword": ""
    }
  ]
    def get_all_channel_bandwidth(self):
        return {'success': True, 'data': [
    {
      "bandwidth": [
        " 20 MHz",
        " 40 MHz",
        " 80 MHz"
      ],
      "channel": [
        "1",
        "36",
        "40",
        "44",
        "48",
        "52",
        "56",
        "60",
        "64",
        "149",
        "153",
        "157",
        "161",
        "165",
        "auto"
      ],
      "rid": 1,
      "type": "5GHz"
    },
    {
      "bandwidth": [
        " 20 MHz",
        " 40 MHz"
      ],
      "channel": [
        "1",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "auto"
      ],
      "rid": 2,
      "type": "2.4GHz"
    }
        ]}

    # 所有 set_* 方法统一返回成功
    def __getattr__(self, name):
        if name.startswith('set_') or name.startswith('del_'):
            def _ok(*args, **kwargs):
                return {'success': True, 'msg': f'[MOCK] {name} ok', 'action': name}
            return _ok
        raise AttributeError(name)