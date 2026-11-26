"""模拟 L2TP 流量采集"""
import random
import time

class MockL2TP:
    def __init__(self):
        self.l2tp_traffic=[]
        self.l2tp=[]

    def mock_get_l2tp_traffic(self):
        return {
            'success': True,
            'data': [
                {
                    'interface': f'l2tp-out{i}',
                    'running': True,
                    'rx_speed': random.randint(0, 10_000_000),
                    'tx_speed': random.randint(0, 5_000_000),
                }
                for i in range(1, 4)
            ],
        }

    def mock_get_l2tp(self):
        self.l2tp=[
            {
                'id': i,
                'name': f'l2tp-out{i}',
                'connect_to':'120.132.15.22',
                'password':'123456',
                'user':'admin',
                'status':True,
                'running': True,
            }
            for i in range(1, 40)
        ]
        return self.l2tp
        