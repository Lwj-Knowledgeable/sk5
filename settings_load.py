"""
统一配置加载：只从项目根目录的 settings.yaml 读取，不依赖系统环境变量。
"""
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


class Settings:
    def __init__(self):
        raw = _load_yaml(BASE_DIR / "settings.yaml")

        # 运行模式
        self.MOCK_MODE: bool = bool(raw.get("mock_mode", False))

        # Flask
        flask_cfg = raw.get("flask", {})
        self.HOST: str = flask_cfg.get("host", "0.0.0.0")
        self.PORT: int = int(flask_cfg.get("port", 8080))
        self.DEBUG: bool = bool(flask_cfg.get("debug", True))

        # 认证
        auth_cfg = raw.get("auth", {})
        self.JWT_SECRET: str = auth_cfg.get("jwt_secret", "dev-jwt-secret-change-me")
        self.JWT_ALGORITHM: str = auth_cfg.get("jwt_algorithm", "HS256")
        self.JWT_EXPIRATION: int = int(auth_cfg.get("jwt_expiration", 630720000))
        self.SIGN_SECRET: str = auth_cfg.get("sign_secret", "dev-sign-secret-change-me")
        self.ENCRYPT_SECRET: str = auth_cfg.get("encrypt_secret", self.SIGN_SECRET)
        self.COOKIE_NAME: str = auth_cfg.get("cookie_name", "auth_token")
        self.COOKIE_SECRET: str = auth_cfg.get("cookie_secret", "dev-cookie-secret-change-me")
        self.COOKIE_EXPIRATION: int = int(auth_cfg.get("cookie_expiration", 86400))

        # H3C AP
        ap_cfg = raw.get("ap", {})
        self.AP_HOST_TEMPLATE: str = ap_cfg.get("host_template", "192.168.88.24{aid}")
        self.AP_USERNAME: str = ap_cfg.get("username", "admin")
        self.AP_PASSWORD: str = ap_cfg.get("password", "")
        self.AP_PORT: int = int(ap_cfg.get("port", 13598))

        # RouterOS
        ros_cfg = raw.get("ros", {})
        self.ROS_HOST: str = ros_cfg.get("host", "10.0.0.1")
        self.ROS_USERNAME: str = ros_cfg.get("username", "admin")
        self.ROS_PASSWORD: str = ros_cfg.get("password", "")
        self.ROS_API_PORT: int = int(ros_cfg.get("api_port", 8728))

        # OpenClash
        clash_cfg = raw.get("clash", {})
        self.CLASH_CONFIG_PATH: str = clash_cfg.get(
            "config_path",
            "config.yaml",
        )
        self.CLASH_API_HOST: str = clash_cfg.get("api_host", "10.0.0.254")
        self.CLASH_API_PORT: int = int(clash_cfg.get("api_port", 9090))
        self.CLASH_API_SECRET: str = clash_cfg.get("api_secret", "")

        # 路径（统一转成绝对路径，基于项目根目录）
        paths_cfg = raw.get("paths", {})
        self.UPLOAD_DIR: Path = BASE_DIR / paths_cfg.get("upload_dir", "uploads")
        self.WWW_DIR: Path = BASE_DIR / paths_cfg.get("www_dir", "www")
        self.BASE_DIR: Path = BASE_DIR


settings = Settings()