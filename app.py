from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from config import ConfigManager
import subprocess
import resetlinestatus
import os, sys, requests, yaml,re,logging
from threading import Lock
import time
from balance import NetBalance
from concurrent.futures import ThreadPoolExecutor,as_completed
from auth import generate_token, verify_token,require_auth,decrypt_request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from h3c_wifi_manager import H3CAPManager
from ap_connection_pool import H3cConnectionPool,H3cConnection,HealthMonitor
from settings_load import settings
from functools import wraps
# 设置日志格式：时间+动作
def mock_safe_write(func):
    """MOCK 模式下写操作直接返回成功，不执行真实逻辑"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if settings.MOCK_MODE:
            return jsonify({
                'success': True,
                'msg': f'[MOCK] {func.__name__} 模拟执行成功',
                'mock': True,
            })
        return func(*args, **kwargs)
    return wrapper

MOCK_MODE = settings.MOCK_MODE
if MOCK_MODE:
    from mock.mock_ap import MockH3CAPManager
    from mock.mock_l2tp import MockL2TP
    from mock.mock_ros import MockMikrotikConnection
    mock_ros=MockMikrotikConnection()
    mock_l2tp=MockL2TP()
    logging.info('[MOCK] MOCK_MODE 已启用')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s-%(levelname)s-%(funcName)s-%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
def get_resource_path(relative_path):
    """获取资源的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
app = Flask(__name__,
           static_folder=None,  # 禁用自动静态文件处理，避免拦截 API 路由
           static_url_path=None)
UPLOAD_FOLDER='./'

# app.config['SECRET_KEY'] = 'your_secret_key_here'  # 生产环境请使用强密钥
# 设置一个强壮的密钥，用于签名JWT。生产环境中应从环境变量读取！
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7300) # 设置令牌过期时间
jwt = JWTManager(app) # 初始化JWT管理器

# 配置CORS以支持Cookie认证
CORS(app, supports_credentials=True, origins="*",allow_headers=["Authorization", "Authentication", "Content-Type"])  # 允许所有来源的跨域访问，支持Cookie
socketio = SocketIO(app, cors_allowed_origins="*")  # 允许所有来源的WebSocket连接
cm = ConfigManager()
output=''

# 全局创建空池子，零连接开销
ApManager = MockH3CAPManager if MOCK_MODE else H3CAPManager
ap_pool = H3cConnectionPool(lambda aid: ApManager(aid))
ap_monitor=HealthMonitor(ap_pool,interval=3)
#预先扫描创建AP池
def try_connect_ap(aid):
    """
    对单个 IP 尝试创建 manager 并 SSH 连接。
    成功返回 (aid, ip, manager)，失败返回 (aid, ip, None)
    """
    try:
        manager = ApManager(aid)
        if manager.connect():
            logging.info(f'AP 连接成功: aid={aid}')
            return aid,manager
        logging.warning(f'AP SSH 连接失败: aid={aid}')
    except Exception as e:
        logging.error(f'AP 连接异常: aid={aid}, {e}')
    return aid,None

def discover_create_ap_pool():
    if MOCK_MODE:
        ap_list = ['1', '2', '3']
    else:
        ap_list = resetlinestatus.RouteAP().ping_all_thread()
    connected = []
    if len(ap_list) == 0:
        return False
    with ThreadPoolExecutor(max_workers=len(ap_list)) as executor:
        futures = [
            executor.submit(try_connect_ap, aid)
            for aid in ap_list
        ]
        for future in futures:
            aid, manager = future.result()
            if manager:
                conn = H3cConnection(aid, ap_pool._factory, manager=manager)
                ap_pool.put(aid, conn)
                connected.append(aid)

    logging.info(f'启动扫描完成，成功连接 {len(connected)} 台 AP: {connected}')
    # return connected
# 退出
import atexit
def cleanup():
    ap_monitor.stop()
    ap_pool.close_all()
atexit.register(cleanup)
# 创建全局线程池用于处理并发请求
# 根据系统CPU核心数动态调整线程池大小
import multiprocessing
max_workers = min(32, (multiprocessing.cpu_count() or 1) + 4)
executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="api_worker")

# ============ 脚本上传/推送到 RouterOS ============
SCRIPTS_UPLOAD_DIR = get_resource_path('uploads')
os.makedirs(SCRIPTS_UPLOAD_DIR, exist_ok=True)

@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    return send_from_directory(SCRIPTS_UPLOAD_DIR, filename)

@app.route('/api/upload_script', methods=['POST'])
@mock_safe_write
def upload_script():
    """上传脚本并推送到 RouterOS（Winbox/RouterOS）。
    支持两种方式：
    1) multipart/form-data: 包含 file 字段，可选 form 字段 dst 与 import(true/false)
    2) application/json: { url: string, dst?: string, import?: boolean }
    """
    from ros import fetch_file_to_router, import_script_on_router
    file_url = None
    dst = None
    do_import = False
    # multipart 处理
    if 'file' in request.files:
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'msg': '文件名为空'}), 400
        save_path = os.path.join(SCRIPTS_UPLOAD_DIR, file.filename)
        file.save(save_path)
        # 生成可被 RouterOS 访问的 URL
        file_url = request.host_url.rstrip('/') + f"/uploads/{file.filename}"
        dst = request.form.get('dst') or None
        do_import = str(request.form.get('import', '')).lower() in ['1', 'true', 'yes']
    else:
        # JSON 处理
        data = request.get_json(silent=True) or {}
        file_url = data.get('url')
        dst = data.get('dst')
        do_import = bool(data.get('import'))
        if not file_url:
            return jsonify({'success': False, 'msg': '缺少文件或 url'}), 400
    try:
        filename_on_router = fetch_file_to_router(file_url, dst)
        if do_import:
            import_script_on_router(filename_on_router)
        return jsonify({
            'success': True,
            'msg': '上传并推送成功',
            'url': file_url,
            'filename': filename_on_router
        })
    except Exception as e:
        logging.exception('上传脚本到 RouterOS 失败')
        return jsonify({'success': False, 'msg': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """客户端连接时的处理"""
    print(f'客户端已连接: {request.sid}')
    emit('connected', {'message': '连接成功'})
    global l2tp_traffic_running,l2tp_traffic_thread,L2TP_TRAFFIC_INTERVAL
    if not l2tp_traffic_running:
        l2tp_traffic_running=True
        socketio.start_background_task(l2tp_traffic_worker)
        emit('start_l2tp_traffic', {'status': 'started', 'interval': L2TP_TRAFFIC_INTERVAL})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接时的处理"""
    global l2tp_traffic_running
    l2tp_traffic_running=False
    emit('stop_l2tp_traffic', {'status': 'stopped'})

    print(f'客户端已断开: {request.sid}')

# ============ L2TP 实时流量推送 (WebSocket) ============
# 采集线程状态
l2tp_traffic_running = False
l2tp_traffic_thread = None
# 上一次采样值，用于计算速率: {name: (timestamp, rx_bytes, tx_bytes)}
l2tp_traffic_last = {}
# 默认采样间隔（秒）
L2TP_TRAFFIC_INTERVAL = 2
# 保护采集线程的创建/销毁，避免并发事件导致重复启动
l2tp_traffic_lock = Lock()
# 当前订阅的客户端集合（用于按需启停，避免一个客户端 stop 掉所有人的推送）
l2tp_traffic_clients = set()
def l2tp_traffic_worker(interval=L2TP_TRAFFIC_INTERVAL):
    """后台线程：周期性采集 L2TP 接口流量并通过 WebSocket 广播"""
    global l2tp_traffic_last
    l2tp = resetlinestatus.L2TP()
    while l2tp_traffic_running:
        l2tp_traffic_items = []
        try:
            res = mock_l2tp.mock_get_l2tp_traffic() if MOCK_MODE else l2tp.get_l2tp_traffic()
            if res.get('success'):
                now = time.time()
                for it in res.get('data', []):
                    name = it.get('interface')
                    rx, tx = it.get('rx_speed', 0), it.get('tx_speed', 0)
                    l2tp_traffic_last[name] = (now, rx, tx)
                    l2tp_traffic_items.append({
                        'name': name,
                        'running': it.get('running', False),
                        'rx': rx,
                        'tx': tx,
                    })
                socketio.emit('l2tp_traffic', {
                    'timestamp': now,
                    'success': True,
                    'data': l2tp_traffic_items
                })
            else:
                socketio.emit('l2tp_traffic', {
                    'timestamp': time.time(),
                    'success': False,
                    'data': [],
                    'msg': res.get('msg', '采集失败')
                })
        except Exception as e:
            logging.error(f'L2TP流量采集出错: {e}')
            socketio.emit('l2tp_traffic', {
                'timestamp': time.time(),
                'success': False,
                'data': [],
                'msg': str(e)
            })
        # 分片休眠，便于快速响应停止指令
        slept = 0.0
        while l2tp_traffic_running and slept < interval:
            socketio.sleep(0.2)
            slept += 0.2

@socketio.on('start_l2tp_traffic')
def handle_l2tp_traffic():
    global l2tp_traffic_running
    l2tp_traffic_running=True
    emit('start_l2tp_traffic', {'status': 'started', 'interval': L2TP_TRAFFIC_INTERVAL})
    l2tp_traffic_worker()

@socketio.on('stop_l2tp_traffic')
def handle_stop_l2tp_traffic():
    global l2tp_traffic_running
    l2tp_traffic_running=False
    emit('l2tp_traffic_status', {'status': 'stopped'})

@app.route('/api/l2tp_traffic', methods=['GET'])
@require_auth()
def get_l2tp_traffic():
    """获取一次 L2TP 实时流量快照（REST 备用接口）"""
    return resetlinestatus.L2TP().get_l2tp_traffic()

@app.route('/auth', methods=['POST','GET'])
def auth(time_auth=False):
    try:
        data = request.get_json() or {}
        encrypted_key = data.get('token')
        print(f"认证请求收到，encrypted_key长度: {len(encrypted_key) if encrypted_key else 0}")
        if not encrypted_key:
            print("认证失败：缺少 token")
            return jsonify({'success': False, 'msg': '缺少 token'}), 400
        decrypted = decrypt_request(encrypted_key)
        print(f"解密结果: {decrypted}")
        if not decrypted:
            print("认证失败：解密失败")
            return jsonify({'success': False, 'msg': '解密失败'}), 400
        # decrypted 就是原始 JSON，假如前端发送的是 { "payload": "YmJjfDE3..."} 等
        # 如果你直接传 base64 字符串，可以在这里做第二次 base64 还原：
        from base64 import b64decode
        plain = b64decode(decrypted).decode('utf-8')  # 变成 "abdaeeifoajn|1731312345678"
        print(f"base64解码结果: {plain}")
        message, ts = plain.split('|', 1)
        ts_int = int(ts)
        print(f"解析结果 - message: {message}, timestamp: {ts_int}")
        if time_auth:
            # 时间戳校验（示例：允许 5 分钟窗口）
            current_time = time.time() * 1000
            time_diff = abs(current_time - ts_int)
            print(f"时间校验 - 当前时间: {current_time}, 请求时间: {ts_int}, 差值: {time_diff}ms")
            if time_diff > 5 * 60 * 1000:
                print(f"认证失败：请求过期，差值 {time_diff}ms > 300000ms")
                return jsonify({'success': False, 'msg': '请求过期'}), 403
        token = generate_token(message)
        print(f"认证成功，生成token: {token[:20]}...")
        return jsonify({'success': True, 'token': token})
    except Exception as e:
        print(f"认证过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'msg': f'认证失败: {str(e)}'}), 500

@app.route('/api/data', methods=['GET'])
@require_auth()
def get_items():
    try:
        data = cm.getList()
        if MOCK_MODE:
            data = mock_ros.get_iprule_proxy_status(data)
            return data
        data = resetlinestatus.setStatus(data)
        return data
    except Exception as e:
        return {'error': str(e)}

@app.route('/api/ishmpb', methods=['GET'])
@require_auth()
def getIshmpb():
    if MOCK_MODE:
        return {'ok':True,'data':mock_ros.hmpb_status()}
    return {'ok':True,'data':resetlinestatus.hmpb_status()}

@app.route('/api/initialize', methods=['GET'])
@require_auth()
def initialize():
    return {'success': cm.reset_factory_settings()}

@app.route('/api/update', methods=['POST'])
@require_auth()
def update():
    # print(request.json)
    cm.__init__()
    return {"ok": cm.update(request.json.get("items"))}

@app.route('/api/city_delay', methods=['POST'])
@require_auth()
def city_delay():
    if MOCK_MODE:
        return {"data":mock_ros.city_delay(request.json)}
    return {"data":cm.updateCityDelay(request.json)}

@app.route('/api/location', methods=['POST'])
@require_auth()
def location():
    return cm.updatearea(request.json)

@app.route('/api/hmpb', methods=['GET'])
@require_auth()
def hmpb():
    if MOCK_MODE:
        mock_ros.set_hmpb_status(True)
        return {'ok':True,'data':True}

    result=cm.run_script("06-Douyin-Shipin-PingBi")
    return result

@app.route('/api/cancelhmpb',methods=['GET'])
@require_auth()
def cancelhmpb():
    if MOCK_MODE:
        mock_ros.set_hmpb_status(False)
        return {'ok':True,'data':False}
    result=cm.run_script("07-Douyin-Shiping-ZhengChang")
    return result

@app.route('/api/qhbd',methods=['POST'])
@require_auth()
def qhbd():
    if MOCK_MODE:
        mock_ros.qhbd(False)
        return {'ok':True,'data':False}

    cm.changipaddr(request.get_json())
    return {'ok':True}

@app.route('/api/mac',methods=['GET'])
@require_auth()
def changmac():
    if MOCK_MODE:
        return {'success':True,'msg':'修改MAC成功'}
    result=cm.run_script("huan_sk_MAC&SSID")
    return result

@app.route('/api/resetyaml',methods=['GET'])
@require_auth()
def resetYaml():
    cm.__init__()
    return {"data":cm.reset_factory_settings()}

@app.route('/api/iprules',methods=['GET'])
@require_auth()
def getiprules():
    return cm.localaddr()

@app.route('/api/singleline',methods=['POST'])
@require_auth()
def singleline():
    return resetlinestatus.setStatus(request.json)

@app.route('/api/setlineproxy',methods=['POST'])
@require_auth()
def setlineproxy():
    if MOCK_MODE:
        return mock_ros.set_iprule_proxy(request.json)
    resetlinestatus.setlineproxy(request.json)
    cm.__init__()
    return resetlinestatus.setStatus(request.json)

@app.route('/api/setlinelocal',methods=['POST'])
@require_auth()
def setlinelocal():
    if MOCK_MODE:
        return mock_ros.set_iprule_local(request.json)
    resetlinestatus.setlinelocal(request.json)
    cm.__init__()
    return resetlinestatus.setStatus(request.json)

@app.route('/api/stopclash',methods=['GET'])
@require_auth()
def clashsh():  
    return {'data':cm.stopclash()}

@app.route('/api/startclash',methods=['GET'])
@require_auth()
def stopclashsh():
    return {'data':cm.startclash()}

@app.route('/api/check_openclash',methods=['GET'])
@require_auth()
def check_openclash():
    return cm.check_openclash_status()

@app.route('/stream_log',methods=['GET'])
def stream_logs():
    def generate():
        proc = subprocess.Popen(['tail', '-f', '/tmp/openclash.log'], stdout=subprocess.PIPE)
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            yield f"data: {line.decode()}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/uploadyaml',methods=['POST'])
@require_auth()
def upload_yaml():
    if 'file' not in request.files:
        return {'success': False, 'msg': '没有文件'}
    file = request.files['file']
    if not file.filename.endswith('.yaml'):
        return {'success': False, 'msg': '只允许上传.yaml文件'}
    save_path = os.path.join(UPLOAD_FOLDER, 'bp.yaml')
    file.save(save_path)
    cm.__init__()
    return {'success': True, 'msg': '保存成功'}

@app.route('/api/resetyamlfile',methods=['GET'])
@require_auth()
def resetyamlfile():
    with open(os.path.join(UPLOAD_FOLDER, 'bp.yaml'), 'r') as f:
        yaml_content = f.read()
    cm.rulesManager(yaml_content)
    cm.writeYaml()
    cm.__init__()
    return {'success': True, 'msg': '恢复配置文件成功'}

@app.route('/api/isbp',methods=['GET'])
@require_auth()
def isbp():
    if os.path.exists(os.path.join(UPLOAD_FOLDER, 'bp.yaml')):
        return {'success': True}
    else:
        return {'success': False}

@app.route('/api/verify_pwd',methods=['POST'])
@require_auth()
def verify_pwd():
    cm.__init__()
    passwd={
            'sk5':'123456',
            'balance':'123456',
            'api':'123456',
            'wifi':'123456'
        }
    if os.path.exists(get_resource_path('password.txt')):
        with open(get_resource_path('password.txt'), 'r') as f:
            lines = f.read().splitlines()
            for line in lines:
                pssplit=line.split('|')
                passwd[pssplit[0]]=pssplit[1]
        print(passwd)
    else:
        with open(get_resource_path('password.txt'), 'w') as f:
            f.write(f'sk5|{passwd["sk5"]}\n')
            f.write(f'balance|{passwd["balance"]}\n')
            f.write(f'api|{passwd["api"]}\n')
            f.write(f'wifi|{passwd["wifi"]}\n')
    if request.json['password'] == passwd[request.json['menu']]:
        return {'success':True,'msg':'密码正确'}
    else:
        return {'success':False,'msg':'密码错误'}


@app.route('/api/add_api_url',methods=['POST'])
@require_auth()
def add_apiurl():
    apiurl=request.json['url']
    res=requests.get(apiurl)
    if res.status_code == 200:
        try:
            text=res.json()
            return {'success':True,'msg':text}
        except:
            return {'success':False,'msg':'所给api链接获取的代理格式不正确！请替换json数据格式，直接输出为数组！！'}
    else:
        return {'success':False,'msg':'api请求失败！'}


@app.route('/api/restartserver',methods=['GET'])
@require_auth()
def restartserver():
    cm.__init__()
    return {'success':True}

@app.route('/api/balance_port',methods=['GET'])
@require_auth()
def balance_port():
    if MOCK_MODE:
        data=mock_ros.balance_port()
        return {'success': True, 'data': data}
    netbalance=NetBalance()
    return netbalance.get_port_dhcp()

@app.route('/api/setbalance',methods=['POST'])
@require_auth()
@mock_safe_write
def setbalance():
    netbalance=NetBalance()
    return netbalance.set_netbalance(request.json)

@app.route('/api/set_ether_status',methods=['POST'])
@require_auth()
@mock_safe_write
def set_ether_status():
    netbalance=NetBalance()
    return netbalance.set_ether_status(request.json)

@app.route('/api/getAP',methods=['get'])
@require_auth()
def getAP():
    """优化后的获取AP信息API - 并行处理"""
    try:
        if MOCK_MODE:
            data=[]
            for i in range(1, 4):
                connection=ap_pool.get(str(i))
                dataitem=connection.execute(lambda m: m.get_ap())
                data.extend(dataitem)
            return {'success': True, 'data': data}
        # 使用缓存的AP列表
        ip_list = ap_pool.all_aids()
        if not ip_list:
            return jsonify({'success': False, 'msg': '没有可用的AP设备','data':[]})
        # 并行处理所有AP - 优化线程池大小
        ap_info = []
        def _process_single_ap_wifi(ap_pool,aid, timeout=60):
            """处理单个AP的WiFi信息，带超时控制"""
            connection = None
            try:
                connection = ap_pool.get(aid)
                if not connection:
                    logging.info(f"无法获取AP {aid} 的连接")
                    return None

                def _fetch_wifi_info(manager):
                    re_try=0
                    radio_count=manager.get_radio_count(use_cache=False)
                    while manager.radio_type_dict == {} and re_try<3:
                        re_try+=1
                        time.sleep(0.1)
                        manager.get_radio_type(radio_count)
                    wifi_count = manager.get_wifi_count()
                    return manager.get_allwifi_info(wifi_count)
                return connection.execute(lambda m: _fetch_wifi_info(m))
            except Exception as e:
                logging.error(f"处理AP {aid} WiFi信息失败: {e}")
                return None
        # 根据CPU核心数和AP数量动态调整线程池大小
        optimal_workers = len(ip_list)
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            # 提交所有任务
            future_to_ip = {executor.submit(_process_single_ap_wifi, ap_pool, ip): ip for ip in ip_list}
            # 收集结果
            for future in as_completed(future_to_ip):
                result = future.result()
                if result:
                    ap_info.extend(result)  # 注意这里用extend，因为每个AP可能有多个WiFi
        return jsonify({'success': True, 'data': ap_info})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'获取失败: {str(e)}'})

@app.route('/api/getRadio',methods=['get'])
@require_auth()
def getradio():
    """优化后的获取Radio信息API - 并行处理"""
    try:
        if MOCK_MODE:
            data=[]
            for i in range(1, 4):
                connection=ap_pool.get(str(i))
                dataitem=connection.execute(lambda m: m.get_radio())
                data.extend(dataitem)
            return {'success': True, 'data': data}
        # 使用缓存的AP列表
        ip_list = ap_pool.all_aids()
        if not ip_list:
            return {'success': False, 'msg': '没有可用的AP设备','data':[]}
        # 并行处理所有AP - 优化线程池大小
        radio_info = []
        def _process_single_ap_radio(ap_pool,aid):
            """处理单个AP的Radio信息，带超时控制"""
            connection = None
            try:
                connection = ap_pool.get(aid)
                if not connection:
                    return None
                # 连接已经由连接池管理，这里不需要重新连接
                def _fetch_radio_info(manager):
                    radio_count = manager.get_radio_count(use_cache=False)
                    re_try=0
                    while manager.radio_type_dict == {} and re_try<3:
                        re_try+=1
                        time.sleep(0.1)
                        manager.get_radio_type(radio_count) 
                    return manager.get_radio_info(radio_count)
                return connection.execute(lambda m: _fetch_radio_info(m))
            except Exception as e:
                logging.error(f"处理AP {aid} Radio信息失败: {e}")
                return None
        # 根据CPU核心数和AP数量动态调整线程池大小
        optimal_workers = len(ip_list)
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            future_to_ip = {executor.submit(_process_single_ap_radio, ap_pool, ip): ip for ip in ip_list}
            for future in as_completed(future_to_ip):
                ap_id = future_to_ip[future]
                try:
                    result = future.result()
                except Exception as e:
                    logging.error(f"获取AP {ap_id} 射频信息出错: {e}")
                    continue
                if result is None:
                    continue
                if isinstance(result, list):
                    radio_info.extend(result)
                elif isinstance(result, dict):
                    radio_info.append(result)
                else:
                    logging.warning(f"AP {ap_id} 返回了非预期类型: {type(result)}，已忽略")
        return {'success': True, 'data': radio_info}
    except Exception as e:
        return {'success': False, 'msg': f'获取失败: {str(e)}'}

@app.route('/api/setAP',methods=['POST'])
@require_auth()
@mock_safe_write
def setap():
    connection = None
    try:
        reqjson=request.json
        aid=reqjson['wifi_data'][0]['aid']
        connection=ap_pool.get(aid)
        def _set_ap(manager):
            try:
                if isinstance(reqjson['wifi_data'], list):
                    success_count=0
                    wifi_list=[]
                    wid_list=[item['wid'] for item in reqjson['wifi_data']]
                    for item in reqjson['wifi_data']:
                        result = manager.set_ap(item,reqjson['action'])
                        if result['success']: 
                            wifi_list.append(item['wid'])
                            success_count+=1
                    if reqjson['action']=='add':
                        physical_port_list=manager.physical_port_list
                        retry=0
                        while retry<3 and len(physical_port_list)==0:
                            physical_port_list=manager.get_physical_port()
                            retry+=1
                            time.sleep(1)
                        if len(physical_port_list)==0:
                            manager.del_wifi(wid_list)
                            return {'success':False,'msg':f'设置物理端口为tagged失败，重试{retry}次，请重新添加SSID'}
                        else:
                            manager.set_vlan_tagged()
                    if success_count == len(reqjson['wifi_data']):
                        radio_to_wid={}
                        if reqjson['action']=='add':
                            for i in reqjson['wifi_data']:
                                if i.get('radio_bind'):
                                    radio_bind=i['radio_bind'][0]
                                    radio_rid=radio_bind.split('(')[1].split(')')[0]
                            manager.set_radio_status(radio_rid,1)
                        return {'success':True,'msg':f'设置成功'}
                    else:
                        manager.del_wifi(wid_list)
                        return {'success':False,'msg':f'设置成功WIFI{success_count}个，失败{len(reqjson["wifi_data"])-success_count}个,wifi_list:{wifi_list}'}
                else:
                    return {'success':False,'msg':'所给wifi_data格式不正确！！'}                
            except Exception as e:
                return {'success':False,'msg':f'设置AP失败: {str(e)}'}
        return connection.execute(lambda m: _set_ap(m))
    except Exception as e:
        return {'success':False,'msg':'设置失败,error:'+str(e)}

@app.route('/api/delwifi',methods=['POST'])
@require_auth()
@mock_safe_write
def delap():
    connection = None
    try:
        reqjson=request.json
        aid=reqjson['aid']
        connection=ap_pool.get(aid)
        result = connection.execute(lambda m :m.del_wifi(reqjson['wifi_list']))
        if result:
            return result
    except Exception as e:
        return {'success':False,'msg':f'删除失败: {str(e)}'}


@app.route('/api/getAPstatus',methods=['POST'])
@require_auth()
def getapstatus():
    try:
        if MOCK_MODE:
            return {'success': True, 'msg': '在线'}
        reqjson=request.json
        ip=reqjson['aid']
        ip_list=resetlinestatus.RouteAP().ping_all_thread()
        if ip in ip_list:
            return {'success':True,'msg':'在线'}
        else:
            return {'success':False,'msg':'离线'}
    except Exception as e:
        return {'success':False,'msg':str(e)}


@app.route('/api/setRadioManage',methods=['POST'])
@require_auth()
@mock_safe_write
def setradiomanage():
    st=time.time()
    reqjson=request.json
    ip=reqjson['radio_data'][0]['aid']
    connection=ap_pool.get(ip)
    def _set_radio_manage(manager):
        radio_count=manager.get_radio_count()
        wifi_count=manager.get_wifi_count()
        logging.info(f'radio_count:{radio_count}')
        radio_list=[{'rid':i,'wid':[]} for i in range(1,radio_count+1)]
        wifi_bandwidth_all=[{i['wid']:i['radio_bind']} for i in reqjson['radio_data']]
        logging.info(f'radio_list:{radio_list}')
        logging.info(f'wifi_bandwidth_all:{wifi_bandwidth_all}')
        for i in wifi_bandwidth_all:
            for k,v in i.items():
                bind_radio=[int(re.search(r'\((\d+)\)',r).group(1)) for r in v]
                logging.info(f'bind_radio:{bind_radio}')
                for j in radio_list:
                    if int(j['rid']) in bind_radio:
                        j['wid'].append(int(k))
                        # break
        logging.info(f'radio_list:{radio_list}')
        logging.info(f'wifi_bandwidth_all:{wifi_bandwidth_all}')
        isstatus_all=[]
        for item in radio_list:
            if item["wid"] == []:
                result=manager.set_radio_status(item["rid"],0)
            else:
                result=manager.set_radio_status(item["rid"],1)
            isstatus_all.append({'rid':item['rid'],'action':result['action'] ,'success':result['success'],'msg':result['msg']})
            logging.info(f'当前频率设置rid:{item["rid"]}的wifi:{item["wid"]}')
            result = manager.set_radio_manage(item["rid"],item["wid"],wifi_count)
            isstatus_all.append({'rid':item['rid'],'action':result['action'] ,'success':result['success'],'msg':result['msg']})
        et=time.time()
        logging.info(f'设置耗时: {et-st}秒')
        return {'success':True,'msg':isstatus_all}
    return connection.execute(lambda m: _set_radio_manage(m))

@app.route('/api/get_channel_bandwidth',methods=['POST'])
@require_auth()
def get_channel_bandwidth():
    if MOCK_MODE:
        return {'success': True, 'data': ap_pool.get(1).execute(lambda m: m.get_all_channel_bandwidth())}
    reqjson=request.json
    ip=reqjson['aid']
    connection=ap_pool.get(ip)
    result = connection.execute(lambda m :m.get_all_channel_bandwidth())
    if isinstance(result, dict):
        return result
    else:
        return {'success':False,'msg':str(result)}

@app.route('/api/setchannel',methods=['POST'])
@require_auth()
@mock_safe_write
def setchannel():
    reqjson=request.json
    ip=reqjson['aid']
    rid=int(reqjson['rid'])
    channel=reqjson['channel']
    connection=ap_pool.get(ip)
    return connection.execute(lambda m: m.set_channel(rid,channel))

@app.route('/api/setbandwidth',methods=['POST'])
@require_auth()
@mock_safe_write
def setbandwidth():
    reqjson=request.json
    ip=reqjson['aid']
    rid=int(reqjson['rid'])
    bandwidth=int(reqjson['bandwidth'].split(' ')[1])
    connection=ap_pool.get(ip)
    return connection.execute(lambda m :m.set_bandwidth(rid,bandwidth))

@app.route('/api/setMaxpower',methods=['POST'])
@require_auth()
@mock_safe_write
def setmaxpower():
    reqjson=request.json
    ip=reqjson['aid']
    rid=int(reqjson['rid'])
    power=reqjson['max_power']
    connection=ap_pool.get(ip)
    return connection.execute(lambda m :m.set_max_power(rid,power))

@app.route('/api/getScript',methods=['GET'])
@require_auth()
def getScript():
    if MOCK_MODE:
        return {'success': True, 'data': mock_ros.mock_get_script()}
    return resetlinestatus.WinScript().get_script()


@app.route('/api/runScript',methods=['POST'])
@require_auth()
@mock_safe_write
def runScript():
    # 直接获取请求数据，不依赖异步线程中的request对象
    reqjson = request.get_json()
    try:
        return resetlinestatus.WinScript().run_script(reqjson)
    except Exception as e:
        return {'success': False, 'msg': str(e)}

@app.route('/api/balance_scheduler',methods=['POST'])
@require_auth()
def balance_scheduler():
    netbalance=NetBalance()
    return netbalance.run_scheduler(request.json['status'])

@app.route('/api/balance_scheduler_status',methods=['GET'])
@require_auth()
@mock_safe_write
def balance_scheduler_status():
    netbalance=NetBalance()
    return netbalance.get_scheduler_status()

@app.route('/api/set_ALIWC_d_or_p',methods=['POST'])
@require_auth()
@mock_safe_write
def set_ALIWC_d_or_p():
    reqjson=request.json
    if reqjson['status']=='d':
        return ConfigManager().add_aliwc_direct_rules()
    else:
        return ConfigManager().remove_aliwc_direct_rules()

@app.route('/api/get_ALIWC_status',methods=['GET'])
@require_auth()
def get_ALIWC_status():
    return ConfigManager().get_aliwc_status()

@app.route('/api/l2tp',methods=['GET'])
@require_auth()
def get_l2tp_data():
    if MOCK_MODE:
        return {'success': True, 'data': mock_l2tp.mock_get_l2tp()}
    return resetlinestatus.L2TP().get_l2tp_data()

@app.route('/api/set_l2tp',methods=['POST'])
@require_auth()
@mock_safe_write
def set_l2tp():
    reqjson=request.json
    success_count=0
    for i in reqjson:
        if not resetlinestatus.L2TP().set_l2tp(i):
            continue
        else:
            success_count+=1
    if success_count==len(reqjson):
        return {'success':True,'msg':'设置L2TP成功'}
    else:
        return {'success':False,'msg':f'设置L2TP失败，成功{success_count}个，失败{len(reqjson)-success_count}个'}
        
@app.route('/api/set_l2tp_status',methods=['POST'])
@require_auth()
@mock_safe_write
def set_l2tp_status():
    reqjson=request.json
    if resetlinestatus.L2TP().set_l2tp_status(reqjson):
        return {'success':True,'msg':'设置L2TP状态成功'}
    else:
        return {'success':False,'msg':'设置L2TP状态失败'}

@app.route('/api/set_ether_type',methods=['POST'])
@require_auth()
@mock_safe_write
def set_ether_type():
    reqjson=request.json
    netbalance=NetBalance()
    result=netbalance.set_ether_type(reqjson)
    return result


@app.route('/')
def index():
    return send_from_directory(get_resource_path('www'), 'index.html')  # 默认访问 index.html

@app.route('/<path:filename>', methods=['GET', 'HEAD'])
def serve_static_file(filename):
    # 只处理 GET 和 HEAD 请求，避免拦截 API 路由的 POST 等请求
    # 排除 API 路由路径，即使它们是 GET 请求也不处理
    api_prefixes = ['auth', 'api', 'socket.io','l2tp_traffic']
    if any(filename.startswith(prefix) for prefix in api_prefixes):
        from flask import abort
        abort(404)  # 返回 404，让 Flask 知道这个路由不处理这个请求
    return send_from_directory(get_resource_path('www'), filename)

@app.route('/api/untn_net', methods=['GET'])
@require_auth()
def check_untn_net():
    if MOCK_MODE:
        return {'success': True, 'exists': True, 'msg': '网卡utun存在'}
    """探测Alpine系统是否存在网卡untn"""
    def _check_untn_net_status():
        """检查网卡utun是否存在（内部函数）"""
        try:    
            # 方法2: 使用 ip link show 命令检查
            try:
                result = subprocess.run(
                    ['ip', 'link', 'show', 'utun'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                print(result.stdout.strip(),result.returncode)
                if result.returncode == 0:
                    return {
                        'success': True,
                        'exists': True,
                        'msg': '网卡utun存在',
                        'method': 'ip_link',
                        'output': result.stdout.strip()
                    }
            except subprocess.TimeoutExpired:
                pass
            except FileNotFoundError:
                pass
            # 所有方法都未找到网卡
            return {
                'success': True,
                'exists': False,
                'msg': '网卡utun不存在'
            }
        except Exception as e:
            logging.error(f'检查网卡utun时出错: {str(e)}')
            return {
                'success': False,
                'exists': False,
                'msg': f'检查网卡utun时出错: {str(e)}'
            }
    return _check_untn_net_status()

if __name__ == '__main__':
    try:
        discover_create_ap_pool()
        ap_monitor.start()
        socketio.run(
            app, 
            host=settings.HOST, 
            port=settings.PORT, 
            allow_unsafe_werkzeug=True, 
            debug=settings.DEBUG,
            use_reloader=True)
    finally:
        # 应用关闭时清理线程池
        cleanup()
        executor.shutdown(wait=True)