import threading,time,os
import concurrent.futures
import resetlinestatus
from settings_load import settings
MOCK_MODE = settings.MOCK_MODE

import logging
logger=logging.getLogger(__name__)

class H3cConnection:
    """单个 AP 的连接包装：锁 + 存活探测 + 重连"""
    def __init__(self, aid, factory,manager=None):
        self.aid = aid
        self._factory = factory          # 返回 H3CAPManager 空对象的函数
        self._lock = threading.Lock()    # 同一 AP 串行访问
        self._manager = manager          # H3cAPManager 实例
        self._last_ok = 0

    def is_alive(self):
        """低开销存活判断：send_ignore"""
        if self._manager is None:
            return False
        try:
            transport = self._manager.ssh.get_transport() if self._manager.ssh else None
            if transport is None or not transport.is_active():
                return False
            transport.send_ignore()
            return True
        except Exception:
            return False

    def _ensure_connected(self):
        """确保连接可用，必要时重建。调用方必须已持有锁"""
        if MOCK_MODE:
            return True
        if self.is_alive():
            return True
        # 断开旧连接（可能已经半死）
        try:
            if self._manager:
                self._manager.disconnect()
        except Exception:
            pass
        self._manager = self._factory(self.aid)
        ok = self._manager.connect()
        if ok:
            self._last_ok = time.time()
        return ok

    def execute(self, func, *args, **kwargs):
        """
        在锁内执行 func(manager, *args, **kwargs)。
        自动保证连接可用；执行失败时标记连接失效，下次会重连。
        """
        logger.info(f'AP {self.aid} 等待锁')
        with self._lock:
            logger.info(f'AP {self.aid} 获得锁')
            if not self._ensure_connected():
                return {'success': False, 'msg': f'AP {self.aid} 连接失败'}
            try:
                return func(self._manager, *args, **kwargs)
            except Exception as e:
                logger.error(f'AP {self.aid} 执行失败: {e}')
                # 标记为需要重连：下一次 is_alive 会失败并触发重建
                self._manager = None if 'closed' in str(e).lower() else self._manager
                return {'success': False, 'msg': str(e)}

    def close(self):
        with self._lock:
            if self._manager:
                try:
                    self._manager.disconnect()
                except Exception as e:
                    logger.error(f'AP {self.aid} 断开失败: {e}')
                self._manager = None


class H3cConnectionPool:
    def __init__(self, factory):
        self._factory = factory #factory是H3cConnection类
        self._conns = {}
        self._pool_lock = threading.Lock()

    def get(self, aid):
        with self._pool_lock:
            conn = self._conns.get(aid)
            if conn is None:
                conn = H3cConnection(aid, self._factory)
                self._conns[aid] = conn
            return conn

    def put(self, aid, conn):
        with self._pool_lock:
            self._conns[aid] = conn

    def remove(self, aid):
        """AP 从清单删除时调用，断开并移除"""
        with self._pool_lock:
            conn = self._conns.pop(aid, None)
        if conn:
            conn.close()

    def all_aids(self):
        with self._pool_lock:
            return list(self._conns.keys())

    def close_all(self):
        with self._pool_lock:
            conns = list(self._conns.values())
            self._conns.clear()
        for c in conns:
            c.close()

class HealthMonitor:
    def __init__(self, pool, interval=60):
        self.pool = pool #pool是H3cConnectionPool类
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.ap_ping_cache = []
        self._status = {}

    def start(self):
        self._thread.start()

    def _run(self):
        while not self._stop.wait(self.interval):
            self._check_once()

    def _check_once(self):
        if MOCK_MODE:
            ap_list = self.pool.all_aids()
        else:
            ap_list = resetlinestatus.RouteAP().ping_all_thread()         # 每轮重新读清单，自动发现新增/删除
        configured_aids = {ap for ap in ap_list}

        # 1. 清单里已删除的 AP：从池里移除
        for aid in self.pool.all_aids():
            if aid not in configured_aids:
                self.pool.remove(aid)
                self._status.pop(aid, None)
                logging.info(f'AP {aid} 已从清单移除，断开连接')

        # 2. 并发检查清单里的每个 AP
        def check(aid):
            # if not resetlinestatus.RouteAP().ping_single(aid, resetlinestatus.API(), thread=False):
            if aid not in ap_list:
                self._status[aid] = 'offline'
                return
            conn = self.pool.get(aid)
            result = conn.execute(lambda m: {'success': True}) 
            self._status[aid] = 'online' if result.get('success') else 'offline'

        if ap_list:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(ap_list))) as executor:
                list(executor.map(check, ap_list))

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=5)


