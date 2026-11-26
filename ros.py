from librouteros import connect
import logging
from librouteros.exceptions import ConnectionClosed,TrapError,FatalError
from settings_load import settings
logger=logging.getLogger(__name__)

# ========================================================================
# [MOCK-新增] 以下为 MOCK 模式相关改动，用于无硬件时返回模拟数据。
#   1) MOCK_MODE 常量：原先本文件直接连接真实 RouterOS，无任何模拟分支。
#   2) mikrotik_connection()：MOCK 模式下改用 mock/mock_ros.py 的模拟连接。
#   3) fetch_file_to_router() / import_script_on_router()：全新函数。
#      原因：app.py 的 /api/upload_script 一直在 from ros import 这两个函数，
#      但 ros.py 中并不存在，导致该接口即使在真实模式下也必然 ImportError。
# ========================================================================
MOCK_MODE = settings.MOCK_MODE


def mikrotik_connection(timeout=30, quiet=False):
    # [MOCK-新增] MOCK 模式走模拟连接，不发起任何真实网络请求

    MIKROTIK_CONFIG = {
    'host': settings.ROS_HOST,
    'username': settings.ROS_USERNAME,
    'password': settings.ROS_PASSWORD,
    'port': settings.ROS_API_PORT # 默认API端口
}
    try:
        conn = connect(
            host=MIKROTIK_CONFIG['host'],
            username=MIKROTIK_CONFIG['username'],
            password=MIKROTIK_CONFIG['password'],
            port=MIKROTIK_CONFIG['port'],
            timeout=timeout
        )
        if not quiet:
            logger.info(f"成功连接到 {MIKROTIK_CONFIG['host']}")
        return conn
    except (ConnectionClosed, FatalError, TrapError) as e:
        logger.error(f"连接 {MIKROTIK_CONFIG['host']} 失败: {str(e)}")
        raise RuntimeError(f"连接失败: {MIKROTIK_CONFIG['host']} 失败: {str(e)}") from e

# [MOCK-新增] 全新函数：把远程脚本文件下载到路由器，返回路由器上的文件名
def fetch_file_to_router(url, dst=None):
    """把远程脚本文件下载到路由器，返回路由器上的文件名

    MOCK 模式下不会真正下载，只返回模拟的文件名。
    """
    # [MOCK-新增] MOCK 分支
    if MOCK_MODE:
        from mock.mock_ros import mock_fetch_file_to_router
        return mock_fetch_file_to_router(url, dst)

    conn = mikrotik_connection()
    try:
        kwargs = {'url': url}
        if dst:
            kwargs['dst'] = dst
        result = list(conn(cmd='/tool/fetch', **kwargs))
        logger.info(f'获取脚本结果：{result}')
        for item in result:
            if item.get('status') == 'finished':
                return item.get('file-name') or dst or url.split('/')[-1]
        raise RuntimeError(f'下载脚本失败: {result}')
    finally:
        conn.close()


# [MOCK-新增] 全新函数：在路由器上导入指定脚本文件(.rsc)
def import_script_on_router(filename):
    """在路由器上导入指定脚本文件(.rsc)"""
    # [MOCK-新增] MOCK 分支
    if MOCK_MODE:
        from mock.mock_ros import mock_import_script_on_router
        return mock_import_script_on_router(filename)

    conn = mikrotik_connection()
    try:
        conn('/import', **{'file-name': filename})
        logger.info(f'导入脚本成功：{filename}')
        return True
    except (TrapError, FatalError, ConnectionClosed) as e:
        raise RuntimeError(f"导入脚本失败: {str(e)}") from e
    finally:
        conn.close()

