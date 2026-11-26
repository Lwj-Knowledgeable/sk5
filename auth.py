"""
Flask API 认证加密模块
提供 JWT Token 认证和请求签名验证
"""
import os,time,hmac,hashlib,base64,json,logging,jwt
from functools import wraps
from flask import request, jsonify
from settings_load import settings
logger=logging.getLogger(__name__)
# JWT 密钥（生产环境应从环境变量或配置文件读取）
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRATION = settings.JWT_EXPIRATION
# 请求签名密钥
SIGN_SECRET = 'your-sign-secret-change-in-production'
def generate_token(user_id):
    """生成 JWT Token"""
    payload = {
        'user_id': user_id,
        'exp': int(time.time()) + JWT_EXPIRATION,
        'iat': int(time.time())
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token):
    """验证 JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_signature(data, secret=SIGN_SECRET):
    """生成请求签名"""
    # 将数据转换为 JSON 字符串并按 key 排序
    if isinstance(data, dict):
        sorted_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
    else:
        sorted_data = str(data)
    
    # 使用 HMAC-SHA256 生成签名
    signature = hmac.new(
        secret.encode('utf-8'),
        sorted_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_signature(data, signature, secret=SIGN_SECRET):
    """验证请求签名"""
    expected_signature = generate_signature(data, secret)
    return hmac.compare_digest(expected_signature, signature)


def require_auth(allow_public=False):
    """
    API 认证装饰器
    
    Args:
        allow_public: 是否允许公开访问（不需要 token）
    
    使用方式:
        @app.route('/api/data')
        @require_auth()
        def get_data():
            return jsonify({'data': 'protected'})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 公开接口直接通过
            if allow_public:
                return func(*args, **kwargs)
            
            # 获取 token
            token = None
            
            # 从 Header 中获取 token
            logger.info(f'请求头：{dict(request.headers)}')
            auth_header = request.headers.get('Authorization')
            logger.info(f'Authorization header: {auth_header}')
            if auth_header:
                try:
                    # 支持 "Bearer <token>" 格式
                    parts = auth_header.split(' ')
                    logger.info(f'parts：{parts}')
                    if len(parts) == 2 and parts[0] == 'Bearer':
                        token = parts[1]
                    elif len(parts) == 1:
                        token = parts[0]
                except:
                    pass
            
            # 如果 Header 中没有，尝试从请求参数中获取
            if not token:
                token = request.args.get('token') or (request.json.get('token') if request.is_json else None)
                logger.info(f'从请求参数获取 token: {token}')
            
            # 验证 token
            if not token:
                return jsonify({
                    'success': False,
                    'msg': '缺少认证 Token',
                    'code': 401
                }), 401
            
            payload = verify_token(token)
            if not payload:
                return jsonify({
                    'success': False,
                    'msg': 'Token 无效或已过期',
                    'code': 401
                }), 401
            
            # 将用户信息存储到 request 对象中，供路由函数使用
            request.user = payload
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_signature(require_timestamp=False, timestamp_window=300):
    """
    请求签名验证装饰器
    
    Args:
        require_timestamp: 是否要求时间戳（防止重放攻击）
        timestamp_window: 时间戳窗口（秒），默认5分钟
    
    使用方式:
        @app.route('/api/sensitive')
        @require_signature()
        def sensitive_api():
            return jsonify({'data': 'sensitive'})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取签名
            signature = request.headers.get('X-Signature')
            timestamp = request.headers.get('X-Timestamp')
            
            if not signature:
                return jsonify({
                    'success': False,
                    'msg': '缺少请求签名',
                    'code': 403
                }), 403
            
            # 验证时间戳（防止重放攻击）
            if require_timestamp:
                if not timestamp:
                    return jsonify({
                        'success': False,
                        'msg': '缺少时间戳',
                        'code': 403
                    }), 403
                
                try:
                    ts = int(timestamp)
                    current_ts = int(time.time())
                    if abs(current_ts - ts) > timestamp_window:
                        return jsonify({
                            'success': False,
                            'msg': '请求时间戳无效',
                            'code': 403
                        }), 403
                except ValueError:
                    return jsonify({
                        'success': False,
                        'msg': '时间戳格式错误',
                        'code': 403
                    }), 403
            
            # 获取请求数据
            if request.method == 'GET':
                data = dict(request.args)
            else:
                if request.is_json:
                    data = request.get_json() or {}
                elif request.form:
                    data = request.form.to_dict()
                else:
                    data = {}
            
            # 验证签名
            if not verify_signature(data, signature):
                logging.warning(f'签名验证失败: {request.path}')
                return jsonify({
                    'success': False,
                    'msg': '签名验证失败',
                    'code': 403
                }), 403
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def encrypt_response(data):
    """
    响应数据加密（可选，如果需要对响应加密）
    
    Args:
        data: 要加密的数据
    
    Returns:
        加密后的数据（base64编码）
    """
    # 这里可以实现 AES 等加密算法
    # 目前先返回原数据（可根据需求扩展）
    import json
    json_str = json.dumps(data, ensure_ascii=False)
    return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')


def decrypt_request(encrypted_data, secret_key=None):
    """
    解密请求数据
    
    Args:
        encrypted_data: 加密的数据（base64编码）
        secret_key: 解密密钥，如果为None则使用默认密钥
    
    Returns:
        解密后的数据（字典），解密失败返回None
    """
    if secret_key is None:
        # 使用环境变量或默认密钥
        secret_key = os.getenv('ENCRYPT_SECRET', SIGN_SECRET)
    
    try:
        # 先进行 base64 解码
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # 尝试使用 AES 解密（如果数据是 AES 加密的）
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            
            # 生成固定长度的密钥（32字节用于AES-256）
            key = hashlib.sha256(secret_key.encode('utf-8')).digest()
            
            # 提取 IV（前16字节）和密文
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            # 创建 AES 解密器
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_bytes = unpad(cipher.decrypt(ciphertext), AES.block_size)
            json_str = decrypted_bytes.decode('utf-8')
            
        except (ImportError, ValueError, Exception):
            # 如果 AES 解密失败，尝试直接 base64 解码（向后兼容）
            json_str = encrypted_bytes.decode('utf-8')
        
        # 尝试解析 JSON，如果失败则直接返回字符串（用于认证场景）
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 如果不是 JSON，直接返回字符串（用于认证场景，如 "abdaeeifoajn|timestamp" 的 base64）
            return json_str
    except Exception as e:
        logging.error(f'解密失败: {str(e)}')
        return None


def encrypt_request(data, secret_key=None):
    """
    加密请求数据
    
    Args:
        data: 要加密的数据（字典）
        secret_key: 加密密钥，如果为None则使用默认密钥
    
    Returns:
        加密后的数据（base64编码字符串）
    """
    if secret_key is None:
        secret_key = os.getenv('ENCRYPT_SECRET', SIGN_SECRET)
    
    try:
        # 将数据转换为 JSON 字符串
        json_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        json_bytes = json_str.encode('utf-8')
        
        # 尝试使用 AES 加密
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad
            import secrets
            
            # 生成固定长度的密钥（32字节用于AES-256）
            key = hashlib.sha256(secret_key.encode('utf-8')).digest()
            
            # 生成随机 IV
            iv = secrets.token_bytes(16)
            
            # 创建 AES 加密器
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_data = pad(json_bytes, AES.block_size)
            ciphertext = cipher.encrypt(padded_data)
            
            # 组合 IV 和密文，然后 base64 编码
            encrypted_bytes = iv + ciphertext
            return base64.b64encode(encrypted_bytes).decode('utf-8')
            
        except ImportError:
            # 如果没有 Crypto 库，使用简单的 base64 编码
            return base64.b64encode(json_bytes).decode('utf-8')
            
    except Exception as e:
        logging.error(f'加密失败: {str(e)}')
        return None


# Cookie 认证相关配置
COOKIE_NAME = settings.COOKIE_NAME
COOKIE_SECRET = settings.COOKIE_SECRET
COOKIE_EXPIRATION = settings.COOKIE_EXPIRATION


def generate_cookie_token(user_id, menu='sk5'):
    """生成 Cookie 认证 Token"""
    payload = {
        'user_id': user_id,
        'menu': menu,
        'exp': int(time.time()) + COOKIE_EXPIRATION,
        'iat': int(time.time())
    }
    token = jwt.encode(payload, COOKIE_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_cookie_token(token):
    """验证 Cookie Token"""
    try:
        payload = jwt.decode(token, COOKIE_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_cookie_auth(allow_public=False):
    """
    Cookie 认证装饰器
    
    Args:
        allow_public: 是否允许公开访问（不需要 cookie）
    
    使用方式:
        @app.route('/api/data')
        @require_cookie_auth()
        def get_data():
            return jsonify({'data': 'protected'})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 公开接口直接通过
            if allow_public:
                return func(*args, **kwargs)
            
            # 从 Cookie 中获取认证 token
            token = request.cookies.get(COOKIE_NAME)
            
            # 验证 token
            if not token:
                return jsonify({
                    'success': False,
                    'msg': '缺少认证 Cookie，请先登录',
                    'code': 401
                }), 401
            
            payload = verify_cookie_token(token)
            if not payload:
                return jsonify({
                    'success': False,
                    'msg': 'Cookie 无效或已过期，请重新登录',
                    'code': 401
                }), 401
            
            # 将用户信息存储到 request 对象中，供路由函数使用
            request.user = payload
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# if __name__ == '__main__':
#     logger.info(verify_token('3AL/DyQikZxeXfBRuorwKdSg6/6GrNp/3FBHe2koNGbdDIaRnTX6i/tiIMztoGuayxME/iyPU5F6zBRxNyYBiQ=='))