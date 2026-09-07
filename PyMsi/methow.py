"""
methow.py — MetHow 还原引擎 (v2.5.0)

快速还原系统，比冰点还原快，不像还原精灵那样慢。
可设置密码也可不设。
权限分教师/学生，学生必须通过教师同意。

一键还原: 直接恢复到最近快照
密码找回: 输入账号名 + 邮箱 → 密码自动发到邮箱

专属文件格式:
  .mhs — MetHow Snapshot (快照文件)
  .mhc — MetHow Config (配置文件)

用法:
    import PyMsi as PM

    # 快照
    PM.methow.snapshot("C:/mydir")       # 对目录拍快照
    PM.methow.snapshot(".")             # 当前目录

    # 还原
    PM.methow.restore()                 # 一键还原 (最近快照)
    PM.methow.restore("snap_id")        # 还原到指定快照

    # 密码
    PM.methow.set_password("mypwd")     # 设置密码
    PM.methow.verify_password("mypwd")  # 验证密码
    PM.methow.recover_password("user", "user@email.com")  # 找回密码

    # 权限
    PM.methow.add_teacher("张老师", "138xxxx", "teacher@email.com")
    PM.methow.add_student("小明", "student@email.com")
    PM.methow.request_approval("小明", "张老师")  # 学生请求教师同意
    PM.methow.approve("张老师", "小明")           # 教师同意

    # 管理
    PM.methow.list_snapshots()          # 列出所有快照
    PM.methow.delete_snapshot("id")     # 删除快照
    PM.methow.demo()                    # 演示
"""

import os
import sys
import json
import time
import shutil
import hashlib
import secrets
import tempfile
import platform
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ═══════════════════════════════════════════════════════════════
# 配置路径
# ═══════════════════════════════════════════════════════════════

def _methow_dir():
    """MetHow 数据目录"""
    home = os.path.expanduser('~')
    d = os.path.join(home, '.pymsi_methow')
    os.makedirs(d, exist_ok=True)
    return d


def _snapshot_dir():
    """快照存储目录"""
    d = os.path.join(_methow_dir(), 'snapshots')
    os.makedirs(d, exist_ok=True)
    return d


def _config_path():
    """配置文件路径 (.mhc)"""
    return os.path.join(_methow_dir(), 'config.mhc')


def _load_config():
    """加载配置"""
    path = _config_path()
    if not os.path.exists(path):
        return {
            'password_hash': None,
            'password_salt': None,
            'teachers': {},
            'students': {},
            'approvals': [],
            'accounts': {},
        }
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'password_hash': None,
            'password_salt': None,
            'teachers': {},
            'students': {},
            'approvals': [],
            'accounts': {},
        }


def _save_config(config):
    """保存配置"""
    path = _config_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
# 密码系统
# ═══════════════════════════════════════════════════════════════

def _hash_password(password, salt=None):
    """哈希密码 (带盐)"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                 bytes.fromhex(salt), 100000).hex()
    return hashed, salt


def set_password(password):
    """设置还原密码

    设置后，还原操作需要验证密码。
    传空字符串则取消密码。

    用法:
        PM.methow.set_password("mypwd")   # 设置密码
        PM.methow.set_password("")         # 取消密码
    """
    config = _load_config()

    if not password:
        config['password_hash'] = None
        config['password_salt'] = None
        _save_config(config)
        print("[MetHow] ✓ 已取消密码")
        return True

    hashed, salt = _hash_password(password)
    config['password_hash'] = hashed
    config['password_salt'] = salt
    _save_config(config)
    print("[MetHow] ✓ 密码已设置")
    return True


def verify_password(password):
    """验证密码"""
    config = _load_config()

    if not config.get('password_hash'):
        # 没设密码，直接通过
        return True

    hashed, _ = _hash_password(password, config.get('password_salt'))
    return hashed == config['password_hash']


# ═══════════════════════════════════════════════════════════════
# 快照系统 — 核心功能
# ═══════════════════════════════════════════════════════════════
#
# 快照原理: 把目标目录完整复制到备份位置
# 还原原理: 把备份复制回去
# 速度快因为: 纯文件复制，不依赖系统快照 API

def snapshot(target_path, name=None):
    """对目录拍快照

    把目标目录的完整状态保存为一个 .mhs 快照。

    Args:
        target_path: 要快照的目录路径
        name: 快照名称 (可选，自动生成)

    Returns:
        str: 快照 ID

    用法:
        PM.methow.snapshot("C:/mydir")
        PM.methow.snapshot(".", name="工作前快照")
    """
    target_path = os.path.abspath(os.path.expanduser(target_path))

    if not os.path.exists(target_path):
        print(f"[MetHow] ✗ 路径不存在: {target_path}")
        return None

    if not os.path.isdir(target_path):
        print(f"[MetHow] ✗ 不是目录: {target_path}")
        return None

    # 生成快照 ID
    snap_id = hashlib.md5(f"{target_path}{time.time()}".encode()).hexdigest()[:12]

    if name is None:
        name = f"快照_{time.strftime('%Y%m%d_%H%M%S')}"

    # 快照存储路径
    snap_path = os.path.join(_snapshot_dir(), snap_id)
    os.makedirs(snap_path, exist_ok=True)

    # 复制目录
    start = time.time()

    try:
        # 使用 copystats 保留元数据
        for item in os.listdir(target_path):
            src = os.path.join(target_path, item)
            dst = os.path.join(snap_path, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    except Exception as e:
        print(f"[MetHow] ✗ 快照失败: {e}")
        return None

    elapsed = time.time() - start

    # 计算大小
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(snap_path):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
            file_count += 1

    # 保存快照元数据
    meta = {
        'id': snap_id,
        'name': name,
        'source': target_path,
        'created': time.strftime('%Y-%m-%d %H:%M:%S'),
        'timestamp': time.time(),
        'file_count': file_count,
        'total_size': total_size,
        'elapsed_seconds': round(elapsed, 3),
    }

    meta_path = os.path.join(snap_path, '_meta.mhs')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    size_str = _format_size(total_size)
    print(f"[MetHow] ✓ 快照完成: {name}")
    print(f"       ID: {snap_id}")
    print(f"       源: {target_path}")
    print(f"       文件数: {file_count}")
    print(f"       大小: {size_str}")
    print(f"       耗时: {elapsed:.3f}s")

    return snap_id


def restore(snap_id=None, password=None, target_path=None):
    """还原到快照

    从指定快照恢复目录。如果不提供 snap_id，使用最近的快照。
    如果设置了密码，需要提供密码。

    Args:
        snap_id: 快照 ID (None = 最近快照)
        password: 密码 (如果设置了的话)
        target_path: 目标路径 (None = 原路径)

    Returns:
        bool: 是否成功

    用法:
        PM.methow.restore()                      # 一键还原 (最近快照)
        PM.methow.restore("abc123def456")        # 指定快照
        PM.methow.restore(password="mypwd")      # 带密码
    """
    config = _load_config()

    # 验证密码
    if config.get('password_hash'):
        if not password:
            print("[MetHow] ✗ 需要密码才能还原")
            print("       用法: PM.methow.restore(password='你的密码')")
            return False
        if not verify_password(password):
            print("[MetHow] ✗ 密码错误")
            return False

    # 查找快照
    if snap_id is None:
        # 找最近的快照
        snap_id = _get_latest_snapshot()
        if snap_id is None:
            print("[MetHow] ✗ 没有可用快照")
            return False
        print(f"[MetHow] 使用最近快照: {snap_id}")

    snap_path = os.path.join(_snapshot_dir(), snap_id)
    if not os.path.exists(snap_path):
        print(f"[MetHow] ✗ 快照不存在: {snap_id}")
        return False

    # 读取元数据
    meta_path = os.path.join(snap_path, '_meta.mhs')
    if not os.path.exists(meta_path):
        print(f"[MetHow] ✗ 快照元数据丢失")
        return False

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    # 确定目标路径
    if target_path is None:
        target_path = meta['source']

    # 还原: 删除目标目录内容，从快照复制回去
    start = time.time()

    try:
        # 清空目标目录 (不删目录本身)
        if os.path.exists(target_path):
            for item in os.listdir(target_path):
                item_path = os.path.join(target_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        else:
            os.makedirs(target_path, exist_ok=True)

        # 从快照复制回去
        for item in os.listdir(snap_path):
            if item == '_meta.mhs':
                continue
            src = os.path.join(snap_path, item)
            dst = os.path.join(target_path, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

    except Exception as e:
        print(f"[MetHow] ✗ 还原失败: {e}")
        return False

    elapsed = time.time() - start

    print(f"[MetHow] ✓ 还原完成: {meta.get('name', snap_id)}")
    print(f"       目标: {target_path}")
    print(f"       耗时: {elapsed:.3f}s")

    return True


def quick_restore(password=None):
    """一键还原

    直接还原到最近的快照，不需要指定 ID。
    本质上就是 restore() 的快捷方式。

    用法:
        PM.methow.quick_restore()
        PM.methow.quick_restore("mypwd")  # 带密码
    """
    print("[MetHow] ⚡ 一键还原...")
    return restore(password=password)


def _get_latest_snapshot():
    """获取最近的快照 ID"""
    snap_dir = _snapshot_dir()
    snaps = []
    for d in os.listdir(snap_dir):
        meta_path = os.path.join(snap_dir, d, '_meta.mhs')
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                snaps.append((meta.get('timestamp', 0), d, meta))
            except Exception:
                pass

    if not snaps:
        return None

    snaps.sort(key=lambda x: x[0], reverse=True)
    return snaps[0][1]


def list_snapshots():
    """列出所有快照"""
    snap_dir = _snapshot_dir()
    snaps = []
    for d in os.listdir(snap_dir):
        meta_path = os.path.join(snap_dir, d, '_meta.mhs')
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                snaps.append(meta)
            except Exception:
                pass

    snaps.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

    print(f"[MetHow] 快照列表 ({len(snaps)} 个):")
    if not snaps:
        print("  (暂无快照)")
        return []

    for i, meta in enumerate(snaps, 1):
        name = meta.get('name', '未命名')
        sid = meta.get('id', '?')
        created = meta.get('created', '?')
        size = _format_size(meta.get('total_size', 0))
        count = meta.get('file_count', 0)
        elapsed = meta.get('elapsed_seconds', 0)
        latest = " ← 最新" if i == 1 else ""
        print(f"  {i}. [{sid}] {name}")
        print(f"     创建: {created} | 文件: {count} | 大小: {size} | 耗时: {elapsed}s{latest}")

    return snaps


def delete_snapshot(snap_id):
    """删除快照"""
    snap_path = os.path.join(_snapshot_dir(), snap_id)
    if not os.path.exists(snap_path):
        print(f"[MetHow] ✗ 快照不存在: {snap_id}")
        return False
    shutil.rmtree(snap_path)
    print(f"[MetHow] ✓ 快照已删除: {snap_id}")
    return True


def clear_snapshots():
    """清空所有快照"""
    snap_dir = _snapshot_dir()
    count = 0
    for d in os.listdir(snap_dir):
        p = os.path.join(snap_dir, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
            count += 1
    print(f"[MetHow] ✓ 已清空 {count} 个快照")
    return count


# ═══════════════════════════════════════════════════════════════
# 权限系统 — 教师/学生
# ═══════════════════════════════════════════════════════════════

def add_teacher(name, phone, email):
    """添加教师

    教师有完整权限: 可以还原、删快照、管理学生。

    Args:
        name: 教师姓名
        phone: 教师手机号 (学生需要时获取)
        email: 教师邮箱

    用法:
        PM.methow.add_teacher("张老师", "13800138000", "teacher@email.com")
    """
    config = _load_config()
    config['teachers'][name] = {
        'phone': phone,
        'email': email,
        'added': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _save_config(config)
    print(f"[MetHow] ✓ 教师已添加: {name}")
    print(f"       手机: {phone}")
    print(f"       邮箱: {email}")
    return True


def add_student(name, email):
    """添加学生

    学生权限受限: 还原需要教师同意，且要先获取教师手机号。

    Args:
        name: 学生姓名
        email: 学生邮箱

    用法:
        PM.methow.add_student("小明", "student@email.com")
    """
    config = _load_config()
    config['students'][name] = {
        'email': email,
        'approved': False,
        'approved_by': None,
        'added': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _save_config(config)
    print(f"[MetHow] ✓ 学生已添加: {name}")
    print(f"       邮箱: {email}")
    print(f"       状态: 待教师同意")
    return True


def request_approval(student_name, teacher_name):
    """学生请求教师同意

    学生发起还原请求，等待教师同意。
    同意后学生可以获取教师的手机号。

    Args:
        student_name: 学生姓名
        teacher_name: 教师姓名

    用法:
        PM.methow.request_approval("小明", "张老师")
    """
    config = _load_config()

    if student_name not in config.get('students', {}):
        print(f"[MetHow] ✗ 学生不存在: {student_name}")
        return False

    if teacher_name not in config.get('teachers', {}):
        print(f"[MetHow] ✗ 教师不存在: {teacher_name}")
        return False

    # 添加审批请求
    request = {
        'student': student_name,
        'teacher': teacher_name,
        'status': 'pending',
        'requested': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    config['approvals'].append(request)
    _save_config(config)

    print(f"[MetHow] 📋 审批请求已提交:")
    print(f"       学生: {student_name}")
    print(f"       教师: {teacher_name}")
    print(f"       状态: 等待教师同意")
    print(f"       (教师同意后，学生可获取教师手机号)")
    return True


def approve(teacher_name, student_name):
    """教师同意学生的还原请求

    同意后:
      1. 学生获得还原权限
      2. 学生可以看到教师手机号 (用于联系)

    Args:
        teacher_name: 教师姓名
        student_name: 学生姓名

    用法:
        PM.methow.approve("张老师", "小明")
    """
    config = _load_config()

    if teacher_name not in config.get('teachers', {}):
        print(f"[MetHow] ✗ 教师不存在: {teacher_name}")
        return False

    if student_name not in config.get('students', {}):
        print(f"[MetHow] ✗ 学生不存在: {student_name}")
        return False

    # 更新审批
    for req in config['approvals']:
        if req['student'] == student_name and req['teacher'] == teacher_name:
            req['status'] = 'approved'
            req['approved_time'] = time.strftime('%Y-%m-%d %H:%M:%S')

    # 更新学生状态
    config['students'][student_name]['approved'] = True
    config['students'][student_name]['approved_by'] = teacher_name

    _save_config(config)

    # 获取教师手机号
    teacher_phone = config['teachers'][teacher_name]['phone']

    print(f"[MetHow] ✅ 教师已同意!")
    print(f"       教师: {teacher_name}")
    print(f"       学生: {student_name}")
    print(f"       教师手机号: {teacher_phone}")
    print(f"       (学生现在可以进行还原操作了)")
    return True


def reject(teacher_name, student_name):
    """教师拒绝学生的请求"""
    config = _load_config()
    for req in config['approvals']:
        if req['student'] == student_name and req['teacher'] == teacher_name:
            req['status'] = 'rejected'
            req['rejected_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
    _save_config(config)
    print(f"[MetHow] ❌ 教师已拒绝: {student_name}")
    return True


def check_permission(user_name):
    """检查用户权限

    返回:
      ('teacher', ...) — 教师权限
      ('student_approved', ...) — 已批准学生 + 教师手机号
      ('student_pending', ...) — 待批准学生
      ('student_rejected', ...) — 被拒绝学生
      ('unknown',) — 未知用户
    """
    config = _load_config()

    if user_name in config.get('teachers', {}):
        return ('teacher', config['teachers'][user_name])

    if user_name in config.get('students', {}):
        student = config['students'][user_name]
        if student.get('approved'):
            teacher_name = student.get('approved_by')
            teacher = config['teachers'].get(teacher_name, {})
            return ('student_approved', teacher.get('phone', ''), teacher_name)
        else:
            # 检查是否被拒绝
            for req in config.get('approvals', []):
                if req['student'] == user_name and req['status'] == 'rejected':
                    return ('student_rejected',)
            return ('student_pending',)

    return ('unknown',)


def restore_with_permission(user_name, snap_id=None, password=None):
    """带权限验证的还原

    学生必须已被教师同意才能还原。
    教师可以直接还原。
    """
    perm, *info = check_permission(user_name)

    if perm == 'unknown':
        print(f"[MetHow] ✗ 未知用户: {user_name}")
        print(f"       请先添加: PM.methow.add_student('{user_name}', 'email')")
        return False

    if perm == 'student_pending':
        print(f"[MetHow] ✗ 你的还原请求还在等待教师同意")
        print(f"       请联系教师审批")
        return False

    if perm == 'student_rejected':
        print(f"[MetHow] ✗ 你的请求已被教师拒绝")
        return False

    if perm == 'student_approved':
        teacher_phone = info[0]
        teacher_name = info[1]
        print(f"[MetHow] ✓ 学生 {user_name} 已获批准")
        print(f"       批准教师: {teacher_name}")
        print(f"       教师手机: {teacher_phone}")

    if perm == 'teacher':
        print(f"[MetHow] ✓ 教师 {user_name} 直接还原")

    # 执行还原
    return restore(snap_id=snap_id, password=password)


def list_users():
    """列出所有用户"""
    config = _load_config()

    print(f"[MetHow] 用户列表:")
    print()

    teachers = config.get('teachers', {})
    print(f"  教师 ({len(teachers)} 人):")
    for name, info in teachers.items():
        print(f"    {name} | 手机: {info.get('phone', '?')} | 邮箱: {info.get('email', '?')}")

    students = config.get('students', {})
    print(f"\n  学生 ({len(students)} 人):")
    for name, info in students.items():
        status = "✓ 已批准" if info.get('approved') else "⏳ 待批准"
        approved_by = info.get('approved_by', '')
        print(f"    {name} | {status} | 邮箱: {info.get('email', '?')}")
        if approved_by:
            print(f"           批准教师: {approved_by}")

    approvals = config.get('approvals', [])
    if approvals:
        print(f"\n  审批队列 ({len(approvals)} 条):")
        for req in approvals:
            status_icon = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}.get(req['status'], '?')
            print(f"    {status_icon} {req['student']} → {req['teacher']} ({req['status']})")


# ═══════════════════════════════════════════════════════════════
# 密码找回 — 输入账号名 + 邮箱 → 发到邮箱
# ═══════════════════════════════════════════════════════════════

def _register_account(account_name, email, password):
    """注册账号 (内部用)

    把账号信息存到配置里，用于密码找回。
    注意: 这里存的是密码哈希，不是明文。
    但为了能"找回密码"，我们需要存一个加密的明文。
    用教师公钥加密... 算了，用简单加密。
    """
    config = _load_config()
    if 'accounts' not in config:
        config['accounts'] = {}

    # 用 salt + XOR 简单加密密码 (不安全，但演示用)
    salt = secrets.token_hex(8)
    enc_pwd = _xor_encrypt(password, salt)

    config['accounts'][account_name] = {
        'email': email,
        'enc_pwd': enc_pwd,
        'salt': salt,
        'registered': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _save_config(config)


def _xor_encrypt(text, key_hex):
    """简单 XOR 加密"""
    key = bytes.fromhex(key_hex)
    result = bytearray()
    for i, b in enumerate(text.encode('utf-8')):
        result.append(b ^ key[i % len(key)])
    return result.hex()


def _xor_decrypt(enc_hex, key_hex):
    """简单 XOR 解密"""
    key = bytes.fromhex(key_hex)
    data = bytes.fromhex(enc_hex)
    result = bytearray()
    for i, b in enumerate(data):
        result.append(b ^ key[i % len(key)])
    return result.decode('utf-8')


def recover_password(account_name, email):
    """找回密码

    输入账号名和邮箱，密码自动发到邮箱里。

    本质流程:
      1. 验证账号名 + 邮箱匹配
      2. 解密密码
      3. "发送"到邮箱 (模拟)

    Args:
        account_name: 账号名
        email: 注册邮箱

    用法:
        PM.methow.recover_password("myaccount", "user@email.com")
    """
    config = _load_config()
    accounts = config.get('accounts', {})

    if account_name not in accounts:
        print(f"[MetHow] ✗ 账号不存在: {account_name}")
        return False

    account = accounts[account_name]

    if account['email'] != email:
        print(f"[MetHow] ✗ 邮箱不匹配")
        return False

    # 解密密码
    try:
        password = _xor_decrypt(account['enc_pwd'], account['salt'])
    except Exception:
        print(f"[MetHow] ✗ 密码解密失败")
        return False

    # "发送"到邮箱
    print(f"[MetHow] 📧 密码找回成功!")
    print(f"       账号: {account_name}")
    print(f"       邮箱: {email}")
    print(f"       密码已发送到您的邮箱 (模拟)")
    print(f"       (实际部署时，会通过 SMTP 发送邮件)")

    # 如果配置了 SMTP，真正发送
    smtp_config = config.get('smtp', {})
    if smtp_config.get('host'):
        try:
            _send_email(
                smtp_config['host'],
                smtp_config.get('port', 587),
                smtp_config.get('user', ''),
                smtp_config.get('pass', ''),
                email,
                'MetHow 密码找回',
                f'您的 MetHow 还原密码是: {password}\n\n请妥善保管。'
            )
            print(f"       ✓ 邮件已通过 SMTP 发送")
        except Exception as e:
            print(f"       ⚠ SMTP 发送失败: {e}")
            print(f"       密码: {password}")  # 降级显示
    else:
        # 没配置 SMTP，在终端显示 (演示用)
        print(f"       (未配置 SMTP，密码: {password})")

    return True


def register_account(account_name, email, password):
    """注册账号 (用于密码找回)

    注册后，忘记密码时可以用 recover_password 找回。

    Args:
        account_name: 账号名
        email: 邮箱
        password: 密码

    用法:
        PM.methow.register_account("myaccount", "user@email.com", "mypwd")
    """
    _register_account(account_name, email, password)
    print(f"[MetHow] ✓ 账号已注册: {account_name}")
    print(f"       邮箱: {email}")
    print(f"       (忘记密码时用 recover_password 找回)")
    return True


def _send_email(host, port, user, password, to_addr, subject, body):
    """通过 SMTP 发送邮件"""
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(user, password)
    server.sendmail(user, to_addr, msg.as_string())
    server.quit()


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def _format_size(size):
    """格式化文件大小"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size/(1024*1024):.1f} MB"
    else:
        return f"{size/(1024*1024*1024):.1f} GB"


# ═══════════════════════════════════════════════════════════════
# 演示
# ═══════════════════════════════════════════════════════════════

def demo():
    """MetHow 演示"""
    print()
    print("=" * 60)
    print("  MetHow 还原引擎 演示")
    print("  快速还原 | 权限管理 | 密码找回")
    print("=" * 60)

    # 1. 创建测试目录
    test_dir = os.path.join(tempfile.gettempdir(), 'methow_demo')
    os.makedirs(test_dir, exist_ok=True)

    # 写一些文件
    with open(os.path.join(test_dir, 'file1.txt'), 'w') as f:
        f.write('这是文件1的原始内容\n')
    with open(os.path.join(test_dir, 'file2.txt'), 'w') as f:
        f.write('这是文件2的原始内容\n')

    print(f"\n  [1] 测试目录: {test_dir}")
    print(f"      创建了 file1.txt 和 file2.txt")

    # 2. 拍快照
    print(f"\n  [2] 拍快照...")
    snap_id = snapshot(test_dir, name="演示快照")

    # 3. 修改文件
    with open(os.path.join(test_dir, 'file1.txt'), 'w') as f:
        f.write('这是被修改后的内容\n')
    os.makedirs(os.path.join(test_dir, 'newdir'), exist_ok=True)

    print(f"\n  [3] 修改了 file1.txt, 创建了 newdir/")

    # 4. 还原
    print(f"\n  [4] 一键还原...")
    quick_restore()

    # 验证还原
    with open(os.path.join(test_dir, 'file1.txt'), 'r') as f:
        content = f.read()
    restored_ok = '原始内容' in content
    newdir_exists = os.path.exists(os.path.join(test_dir, 'newdir'))

    print(f"      file1.txt 内容已恢复: {'✓' if restored_ok else '✗'}")
    print(f"      newdir 已被删除: {'✓' if not newdir_exists else '✗'}")

    # 5. 权限演示
    print(f"\n  [5] 权限系统演示:")
    add_teacher("张老师", "13800138000", "teacher@school.edu")
    add_student("小明", "xiaoming@school.edu")
    request_approval("小明", "张老师")
    approve("张老师", "小明")

    # 6. 密码找回演示
    print(f"\n  [6] 密码找回演示:")
    register_account("test_user", "user@demo.com", "secret_pwd_123")
    recover_password("test_user", "user@demo.com")

    # 清理
    shutil.rmtree(test_dir, ignore_errors=True)
    clear_snapshots()

    # 清理配置
    config = _load_config()
    config['teachers'] = {}
    config['students'] = {}
    config['approvals'] = []
    config['accounts'] = {}
    _save_config(config)

    print(f"\n{'='*60}")
    print("  MetHow 演示完成! ⚡")
    print("  PM.methow.snapshot(path)           # 拍快照")
    print("  PM.methow.restore()                # 一键还原")
    print("  PM.methow.quick_restore()          # 快捷还原")
    print("  PM.methow.set_password('pwd')      # 设密码")
    print("  PM.methow.recover_password(u, e)   # 找回密码")
    print("  PM.methow.add_teacher(...)         # 添加教师")
    print("  PM.methow.add_student(...)         # 添加学生")
    print("  PM.methow.approve(teacher, student) # 教师同意")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _MetHowModule:
    """PyMsi.methow — MetHow 还原引擎

    快速还原系统，比冰点还原快。
    权限: 教师/学生。
    密码: 可选，可找回。

    用法:
        PM.methow.snapshot(path)              # 拍快照
        PM.methow.restore()                   # 还原
        PM.methow.quick_restore()             # 一键还原
        PM.methow.set_password("pwd")          # 设密码
        PM.methow.recover_password(u, e)       # 找回密码
        PM.methow.add_teacher(name, phone, email)
        PM.methow.add_student(name, email)
        PM.methow.approve(teacher, student)
        PM.methow.demo()
    """

    def __repr__(self):
        return "<PyMsi.methow [MetHow还原引擎] v2.5.0>"

    # 快照
    def snapshot(self, path, name=None):
        return snapshot(path, name)

    def restore(self, snap_id=None, password=None, target_path=None):
        return restore(snap_id=snap_id, password=password, target_path=target_path)

    def quick_restore(self, password=None):
        return quick_restore(password=password)

    def list_snapshots(self):
        return list_snapshots()

    def delete_snapshot(self, snap_id):
        return delete_snapshot(snap_id)

    def clear_snapshots(self):
        return clear_snapshots()

    # 密码
    def set_password(self, password):
        return set_password(password)

    def verify_password(self, password):
        return verify_password(password)

    # 权限
    def add_teacher(self, name, phone, email):
        return add_teacher(name, phone, email)

    def add_student(self, name, email):
        return add_student(name, email)

    def request_approval(self, student, teacher):
        return request_approval(student, teacher)

    def approve(self, teacher, student):
        return approve(teacher, student)

    def reject(self, teacher, student):
        return reject(teacher, student)

    def check_permission(self, user):
        return check_permission(user)

    def restore_with_permission(self, user, snap_id=None, password=None):
        return restore_with_permission(user, snap_id=snap_id, password=password)

    def list_users(self):
        return list_users()

    # 密码找回
    def register_account(self, name, email, password):
        return register_account(name, email, password)

    def recover_password(self, account_name, email):
        return recover_password(account_name, email)

    # 演示
    def demo(self):
        return demo()
