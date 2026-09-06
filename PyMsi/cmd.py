"""
cmd.py — 终端扩展引擎 (v2.4.0)

把 WINDOWS 的命令能在 LINUX 上面使用
本质就是把 WINDOWS 的命令全部映射成 LINUX 上面的功能

独特扩展:
  Pjsoi "你的python目录"
    把路径存到 .msh (自己的数据文件)，不是系统环境变量
    以后在这个终端里不用输全路径就能直接用 python

  Pytem "你的python目录"
    直接搞到系统 PATH，跳过 msh

专属终端文件:
  .mhn — 终端历史记录文件 (M History Node)
  .fsu — 终端快捷方式文件 (Fast Shell Unit)
  .msh — 终端配置文件 (My SHell)

跨平台:
  Windows: 调用 cmd/powershell，Win11 圆角 / Win10 方角
  Linux:   用系统自带终端 (gnome-terminal / konsole / xterm)
  macOS:   用 Terminal.app / iTerm2

纯 Python 标准库 + 系统 API，零第三方依赖。

用法:
    import PyMsi as PM

    # 启动终端
    PM.cmd()                    # 打开 PyMsi 终端
    PM.cmd("dir")               # 执行一条命令
    PM.cmd.run("notepad.exe")   # 运行程序 (跨平台)

    # Pjsoi: Python 目录加入 .msh
    PM.cmd.Pjsoi("C:/Python312")

    # Pytem: Python 目录加入系统 PATH
    PM.cmd.Pytem("C:/Python312")

    # .msh 配置
    PM.cmd.msh_path()           # 查看 .msh 路径
    PM.cmd.msh_list()           # 列出 .msh 里的路径
    PM.cmd.msh_add("路径")      # 添加路径到 .msh
    PM.cmd.msh_remove("路径")   # 从 .msh 移除路径

    # .mhn 历史记录
    PM.cmd.mhn()                # 查看历史
    PM.cmd.mhn_clear()          # 清空历史
    PM.cmd.mhn_export("out.mhn") # 导出历史

    # .fsu 快捷方式
    PM.cmd.fsu_save("name", "command")  # 保存快捷方式
    PM.cmd.fsu_run("name")               # 运行快捷方式
    PM.cmd.fsu_list()                    # 列出所有快捷方式
    PM.cmd.fsu_delete("name")            # 删除快捷方式

    # 跨平台命令
    PM.cmd.dir(".")              # 列目录 (dir/ls 通用)
    PM.cmd.copy("a", "b")        # 复制 (copy/cp 通用)
    PM.cmd.del_("file")          # 删除 (del/rm 通用)
    PM.cmd.md("dir")             # 建目录 (md/mkdir 通用)
    PM.cmd.rd("dir")             # 删目录 (rd/rmdir 通用)
    PM.cmd.type("file")          # 显示内容 (type/cat 通用)
    PM.cmd.echo("hello")         # 输出文本
    PM.cmd.cls()                 # 清屏 (cls/clear 通用)
    PM.cmd.ipconfig()            # 网络信息 (ipconfig/ifconfig/ip)

    # 演示
    PM.cmd.demo()
"""

import os
import sys
import subprocess
import shlex
import json
import time
import tempfile
import platform
import shutil


# ═══════════════════════════════════════════════════════════════
# 一、平台检测
# ═══════════════════════════════════════════════════════════════

def _get_os():
    """获取当前操作系统: 'windows' / 'linux' / 'macos'"""
    s = platform.system().lower()
    if 'win' in s:
        return 'windows'
    elif 'darwin' in s:
        return 'macos'
    elif 'linux' in s:
        return 'linux'
    else:
        return s


def _get_shell():
    """获取当前系统的默认 shell"""
    os_type = _get_os()
    if os_type == 'windows':
        return os.environ.get('COMSPEC', 'cmd.exe')
    elif os_type == 'macos':
        return os.environ.get('SHELL', '/bin/zsh')
    else:
        return os.environ.get('SHELL', '/bin/bash')


# ═══════════════════════════════════════════════════════════════
# 二、.msh 配置系统 (My SHell)
# ═══════════════════════════════════════════════════════════════
#
# .msh 文件存储用户的自定义路径和配置，不修改系统环境变量

def _msh_path():
    """获取 .msh 文件路径"""
    home = os.path.expanduser('~')
    return os.path.join(home, '.pymsi.msh')


def _msh_load():
    """加载 .msh 配置"""
    path = _msh_path()
    if not os.path.exists(path):
        return {'paths': [], 'aliases': {}, 'settings': {}}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'paths': [], 'aliases': {}, 'settings': {}}


def _msh_save(config):
    """保存 .msh 配置"""
    path = _msh_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def msh_path():
    """查看 .msh 文件路径"""
    p = _msh_path()
    print(f"[cmd] .msh 路径: {p}")
    print(f"       存在: {'是' if os.path.exists(p) else '否'}")
    return p


def msh_list():
    """列出 .msh 里的所有路径"""
    config = _msh_load()
    print(f"[cmd] .msh 中的路径 ({len(config['paths'])} 条):")
    for i, p in enumerate(config['paths'], 1):
        exists = '✓' if os.path.exists(p) else '✗'
        print(f"  {i}. {exists} {p}")
    if config.get('aliases'):
        print(f"\n[cmd] 别名 ({len(config['aliases'])} 个):")
        for name, cmd in config['aliases'].items():
            print(f"  {name} → {cmd}")
    return config


def msh_add(path):
    """添加路径到 .msh

    注意: 这不是系统环境变量，只在 PyMsi 终端里有效。
    """
    path = os.path.abspath(os.path.expanduser(path))
    config = _msh_load()

    if path in config['paths']:
        print(f"[cmd] 路径已在 .msh 中: {path}")
        return False

    if not os.path.exists(path):
        print(f"[cmd] ⚠  路径不存在，但仍然添加: {path}")

    config['paths'].append(path)
    _msh_save(config)
    print(f"[cmd] ✓ 已添加到 .msh: {path}")
    print(f"       (只在 PyMsi 终端中有效，不是系统环境变量)")
    return True


def msh_remove(path):
    """从 .msh 移除路径"""
    config = _msh_load()
    path = os.path.abspath(os.path.expanduser(path))

    if path not in config['paths']:
        # 尝试模糊匹配
        for p in list(config['paths']):
            if path in p or p.endswith(path):
                path = p
                break
        else:
            print(f"[cmd] 路径不在 .msh 中: {path}")
            return False

    config['paths'].remove(path)
    _msh_save(config)
    print(f"[cmd] ✓ 已从 .msh 移除: {path}")
    return True


def _msh_get_env():
    """获取包含 .msh 路径的环境变量字典"""
    config = _msh_load()
    env = os.environ.copy()
    if config['paths']:
        # 把 .msh 里的路径加到 PATH 最前面
        msh_paths = os.pathsep.join(config['paths'])
        old_path = env.get('PATH', '')
        env['PATH'] = msh_paths + os.pathsep + old_path
    return env


# ═══════════════════════════════════════════════════════════════
# 三、Pjsoi 和 Pytem — Python 路径管理
# ═══════════════════════════════════════════════════════════════

def Pjsoi(python_dir):
    """Pjsoi: Python 目录加入 .msh

    把 Python 目录存到 .msh (自己的数据文件)，不是系统环境变量。
    以后在 PyMsi 终端里不用输全路径就能直接用 python。

    Args:
        python_dir: Python 安装目录 (如 "C:/Python312")

    用法:
        PM.cmd.Pjsoi("C:/Python312")
        # 然后在 PyMsi 终端里就能直接用 python
    """
    python_dir = os.path.abspath(os.path.expanduser(python_dir))

    # 检查是不是有效的 Python 目录
    python_exe = os.path.join(python_dir, 'python.exe' if _get_os() == 'windows' else 'python3')
    if not os.path.exists(python_exe):
        python_exe2 = os.path.join(python_dir, 'python')
        if os.path.exists(python_exe2):
            python_exe = python_exe2
        else:
            print(f"[cmd] ⚠  未找到 python 可执行文件: {python_exe}")
            print(f"       仍然添加到 .msh")

    # 添加到 .msh
    result = msh_add(python_dir)

    # 同时添加 Scripts 目录 (Windows pip 等工具)
    scripts_dir = os.path.join(python_dir, 'Scripts' if _get_os() == 'windows' else 'bin')
    if os.path.exists(scripts_dir):
        config = _msh_load()
        if scripts_dir not in config['paths']:
            config['paths'].append(scripts_dir)
            _msh_save(config)
            print(f"[cmd] ✓ 同时添加 Scripts 目录: {scripts_dir}")

    if result:
        print()
        print(f"[cmd] Pjsoi 完成! ✓")
        print(f"       从现在起，在 PyMsi 终端里可以直接用 python")
        print(f"       (注意: 只在 PyMsi 终端里有效，不是系统环境变量)")
        print(f"       要加到系统 PATH 请用: PM.cmd.Pytem(\"{python_dir}\")")

    return result


def Pytem(python_dir):
    """Pytem: Python 目录直接加到系统 PATH

    跳过 .msh，直接搞到系统环境变量 PATH 里。

    ⚠️  会修改系统环境变量，需要管理员/root 权限才能全局生效。
    用户级别的 PATH 修改会写入用户环境变量。

    Args:
        python_dir: Python 安装目录

    用法:
        PM.cmd.Pytem("C:/Python312")
    """
    python_dir = os.path.abspath(os.path.expanduser(python_dir))

    if not os.path.isdir(python_dir):
        print(f"[cmd] ✗ 目录不存在: {python_dir}")
        return False

    os_type = _get_os()

    if os_type == 'windows':
        # Windows: 写入用户环境变量
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                'Environment', 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
            current_path, _ = winreg.QueryValueEx(key, 'Path')

            if python_dir in current_path:
                print(f"[cmd] 已经在系统 PATH 中: {python_dir}")
                winreg.CloseKey(key)
                return True

            new_path = current_path + ';' + python_dir
            winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)

            # 同时添加 Scripts
            scripts_dir = os.path.join(python_dir, 'Scripts')
            if os.path.exists(scripts_dir) and scripts_dir not in current_path:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                    'Environment', 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
                cur, _ = winreg.QueryValueEx(key, 'Path')
                winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, cur + ';' + scripts_dir)
                winreg.CloseKey(key)

            print(f"[cmd] ✓ 已添加到用户 PATH: {python_dir}")
            print(f"       (需要重新打开终端才能生效)")
            return True

        except ImportError:
            print(f"[cmd] ✗ 无法访问 Windows 注册表")
            return False
        except Exception as e:
            print(f"[cmd] ✗ 添加失败: {e}")
            return False

    else:
        # Linux / macOS: 写入 ~/.bashrc 或 ~/.zshrc
        shell = _get_shell()
        shell_name = os.path.basename(shell)
        if 'zsh' in shell_name:
            rc_file = os.path.expanduser('~/.zshrc')
        elif 'bash' in shell_name:
            rc_file = os.path.expanduser('~/.bashrc')
        else:
            rc_file = os.path.expanduser('~/.profile')

        line = f'export PATH="{python_dir}:$PATH"'

        # 检查是否已经添加
        if os.path.exists(rc_file):
            with open(rc_file, 'r') as f:
                content = f.read()
            if python_dir in content:
                print(f"[cmd] 已经在 {rc_file} 中")
                return True

        # 追加
        with open(rc_file, 'a') as f:
            f.write(f'\n# PyMsi Pytem added\n')
            f.write(line + '\n')
            # 同时加 bin 目录
            bin_dir = os.path.join(python_dir, 'bin')
            if os.path.exists(bin_dir):
                f.write(f'export PATH="{bin_dir}:$PATH"\n')

        print(f"[cmd] ✓ 已添加到 {rc_file}")
        print(f"       (运行 source {rc_file} 立即生效，或重新打开终端)")
        return True


# ═══════════════════════════════════════════════════════════════
# 四、跨平台命令映射 (Windows → Linux/Mac)
# ═══════════════════════════════════════════════════════════════

# Windows 命令 → 对应 Linux/Mac 命令的映射
_COMMAND_MAP = {
    # 文件操作
    'dir': 'ls -la',
    'dir /w': 'ls',
    'dir /p': 'ls | less',
    'dir /s': 'find .',
    'copy': 'cp',
    'xcopy': 'cp -r',
    'del': 'rm',
    'erase': 'rm',
    'ren': 'mv',
    'rename': 'mv',
    'move': 'mv',
    'md': 'mkdir -p',
    'mkdir': 'mkdir -p',
    'rd': 'rm -rf',
    'rmdir': 'rm -rf',
    'type': 'cat',
    'more': 'more',
    'findstr': 'grep',

    # 系统
    'cls': 'clear',
    'ver': 'uname -a',
    'systeminfo': 'uname -a',
    'ipconfig': 'ifconfig',
    'ipconfig /all': 'ifconfig -a',
    'ping': 'ping -c 4',
    'tracert': 'traceroute',
    'tasklist': 'ps aux',
    'taskkill': 'kill',
    'shutdown': 'shutdown',
    'shutdown /s': 'shutdown now',
    'shutdown /r': 'shutdown -r now',
    'shutdown /a': 'shutdown -c',

    # 网络
    'netstat': 'netstat',
    'netstat -ano': 'netstat -tulpn',
    'nslookup': 'nslookup',

    # 磁盘
    'chkdsk': 'fsck',
    'defrag': 'fstrim',
    'format': 'mkfs',

    # 用户
    'whoami': 'whoami',
    'net user': 'cat /etc/passwd',
    'net localgroup': 'groups',

    # 其他
    'echo': 'echo',
    'pause': 'read -p "Press any key to continue..."',
    'exit': 'exit',
    'cd': 'cd',
    'pushd': 'pushd',
    'popd': 'popd',
    'path': 'echo $PATH',
    'set': 'env',
    'color': 'true',  # Linux 终端默认有颜色
    'title': 'true',
    'prompt': 'true',
    'tree': 'tree',
    'fc': 'diff',
    'comp': 'diff',
    'attrib': 'chmod',
    'cacls': 'chown',
}


def _map_command(cmd_str):
    """将 Windows 风格命令映射为当前平台命令

    Args:
        cmd_str: 命令字符串 (如 "dir /w")

    Returns:
        str: 映射后的命令
    """
    os_type = _get_os()
    if os_type == 'windows':
        return cmd_str  # Windows 不用映射

    # 尝试完整匹配 (带参数)
    cmd_lower = cmd_str.lower().strip()

    # 从长到短匹配，避免 "dir" 匹配了 "dir /w" 还没匹配
    sorted_map = sorted(_COMMAND_MAP.keys(), key=len, reverse=True)
    for win_cmd in sorted_map:
        if cmd_lower == win_cmd:
            return _COMMAND_MAP[win_cmd]
        if cmd_lower.startswith(win_cmd + ' '):
            args = cmd_str[len(win_cmd):]
            mapped = _COMMAND_MAP[win_cmd]
            # 如果映射命令有自己的参数处理，直接拼接
            return mapped + args

    # 没匹配到，原样返回
    return cmd_str


# ═══════════════════════════════════════════════════════════════
# 五、命令执行
# ═══════════════════════════════════════════════════════════════

def run(command, cwd=None, capture=False, interactive=False):
    """执行命令 (跨平台)

    自动把 Windows 风格命令映射成当前平台命令。
    使用 .msh 中的 PATH 增强。

    Args:
        command: 命令字符串
        cwd: 工作目录
        capture: 是否捕获输出 (True 返回输出字符串)
        interactive: 是否交互模式 (直接继承 stdin/stdout)

    Returns:
        capture=True 时返回 (returncode, stdout, stderr)
        否则返回 returncode
    """
    # Windows 命令 → 当前平台命令
    mapped_cmd = _map_command(command)

    # 使用 .msh 增强的环境变量
    env = _msh_get_env()

    os_type = _get_os()

    if interactive:
        # 交互模式: 用系统 shell 执行
        if os_type == 'windows':
            result = subprocess.run(mapped_cmd, shell=True, cwd=cwd, env=env)
        else:
            result = subprocess.run(mapped_cmd, shell=True, cwd=cwd, env=env,
                                   executable=_get_shell())
        return result.returncode
    elif capture:
        # 捕获输出
        result = subprocess.run(
            mapped_cmd,
            shell=True,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr
    else:
        # 打印输出
        result = subprocess.run(
            mapped_cmd,
            shell=True,
            cwd=cwd,
            env=env,
            text=True,
        )
        return result.returncode


# ═══════════════════════════════════════════════════════════════
# 六、常用跨平台命令 (函数式)
# ═══════════════════════════════════════════════════════════════

def dir_(path='.'):
    """列目录 (dir / ls 通用)"""
    return run(f'dir {path}')


def copy_(src, dst):
    """复制文件 (copy / cp 通用)"""
    return run(f'copy "{src}" "{dst}"')


def del_(path):
    """删除文件 (del / rm 通用)"""
    return run(f'del "{path}"')


def md(path):
    """创建目录 (md / mkdir 通用)"""
    return run(f'md "{path}"')


def rd(path):
    """删除目录 (rd / rm -rf 通用)"""
    return run(f'rd "{path}"')


def type_(file):
    """显示文件内容 (type / cat 通用)"""
    return run(f'type "{file}"')


def echo(text):
    """输出文本"""
    return run(f'echo "{text}"')


def cls():
    """清屏 (cls / clear 通用)"""
    return run('cls')


def ipconfig_():
    """网络信息 (ipconfig / ifconfig / ip 通用)"""
    return run('ipconfig')


def tasklist_():
    """进程列表 (tasklist / ps 通用)"""
    return run('tasklist')


def ping_(host, count=4):
    """ping"""
    if _get_os() == 'windows':
        return run(f'ping -n {count} {host}')
    else:
        return run(f'ping -c {count} {host}')


# ═══════════════════════════════════════════════════════════════
# 七、.mhn 终端历史记录 (M History Node)
# ═══════════════════════════════════════════════════════════════

def _mhn_path():
    """获取 .mhn 文件路径"""
    home = os.path.expanduser('~')
    return os.path.join(home, '.pymsi.mhn')


def _mhn_load():
    """加载历史记录"""
    path = _mhn_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception:
        return []


def _mhn_append(command):
    """添加一条历史记录"""
    path = _mhn_path()
    with open(path, 'a', encoding='utf-8') as f:
        f.write(command + '\n')


def mhn(count=None):
    """查看终端历史记录 (.mhn)

    Args:
        count: 显示最近 N 条 (None = 全部)
    """
    history = _mhn_load()
    if count:
        history = history[-count:]

    print(f"[cmd] 终端历史记录 ({len(history)} 条, .mhn)")
    for i, cmd in enumerate(history, 1):
        print(f"  {i:4d}  {cmd}")

    return history


def mhn_clear():
    """清空历史记录"""
    path = _mhn_path()
    if os.path.exists(path):
        os.remove(path)
        print("[cmd] ✓ 历史记录已清空 (.mhn)")
    else:
        print("[cmd] 没有历史记录")
    return True


def mhn_export(output_path):
    """导出历史记录到 .mhn 文件"""
    history = _mhn_load()
    with open(output_path, 'w', encoding='utf-8') as f:
        for cmd in history:
            f.write(cmd + '\n')
    print(f"[cmd] ✓ 历史记录已导出: {output_path} ({len(history)} 条)")
    return output_path


def mhn_import(input_path):
    """从 .mhn 文件导入历史记录"""
    if not os.path.exists(input_path):
        print(f"[cmd] ✗ 文件不存在: {input_path}")
        return False
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    # 追加到当前历史
    path = _mhn_path()
    with open(path, 'a', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')
    print(f"[cmd] ✓ 已导入 {len(lines)} 条历史记录")
    return True


# ═══════════════════════════════════════════════════════════════
# 八、.fsu 快捷方式 (Fast Shell Unit)
# ═══════════════════════════════════════════════════════════════
#
# .fsu 文件格式: 保存一个命令的快捷方式
# 结构: JSON 格式，包含名称、命令、描述等

def _fsu_dir():
    """获取 .fsu 文件目录"""
    home = os.path.expanduser('~')
    d = os.path.join(home, '.pymsi_fsu')
    os.makedirs(d, exist_ok=True)
    return d


def fsu_save(name, command, description=''):
    """保存快捷方式为 .fsu 文件

    Args:
        name: 快捷方式名称
        command: 命令字符串
        description: 描述

    Returns:
        str: .fsu 文件路径
    """
    fsu_data = {
        'name': name,
        'command': command,
        'description': description,
        'created': time.ctime(),
        'os': _get_os(),
    }

    path = os.path.join(_fsu_dir(), f'{name}.fsu')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(fsu_data, f, ensure_ascii=False, indent=2)

    print(f"[cmd] ✓ 快捷方式已保存: {name}")
    print(f"       命令: {command}")
    print(f"       文件: {path}")
    return path


def fsu_load(name):
    """加载 .fsu 快捷方式"""
    path = os.path.join(_fsu_dir(), f'{name}.fsu')
    if not os.path.exists(path):
        # 尝试直接从文件路径加载
        if os.path.exists(name) and name.endswith('.fsu'):
            path = name
        else:
            return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def fsu_run(name, args=''):
    """运行 .fsu 快捷方式

    Args:
        name: 快捷方式名称或 .fsu 文件路径
        args: 附加参数
    """
    fsu = fsu_load(name)
    if fsu is None:
        print(f"[cmd] ✗ 快捷方式不存在: {name}")
        return 1

    command = fsu['command']
    if args:
        command = command + ' ' + args

    print(f"[cmd] FSU: {fsu['name']} → {command}")
    return run(command, interactive=True)


def fsu_list():
    """列出所有 .fsu 快捷方式"""
    d = _fsu_dir()
    files = [f for f in os.listdir(d) if f.endswith('.fsu')]
    files.sort()

    print(f"[cmd] 快捷方式列表 ({len(files)} 个):")
    if not files:
        print("  (暂无)")
        return []

    for f in files:
        path = os.path.join(d, f)
        try:
            with open(path, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            name = data.get('name', f.replace('.fsu', ''))
            cmd = data.get('command', '')
            desc = data.get('description', '')
            display = f"  {name:20s} → {cmd[:50]}"
            if desc:
                display += f" ({desc[:30]})"
            print(display)
        except Exception:
            print(f"  {f}  (损坏)")

    return files


def fsu_delete(name):
    """删除 .fsu 快捷方式"""
    path = os.path.join(_fsu_dir(), f'{name}.fsu')
    if not os.path.exists(path):
        print(f"[cmd] ✗ 快捷方式不存在: {name}")
        return False
    os.remove(path)
    print(f"[cmd] ✓ 已删除快捷方式: {name}")
    return True


# ═══════════════════════════════════════════════════════════════
# 九、终端启动
# ═══════════════════════════════════════════════════════════════

def terminal():
    """启动 PyMsi 终端 (交互式)

    跨平台终端，支持:
      - Windows 命令在 Linux/Mac 上也能用
      - .msh 路径增强
      - .mhn 历史记录
      - .fsu 快捷方式
    """
    os_type = _get_os()
    print()
    print("═" * 60)
    print("  PyMsi 终端 (cmd)")
    print(f"  平台: {os_type}  |  Shell: {_get_shell()}")
    print("  输入 help 查看帮助, exit 退出")
    print("═" * 60)
    print()

    history = _mhn_load()
    msh_config = _msh_load()

    if msh_config['paths']:
        print(f"[.msh] 已加载 {len(msh_config['paths'])} 条路径增强")

    if history:
        print(f"[.mhn] 历史记录: {len(history)} 条")

    print()

    while True:
        try:
            cwd = os.getcwd()
            prompt = f"PyMsi:{cwd}$ "
            line = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        # 历史记录
        _mhn_append(line)

        # 特殊命令
        if line.lower() in ('exit', 'quit', 'bye'):
            break

        if line.lower() == 'help':
            _print_help()
            continue

        if line.lower() == 'msh':
            msh_list()
            continue

        if line.lower() == 'mhn':
            mhn()
            continue

        if line.lower() == 'fsu':
            fsu_list()
            continue

        if line.lower().startswith('pjsoi '):
            path = line[6:].strip().strip('"\'')
            Pjsoi(path)
            continue

        if line.lower().startswith('pytem '):
            path = line[6:].strip().strip('"\'')
            Pytem(path)
            continue

        if line.lower().startswith('fsu '):
            # fsu <name> [args...]
            parts = line[4:].split(None, 1)
            if parts:
                name = parts[0]
                args = parts[1] if len(parts) > 1 else ''
                fsu_run(name, args)
            continue

        if line.lower().startswith('cd '):
            target = line[3:].strip().strip('"\'')
            try:
                os.chdir(target)
            except Exception as e:
                print(f"cd: {e}")
            continue

        # 普通命令: 映射 + 执行
        try:
            run(line, interactive=True)
        except KeyboardInterrupt:
            print()
            continue

    print()
    print("[cmd] 再见！")


def _print_help():
    """打印帮助信息"""
    print()
    print("PyMsi 终端帮助:")
    print()
    print("  核心命令:")
    print("    help            显示帮助")
    print("    exit/quit       退出终端")
    print("    cd <dir>        切换目录")
    print()
    print("  独特扩展:")
    print("    Pjsoi <dir>     Python 目录加入 .msh (不是系统环境变量)")
    print("    Pytem <dir>     Python 目录加入系统 PATH")
    print("    msh             查看 .msh 配置")
    print("    mhn             查看历史记录 (.mhn)")
    print("    fsu             列出快捷方式 (.fsu)")
    print("    fsu <name>      运行快捷方式")
    print()
    print("  跨平台命令 (Windows 风格也能用):")
    print("    dir / copy / del / md / rd / type")
    print("    cls / ver / ipconfig / tasklist")
    print("    ping / tracert / netstat / nslookup")
    print("    findstr / fc / tree / attrib")
    print()
    print("  专属文件格式:")
    print("    .msh   终端配置 (路径/别名)")
    print("    .mhn   终端历史记录")
    print("    .fsu   快捷方式文件")
    print()


# ═══════════════════════════════════════════════════════════════
# 十、演示
# ═══════════════════════════════════════════════════════════════

def demo():
    """cmd 模块演示"""
    print()
    print("=" * 60)
    print("  PyMsi 终端扩展 (cmd) 演示")
    print("  Windows 命令也能在 Linux 上用 | .msh .mhn .fsu")
    print("=" * 60)

    # 1. 平台信息
    print(f"\n  [1] 平台信息:")
    print(f"      操作系统: {_get_os()}")
    print(f"      系统 Shell: {_get_shell()}")

    # 2. 命令映射演示
    print(f"\n  [2] 命令映射演示:")
    test_cmds = [
        'dir',
        'dir /w',
        'copy a.txt b.txt',
        'del test.txt',
        'md mydir',
        'rd mydir',
        'type file.txt',
        'cls',
        'ipconfig',
        'tasklist',
        'findstr "hello" file.txt',
        'ping example.com',
    ]
    for cmd in test_cmds:
        mapped = _map_command(cmd)
        same = cmd == mapped
        status = "相同" if same else f"→ {mapped}"
        print(f"      {cmd:30s} {status}")

    # 3. .msh 配置
    print(f"\n  [3] .msh 配置:")
    print(f"      .msh 路径: {_msh_path()}")
    config = _msh_load()
    print(f"      路径数: {len(config['paths'])}")
    print(f"      别名数: {len(config.get('aliases', {}))}")

    # 4. .fsu 快捷方式
    print(f"\n  [4] .fsu 快捷方式:")
    # 保存一个测试快捷方式
    test_fsu = os.path.join(tempfile.gettempdir(), 'test_hello.fsu')
    fsu_save('test_hello', 'echo "Hello from FSU!"', '测试快捷方式')
    fsu_list()
    # 清理测试
    fsu_delete('test_hello')

    # 5. .mhn 历史记录
    print(f"\n  [5] .mhn 历史记录:")
    print(f"      .mhn 路径: {_mhn_path()}")
    hist = _mhn_load()
    print(f"      历史记录数: {len(hist)}")

    # 6. 执行命令演示
    print(f"\n  [6] 执行命令演示 (dir/ls):")
    ret, out, err = run('dir', capture=True)
    lines = out.strip().split('\n')[:5]
    for line in lines:
        print(f"      {line[:60]}")
    if len(out.strip().split('\n')) > 5:
        print(f"      ... 还有 {len(out.strip().split(chr(10))) - 5} 行")

    print("\n" + "=" * 60)
    print("  cmd 演示完成! 🖥️")
    print("  PM.cmd()                → 启动交互终端")
    print("  PM.cmd.Pjsoi(path)      → Python 目录加入 .msh")
    print("  PM.cmd.Pytem(path)      → Python 目录加入系统 PATH")
    print("  PM.cmd.run(cmd)         → 执行命令 (跨平台)")
    print("  PM.cmd.fsu_save(n, c)   → 保存 .fsu 快捷方式")
    print("  PM.cmd.fsu_run(name)    → 运行 .fsu 快捷方式")
    print("  PM.cmd.mhn()            → 查看 .mhn 历史")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# 十一、PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _CmdModule:
    """PyMsi.cmd — 终端扩展引擎

    把 WINDOWS 的命令能在 LINUX 上面使用
    本质就是把 WINDOWS 的命令全部映射成 LINUX 上面的功能

    独特扩展:
      Pjsoi "你的python目录"  → 存到 .msh (不是系统环境变量)
      Pytem "你的python目录"  → 直接加到系统 PATH

    专属终端文件:
      .msh  — 配置文件 (路径/别名)
      .mhn  — 历史记录
      .fsu  — 快捷方式

    用法:
        PM.cmd()                        # 启动交互终端
        PM.cmd.run("dir")               # 执行命令 (跨平台)
        PM.cmd.Pjsoi("C:/Python312")    # Python → .msh
        PM.cmd.Pytem("C:/Python312")    # Python → 系统 PATH
        PM.cmd.msh_list()               # 查看 .msh
        PM.cmd.mhn()                    # 查看 .mhn 历史
        PM.cmd.fsu_save("x", "cmd")     # 保存 .fsu
        PM.cmd.fsu_run("x")             # 运行 .fsu
        PM.cmd.demo()                   # 演示
    """

    def __repr__(self):
        return "<PyMsi.cmd [终端扩展引擎] v2.4.0>"

    def __call__(self, command=None):
        """启动终端或执行命令"""
        if command is None:
            return terminal()
        else:
            return run(command, interactive=True)

    def run(self, command, cwd=None, capture=False, interactive=False):
        """执行命令"""
        return run(command, cwd=cwd, capture=capture, interactive=interactive)

    def terminal(self):
        """启动交互终端"""
        return terminal()

    def Pjsoi(self, python_dir):
        """Pjsoi: Python 目录加入 .msh"""
        return Pjsoi(python_dir)

    def Pytem(self, python_dir):
        """Pytem: Python 目录加入系统 PATH"""
        return Pytem(python_dir)

    # .msh 配置
    def msh_path(self):
        return msh_path()

    def msh_list(self):
        return msh_list()

    def msh_add(self, path):
        return msh_add(path)

    def msh_remove(self, path):
        return msh_remove(path)

    # .mhn 历史
    def mhn(self, count=None):
        return mhn(count)

    def mhn_clear(self):
        return mhn_clear()

    def mhn_export(self, path):
        return mhn_export(path)

    def mhn_import(self, path):
        return mhn_import(path)

    # .fsu 快捷方式
    def fsu_save(self, name, command, description=''):
        return fsu_save(name, command, description)

    def fsu_run(self, name, args=''):
        return fsu_run(name, args)

    def fsu_list(self):
        return fsu_list()

    def fsu_delete(self, name):
        return fsu_delete(name)

    # 常用命令
    def dir(self, path='.'):
        return dir_(path)

    def copy(self, src, dst):
        return copy_(src, dst)

    def delete(self, path):
        return del_(path)

    def md(self, path):
        return md(path)

    def rd(self, path):
        return rd(path)

    def type(self, file):
        return type_(file)

    def echo(self, text):
        return echo(text)

    def cls(self):
        return cls()

    def ipconfig(self):
        return ipconfig_()

    def tasklist(self):
        return tasklist_()

    def ping(self, host, count=4):
        return ping_(host, count)

    def demo(self):
        return demo()
