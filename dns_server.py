#!/usr/bin/env python3
"""
简单的DNS服务器实现，基于dnslib库
支持基本的A记录解析和上游DNS转发
"""

import argparse
import datetime
import sys
import time
import threading
import traceback
from typing import Dict, Optional

try:
    from dnslib import DNSLabel, QTYPE, RR, dns
    from dnslib.server import DNSServer, DNSHandler, BaseResolver, DNSLogger
except ImportError:
    print("请安装dnslib: pip install dnslib")
    sys.exit(1)

class RecordResolver(BaseResolver):
    """
    自定义DNS解析器，支持静态记录和上游DNS转发
    """
    def __init__(self, zone_file: str = None, upstream: str = None):
        """
        初始化解析器
        
        Args:
            zone_file: 区域文件路径，包含静态DNS记录
            upstream: 上游DNS服务器地址，格式为"ip:port"
        """
        self.records = {}  # 存储静态DNS记录
        self.upstream = upstream
        
        # 如果提供了区域文件，加载静态记录
        if zone_file:
            self.load_zone_file(zone_file)
    
    def load_zone_file(self, zone_file: str):
        """
        从区域文件加载静态DNS记录
        
        格式示例:
        example.com. A 192.168.1.1
        *.example.com. A 192.168.1.2
        """
        try:
            with open(zone_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    
                    domain, record_type, value = parts[0], parts[1], parts[2]
                    if domain.endswith('.'):
                        domain = domain[:-1]
                    
                    # 目前只支持A记录
                    if record_type == 'A':
                        self.add_record(domain, value)
        except Exception as e:
            print(f"加载区域文件出错: {e}")
    
    def add_record(self, domain: str, ip_address: str):
        """添加一条A记录"""
        self.records[domain] = ip_address
        print(f"添加记录: {domain} -> {ip_address}")
    
    def resolve(self, request, handler):
        """
        解析DNS请求
        
        如果请求的域名在静态记录中，返回对应的IP
        否则，如果配置了上游DNS，转发请求
        """
        reply = request.reply()
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        
        # 将域名转换为字符串，并移除末尾的点
        domain = str(qname).rstrip('.')
        
        # 检查是否有匹配的静态记录
        if domain in self.records and qtype == 'A':
            ip = self.records[domain]
            print(f"找到静态记录: {domain} -> {ip}")
            
            # 创建A记录响应
            reply.add_answer(RR(
                rname=qname,
                rtype=getattr(QTYPE, qtype),
                rclass=1,  # IN类
                ttl=60,    # TTL为60秒
                rdata=dns.A(ip)
            ))
        # 检查通配符记录
        elif qtype == 'A':
            # 尝试查找通配符记录
            for pattern, ip in self.records.items():
                if pattern.startswith('*') and domain.endswith(pattern[1:]):
                    print(f"找到通配符记录: {pattern} -> {ip} (匹配 {domain})")
                    reply.add_answer(RR(
                        rname=qname,
                        rtype=getattr(QTYPE, qtype),
                        rclass=1,
                        ttl=60,
                        rdata=dns.A(ip)
                    ))
                    break
            else:
                # 如果没有找到匹配的记录，尝试上游DNS
                if self.upstream:
                    try:
                        print(f"转发请求到上游DNS: {domain}")
                        from dnslib.dns import DNSRecord
                        upstream_request = DNSRecord.question(domain)
                        upstream_reply = upstream_request.send(self.upstream.split(':')[0], 
                                                             int(self.upstream.split(':')[1]) if ':' in self.upstream else 53,
                                                             timeout=5)
                        upstream_reply = DNSRecord.parse(upstream_reply)
                        
                        # 复制上游响应的答案、权威和附加记录
                        for rr in upstream_reply.rr:
                            reply.add_answer(rr)
                        for auth in upstream_reply.auth:
                            reply.add_auth(auth)
                        for ar in upstream_reply.ar:
                            reply.add_ar(ar)
                    except Exception as e:
                        print(f"上游DNS查询失败: {e}")
        
        return reply

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简单的DNS服务器')
    parser.add_argument('--port', '-p', type=int, default=53,
                      help='监听端口 (默认: 53)')
    parser.add_argument('--address', '-a', default='0.0.0.0',
                      help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--zone', '-z', default=None,
                      help='区域文件路径')
    parser.add_argument('--upstream', '-u', default='8.8.8.8:53',
                      help='上游DNS服务器 (默认: 8.8.8.8:53)')
    
    args = parser.parse_args()
    
    resolver = RecordResolver(args.zone, args.upstream)
    
    # 添加一些默认记录用于测试
    resolver.add_record('example.com', '192.168.1.1')
    resolver.add_record('*.example.com', '192.168.1.2')
    
    # 创建DNS服务器
    logger = DNSLogger()
    server = DNSServer(resolver, port=args.port, address=args.address, logger=logger)
    
    print(f"启动DNS服务器在 {args.address}:{args.port}")
    print(f"上游DNS服务器: {args.upstream}")
    if args.zone:
        print(f"加载区域文件: {args.zone}")
    
    try:
        # 启动服务器
        server.start_thread()
        
        # 保持主线程运行
        while server.isAlive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("接收到中断信号，关闭服务器...")
    finally:
        server.stop()
        print("DNS服务器已停止")

if __name__ == '__main__':
    main()