"""
svr.py — PyMsi 虚拟服务器模块 (v2.6.0)

把文件夹设成服务器上的东西。
服务器最高 SSD = 15 GB，文件夹最多 15 GB，多了报异常 (不崩溃)。

可以新建空服务器。
SSD 硬盘大小随便定: 最大 10 GB，最小 5 KB。
本质不是真的占那么多 GB，只是在硬盘里"画"一个能用的区域。
如果硬盘太小没法直接调到 15 GB，就新建虚拟盘放进去。

专属文件格式:
  .svr  — 服务器配置文件
  .ssd  — 虚拟 SSD 磁盘镜像

用法:
    import PyMsi as PM

    # 新建空服务器
    svr = PM.svr.create("my_server", ssd_size="5GB")

    # 把文件夹设成服务器内容
    svr = PM.svr.from_folder("my_server", "/path/to/folder")

    # 服务器操作
    svr.info()                    # 服务器信息
    svr.list_files()              # 列出文件
    svr.upload("local.txt", "remote.txt")   # 上传文件
    svr.download("remote.txt", "local.txt") # 下载文件
    svr.delete("remote.txt")      # 删除文件
    svr.mkdir("subdir")           # 建目录
    svr.used()                    # 已用空间
    svr.free()                    # 剩余空间

    # 调整 SSD 大小
    svr.resize("8GB")             # 调整 SSD 大小

    # 虚拟盘
    PM.svr.create_vdisk("vdisk", "10GB")

    # 服务器列表
    PM.svr.list_servers()

    # 演示
    PM.svr.demo()
"""

import os
import sys
import json
import time
import shutil
import hashlib
import secrets
import tempfile
import struct
import zlib
import platform
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

MAX_SERVER_SSD = 15 * 1024 * 1024 * 1024   # 15 GB — 服务器最高 SSD
MIN_SSD_SIZE  = 5 * 1024                     # 5 KB — 最小 SSD
MAX_SSD_SIZE  = 10 * 1024 * 1024 * 1024     # 10 GB — 最大单 SSD


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def _parse_size(size_str):
    """解析大小字符串 → 字节数

    支持: 5KB, 5K, 10MB, 10M, 2GB, 2G, 1TB, 1T
    大小写不敏感。
    """
    if isinstance(size_str, (int, float)):
        return int(size_str)

    s = size_str.strip().upper()
    s = s.replace(' ', '')

    units = {
        'B':  1,
        'KB': 1024,
        'K':  1024,
        'MB': 1024 * 1024,
        'M':  1024 * 1024,
        'GB': 1024 * 1024 * 1024,
        'G':  1024 * 1024 * 1024,
        'TB': 1024 * 1024 * 1024 * 1024,
        'T':  1024 * 1024 * 1024 * 1024,
    }

    for unit in sorted(units.keys(), key=len, reverse=True):
        if s.endswith(unit):
            num = s[:-len(unit)]
            try:
                return int(float(num) * units[unit])
            except ValueError:
                pass

    # 纯数字 → 字节
    try:
        return int(float(s))
    except ValueError:
        raise ValueError(f"无法解析大小: {size_str}")


def _format_size(bytes_):
    """格式化字节数 → 人类可读"""
    if bytes_ < 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_)
    for u in units:
        if size < 1024 or u == 'TB':
            if u == 'B':
                return f"{int(size)} B"
            return f"{size:.2f} {u}"
        size /= 1024
    return f"{size:.2f} PB"


def _dir_size(path):
    """计算目录总大小 (字节)"""
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def _dir_file_count(path):
    """目录文件数"""
    count = 0
    for root, dirs, files in os.walk(path):
        count += len(files)
    return count


# ═══════════════════════════════════════════════════════════════
# 异常
# ═══════════════════════════════════════════════════════════════

class ServerError(Exception):
    """服务器错误 (不崩溃，只是异常)"""
    pass


class QuotaExceededError(ServerError):
    """超出 SSD 配额"""
    pass


class SSDError(ServerError):
    """SSD 操作错误"""
    pass


# ═══════════════════════════════════════════════════════════════
# 数据目录
# ═══════════════════════════════════════════════════════════════

def _servers_dir():
    """服务器数据根目录"""
    home = os.path.expanduser('~')
    d = os.path.join(home, '.pymsi_servers')
    os.makedirs(d, exist_ok=True)
    return d


def _server_dir(name):
    """单个服务器目录"""
    return os.path.join(_servers_dir(), name)


def _server_config_path(name):
    """服务器配置文件 (.svr) 路径"""
    return os.path.join(_servers_dir(), f'{name}.svr')


def _vdisk_dir():
    """虚拟盘目录"""
    d = os.path.join(_servers_dir(), '_vdisks')
    os.makedirs(d, exist_ok=True)
    return d


# ═══════════════════════════════════════════════════════════════
# 虚拟 SSD 磁盘 (.ssd 文件)
# ═══════════════════════════════════════════════════════════════
#
# 原理: 一个 .ssd 文件就是一个虚拟磁盘。
# 文件结构:
#   header: "SSD\0" + version(4B) + total_size(8B) + used_size(8B) + file_count(4B)
#   文件表: 每个文件条目 = name_len(2B) + name + offset(8B) + size(8B) + checksum(4B)
#   数据区: 文件内容

_SSD_MAGIC = b'SSD\x00'
_SSD_VERSION = 1
_SSD_HEADER_SIZE = 28  # 4 + 4 + 8 + 8 + 4


def create_ssd(path, size_bytes):
    """创建虚拟 SSD 磁盘文件 (.ssd)

    Args:
        path: .ssd 文件路径
        size_bytes: 总大小 (字节)

    Returns:
        dict: SSD 信息
    """
    # 验证大小
    if size_bytes < MIN_SSD_SIZE:
        raise SSDError(f"SSD 大小不能小于 {_format_size(MIN_SSD_SIZE)}")
    if size_bytes > MAX_SSD_SIZE:
        raise SSDError(f"SSD 大小不能超过 {_format_size(MAX_SSD_SIZE)}")

    # 创建文件 (稀疏文件，不实际占满空间)
    with open(path, 'wb') as f:
        # 写 header
        f.write(_SSD_MAGIC)
        f.write(struct.pack('<I', _SSD_VERSION))   # version
        f.write(struct.pack('<Q', size_bytes))      # total_size
        f.write(struct.pack('<Q', _SSD_HEADER_SIZE))  # used (header itself)
        f.write(struct.pack('<I', 0))                # file_count
        # 不填充满，用稀疏方式 — 直接跳到末尾写一个标记
        if size_bytes > _SSD_HEADER_SIZE:
            f.seek(size_bytes - 1)
            f.write(b'\x00')

    return {
        'path': path,
        'total': size_bytes,
        'used': _SSD_HEADER_SIZE,
        'free': size_bytes - _SSD_HEADER_SIZE,
        'files': 0,
    }


def _read_ssd_header(path):
    """读取 SSD header"""
    with open(path, 'rb') as f:
        magic = f.read(4)
        if magic != _SSD_MAGIC:
            raise SSDError(f"不是有效的 SSD 文件: {path}")
        version = struct.unpack('<I', f.read(4))[0]
        total = struct.unpack('<Q', f.read(8))[0]
        used = struct.unpack('<Q', f.read(8))[0]
        file_count = struct.unpack('<I', f.read(4))[0]
    return {
        'version': version,
        'total': total,
        'used': used,
        'free': total - used,
        'file_count': file_count,
    }


def _write_ssd_header(path, header):
    """写入 SSD header"""
    with open(path, 'r+b') as f:
        f.write(_SSD_MAGIC)
        f.write(struct.pack('<I', header.get('version', _SSD_VERSION)))
        f.write(struct.pack('<Q', header['total']))
        f.write(struct.pack('<Q', header['used']))
        f.write(struct.pack('<I', header['file_count']))


def ssd_info(path):
    """获取 SSD 信息"""
    header = _read_ssd_header(path)
    return {
        'path': path,
        'total': header['total'],
        'used': header['used'],
        'free': header['free'],
        'files': header['file_count'],
        'version': header['version'],
        'total_human': _format_size(header['total']),
        'used_human': _format_size(header['used']),
        'free_human': _format_size(header['free']),
    }


def ssd_resize(path, new_size_bytes):
    """调整 SSD 大小

    注意: 只能调大到 MAX_SSD_SIZE，调小会检查已用空间。
    """
    if new_size_bytes < MIN_SSD_SIZE:
        raise SSDError(f"SSD 大小不能小于 {_format_size(MIN_SSD_SIZE)}")
    if new_size_bytes > MAX_SSD_SIZE:
        raise SSDError(f"SSD 大小不能超过 {_format_size(MAX_SSD_SIZE)}")

    header = _read_ssd_header(path)

    if new_size_bytes < header['used']:
        raise SSDError(
            f"无法缩小到 {_format_size(new_size_bytes)}: "
            f"已用 {_format_size(header['used'])}"
        )

    # 调整文件大小
    with open(path, 'r+b') as f:
        f.truncate(new_size_bytes)

    # 更新 header
    header['total'] = new_size_bytes
    header['free'] = new_size_bytes - header['used']
    _write_ssd_header(path, header)

    return ssd_info(path)


def ssd_check(path):
    """检查 SSD 完整性"""
    try:
        header = _read_ssd_header(path)
        file_size = os.path.getsize(path)
        return {
            'valid': True,
            'header_total': header['total'],
            'file_size': file_size,
            'match': header['total'] == file_size,
            'version': header['version'],
            'file_count': header['file_count'],
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}


# ═══════════════════════════════════════════════════════════════
# 服务器类
# ═══════════════════════════════════════════════════════════════

class Server:
    """虚拟服务器

    把一个文件夹设成服务器上的东西。
    最高 SSD = 15 GB，超过报异常。
    """

    def __init__(self, name, ssd_size=None, folder=None):
        """创建服务器 (内部用，用 create/from_folder 工厂方法)"""
        self.name = name
        self._dir = _server_dir(name)
        self._config_path = _server_config_path(name)
        self._ssd_path = None
        self._use_vdisk = False

    def _load_config(self):
        """加载配置"""
        if not os.path.exists(self._config_path):
            return None
        with open(self._config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_config(self, config):
        """保存配置"""
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    # ─── 信息 ───

    def info(self):
        """服务器信息"""
        config = self._load_config()
        if not config:
            return {'name': self.name, 'status': 'error', 'error': '配置丢失'}

        used = _dir_size(self._dir)
        total = config.get('ssd_total', MAX_SERVER_SSD)
        files = _dir_file_count(self._dir)

        info = {
            'name': self.name,
            'status': 'running',
            'ssd_total': total,
            'ssd_total_human': _format_size(total),
            'ssd_used': used,
            'ssd_used_human': _format_size(used),
            'ssd_free': total - used,
            'ssd_free_human': _format_size(total - used),
            'ssd_usage_percent': round(used / total * 100, 1) if total else 0,
            'file_count': files,
            'created': config.get('created', ''),
            'use_vdisk': config.get('use_vdisk', False),
            'vdisk_path': config.get('vdisk_path', ''),
            'ssd_path': config.get('ssd_path', ''),
            'root': self._dir,
        }

        print(f"[Server] {self.name}")
        print(f"  状态: 运行中")
        print(f"  SSD:  {info['ssd_used_human']} / {info['ssd_total_human']} "
              f"({info['ssd_usage_percent']}%)")
        print(f"  剩余: {info['ssd_free_human']}")
        print(f"  文件: {files} 个")
        if info['use_vdisk']:
            print(f"  模式: 虚拟盘 ({info['vdisk_path']})")
        else:
            print(f"  模式: 目录模式")
        print(f"  根目录: {self._dir}")

        return info

    def used(self):
        """已用空间 (字节)"""
        return _dir_size(self._dir)

    def free(self):
        """剩余空间 (字节)"""
        config = self._load_config()
        total = config.get('ssd_total', MAX_SERVER_SSD) if config else MAX_SERVER_SSD
        return max(0, total - self.used())

    def total(self):
        """总空间 (字节)"""
        config = self._load_config()
        return config.get('ssd_total', MAX_SERVER_SSD) if config else MAX_SERVER_SSD

    # ─── 文件操作 ───

    def _check_quota(self, additional_bytes=0):
        """检查配额，超出抛异常"""
        config = self._load_config()
        total = config.get('ssd_total', MAX_SERVER_SSD) if config else MAX_SERVER_SSD
        used = _dir_size(self._dir)
        if used + additional_bytes > total:
            raise QuotaExceededError(
                f"SSD 配额不足!\n"
                f"  总空间: {_format_size(total)}\n"
                f"  已用:   {_format_size(used)}\n"
                f"  剩余:   {_format_size(total - used)}\n"
                f"  需要:   {_format_size(additional_bytes)}\n"
                f"  (服务器最高 SSD = 15 GB)"
            )

    def upload(self, local_path, remote_path=''):
        """上传文件到服务器

        Args:
            local_path: 本地文件路径
            remote_path: 服务器上的路径 (空 = 文件名)

        Returns:
            bool: 是否成功
        """
        local_path = os.path.expanduser(local_path)

        if not os.path.exists(local_path):
            raise ServerError(f"本地文件不存在: {local_path}")

        # 计算要上传的大小
        if os.path.isdir(local_path):
            upload_size = _dir_size(local_path)
        else:
            upload_size = os.path.getsize(local_path)

        # 检查配额
        self._check_quota(upload_size)

        # 目标路径
        if not remote_path:
            remote_path = os.path.basename(local_path)
        dest = os.path.join(self._dir, remote_path.lstrip('/'))

        # 创建父目录
        os.makedirs(os.path.dirname(dest) or self._dir, exist_ok=True)

        # 复制
        if os.path.isdir(local_path):
            shutil.copytree(local_path, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(local_path, dest)

        print(f"[Server] ✓ 已上传: {remote_path} "
              f"({_format_size(upload_size)})")
        return True

    def download(self, remote_path, local_path):
        """从服务器下载文件

        Args:
            remote_path: 服务器上的路径
            local_path: 本地保存路径
        """
        src = os.path.join(self._dir, remote_path.lstrip('/'))

        if not os.path.exists(src):
            raise ServerError(f"服务器上不存在: {remote_path}")

        os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)

        if os.path.isdir(src):
            shutil.copytree(src, local_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src, local_path)

        size = _dir_size(src) if os.path.isdir(src) else os.path.getsize(src)
        print(f"[Server] ✓ 已下载: {remote_path} → {local_path} "
              f"({_format_size(size)})")
        return True

    def list_files(self, path='/'):
        """列出服务器上的文件"""
        full_path = os.path.join(self._dir, path.lstrip('/'))

        if not os.path.exists(full_path):
            raise ServerError(f"路径不存在: {path}")

        if os.path.isfile(full_path):
            size = os.path.getsize(full_path)
            print(f"[Server] {path} ({_format_size(size)})")
            return [{'name': os.path.basename(path), 'size': size, 'type': 'file'}]

        items = []
        for name in sorted(os.listdir(full_path)):
            fp = os.path.join(full_path, name)
            is_dir = os.path.isdir(fp)
            size = _dir_size(fp) if is_dir else os.path.getsize(fp)
            items.append({
                'name': name,
                'size': size,
                'size_human': _format_size(size),
                'type': 'dir' if is_dir else 'file',
            })

        rel = '/' if path == '/' else path
        print(f"[Server] {self.name}:{rel}")
        for item in items:
            icon = '📁' if item['type'] == 'dir' else '📄'
            print(f"  {icon} {item['name']:30s} {item['size_human']:>10s}")

        return items

    def delete(self, remote_path):
        """删除服务器上的文件/目录"""
        src = os.path.join(self._dir, remote_path.lstrip('/'))

        if not os.path.exists(src):
            raise ServerError(f"不存在: {remote_path}")

        if os.path.isdir(src):
            shutil.rmtree(src)
        else:
            os.remove(src)

        print(f"[Server] ✓ 已删除: {remote_path}")
        return True

    def mkdir(self, path):
        """创建目录"""
        full = os.path.join(self._dir, path.lstrip('/'))
        os.makedirs(full, exist_ok=True)
        print(f"[Server] ✓ 已创建目录: {path}")
        return True

    def read_file(self, remote_path):
        """读取文件内容"""
        src = os.path.join(self._dir, remote_path.lstrip('/'))
        if not os.path.exists(src):
            raise ServerError(f"不存在: {remote_path}")
        with open(src, 'r', encoding='utf-8') as f:
            return f.read()

    def write_file(self, remote_path, content):
        """写入文件内容"""
        # 先检查配额
        add_size = len(content.encode('utf-8'))
        self._check_quota(add_size)

        dest = os.path.join(self._dir, remote_path.lstrip('/'))
        os.makedirs(os.path.dirname(dest) or self._dir, exist_ok=True)

        with open(dest, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[Server] ✓ 已写入: {remote_path} "
              f"({_format_size(add_size)})")
        return True

    # ─── SSD 调整 ───

    def resize(self, new_size):
        """调整 SSD 大小

        Args:
            new_size: 新的大小 (如 "8GB", "500MB", 或字节数)
        """
        new_bytes = _parse_size(new_size)
        config = self._load_config()
        if not config:
            raise ServerError("服务器配置丢失")

        current_used = self.used()

        # 验证
        if new_bytes < MIN_SSD_SIZE:
            raise SSDError(f"SSD 大小不能小于 {_format_size(MIN_SSD_SIZE)}")
        if new_bytes > MAX_SERVER_SSD:
            raise SSDError(
                f"SSD 大小不能超过服务器最高限制: {_format_size(MAX_SERVER_SSD)}"
            )
        if new_bytes < current_used:
            raise SSDError(
                f"无法缩小到 {_format_size(new_bytes)}: "
                f"已用 {_format_size(current_used)}"
            )

        # 检查真实磁盘空间够不够
        real_disk_free = shutil.disk_usage(self._dir).free if hasattr(shutil, 'disk_usage') else float('inf')

        # 如果真实磁盘不够 15 GB，用虚拟盘
        if real_disk_free < MAX_SERVER_SSD and not config.get('use_vdisk'):
            print(f"[Server] ⚠  真实磁盘剩余不足 {_format_size(MAX_SERVER_SSD)}")
            print(f"         启用虚拟盘模式 (SSD 文件放在虚拟盘里)")
            vdisk_path = os.path.join(_vdisk_dir(), f'{self.name}.ssd')
            create_ssd(vdisk_path, new_bytes)
            config['use_vdisk'] = True
            config['vdisk_path'] = vdisk_path
            config['ssd_path'] = vdisk_path
        elif config.get('use_vdisk'):
            # 已有虚拟盘，调整大小
            ssd_resize(config['ssd_path'], new_bytes)

        # 更新配置
        config['ssd_total'] = new_bytes
        self._save_config(config)

        print(f"[Server] ✓ SSD 已调整为 {_format_size(new_bytes)}")
        print(f"         已用: {_format_size(current_used)}")
        print(f"         剩余: {_format_size(new_bytes - current_used)}")
        return True

    # ─── 服务器控制 ───

    def stop(self):
        """停止服务器"""
        config = self._load_config()
        if config:
            config['status'] = 'stopped'
            config['stopped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._save_config(config)
        print(f"[Server] ✓ {self.name} 已停止")
        return True

    def start(self):
        """启动服务器"""
        config = self._load_config()
        if config:
            config['status'] = 'running'
            config['started_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._save_config(config)
        print(f"[Server] ✓ {self.name} 已启动")
        return True

    def destroy(self):
        """销毁服务器 (删除所有数据)"""
        if os.path.exists(self._dir):
            shutil.rmtree(self._dir)
        if os.path.exists(self._config_path):
            os.remove(self._config_path)
        # 清理虚拟盘
        config = self._load_config()
        if config and config.get('vdisk_path') and os.path.exists(config['vdisk_path']):
            os.remove(config['vdisk_path'])
        print(f"[Server] ✓ 服务器 {self.name} 已销毁")
        return True

    def reset(self):
        """重置服务器 (清空所有文件，保留配置)"""
        for item in os.listdir(self._dir):
            path = os.path.join(self._dir, item)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        print(f"[Server] ✓ {self.name} 已重置 (文件已清空)")
        return True


# ═══════════════════════════════════════════════════════════════
# 工厂函数
# ═══════════════════════════════════════════════════════════════

def create(name, ssd_size="5GB"):
    """新建一个空服务器

    Args:
        name: 服务器名称
        ssd_size: SSD 大小 (如 "5GB", "500MB")
                  最大 10 GB，最小 5 KB

    Returns:
        Server: 服务器实例
    """
    size_bytes = _parse_size(ssd_size)

    # 验证
    if size_bytes < MIN_SSD_SIZE:
        raise SSDError(f"SSD 大小不能小于 {_format_size(MIN_SSD_SIZE)}")
    if size_bytes > MAX_SSD_SIZE:
        raise SSDError(f"SSD 大小不能超过 {_format_size(MAX_SSD_SIZE)} (单盘上限)")
    if size_bytes > MAX_SERVER_SSD:
        raise SSDError(f"服务器最高 SSD = {_format_size(MAX_SERVER_SSD)}")

    # 检查配置是否已存在
    config_path = _server_config_path(name)
    if os.path.exists(config_path):
        raise ServerError(f"服务器已存在: {name}")

    # 创建目录
    server_dir = _server_dir(name)
    os.makedirs(server_dir, exist_ok=True)

    # 检查真实磁盘空间
    real_disk_free = float('inf')
    if hasattr(shutil, 'disk_usage'):
        try:
            real_disk_free = shutil.disk_usage(server_dir).free
        except Exception:
            pass

    use_vdisk = False
    vdisk_path = ''
    ssd_path = ''

    # 如果真实磁盘不够 15 GB，创建虚拟盘
    if real_disk_free < MAX_SERVER_SSD:
        print(f"[Server] ⚠  真实磁盘剩余 {_format_size(real_disk_free)}")
        print(f"         小于 {_format_size(MAX_SERVER_SSD)}，启用虚拟盘模式")
        print(f"         (SSD 文件放在虚拟盘里，不实际占满空间)")
        vdisk_path = os.path.join(_vdisk_dir(), f'{name}.ssd')
        create_ssd(vdisk_path, size_bytes)
        use_vdisk = True
        ssd_path = vdisk_path

    # 配置
    config = {
        'name': name,
        'ssd_total': size_bytes,
        'created': time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'running',
        'use_vdisk': use_vdisk,
        'vdisk_path': vdisk_path,
        'ssd_path': ssd_path,
        'max_ssd': MAX_SERVER_SSD,
        'version': '1.0',
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    svr = Server(name)
    print(f"[Server] ✓ 服务器 {name} 已创建")
    print(f"         SSD: {_format_size(size_bytes)}")
    print(f"         模式: {'虚拟盘' if use_vdisk else '目录'}")
    print(f"         根目录: {server_dir}")

    return svr


def from_folder(name, folder_path, ssd_size=None):
    """把文件夹设成服务器上的东西

    Args:
        name: 服务器名称
        folder_path: 本地文件夹路径
        ssd_size: SSD 大小 (None = 自动计算，不超过 15GB)

    Returns:
        Server: 服务器实例
    """
    folder_path = os.path.abspath(os.path.expanduser(folder_path))

    if not os.path.exists(folder_path):
        raise ServerError(f"文件夹不存在: {folder_path}")
    if not os.path.isdir(folder_path):
        raise ServerError(f"不是目录: {folder_path}")

    # 计算文件夹大小
    folder_size = _dir_size(folder_path)

    # 检查是否超过 15 GB
    if folder_size > MAX_SERVER_SSD:
        raise QuotaExceededError(
            f"文件夹大小 {_format_size(folder_size)} 超过服务器最高 SSD ({_format_size(MAX_SERVER_SSD)})!\n"
            f"请减小文件夹大小后重试。"
        )

    # 确定 SSD 大小
    if ssd_size:
        size_bytes = _parse_size(ssd_size)
        if size_bytes < folder_size:
            raise SSDError(
                f"SSD 大小 {_format_size(size_bytes)} 小于文件夹大小 {_format_size(folder_size)}"
            )
        if size_bytes > MAX_SERVER_SSD:
            raise SSDError(f"SSD 大小不能超过 {_format_size(MAX_SERVER_SSD)}")
    else:
        # 自动: 取文件夹大小和 5GB 的较大值，但不超 15GB
        size_bytes = max(folder_size, 5 * 1024 * 1024 * 1024)
        size_bytes = min(size_bytes, MAX_SERVER_SSD)

    # 创建服务器
    svr = create(name, ssd_size=str(size_bytes) + 'B')

    # 复制文件夹内容
    server_dir = _server_dir(name)
    for item in os.listdir(folder_path):
        src = os.path.join(folder_path, item)
        dst = os.path.join(server_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    print(f"[Server] ✓ 文件夹已部署到服务器: {name}")
    print(f"         源文件夹: {folder_path}")
    print(f"         文件大小: {_format_size(folder_size)}")
    print(f"         SSD 总大小: {_format_size(size_bytes)}")

    return svr


def get(name):
    """获取已存在的服务器"""
    config_path = _server_config_path(name)
    if not os.path.exists(config_path):
        raise ServerError(f"服务器不存在: {name}")
    return Server(name)


def list_servers():
    """列出所有服务器"""
    sdir = _servers_dir()
    servers = []
    for f in os.listdir(sdir):
        if f.endswith('.svr'):
            name = f[:-4]
            try:
                with open(os.path.join(sdir, f), 'r', encoding='utf-8') as fp:
                    config = json.load(fp)
                used = _dir_size(_server_dir(name))
                total = config.get('ssd_total', 0)
                status = config.get('status', 'running')
                servers.append({
                    'name': name,
                    'status': status,
                    'ssd_total': total,
                    'ssd_total_human': _format_size(total),
                    'ssd_used': used,
                    'ssd_used_human': _format_size(used),
                    'files': _dir_file_count(_server_dir(name)),
                })
            except Exception:
                servers.append({'name': name, 'status': 'error'})

    print(f"[Server] 服务器列表 ({len(servers)} 个):")
    if not servers:
        print("  (暂无服务器)")
    for s in servers:
        icon = '🟢' if s.get('status') == 'running' else '🔴'
        print(f"  {icon} {s['name']:20s} "
              f"{s.get('ssd_used_human', '?'):>8s} / {s.get('ssd_total_human', '?'):>8s} "
              f"({s.get('files', 0)} 文件)")

    return servers


def delete_server(name):
    """删除服务器"""
    svr = get(name)
    svr.destroy()
    return True


# ═══════════════════════════════════════════════════════════════
# 虚拟盘管理
# ═══════════════════════════════════════════════════════════════

def create_vdisk(name, size):
    """创建虚拟盘 (.ssd 文件)

    Args:
        name: 虚拟盘名称
        size: 大小 (如 "10GB")
    """
    size_bytes = _parse_size(size)
    path = os.path.join(_vdisk_dir(), f'{name}.ssd')

    if os.path.exists(path):
        raise ServerError(f"虚拟盘已存在: {name}")

    info = create_ssd(path, size_bytes)

    print(f"[Server] ✓ 虚拟盘已创建: {name}")
    print(f"         文件: {path}")
    print(f"         大小: {_format_size(size_bytes)} (稀疏文件)")

    return info


def list_vdisks():
    """列出所有虚拟盘"""
    vd = _vdisk_dir()
    disks = []
    for f in os.listdir(vd):
        if f.endswith('.ssd'):
            name = f[:-4]
            path = os.path.join(vd, f)
            try:
                info = ssd_info(path)
                disks.append(info)
            except Exception:
                disks.append({'name': name, 'valid': False})

    print(f"[Server] 虚拟盘列表 ({len(disks)} 个):")
    for d in disks:
        if d.get('valid', True):
            print(f"  💾 {d['path'].split('/')[-1]:30s} "
                  f"{d['used_human']:>8s} / {d['total_human']:>8s}")
        else:
            print(f"  ❌ {d['name']:30s} (损坏)")

    return disks


def delete_vdisk(name):
    """删除虚拟盘"""
    path = os.path.join(_vdisk_dir(), f'{name}.ssd')
    if not os.path.exists(path):
        raise ServerError(f"虚拟盘不存在: {name}")
    os.remove(path)
    print(f"[Server] ✓ 虚拟盘已删除: {name}")
    return True


# ═══════════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════════

def demo():
    """svr 模块演示"""
    print()
    print("=" * 60)
    print("  PyMsi 虚拟服务器 (svr) 演示")
    print("  SSD 最高 15GB | 虚拟盘 | 配额管理")
    print("=" * 60)

    # 1. 新建空服务器
    print(f"\n  [1] 新建空服务器 (SSD = 100MB):")
    svr = create("demo_svr", ssd_size="100MB")

    # 2. 上传文件
    print(f"\n  [2] 上传文件:")
    tmp = tempfile.mkdtemp()
    test_file = os.path.join(tmp, "hello.txt")
    with open(test_file, 'w') as f:
        f.write("Hello from server!\n" * 100)
    svr.upload(test_file, "hello.txt")

    # 3. 上传文件夹
    sub = os.path.join(tmp, "data")
    os.makedirs(sub, exist_ok=True)
    for i in range(5):
        with open(os.path.join(sub, f"file{i}.txt"), 'w') as f:
            f.write(f"file {i} content\n" * 50)
    svr.upload(sub, "data")

    # 4. 列出文件
    print(f"\n  [3] 列出文件:")
    svr.list_files()

    # 5. 服务器信息
    print(f"\n  [4] 服务器信息:")
    svr.info()

    # 6. 调整 SSD 大小
    print(f"\n  [5] 调整 SSD → 200MB:")
    svr.resize("200MB")

    # 7. 写入大文件测试配额
    print(f"\n  [6] 测试配额限制 (尝试写入超大文件):")
    big_content = "X" * (150 * 1024 * 1024)  # 150MB
    try:
        svr.write_file("big_file.txt", big_content)
    except QuotaExceededError as e:
        print(f"      ✓ 正确抛出异常 (不崩溃):")
        for line in str(e).split('\n'):
            print(f"        {line}")

    # 8. 下载文件
    print(f"\n  [7] 下载文件:")
    download_path = os.path.join(tmp, "downloaded.txt")
    svr.download("hello.txt", download_path)
    print(f"      下载大小: {os.path.getsize(download_path)} bytes")

    # 9. 读取文件
    print(f"\n  [8] 读取文件内容 (前50字符):")
    content = svr.read_file("hello.txt")
    print(f"      {content[:50]}...")

    # 10. 服务器列表
    print(f"\n  [9] 所有服务器:")
    list_servers()

    # 11. 虚拟盘
    print(f"\n  [10] 虚拟盘:")
    create_vdisk("test_vdisk", "50MB")
    list_vdisks()

    # 清理
    svr.destroy()
    delete_vdisk("test_vdisk")
    shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'='*60}")
    print("  虚拟服务器演示完成! 🖥️")
    print("  PM.svr.create('name', '5GB')         # 新建空服务器")
    print("  PM.svr.from_folder('name', 'path')   # 文件夹→服务器")
    print("  svr.upload(local, remote)            # 上传")
    print("  svr.download(remote, local)          # 下载")
    print("  svr.info()                           # 服务器信息")
    print("  svr.resize('8GB')                    # 调整SSD")
    print("  svr.list_files()                     # 列文件")
    print("  PM.svr.create_vdisk('vd', '10GB')   # 虚拟盘")
    print("  PM.svr.list_servers()                # 服务器列表")
    print("  PM.svr.demo()                        # 演示")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _SvrModule:
    """PyMsi.svr — 虚拟服务器模块

    把文件夹设成服务器上的东西。
    服务器最高 SSD = 15 GB，多了直接报异常 (不崩溃)。
    SSD 硬盘大小随便定: 最大 10 GB，最小 5 KB。
    本质是在硬盘里画一个能用的区域。
    如果硬盘太小没法直接调到 15 GB，新建虚拟盘放进去。

    专属文件:
      .svr — 服务器配置文件
      .ssd — 虚拟 SSD 磁盘镜像

    用法:
        # 新建空服务器
        svr = PM.svr.create("my_server", ssd_size="5GB")

        # 把文件夹设成服务器内容
        svr = PM.svr.from_folder("my_server", "/path/to/folder")

        # 服务器操作
        svr.info()
        svr.list_files()
        svr.upload("local.txt", "remote.txt")
        svr.download("remote.txt", "local.txt")
        svr.delete("remote.txt")
        svr.mkdir("subdir")
        svr.resize("8GB")
        svr.used()
        svr.free()

        # 虚拟盘
        PM.svr.create_vdisk("vdisk", "10GB")
        PM.svr.list_vdisks()

        # 管理
        PM.svr.list_servers()
        PM.svr.delete_server("name")

        # 演示
        PM.svr.demo()
    """

    def __repr__(self):
        return "<PyMsi.svr [虚拟服务器] v2.6.0>"

    def __call__(self, name=None):
        """获取或创建服务器"""
        if name is None:
            list_servers()
            return None
        try:
            return get(name)
        except ServerError:
            print(f"[Server] 服务器 {name} 不存在，使用 PM.svr.create() 创建")
            return None

    def create(self, name, ssd_size="5GB"):
        """新建空服务器"""
        return create(name, ssd_size)

    def from_folder(self, name, folder_path, ssd_size=None):
        """把文件夹设成服务器内容"""
        return from_folder(name, folder_path, ssd_size)

    def get(self, name):
        """获取已存在的服务器"""
        return get(name)

    def list_servers(self):
        """列出所有服务器"""
        return list_servers()

    def delete_server(self, name):
        """删除服务器"""
        return delete_server(name)

    def create_vdisk(self, name, size):
        """创建虚拟盘"""
        return create_vdisk(name, size)

    def list_vdisks(self):
        """列出虚拟盘"""
        return list_vdisks()

    def delete_vdisk(self, name):
        """删除虚拟盘"""
        return delete_vdisk(name)

    def ssd_info(self, path):
        """SSD 信息"""
        return ssd_info(path)

    def ssd_check(self, path):
        """检查 SSD 完整性"""
        return ssd_check(path)

    def demo(self):
        """演示"""
        return demo()

    def parse_size(self, size_str):
        """解析大小字符串"""
        return _parse_size(size_str)

    def format_size(self, bytes_):
        """格式化字节数"""
        return _format_size(bytes_)

    # 常量
    @property
    def MAX_SSD(self):
        """服务器最高 SSD (15 GB)"""
        return MAX_SERVER_SSD

    @property
    def MAX_SSD_HUMAN(self):
        return _format_size(MAX_SERVER_SSD)

    @property
    def MIN_SSD_SIZE(self):
        """最小 SSD (5 KB)"""
        return MIN_SSD_SIZE

    @property
    def MAX_SSD_SIZE(self):
        """最大单 SSD (10 GB)"""
        return MAX_SSD_SIZE
