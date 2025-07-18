# 简单DNS服务器

这是一个基于Python和dnslib库实现的简单DNS服务器，支持基本的DNS解析功能。

## 功能特点

- 支持A记录（IPv4地址）解析
- 支持通配符域名解析（如 `*.example.com`）
- 支持从区域文件加载静态DNS记录
- 支持上游DNS服务器转发（对于未在本地配置的域名）
- 轻量级设计，易于理解和扩展

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/joelin818818/simple-dns-server.git
cd simple-dns-server
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

使用默认配置启动DNS服务器：

```bash
python dns_server.py
```

这将在所有网络接口（0.0.0.0）上的53端口启动DNS服务器，并使用8.8.8.8:53作为上游DNS服务器。

### 命令行参数

可以通过命令行参数自定义DNS服务器的行为：

```bash
python dns_server.py --help
```

参数说明：

- `--port`, `-p`: 监听端口（默认：53）
- `--address`, `-a`: 监听地址（默认：0.0.0.0）
- `--zone`, `-z`: 区域文件路径
- `--upstream`, `-u`: 上游DNS服务器（默认：8.8.8.8:53）

示例：

```bash
# 在本地地址127.0.0.1的5053端口启动服务器
python dns_server.py --address 127.0.0.1 --port 5053

# 使用自定义区域文件和上游DNS服务器
python dns_server.py --zone example.zone --upstream 1.1.1.1:53
```

### 区域文件格式

区域文件用于配置静态DNS记录，格式如下：

```
# 注释以#开头
域名 记录类型 值
```

示例：

```
example.com. A 192.168.1.1
www.example.com. A 192.168.1.2
*.test.com. A 192.168.2.1
```

注意：
- 域名后面的点（.）是可选的
- 目前仅支持A记录类型
- 通配符域名使用星号（*）表示

## 测试

启动DNS服务器后，可以使用以下命令测试：

```bash
# 使用dig命令测试
dig @127.0.0.1 -p 53 example.com

# 使用nslookup命令测试
nslookup example.com 127.0.0.1
```

## 注意事项

- 在Linux/macOS系统上，绑定53端口需要root权限
- 此DNS服务器仅用于学习和测试目的，不建议在生产环境中使用
- 当前版本仅支持UDP协议和A记录类型

## 扩展

可以通过修改`dns_server.py`文件来扩展功能，例如：

- 添加对更多DNS记录类型的支持（AAAA、MX、CNAME等）
- 实现DNS缓存机制
- 添加更多的安全特性
- 支持TCP协议

## 许可证

MIT