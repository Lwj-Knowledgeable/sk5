# 软路由 + 无线 AP 自动化管理平台

基于 Flask + Vue3 的软路由（RouterOS）与华三无线 AP 自动化管理系统，提供 AP 连接池管理、WiFi/射频批量配置、L2TP 实时流量推送、多线路负载均衡、OpenClash 规则管理等能力。

> ⚠️ 本项目面向真实 H3C 无线 AP 与 RouterOS 软路由环境。仓库提供 **MOCK 模式**，无需任何硬件即可启动完整后端 API、WebSocket 推送与前端交互，便于体验与代码评审。

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [快速开始（MOCK 模式）](#快速开始mock-模式)
- [真实环境部署](#真实环境部署)
- [目录结构](#目录结构)
- [核心设计](#核心设计)
- [API 概览](#api-概览)
- [安全说明](#安全说明)
- [免责声明](#免责声明)

---

## 功能特性

- **AP 连接池**：基于 SSH 的华三 AP 连接复用，带存活探测、自动重连、串行访问锁，避免频繁握手。
- **健康监控**：后台线程周期性 ping + 探活，自动发现新增/下线 AP，清理失效连接。
- **WiFi / 射频管理**：批量查询与设置 SSID、射频绑定、信道、带宽、最大功率、VLAN tagged 等。
- **L2TP 实时流量**：Socket.IO 秒级推送接口流量，前端零轮询。
- **多线路负载均衡**：基于 RouterOS API 管理网桥、DHCP、PPPoE、静态 IP、路由与 PCC 调度器。
- **OpenClash 规则管理**：YAML 规则读写、代理延迟/地区检测、支付宝/微信直连规则、配置热重启。
- **多层认证**：JWT Token + HMAC 请求签名 + AES 请求加密，支持可选时间戳防重放。
- **脚本上传与推送**：上传脚本文件并推送到 RouterOS 执行。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3、Flask、Flask-SocketIO、Flask-CORS、PyJWT、Paramiko、PyYAML、Requests |
| 实时通信 | Socket.IO（WebSocket + 长轮询降级） |
| 网络设备 | H3C 无线 AP（SSH）、MikroTik RouterOS（API） |
| 前端 | Vue3、Pinia、Vite、socket.io-client |
| 部署 | Docker |
| 并发 | ThreadPoolExecutor、threading.Lock、后台监控线程 |

---

## 系统架构

```mermaid
flowchart LR
    Vue[Vue3 前端<br/>Pinia + Vite] -->|HTTP /api/*
    Vue -->|WebSocket /socket.i
    Flask --> Auth[JWT / 签名 / AES 认证]
    Flask --> Pool[AP 连接池<br/>H3cConnectionPool]
    Flask --> Monitor[健康监控<br/>HealthMonitor]
    Flask --> RouterOS[RouterOS API<br/>balance.py/resetlinestatus.py]
    Flask --> Clash[OpenClash YAML<br/>config.py]
    Pool -->|SSH| AP1[H3C AP]
    Pool -->|SSH| AP2[H3C AP]
    RouterOS -->|API| ROS[MikroTik 软路由]
    Flask -->|Socket.IO 广播| Vue
```

---

## 快速开始（MOCK 模式）

无需任何 AP 或路由器，即可启动后端与前端，体验完整 API 与 WebSocket 推送。

### 1. 克隆并安装依赖

```bash
git clone https://github.com/<your-name>/<repo>.git
cd <repo>
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
### 2. 配置setting.yaml变量,与配置password.txt(涉及前端部分API密码认证)
至少设置：

MOCK_MODE=true
JWT_SECRET=dev-secret
COOKIE_SECRET=dev-cookie-secret
ENCRYPT_SECRET=dev-encrypt-secret

### 3. 启动后端
```bash
python app.py
# 默认监听 0.0.0.0:8080
```
启动日志应看到：
```
[MOCK] AP 连接池已启用模拟模式
[MOCK] RouterOS API 返回模拟数据
启动扫描完成，成功连接 N 台 AP: [...]
```
### 4. 启动前端
```bash
cd frontend
npm install
npm run dev
# Vite 默认 5173，已配置 /socket.io 代理到 8080
```
浏览器访问 `http://localhost:5173`，即可看到 AP 列表、L2TP 流量实时曲线、负载均衡面板等（数据均为模拟）。

### 5. MOCK 模式下可体验的功能
- AP 列表 / WiFi / 射频信息查询（返回模拟数据）
- L2TP 流量 Socket.IO 实时推送（模拟随机流量）
- 负载均衡端口状态、调度器状态（模拟）
- OpenClash 规则读写（使用本地示例 `config.example.yaml`）
- 脚本上传（保存到 `uploads/`，不真正推送到路由器）
---
## 真实环境部署

1. 准备 H3C AP（开启 SSH，默认端口 13598）与 MikroTik RouterOS（开启 API）。
2. 修改 `setting.yaml` 中的 AP 地址规则、账号密码,ROS的地址、账号密码，根据项目需求修改flask配置。
3. 配置 `config.py` 中 `path` 指向真实 OpenClash `config.yaml`。

```
# ===== H3C AP =====
ap:
  host_template: "192.168.88.24{aid}"
  username: "admin"
  password: "change-me"
  port: 13598

# ===== RouterOS =====
ros:
  host: "10.0.0.1"
  username: "firewall"
  password: "327462@Zhou"
  api_port: 18891

# ===== OpenClash =====
clash:
  config_path: "config.example.yaml"   # mock 模式用示例文件
  api_host: "10.0.0.254"
  api_port: 9090
  api_secret: "change-me"
```

---

## 目录结构

```
.
├── app.py                  # Flask 入口、路由、Socket.IO 事件
├── auth.py                 # JWT / 签名 / AES 认证
├── ap_connection_pool.py   # AP 连接池 + 健康监控
├── h3c_wifi_manager.py     # H3C AP SSH 管理
├── balance.py              # RouterOS 负载均衡
├── config.py               # OpenClash YAML 规则管理
├── resetlinestatus.py      # RouterOS 线路状态 / L2TP / 脚本
├── ros.py                  # RouterOS API 封装
├── settings_load.py        # setting.yaml配置读取
├── mock/                   # MOCK 模式实现（本仓库新增）
│   ├── mock_ap.py
│   ├── mock_ros.py
│   └── mock_l2tp.py
├── frontend/               # Vue3 + Vite 前端
├── deploy/                 # Nginx / Docker 配置
├── uploads/                # 上传脚本目录（.gitignore）
├── config.yaml             # Openclah config配置
├── setting.yaml            # 项目配置
├── requirements.txt
└── README.md
```

---

## 核心设计

### AP 连接池

- `H3cConnection`：单 AP 包装，`threading.Lock` 保证同 AP 串行访问，`is_alive()` 用 `transport.send_ignore()` 低开销探活，失效时自动重连。
- `H3cConnectionPool`：`aid -> H3cConnection` 映射，线程安全。
- `HealthMonitor`：后台线程周期性 `ping_all_thread()` + 并发探活，自动移除下线 AP。

### 并发采集

`/api/getAP`、`/api/getRadio` 使用 `ThreadPoolExecutor` 按 AP 数量动态开线程，`as_completed` 收集结果，避免单 AP 超时拖慢整体。

### 实时推送

`l2tp_traffic_worker` 后台线程按 `L2TP_TRAFFIC_INTERVAL` 采集，`socketio.emit` 广播；分片 `socketio.sleep(0.2)` 保证快速响应停止指令。

### 认证

- JWT：`generate_token` / `verify_token`，`exp` 20 年，支持 `leeway` 容错。
- 签名：HMAC-SHA256，`X-Signature` 头。
- 加密：AES-CBC（无 Crypto 库时降级 base64）。
- 时间戳：`require_auth(require_timestamp=True)` 可选防重放。

---

## API 概览

所有 `/api/*` 接口均需 `Authorization: Bearer <token>`（由 `/auth` 获取）。
完整路由见 `app.py`，以下按模块列出代表性接口。

### 认证
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/auth` | 登录换 JWT |

### AP 管理
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/getAP` | 并行获取所有 AP 的 WiFi 信息 |
| GET | `/api/getRadio` | 并行获取所有 AP 的射频信息 |
| POST | `/api/setAP` | 批量新增/修改 WiFi |
| POST | `/api/delwifi` | 删除 WiFi |
| POST | `/api/setRadioManage` | 设置射频与 WiFi 绑定 |
| POST | `/api/setchannel` / `/api/setbandwidth` / `/api/setMaxpower` | 设置信道 / 带宽 / 最大功率 |
| POST | `/api/getAPstatus` | 查询单 AP 在线状态 |

### 代理规则 / OpenClash
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/data` | 获取代理规则列表 |
| POST | `/api/update` | 更新代理规则 |
| POST | `/api/city_delay` | 批量检测代理延迟 |
| POST | `/api/location` | 批量检测代理地区 |
| GET | `/api/ishmpb` | 画面屏蔽状态 |
| GET | `/api/hmpb` / `/api/cancelhmpb` | 开启 / 关闭画面屏蔽 |
| GET | `/api/iprules` | 本地 IP 规则 |
| POST | `/api/qhbd` | 切换本地 IP 绑定 |
| GET | `/api/stopclash` / `/api/startclash` | 停止 / 启动 OpenClash |
| GET | `/api/check_openclash` | OpenClash 运行状态 |
| POST | `/api/uploadyaml` | 上传 YAML 配置 |
| GET | `/api/resetyaml` / `/api/resetyamlfile` | 恢复出厂 / 恢复 YAML |
| POST | `/api/set_ALIWC_d_or_p` | 支付宝/微信直连开关 |
| GET | `/api/get_ALIWC_status` | 直连状态 |
| POST | `/api/add_api_url` | 添加代理 API 地址 |

### 线路 / 负载均衡
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/balance_port` | 端口与 DHCP 状态 |
| POST | `/api/setbalance` | 设置端口负载均衡 |
| POST | `/api/set_ether_status` | 启用/禁用端口 |
| POST | `/api/set_ether_type` | 设置端口接入方式（dhcp/ip/ppoe） |
| POST | `/api/balance_scheduler` | 启停 PCC 调度器 |
| GET | `/api/balance_scheduler_status` | PCC 调度器状态 |
| GET | `/api/l2tp` / POST `/api/set_l2tp` | 查询 / 设置 L2TP |
| POST | `/api/set_l2tp_status` | 设置 L2TP 状态 |
| GET | `/api/l2tp_traffic` | L2TP 流量快照 |

### 脚本 / 系统
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/getScript` / POST `/api/runScript` | 获取 / 运行 RouterOS 脚本 |
| POST | `/api/upload_script` | 上传脚本并推送到 RouterOS |
| GET | `/uploads/<filename>` | 访问已上传脚本 |
| GET | `/api/untn_net` | 探测 utun 网卡 |
| GET | `/stream_log` | SSE 实时日志 |

### Socket.IO 事件
`connect`、`disconnect`、`start_l2tp_traffic`、`stop_l2tp_traffic`、`l2tp_traffic`

> 完整路由与参数说明见 `app.py`，或运行后访问 `/api/...` 自行调试。

---
### MOCK 模式说明

MOCK 模式只模拟**只读查询**（AP 列表、射频、L2TP 流量、负载均衡状态等），
写操作（设置 WiFi、射频、负载均衡、上传脚本等）统一返回“模拟执行成功”，
不执行真实设备操作。

这样无需硬件即可体验完整前端交互与主链路，同时避免为 50+ 接口维护冗余 mock。
真实环境请设置 `mock_mode: false` 并配置 `settings.yaml` 中的设备信息。

## 安全说明

- 所有密钥通过配置文件setting.yaml配置，仓库不含真实密钥。
- 生产环境请启用 HTTPS，并收紧 `cors_allowed_origins`。
- 默认账号密码仅为占位，部署前必须修改。

---

## 免责声明

本项目仅用于学习与技术交流。使用前请确保你拥有对相关网络设备的合法管理权限。