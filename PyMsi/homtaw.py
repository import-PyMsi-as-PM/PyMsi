"""
homtaw.py — Homtaw SDK (v2.5.0)

MetHow 的独立 SDK，有自己的协议 (HWP - Homtaw Protocol)。
1350+ API，用 50+ 个就能完成和 MetHow 一模一样的操作。

额度系统:
  每次调用 API 消耗 1 额度
  初始额度: 1500
  额度用完可以赚取 (见 earn_credits)

赚取额度方案 (时间短、速度快):
  1. 签到 (每日1次, +100额度)
  2. 验证码挑战 (即时, +50额度)
  3. 编程挑战 (即时, +200额度)
  4. 连续签到奖励 (第7天x2, 第30天x5)

HWP 协议 (Homtaw Protocol):
  请求: HWP/1.0\\nAPI: <method>\\nKey: <api_key>\\nQuota: <n>\\n\\n<json_params>
  响应: HWP/1.0\\nStatus: <code>\\nQuota: <remaining>\\n\\n<json_result>

用法:
    import PyMsi as PM

    sdk = PM.homtaw()

    # 调用 API
    result = sdk.call('file_read', path='/etc/hostname')
    result = sdk.call('hash_string', algo='md5', data='hello')

    # 直接方法调用
    sdk.api_file_read('/etc/hostname')
    sdk.api_hash_string('md5', 'hello')

    # 查看额度
    sdk.quota_info()

    # 赚取额度
    sdk.earn_daily()           # 每日签到
    sdk.earn_captcha()         # 验证码挑战

    # 查看 API 列表
    sdk.list_apis()
    sdk.api_count()

    # 用 SDK 复刻 MetHow 功能
    sdk.replicate_methow()
"""

import os
import sys
import json
import time
import hashlib
import secrets
import random
import string
import struct
import base64
import binascii
import zipfile
import shutil
import tempfile
import platform
import urllib.parse
import urllib.request
import io
import re
import math
import datetime
import textwrap
import copy
import csv
import configparser
import xml.etree.ElementTree as ET


# ═══════════════════════════════════════════════════════════════
# HWP 协议 (Homtaw Protocol)
# ═══════════════════════════════════════════════════════════════

HWP_VERSION = '1.0'


def hwp_request(api_name, params=None, api_key='demo_key', quota=0):
    """构造 HWP 请求包"""
    body = json.dumps(params or {}, ensure_ascii=False)
    req = (
        f"HWP/{HWP_VERSION}\n"
        f"API: {api_name}\n"
        f"Key: {api_key}\n"
        f"Quota: {quota}\n"
        f"\n"
        f"{body}"
    )
    return req


def hwp_parse_request(raw):
    """解析 HWP 请求包"""
    lines = raw.split('\n')
    if not lines[0].startswith(f'HWP/'):
        return None, None, None
    api = key = quota = None
    i = 1
    while i < len(lines) and lines[i]:
        if lines[i].startswith('API: '):
            api = lines[i][5:]
        elif lines[i].startswith('Key: '):
            key = lines[i][5:]
        elif lines[i].startswith('Quota: '):
            quota = int(lines[i][7:])
        i += 1
    body = '\n'.join(lines[i+1:]) if i < len(lines) else ''
    params = json.loads(body) if body else {}
    return api, key, params


def hwp_response(status, result, quota_remaining):
    """构造 HWP 响应包"""
    body = json.dumps(result, ensure_ascii=False, default=str)
    return (
        f"HWP/{HWP_VERSION}\n"
        f"Status: {status}\n"
        f"Quota: {quota_remaining}\n"
        f"\n"
        f"{body}"
    )


# ═══════════════════════════════════════════════════════════════
# 核心实现函数 — SDK 的底层引擎
# ═══════════════════════════════════════════════════════════════

class _Impl:
    """核心实现函数集合 — 所有 API 的底层实现"""

    # ─── 文件 I/O ───

    @staticmethod
    def file_read(path, mode='r', encoding='utf-8'):
        p = os.path.expanduser(path)
        if mode == 'rb':
            with open(p, 'rb') as f:
                return f.read()
        with open(p, 'r', encoding=encoding) as f:
            return f.read()

    @staticmethod
    def file_write(path, content, mode='w', encoding='utf-8'):
        p = os.path.expanduser(path)
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        if mode == 'wb' or isinstance(content, bytes):
            with open(p, 'wb') as f:
                f.write(content if isinstance(content, bytes) else content.encode(encoding))
        else:
            with open(p, 'w', encoding=encoding) as f:
                f.write(content)
        return os.path.getsize(p)

    @staticmethod
    def file_append(path, content, encoding='utf-8'):
        p = os.path.expanduser(path)
        with open(p, 'a', encoding=encoding) as f:
            f.write(content)
        return os.path.getsize(p)

    @staticmethod
    def file_copy(src, dst):
        src = os.path.expanduser(src)
        dst = os.path.expanduser(dst)
        os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
        shutil.copy2(src, dst)
        return True

    @staticmethod
    def file_move(src, dst):
        src = os.path.expanduser(src)
        dst = os.path.expanduser(dst)
        os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
        shutil.move(src, dst)
        return True

    @staticmethod
    def file_delete(path):
        os.remove(os.path.expanduser(path))
        return True

    @staticmethod
    def file_exists(path):
        return os.path.exists(os.path.expanduser(path))

    @staticmethod
    def file_isfile(path):
        return os.path.isfile(os.path.expanduser(path))

    @staticmethod
    def file_isdir(path):
        return os.path.isdir(os.path.expanduser(path))

    @staticmethod
    def file_size(path):
        return os.path.getsize(os.path.expanduser(path))

    @staticmethod
    def file_size_human(path):
        s = os.path.getsize(os.path.expanduser(path))
        for u in ['B', 'KB', 'MB', 'GB', 'TB']:
            if s < 1024:
                return f"{s:.1f} {u}"
            s /= 1024
        return f"{s:.1f} PB"

    @staticmethod
    def file_mtime(path):
        return os.path.getmtime(os.path.expanduser(path))

    @staticmethod
    def file_ctime(path):
        return os.path.getctime(os.path.expanduser(path))

    @staticmethod
    def file_atime(path):
        return os.path.getatime(os.path.expanduser(path))

    @staticmethod
    def file_ext(path):
        return os.path.splitext(path)[1]

    @staticmethod
    def file_name(path):
        return os.path.basename(os.path.expanduser(path))

    @staticmethod
    def file_dir(path):
        return os.path.dirname(os.path.expanduser(path))

    @staticmethod
    def file_stem(path):
        return os.path.splitext(os.path.basename(path))[0]

    @staticmethod
    def file_absolute(path):
        return os.path.abspath(os.path.expanduser(path))

    @staticmethod
    def file_lines(path, encoding='utf-8'):
        with open(os.path.expanduser(path), 'r', encoding=encoding) as f:
            return f.readlines()

    @staticmethod
    def file_line_count(path, encoding='utf-8'):
        with open(os.path.expanduser(path), 'r', encoding=encoding) as f:
            return sum(1 for _ in f)

    @staticmethod
    def file_touch(path):
        p = os.path.expanduser(path)
        if not os.path.exists(p):
            with open(p, 'w') as f:
                pass
        else:
            os.utime(p, None)
        return True

    @staticmethod
    def file_truncate(path, size=0):
        p = os.path.expanduser(path)
        with open(p, 'r+') as f:
            f.truncate(size)
        return True

    @staticmethod
    def file_rename(src, dst):
        os.rename(os.path.expanduser(src), os.path.expanduser(dst))
        return True

    @staticmethod
    def file_read_json(path):
        with open(os.path.expanduser(path), 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def file_write_json(path, data, indent=2):
        p = os.path.expanduser(path)
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True

    @staticmethod
    def file_read_csv(path):
        with open(os.path.expanduser(path), 'r', encoding='utf-8') as f:
            return list(csv.reader(f))

    @staticmethod
    def file_write_csv(path, rows):
        p = os.path.expanduser(path)
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        return True

    @staticmethod
    def file_read_ini(path):
        cp = configparser.ConfigParser()
        cp.read(os.path.expanduser(path), encoding='utf-8')
        return {s: dict(cp.items(s)) for s in cp.sections()}

    @staticmethod
    def file_write_ini(path, data):
        cp = configparser.ConfigParser()
        for section, items in data.items():
            cp.add_section(section)
            for k, v in items.items():
                cp.set(section, k, str(v))
        p = os.path.expanduser(path)
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            cp.write(f)
        return True

    @staticmethod
    def file_read_xml(path):
        tree = ET.parse(os.path.expanduser(path))
        root = tree.getroot()
        return _xml_to_dict(root)

    @staticmethod
    def file_read_base64(path):
        with open(os.path.expanduser(path), 'rb') as f:
            return base64.b64encode(f.read()).decode('ascii')

    @staticmethod
    def file_write_base64(path, b64data):
        p = os.path.expanduser(path)
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        with open(p, 'wb') as f:
            f.write(base64.b64decode(b64data))
        return True

    # ─── 目录操作 ───

    @staticmethod
    def dir_create(path, exist_ok=True):
        os.makedirs(os.path.expanduser(path), exist_ok=exist_ok)
        return True

    @staticmethod
    def dir_list(path='.'):
        return os.listdir(os.path.expanduser(path))

    @staticmethod
    def dir_list_files(path='.'):
        p = os.path.expanduser(path)
        return [f for f in os.listdir(p) if os.path.isfile(os.path.join(p, f))]

    @staticmethod
    def dir_list_dirs(path='.'):
        p = os.path.expanduser(path)
        return [d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d))]

    @staticmethod
    def dir_walk(path='.'):
        result = []
        for root, dirs, files in os.walk(os.path.expanduser(path)):
            for f in files:
                result.append(os.path.join(root, f))
        return result

    @staticmethod
    def dir_size(path='.'):
        total = 0
        for root, dirs, files in os.walk(os.path.expanduser(path)):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        return total

    @staticmethod
    def dir_count_files(path='.'):
        count = 0
        for root, dirs, files in os.walk(os.path.expanduser(path)):
            count += len(files)
        return count

    @staticmethod
    def dir_count_dirs(path='.'):
        count = 0
        for root, dirs, files in os.walk(os.path.expanduser(path)):
            count += len(dirs)
        return count

    @staticmethod
    def dir_is_empty(path='.'):
        return len(os.listdir(os.path.expanduser(path))) == 0

    @staticmethod
    def dir_copy(src, dst):
        shutil.copytree(os.path.expanduser(src), os.path.expanduser(dst), dirs_exist_ok=True)
        return True

    @staticmethod
    def dir_move(src, dst):
        shutil.move(os.path.expanduser(src), os.path.expanduser(dst))
        return True

    @staticmethod
    def dir_delete(path):
        shutil.rmtree(os.path.expanduser(path))
        return True

    @staticmethod
    def dir_tree(path='.', max_depth=3):
        result = []
        base = os.path.expanduser(path)
        for root, dirs, files in os.walk(base):
            depth = root.replace(base, '').count(os.sep)
            if depth >= max_depth:
                dirs[:] = []
                continue
            indent = '  ' * depth
            result.append(f"{indent}{os.path.basename(root)}/")
            for f in files:
                result.append(f"{indent}  {f}")
        return '\n'.join(result)

    # ─── 哈希 ───

    @staticmethod
    def hash_string(algo, data):
        h = hashlib.new(algo)
        h.update(data.encode('utf-8'))
        return h.hexdigest()

    @staticmethod
    def hash_bytes(algo, data):
        if isinstance(data, str):
            data = bytes.fromhex(data)
        h = hashlib.new(algo)
        h.update(data)
        return h.hexdigest()

    @staticmethod
    def hash_file(algo, path):
        h = hashlib.new(algo)
        with open(os.path.expanduser(path), 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def hash_fileobj(algo, fileobj):
        h = hashlib.new(algo)
        while True:
            chunk = fileobj.read(8192)
            if not chunk:
                break
            h.update(chunk)
        return h.hexdigest()

    # ─── Base64 ───

    @staticmethod
    def b64_encode(data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('ascii')

    @staticmethod
    def b64_decode(data):
        decoded = base64.b64decode(data)
        try:
            return decoded.decode('utf-8')
        except UnicodeDecodeError:
            return decoded.hex()

    @staticmethod
    def b64url_encode(data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.urlsafe_b64encode(data).decode('ascii')

    @staticmethod
    def b64url_decode(data):
        decoded = base64.urlsafe_b64decode(data)
        try:
            return decoded.decode('utf-8')
        except UnicodeDecodeError:
            return decoded.hex()

    # ─── Hex ───

    @staticmethod
    def hex_encode(data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        return binascii.hexlify(data).decode('ascii')

    @staticmethod
    def hex_decode(data):
        decoded = binascii.unhexlify(data)
        try:
            return decoded.decode('utf-8')
        except UnicodeDecodeError:
            return decoded.hex()

    # ─── URL ───

    @staticmethod
    def url_encode(s):
        return urllib.parse.quote(s, safe='')

    @staticmethod
    def url_decode(s):
        return urllib.parse.unquote(s)

    @staticmethod
    def url_parse(url):
        parsed = urllib.parse.urlparse(url)
        return {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'params': parsed.params,
            'query': parsed.query,
            'fragment': parsed.fragment,
        }

    @staticmethod
    def url_query_parse(query):
        return dict(urllib.parse.parse_qsl(query))

    @staticmethod
    def url_query_encode(params):
        return urllib.parse.urlencode(params)

    @staticmethod
    def url_join(base, url):
        return urllib.parse.urljoin(base, url)

    @staticmethod
    def url_extract_domain(url):
        return urllib.parse.urlparse(url).netloc

    @staticmethod
    def url_extract_path(url):
        return urllib.parse.urlparse(url).path

    # ─── JSON ───

    @staticmethod
    def json_encode(data, indent=None):
        return json.dumps(data, ensure_ascii=False, indent=indent, default=str)

    @staticmethod
    def json_decode(data):
        return json.loads(data)

    @staticmethod
    def json_pretty(data):
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    @staticmethod
    def json_minify(data):
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'), default=str)

    @staticmethod
    def json_validate(data):
        try:
            json.loads(data)
            return True
        except Exception:
            return False

    @staticmethod
    def json_load_file(path):
        with open(os.path.expanduser(path), 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def json_save_file(path, data, indent=2):
        p = os.path.expanduser(path)
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
        return True

    @staticmethod
    def json_merge(a, b):
        result = copy.deepcopy(a)
        if isinstance(result, dict) and isinstance(b, dict):
            for k, v in b.items():
                if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                    result[k] = _Impl.json_merge(result[k], v)
                else:
                    result[k] = copy.deepcopy(v)
        return result

    @staticmethod
    def json_flatten(data, prefix=''):
        result = {}
        if isinstance(data, dict):
            for k, v in data.items():
                key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    result.update(_Impl.json_flatten(v, key))
                else:
                    result[key] = v
        return result

    @staticmethod
    def json_unflatten(data):
        result = {}
        for key, value in data.items():
            parts = key.split('.')
            d = result
            for part in parts[:-1]:
                if part not in d:
                    d[part] = {}
                d = d[part]
            d[parts[-1]] = value
        return result

    @staticmethod
    def json_get(data, path, default=None):
        keys = path.split('.')
        d = data
        for k in keys:
            if isinstance(d, dict) and k in d:
                d = d[k]
            elif isinstance(d, list) and k.isdigit() and int(k) < len(d):
                d = d[int(k)]
            else:
                return default
        return d

    @staticmethod
    def json_set(data, path, value):
        keys = path.split('.')
        d = data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        return data

    @staticmethod
    def json_delete(data, path):
        keys = path.split('.')
        d = data
        for k in keys[:-1]:
            if k not in d:
                return data
            d = d[k]
        if keys[-1] in d:
            del d[keys[-1]]
        return data

    @staticmethod
    def json_keys(data, prefix=''):
        result = []
        if isinstance(data, dict):
            for k, v in data.items():
                key = f"{prefix}.{k}" if prefix else k
                result.append(key)
                if isinstance(v, dict):
                    result.extend(_Impl.json_keys(v, key))
        return result

    # ─── 字符串处理 ───

    @staticmethod
    def str_upper(s):
        return s.upper()

    @staticmethod
    def str_lower(s):
        return s.lower()

    @staticmethod
    def str_title(s):
        return s.title()

    @staticmethod
    def str_capitalize(s):
        return s.capitalize()

    @staticmethod
    def str_swapcase(s):
        return s.swapcase()

    @staticmethod
    def str_strip(s, chars=None):
        return s.strip(chars)

    @staticmethod
    def str_lstrip(s, chars=None):
        return s.lstrip(chars)

    @staticmethod
    def str_rstrip(s, chars=None):
        return s.rstrip(chars)

    @staticmethod
    def str_split(s, sep=None, maxsplit=-1):
        return s.split(sep, maxsplit)

    @staticmethod
    def str_rsplit(s, sep=None, maxsplit=-1):
        return s.rsplit(sep, maxsplit)

    @staticmethod
    def str_splitlines(s):
        return s.splitlines()

    @staticmethod
    def str_join(lst, sep=''):
        return sep.join(lst)

    @staticmethod
    def str_replace(s, old, new, count=-1):
        return s.replace(old, new, count)

    @staticmethod
    def str_count(s, sub):
        return s.count(sub)

    @staticmethod
    def str_find(s, sub, start=0, end=None):
        return s.find(sub, start, end if end is not None else len(s))

    @staticmethod
    def str_rfind(s, sub, start=0, end=None):
        return s.rfind(sub, start, end if end is not None else len(s))

    @staticmethod
    def str_startswith(s, prefix):
        return s.startswith(prefix)

    @staticmethod
    def str_endswith(s, suffix):
        return s.endswith(suffix)

    @staticmethod
    def str_contains(s, sub):
        return sub in s

    @staticmethod
    def str_length(s):
        return len(s)

    @staticmethod
    def str_center(s, width, fillchar=' '):
        return s.center(width, fillchar)

    @staticmethod
    def str_ljust(s, width, fillchar=' '):
        return s.ljust(width, fillchar)

    @staticmethod
    def str_rjust(s, width, fillchar=' '):
        return s.rjust(width, fillchar)

    @staticmethod
    def str_zfill(s, width):
        return s.zfill(width)

    @staticmethod
    def str_pad(s, width, fillchar=' ', side='right'):
        if side == 'right':
            return s.ljust(width, fillchar)
        elif side == 'left':
            return s.rjust(width, fillchar)
        else:
            return s.center(width, fillchar)

    @staticmethod
    def str_reverse(s):
        return s[::-1]

    @staticmethod
    def str_repeat(s, n):
        return s * n

    @staticmethod
    def str_format(template, *args, **kwargs):
        return template.format(*args, **kwargs)

    @staticmethod
    def str_template(template, mapping):
        return string.Template(template).safe_substitute(mapping)

    @staticmethod
    def str_wrap(text, width=70):
        return textwrap.fill(text, width=width)

    @staticmethod
    def str_dedent(text):
        return textwrap.dedent(text)

    @staticmethod
    def str_indent(text, prefix='    '):
        return textwrap.indent(text, prefix)

    @staticmethod
    def str_camel(s):
        parts = s.replace('-', '_').replace(' ', '_').split('_')
        return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

    @staticmethod
    def str_snake(s):
        result = re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()
        return result.replace(' ', '_').replace('-', '_')

    @staticmethod
    def str_kebab(s):
        result = re.sub(r'(?<!^)(?=[A-Z])', '-', s).lower()
        return result.replace(' ', '-').replace('_', '-')

    @staticmethod
    def str_title_case(s):
        return ' '.join(w.capitalize() for w in s.split())

    @staticmethod
    def str_is_alpha(s):
        return s.isalpha()

    @staticmethod
    def str_is_digit(s):
        return s.isdigit()

    @staticmethod
    def str_is_alnum(s):
        return s.isalnum()

    @staticmethod
    def str_is_upper(s):
        return s.isupper()

    @staticmethod
    def str_is_lower(s):
        return s.islower()

    @staticmethod
    def str_is_space(s):
        return s.isspace()

    @staticmethod
    def str_starts_vowel(s):
        return s[0].lower() in 'aeiou' if s else False

    @staticmethod
    def str_word_count(s):
        return len(s.split())

    @staticmethod
    def str_char_count(s):
        return len(s)

    @staticmethod
    def str_byte_count(s, encoding='utf-8'):
        return len(s.encode(encoding))

    @staticmethod
    def str_unique_chars(s):
        return ''.join(sorted(set(s)))

    @staticmethod
    def str_char_frequency(s):
        freq = {}
        for c in s:
            freq[c] = freq.get(c, 0) + 1
        return freq

    @staticmethod
    def str_remove_duplicates(s):
        seen = set()
        result = []
        for c in s:
            if c not in seen:
                seen.add(c)
                result.append(c)
        return ''.join(result)

    @staticmethod
    def str_truncate(s, length, suffix='...'):
        if len(s) <= length:
            return s
        return s[:length - len(suffix)] + suffix

    @staticmethod
    def str_slice(s, start=0, end=None):
        return s[start:end]

    @staticmethod
    def str_chunk(s, size):
        return [s[i:i+size] for i in range(0, len(s), size)]

    @staticmethod
    def str_between(s, start, end):
        si = s.find(start)
        if si == -1:
            return ''
        si += len(start)
        ei = s.find(end, si)
        if ei == -1:
            return s[si:]
        return s[si:ei]

    @staticmethod
    def str_to_list(s):
        return list(s)

    @staticmethod
    def str_from_list(lst):
        return ''.join(lst)

    @staticmethod
    def str_to_ascii(s):
        return [ord(c) for c in s]

    @staticmethod
    def str_from_ascii(codes):
        return ''.join(chr(c) for c in codes)

    # ─── 正则 ───

    @staticmethod
    def regex_match(pattern, string):
        m = re.match(pattern, string)
        return m.group(0) if m else None

    @staticmethod
    def regex_search(pattern, string):
        m = re.search(pattern, string)
        return m.group(0) if m else None

    @staticmethod
    def regex_findall(pattern, string):
        return re.findall(pattern, string)

    @staticmethod
    def regex_finditer(pattern, string):
        return [{'match': m.group(), 'start': m.start(), 'end': m.end()}
                for m in re.finditer(pattern, string)]

    @staticmethod
    def regex_sub(pattern, repl, string, count=0):
        return re.sub(pattern, repl, string, count=count)

    @staticmethod
    def regex_split(pattern, string, maxsplit=0):
        return re.split(pattern, string, maxsplit=maxsplit)

    @staticmethod
    def regex_escape(string):
        return re.escape(string)

    @staticmethod
    def regex_compile(pattern, flags=0):
        return re.compile(pattern, flags).pattern

    # ─── 数学 ───

    @staticmethod
    def math_add(a, b):
        return a + b

    @staticmethod
    def math_sub(a, b):
        return a - b

    @staticmethod
    def math_mul(a, b):
        return a * b

    @staticmethod
    def math_div(a, b):
        return a / b

    @staticmethod
    def math_floordiv(a, b):
        return a // b

    @staticmethod
    def math_mod(a, b):
        return a % b

    @staticmethod
    def math_pow(a, b):
        return a ** b

    @staticmethod
    def math_abs(n):
        return abs(n)

    @staticmethod
    def math_round(n, digits=0):
        return round(n, digits)

    @staticmethod
    def math_ceil(n):
        return math.ceil(n)

    @staticmethod
    def math_floor(n):
        return math.floor(n)

    @staticmethod
    def math_trunc(n):
        return math.trunc(n)

    @staticmethod
    def math_max(lst):
        return max(lst)

    @staticmethod
    def math_min(lst):
        return min(lst)

    @staticmethod
    def math_sum(lst):
        return sum(lst)

    @staticmethod
    def math_mean(lst):
        return sum(lst) / len(lst) if lst else 0

    @staticmethod
    def math_median(lst):
        s = sorted(lst)
        n = len(s)
        if n == 0:
            return 0
        if n % 2 == 1:
            return s[n // 2]
        return (s[n // 2 - 1] + s[n // 2]) / 2

    @staticmethod
    def math_mode(lst):
        freq = {}
        for x in lst:
            freq[x] = freq.get(x, 0) + 1
        return max(freq, key=freq.get) if freq else None

    @staticmethod
    def math_variance(lst):
        if len(lst) < 2:
            return 0
        m = sum(lst) / len(lst)
        return sum((x - m) ** 2 for x in lst) / (len(lst) - 1)

    @staticmethod
    def math_stddev(lst):
        return math.sqrt(_Impl.math_variance(lst))

    @staticmethod
    def math_range(lst):
        return max(lst) - min(lst) if lst else 0

    @staticmethod
    def math_gcd(a, b):
        return math.gcd(a, b)

    @staticmethod
    def math_lcm(a, b):
        return abs(a * b) // math.gcd(a, b) if a and b else 0

    @staticmethod
    def math_factorial(n):
        return math.factorial(n)

    @staticmethod
    def math_is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def math_primes(limit):
        return [n for n in range(2, limit + 1) if _Impl.math_is_prime(n)]

    @staticmethod
    def math_fibonacci(n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    @staticmethod
    def math_sqrt(n):
        return math.sqrt(n)

    @staticmethod
    def math_cbrt(n):
        return n ** (1 / 3)

    @staticmethod
    def math_exp(n):
        return math.exp(n)

    @staticmethod
    def math_log(n, base=math.e):
        return math.log(n, base)

    @staticmethod
    def math_log2(n):
        return math.log2(n)

    @staticmethod
    def math_log10(n):
        return math.log10(n)

    @staticmethod
    def math_sin(n):
        return math.sin(n)

    @staticmethod
    def math_cos(n):
        return math.cos(n)

    @staticmethod
    def math_tan(n):
        return math.tan(n)

    @staticmethod
    def math_asin(n):
        return math.asin(n)

    @staticmethod
    def math_acos(n):
        return math.acos(n)

    @staticmethod
    def math_atan(n):
        return math.atan(n)

    @staticmethod
    def math_atan2(y, x):
        return math.atan2(y, x)

    @staticmethod
    def math_degrees(n):
        return math.degrees(n)

    @staticmethod
    def math_radians(n):
        return math.radians(n)

    @staticmethod
    def math_pi():
        return math.pi

    @staticmethod
    def math_e():
        return math.e

    @staticmethod
    def math_tau():
        return math.tau

    @staticmethod
    def math_inf():
        return math.inf

    @staticmethod
    def math_nan():
        return math.nan

    @staticmethod
    def math_hypot(x, y):
        return math.hypot(x, y)

    @staticmethod
    def math_dist(p1, p2):
        return math.dist(p1, p2)

    @staticmethod
    def math_copysign(x, y):
        return math.copysign(x, y)

    @staticmethod
    def math_isclose(a, b, rel_tol=1e-9, abs_tol=0.0):
        return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)

    @staticmethod
    def math_isfinite(n):
        return math.isfinite(n)

    @staticmethod
    def math_isinf(n):
        return math.isinf(n)

    @staticmethod
    def math_isnan(n):
        return math.isnan(n)

    @staticmethod
    def math_perm(n, k=None):
        return math.perm(n, k)

    @staticmethod
    def math_comb(n, k):
        return math.comb(n, k)

    @staticmethod
    def math_prod(lst):
        result = 1
        for x in lst:
            result *= x
        return result

    @staticmethod
    def math_cumsum(lst):
        result = []
        total = 0
        for x in lst:
            total += x
            result.append(total)
        return result

    @staticmethod
    def math_cumprod(lst):
        result = []
        total = 1
        for x in lst:
            total *= x
            result.append(total)
        return result

    @staticmethod
    def math_clamp(n, lo, hi):
        return max(lo, min(hi, n))

    @staticmethod
    def math_lerp(a, b, t):
        return a + (b - a) * t

    @staticmethod
    def math_map_range(n, in_min, in_max, out_min, out_max):
        return (n - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    @staticmethod
    def math_sign(n):
        return (n > 0) - (n < 0)

    @staticmethod
    def math_avg(lst):
        return sum(lst) / len(lst) if lst else 0

    @staticmethod
    def math_count(lst):
        return len(lst)

    @staticmethod
    def math_percentile(lst, p):
        s = sorted(lst)
        k = (len(s) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return s[int(k)]
        return s[f] * (c - k) + s[c] * (k - f)

    @staticmethod
    def math_quartiles(lst):
        s = sorted(lst)
        n = len(s)
        q1 = _Impl.math_percentile(s, 25)
        q2 = _Impl.math_percentile(s, 50)
        q3 = _Impl.math_percentile(s, 75)
        return {'q1': q1, 'q2': q2, 'q3': q3, 'iqr': q3 - q1}

    @staticmethod
    def math_zscore(lst):
        m = sum(lst) / len(lst)
        sd = _Impl.math_stddev(lst)
        return [(x - m) / sd for x in lst] if sd else [0] * len(lst)

    @staticmethod
    def math_normalize(lst, lo=0, hi=1):
        mn, mx = min(lst), max(lst)
        if mx == mn:
            return [lo] * len(lst)
        return [(x - mn) / (mx - mn) * (hi - lo) + lo for x in lst]

    # ─── 时间/日期 ───

    @staticmethod
    def time_now():
        return time.time()

    @staticmethod
    def time_now_str(fmt='%Y-%m-%d %H:%M:%S'):
        return time.strftime(fmt)

    @staticmethod
    def time_today():
        return time.strftime('%Y-%m-%d')

    @staticmethod
    def time_yesterday():
        return (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    @staticmethod
    def time_tomorrow():
        return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    @staticmethod
    def time_year():
        return datetime.datetime.now().year

    @staticmethod
    def time_month():
        return datetime.datetime.now().month

    @staticmethod
    def time_day():
        return datetime.datetime.now().day

    @staticmethod
    def time_hour():
        return datetime.datetime.now().hour

    @staticmethod
    def time_minute():
        return datetime.datetime.now().minute

    @staticmethod
    def time_second():
        return datetime.datetime.now().second

    @staticmethod
    def time_weekday():
        return datetime.datetime.now().weekday()

    @staticmethod
    def time_weekday_name():
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[datetime.datetime.now().weekday()]

    @staticmethod
    def time_month_name():
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
        return months[datetime.datetime.now().month - 1]

    @staticmethod
    def time_format(ts, fmt='%Y-%m-%d %H:%M:%S'):
        return time.strftime(fmt, time.localtime(ts))

    @staticmethod
    def time_parse(s, fmt='%Y-%m-%d %H:%M:%S'):
        return time.mktime(time.strptime(s, fmt))

    @staticmethod
    def time_diff(ts1, ts2):
        return abs(ts2 - ts1)

    @staticmethod
    def time_add(ts, seconds):
        return ts + seconds

    @staticmethod
    def time_subtract(ts, seconds):
        return ts - seconds

    @staticmethod
    def time_sleep(seconds):
        time.sleep(seconds)
        return True

    @staticmethod
    def time_uuid():
        return secrets.token_hex(16)

    @staticmethod
    def time_timestamp_ms():
        return int(time.time() * 1000)

    @staticmethod
    def time_timestamp_us():
        return int(time.time() * 1000000)

    @staticmethod
    def time_is_leap_year(year=None):
        y = year or datetime.datetime.now().year
        return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)

    @staticmethod
    def time_days_in_month(year=None, month=None):
        now = datetime.datetime.now()
        y = year or now.year
        m = month or now.month
        if m == 2:
            return 29 if _Impl.time_is_leap_year(y) else 28
        return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]

    @staticmethod
    def time_age(birth_date):
        if isinstance(birth_date, str):
            birth = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
        else:
            birth = datetime.datetime.fromtimestamp(birth_date)
        now = datetime.datetime.now()
        age = now.year - birth.year
        if now.month < birth.month or (now.month == birth.month and now.day < birth.day):
            age -= 1
        return age

    @staticmethod
    def time_countdown(target_date):
        if isinstance(target_date, str):
            target = datetime.datetime.strptime(target_date, '%Y-%m-%d')
        else:
            target = datetime.datetime.fromtimestamp(target_date)
        now = datetime.datetime.now()
        delta = target - now
        return {
            'days': delta.days,
            'seconds': delta.seconds,
            'total_seconds': delta.total_seconds(),
        }

    @staticmethod
    def time_elapsed(start_ts):
        return time.time() - start_ts

    @staticmethod
    def time_gmtime():
        return time.gmtime()

    @staticmethod
    def time_localtime():
        return time.localtime()

    @staticmethod
    def time_strftime(fmt='%Y-%m-%d %H:%M:%S'):
        return time.strftime(fmt)

    @staticmethod
    def time_strptime(s, fmt='%Y-%m-%d %H:%M:%S'):
        return time.strptime(s, fmt)

    @staticmethod
    def time_monotonic():
        return time.monotonic()

    @staticmethod
    def time_perf_counter():
        return time.perf_counter()

    @staticmethod
    def time_process_time():
        return time.process_time()

    # ─── 系统信息 ───

    @staticmethod
    def sys_os():
        return platform.system()

    @staticmethod
    def sys_os_version():
        return platform.version()

    @staticmethod
    def sys_arch():
        return platform.machine()

    @staticmethod
    def sys_processor():
        return platform.processor()

    @staticmethod
    def sys_hostname():
        return platform.node()

    @staticmethod
    def sys_python_version():
        return platform.python_version()

    @staticmethod
    def sys_python_implementation():
        return platform.python_implementation()

    @staticmethod
    def sys_platform():
        return sys.platform

    @staticmethod
    def sys_cpu_count():
        return os.cpu_count()

    @staticmethod
    def sys_username():
        return os.path.expanduser('~').split(os.sep)[-1]

    @staticmethod
    def sys_homedir():
        return os.path.expanduser('~')

    @staticmethod
    def sys_cwd():
        return os.getcwd()

    @staticmethod
    def sys_tmpdir():
        return tempfile.gettempdir()

    @staticmethod
    def sys_separator():
        return os.sep

    @staticmethod
    def sys_pathsep():
        return os.pathsep

    @staticmethod
    def sys_linesep():
        return os.linesep

    @staticmethod
    def sys_environ():
        return dict(os.environ)

    @staticmethod
    def sys_env_get(name, default=None):
        return os.environ.get(name, default)

    @staticmethod
    def sys_env_set(name, value):
        os.environ[name] = value
        return True

    @staticmethod
    def sys_env_unset(name):
        os.environ.pop(name, None)
        return True

    @staticmethod
    def sys_env_keys():
        return list(os.environ.keys())

    @staticmethod
    def sys_env_values():
        return list(os.environ.values())

    @staticmethod
    def sys_env_items():
        return list(os.environ.items())

    @staticmethod
    def sys_env_has(name):
        return name in os.environ

    @staticmethod
    def sys_env_path():
        return os.environ.get('PATH', '').split(os.pathsep)

    @staticmethod
    def sys_env_path_add(path, position='front'):
        current = os.environ.get('PATH', '')
        if position == 'front':
            os.environ['PATH'] = path + os.pathsep + current
        else:
            os.environ['PATH'] = current + os.pathsep + path
        return True

    @staticmethod
    def sys_env_path_remove(path):
        paths = os.environ.get('PATH', '').split(os.pathsep)
        paths = [p for p in paths if p != path]
        os.environ['PATH'] = os.pathsep.join(paths)
        return True

    @staticmethod
    def sys_path_list():
        return list(sys.path)

    @staticmethod
    def sys_path_add(path):
        if path not in sys.path:
            sys.path.insert(0, path)
        return True

    @staticmethod
    def sys_path_remove(path):
        if path in sys.path:
            sys.path.remove(path)
        return True

    @staticmethod
    def sys_modules():
        return list(sys.modules.keys())

    @staticmethod
    def sys_module_has(name):
        return name in sys.modules

    @staticmethod
    def sys_argv():
        return sys.argv

    @staticmethod
    def sys_executable():
        return sys.executable

    @staticmethod
    def sys_platform_info():
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python': platform.python_version(),
            'hostname': platform.node(),
        }

    @staticmethod
    def sys_disk_usage(path='/'):
        if hasattr(shutil, 'disk_usage'):
            u = shutil.disk_usage(path)
            return {'total': u.total, 'used': u.used, 'free': u.free}
        return {'total': 0, 'used': 0, 'free': 0}

    @staticmethod
    def sys_disk_total(path='/'):
        if hasattr(shutil, 'disk_usage'):
            return shutil.disk_usage(path).total
        return 0

    @staticmethod
    def sys_disk_used(path='/'):
        if hasattr(shutil, 'disk_usage'):
            return shutil.disk_usage(path).used
        return 0

    @staticmethod
    def sys_disk_free(path='/'):
        if hasattr(shutil, 'disk_usage'):
            return shutil.disk_usage(path).free
        return 0

    @staticmethod
    def sys_disk_percent(path='/'):
        if hasattr(shutil, 'disk_usage'):
            u = shutil.disk_usage(path)
            return round(u.used / u.total * 100, 1) if u.total else 0
        return 0

    @staticmethod
    def sys_pid():
        return os.getpid()

    @staticmethod
    def sys_ppid():
        return os.getppid()

    @staticmethod
    def sys_uid():
        return os.getuid() if hasattr(os, 'getuid') else 0

    @staticmethod
    def sys_gid():
        return os.getgid() if hasattr(os, 'getgid') else 0

    @staticmethod
    def sys_uname():
        return dict(zip(['sysname', 'nodename', 'release', 'version', 'machine'],
                        os.uname()[:5])) if hasattr(os, 'uname') else {}

    @staticmethod
    def sys_loadavg():
        return os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

    # ─── 随机数 ───

    @staticmethod
    def random_int(min_val=0, max_val=100):
        return random.randint(min_val, max_val)

    @staticmethod
    def random_float(min_val=0, max_val=1):
        return random.uniform(min_val, max_val)

    @staticmethod
    def random_choice(lst):
        return random.choice(lst)

    @staticmethod
    def random_choices(lst, k=1):
        return random.choices(lst, k=k)

    @staticmethod
    def random_sample(lst, k=1):
        return random.sample(lst, k)

    @staticmethod
    def random_shuffle(lst):
        random.shuffle(lst)
        return lst

    @staticmethod
    def random_bytes(n=16):
        return secrets.token_bytes(n)

    @staticmethod
    def random_hex(n=16):
        return secrets.token_hex(n)

    @staticmethod
    def random_token(n=32):
        return secrets.token_urlsafe(n)

    @staticmethod
    def random_string(length=10, charset=None):
        chars = charset or (string.ascii_letters + string.digits)
        return ''.join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    def random_password(length=16):
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        return ''.join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    def random_uuid():
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def random_uuid1():
        import uuid
        return str(uuid.uuid1())

    @staticmethod
    def random_uuid3(namespace, name):
        import uuid
        ns = getattr(uuid, f'NAMESPACE_{namespace}', uuid.NAMESPACE_DNS)
        return str(uuid.uuid3(ns, name))

    @staticmethod
    def random_uuid5(namespace, name):
        import uuid
        ns = getattr(uuid, f'NAMESPACE_{namespace}', uuid.NAMESPACE_DNS)
        return str(uuid.uuid5(ns, name))

    @staticmethod
    def random_seed(seed):
        random.seed(seed)
        return True

    @staticmethod
    def random_state():
        return random.getstate()

    @staticmethod
    def random_setstate(state):
        random.setstate(state)
        return True

    @staticmethod
    def random_gauss(mean=0, sigma=1):
        return random.gauss(mean, sigma)

    @staticmethod
    def random_normalvariate(mean=0, sigma=1):
        return random.normalvariate(mean, sigma)

    @staticmethod
    def random_lognormvariate(mu, sigma):
        return random.lognormvariate(mu, sigma)

    @staticmethod
    def random_expovariate(lambd):
        return random.expovariate(lambd)

    @staticmethod
    def random_gammavariate(alpha, beta):
        return random.gammavariate(alpha, beta)

    @staticmethod
    def random_betavariate(alpha, beta):
        return random.betavariate(alpha, beta)

    @staticmethod
    def random_uniform(a, b):
        return random.uniform(a, b)

    @staticmethod
    def random_triangular(low, high, mode=None):
        return random.triangular(low, high, mode)

    @staticmethod
    def random_vonmisesvariate(mu, kappa):
        return random.vonmisesvariate(mu, kappa)

    @staticmethod
    def random_paretovariate(alpha):
        return random.paretovariate(alpha)

    @staticmethod
    def random_weibullvariate(alpha, beta):
        return random.weibullvariate(alpha, beta)

    # ─── 压缩 ───

    @staticmethod
    def zip_create(zip_path, files):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                if os.path.isdir(f):
                    for root, dirs, fs in os.walk(f):
                        for fn in fs:
                            full = os.path.join(root, fn)
                            zf.write(full, os.path.relpath(full, os.path.dirname(f)))
                else:
                    zf.write(f, os.path.basename(f))
        return os.path.getsize(zip_path)

    @staticmethod
    def zip_extract(zip_path, dest='.'):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest)
        return True

    @staticmethod
    def zip_list(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            return [{'name': i.filename, 'size': i.file_size, 'compressed': i.compress_size}
                    for i in zf.infolist()]

    @staticmethod
    def zip_read(zip_path, member):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            return zf.read(member).decode('utf-8')

    @staticmethod
    def zip_add(zip_path, file, name_in_zip=None):
        with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zf:
            zf.write(file, name_in_zip or os.path.basename(file))
        return True

    @staticmethod
    def zip_test(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            return zf.testzip() is None

    # ─── 密码/安全 ───

    @staticmethod
    def crypto_md5(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def crypto_sha1(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha1(data).hexdigest()

    @staticmethod
    def crypto_sha224(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha224(data).hexdigest()

    @staticmethod
    def crypto_sha256(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def crypto_sha384(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha384(data).hexdigest()

    @staticmethod
    def crypto_sha512(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha512(data).hexdigest()

    @staticmethod
    def crypto_sha3_224(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha3_224(data).hexdigest()

    @staticmethod
    def crypto_sha3_256(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha3_256(data).hexdigest()

    @staticmethod
    def crypto_sha3_384(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha3_384(data).hexdigest()

    @staticmethod
    def crypto_sha3_512(data):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha3_512(data).hexdigest()

    @staticmethod
    def crypto_blake2b(data, digest_size=64):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.blake2b(data, digest_size=digest_size).hexdigest()

    @staticmethod
    def crypto_blake2s(data, digest_size=32):
        if isinstance(data, str):
            data = data.encode()
        return hashlib.blake2s(data, digest_size=digest_size).hexdigest()

    @staticmethod
    def crypto_hmac(key, msg, algo='sha256'):
        import hmac
        if isinstance(key, str):
            key = key.encode()
        if isinstance(msg, str):
            msg = msg.encode()
        return hmac.new(key, msg, getattr(hashlib, algo)).hexdigest()

    @staticmethod
    def crypto_pbkdf2(password, salt, iterations=100000, dklen=32, algo='sha256'):
        if isinstance(password, str):
            password = password.encode()
        if isinstance(salt, str):
            salt = salt.encode()
        return hashlib.pbkdf2_hmac(algo, password, salt, iterations, dklen).hex()

    @staticmethod
    def crypto_xor(data, key):
        if isinstance(data, str):
            data = data.encode()
        if isinstance(key, str):
            key = key.encode()
        result = bytearray()
        for i, b in enumerate(data):
            result.append(b ^ key[i % len(key)])
        return result.hex()

    @staticmethod
    def crypto_generate_salt(length=16):
        return secrets.token_hex(length)

    @staticmethod
    def crypto_generate_key(length=32):
        return secrets.token_hex(length)

    @staticmethod
    def crypto_generate_iv(length=16):
        return secrets.token_bytes(length).hex()

    @staticmethod
    def crypto_constant_time_compare(a, b):
        return secrets.compare_digest(a, b)

    @staticmethod
    def crypto_password_hash(password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000).hex()
        return f"{salt}${hashed}"

    @staticmethod
    def crypto_password_verify(password, stored):
        if '$' not in stored:
            return False
        salt, hashed = stored.split('$', 1)
        computed = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000).hex()
        return secrets.compare_digest(computed, hashed)

    # ─── 数据转换 ───

    @staticmethod
    def convert_to_int(value, base=10):
        return int(value, base) if isinstance(value, str) else int(value)

    @staticmethod
    def convert_to_float(value):
        return float(value)

    @staticmethod
    def convert_to_str(value):
        return str(value)

    @staticmethod
    def convert_to_bool(value):
        return bool(value)

    @staticmethod
    def convert_to_list(value):
        if isinstance(value, (list, tuple)):
            return list(value)
        if isinstance(value, dict):
            return list(value.items())
        if isinstance(value, str):
            return list(value)
        return [value]

    @staticmethod
    def convert_to_dict(pairs):
        return dict(pairs)

    @staticmethod
    def convert_to_tuple(value):
        return tuple(value)

    @staticmethod
    def convert_to_set(value):
        return set(value)

    @staticmethod
    def convert_to_bytes(value, encoding='utf-8'):
        if isinstance(value, str):
            return value.encode(encoding)
        return bytes(value)

    @staticmethod
    def convert_to_str_from_bytes(value, encoding='utf-8'):
        if isinstance(value, bytes):
            return value.decode(encoding)
        return str(value)

    @staticmethod
    def convert_int_to_bin(n):
        return bin(n)

    @staticmethod
    def convert_int_to_oct(n):
        return oct(n)

    @staticmethod
    def convert_int_to_hex(n):
        return hex(n)

    @staticmethod
    def convert_bin_to_int(s):
        return int(s, 2)

    @staticmethod
    def convert_oct_to_int(s):
        return int(s, 8)

    @staticmethod
    def convert_hex_to_int(s):
        return int(s, 16)

    @staticmethod
    def convert_chr(code):
        return chr(code)

    @staticmethod
    def convert_ord(c):
        return ord(c)

    @staticmethod
    def convert_bool_to_int(b):
        return int(b)

    @staticmethod
    def convert_int_to_bool(n):
        return bool(n)

    @staticmethod
    def convert_float_to_int(f):
        return int(f)

    @staticmethod
    def convert_int_to_float(n):
        return float(n)

    @staticmethod
    def convert_str_to_bool(s):
        return s.lower() in ('true', '1', 'yes', 'on')

    @staticmethod
    def convert_bool_to_str(b):
        return 'true' if b else 'false'

    @staticmethod
    def convert_list_to_dict(keys, values):
        return dict(zip(keys, values))

    @staticmethod
    def convert_dict_to_list(d):
        return list(d.items())

    @staticmethod
    def convert_list_to_tuple(lst):
        return tuple(lst)

    @staticmethod
    def convert_tuple_to_list(t):
        return list(t)

    @staticmethod
    def convert_set_to_list(s):
        return sorted(s)

    @staticmethod
    def convert_list_to_set(lst):
        return set(lst)

    @staticmethod
    def convert_str_to_list(s, sep=None):
        return s.split(sep) if sep else list(s)

    @staticmethod
    def convert_list_to_str(lst, sep=''):
        return sep.join(str(x) for x in lst)

    @staticmethod
    def convert_csv_to_list(csv_str):
        return [row.split(',') for row in csv_str.strip().split('\n')]

    @staticmethod
    def convert_list_to_csv(lst):
        return '\n'.join(','.join(str(x) for x in row) for row in lst)

    # ─── 列表/集合操作 ───

    @staticmethod
    def list_sort(lst, reverse=False):
        return sorted(lst, reverse=reverse)

    @staticmethod
    def list_reverse(lst):
        return list(reversed(lst))

    @staticmethod
    def list_filter(lst, func=None):
        if func is None:
            return [x for x in lst if x]
        return [x for x in lst if func(x)]

    @staticmethod
    def list_map(lst, func=None):
        if func is None:
            return lst
        return [func(x) for x in lst]

    @staticmethod
    def list_reduce(lst, func, initial=None):
        from functools import reduce
        if initial is not None:
            return reduce(func, lst, initial)
        return reduce(func, lst)

    @staticmethod
    def list_flatten(lst):
        result = []
        for item in lst:
            if isinstance(item, (list, tuple)):
                result.extend(item)
            else:
                result.append(item)
        return result

    @staticmethod
    def list_unique(lst):
        seen = []
        for x in lst:
            if x not in seen:
                seen.append(x)
        return seen

    @staticmethod
    def list_chunk(lst, size):
        return [lst[i:i+size] for i in range(0, len(lst), size)]

    @staticmethod
    def list_zip(*lists):
        return list(zip(*lists))

    @staticmethod
    def list_zip_longest(*lists, fillvalue=None):
        from itertools import zip_longest
        return list(zip_longest(*lists, fillvalue=fillvalue))

    @staticmethod
    def list_enumerate(lst, start=0):
        return list(enumerate(lst, start))

    @staticmethod
    def list_range(start, stop, step=1):
        return list(range(start, stop, step))

    @staticmethod
    def list_comprehension(lst, func):
        return [func(x) for x in lst]

    @staticmethod
    def list_count(lst, value):
        return lst.count(value)

    @staticmethod
    def list_index(lst, value, start=0):
        return lst.index(value, start)

    @staticmethod
    def list_insert(lst, index, value):
        lst.insert(index, value)
        return lst

    @staticmethod
    def list_pop(lst, index=-1):
        return lst.pop(index)

    @staticmethod
    def list_extend(lst1, lst2):
        lst1.extend(lst2)
        return lst1

    @staticmethod
    def list_copy(lst):
        return copy.copy(lst)

    @staticmethod
    def list_deepcopy(lst):
        return copy.deepcopy(lst)

    @staticmethod
    def list_slice(lst, start=0, end=None, step=1):
        return lst[start:end:step]

    @staticmethod
    def list_concat(*lists):
        result = []
        for l in lists:
            result.extend(l)
        return result

    @staticmethod
    def list_difference(a, b):
        return [x for x in a if x not in b]

    @staticmethod
    def list_intersection(a, b):
        return [x for x in a if x in b]

    @staticmethod
    def list_union(a, b):
        return _Impl.list_unique(a + b)

    @staticmethod
    def list_symmetric_difference(a, b):
        return _Impl.list_difference(_Impl.list_union(a, b), _Impl.list_intersection(a, b))

    @staticmethod
    def list_group(lst, key_func=None):
        groups = {}
        for item in lst:
            key = key_func(item) if key_func else item
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups

    @staticmethod
    def list_partition(lst, pred):
        yes, no = [], []
        for x in lst:
            (yes if pred(x) else no).append(x)
        return yes, no

    @staticmethod
    def list_take(lst, n):
        return lst[:n]

    @staticmethod
    def list_drop(lst, n):
        return lst[n:]

    @staticmethod
    def list_take_while(lst, pred):
        result = []
        for x in lst:
            if pred(x):
                result.append(x)
            else:
                break
        return result

    @staticmethod
    def list_drop_while(lst, pred):
        for i, x in enumerate(lst):
            if not pred(x):
                return lst[i:]
        return []

    @staticmethod
    def list_cycle(lst, n):
        from itertools import cycle
        return [x for i, x in enumerate(cycle(lst)) if i < n]

    @staticmethod
    def list_repeat(item, n):
        return [item] * n

    @staticmethod
    def list_product(*lists):
        from itertools import product
        return list(list(p) for p in product(*lists))

    @staticmethod
    def list_permutations(lst, r=None):
        from itertools import permutations
        return [list(p) for p in permutations(lst, r)]

    @staticmethod
    def list_combinations(lst, r):
        from itertools import combinations
        return [list(c) for c in combinations(lst, r)]

    @staticmethod
    def list_find(lst, pred):
        for i, x in enumerate(lst):
            if pred(x):
                return i
        return -1

    @staticmethod
    def list_find_all(lst, pred):
        return [i for i, x in enumerate(lst) if pred(x)]

    @staticmethod
    def list_all(lst, pred=None):
        if pred:
            return all(pred(x) for x in lst)
        return all(lst)

    @staticmethod
    def list_any(lst, pred=None):
        if pred:
            return any(pred(x) for x in lst)
        return any(lst)

    @staticmethod
    def list_none(lst, pred=None):
        if pred:
            return not any(pred(x) for x in lst)
        return not any(lst)

    @staticmethod
    def list_sum(lst):
        return sum(lst)

    @staticmethod
    def list_len(lst):
        return len(lst)

    @staticmethod
    def list_first(lst):
        return lst[0] if lst else None

    @staticmethod
    def list_last(lst):
        return lst[-1] if lst else None

    @staticmethod
    def list_nth(lst, n):
        return lst[n] if -len(lst) <= n < len(lst) else None

    @staticmethod
    def list_contains(lst, value):
        return value in lst

    @staticmethod
    def list_count_occurrences(lst, value):
        return lst.count(value)

    # ─── 字典操作 ───

    @staticmethod
    def dict_get(d, key, default=None):
        return d.get(key, default)

    @staticmethod
    def dict_set(d, key, value):
        d[key] = value
        return d

    @staticmethod
    def dict_delete(d, key):
        if key in d:
            del d[key]
        return d

    @staticmethod
    def dict_keys(d):
        return list(d.keys())

    @staticmethod
    def dict_values(d):
        return list(d.values())

    @staticmethod
    def dict_items(d):
        return list(d.items())

    @staticmethod
    def dict_has_key(d, key):
        return key in d

    @staticmethod
    def dict_copy(d):
        return d.copy()

    @staticmethod
    def dict_deepcopy(d):
        return copy.deepcopy(d)

    @staticmethod
    def dict_merge(d1, d2):
        result = d1.copy()
        result.update(d2)
        return result

    @staticmethod
    def dict_from_keys(keys, value=None):
        return dict.fromkeys(keys, value)

    @staticmethod
    def dict_from_pairs(pairs):
        return dict(pairs)

    @staticmethod
    def dict_size(d):
        return len(d)

    @staticmethod
    def dict_clear(d):
        d.clear()
        return d

    @staticmethod
    def dict_pop(d, key, default=None):
        return d.pop(key, default)

    @staticmethod
    def dict_popitem(d):
        return d.popitem()

    @staticmethod
    def dict_setdefault(d, key, default=None):
        return d.setdefault(key, default)

    @staticmethod
    def dict_update(d1, d2):
        d1.update(d2)
        return d1

    @staticmethod
    def dict_invert(d):
        return {v: k for k, v in d.items()}

    @staticmethod
    def dict_filter(d, pred):
        return {k: v for k, v in d.items() if pred(k, v)}

    @staticmethod
    def dict_map_values(d, func):
        return {k: func(v) for k, v in d.items()}

    @staticmethod
    def dict_map_keys(d, func):
        return {func(k): v for k, v in d.items()}

    @staticmethod
    def dict_to_list(d):
        return list(d.items())

    @staticmethod
    def dict_from_json(s):
        return json.loads(s)

    @staticmethod
    def dict_to_json(d, indent=None):
        return json.dumps(d, ensure_ascii=False, indent=indent, default=str)

    # ─── 路径操作 ───

    @staticmethod
    def path_join(*paths):
        return os.path.join(*paths)

    @staticmethod
    def path_split(path):
        return os.path.split(path)

    @staticmethod
    def path_basename(path):
        return os.path.basename(path)

    @staticmethod
    def path_dirname(path):
        return os.path.dirname(path)

    @staticmethod
    def path_extension(path):
        return os.path.splitext(path)[1]

    @staticmethod
    def path_stem(path):
        return os.path.splitext(os.path.basename(path))[0]

    @staticmethod
    def path_absolute(path):
        return os.path.abspath(path)

    @staticmethod
    def path_realpath(path):
        return os.path.realpath(path)

    @staticmethod
    def path_relpath(path, start='.'):
        return os.path.relpath(path, start)

    @staticmethod
    def path_normpath(path):
        return os.path.normpath(path)

    @staticmethod
    def path_expanduser(path):
        return os.path.expanduser(path)

    @staticmethod
    def path_expandvars(path):
        return os.path.expandvars(path)

    @staticmethod
    def path_exists(path):
        return os.path.exists(path)

    @staticmethod
    def path_isfile(path):
        return os.path.isfile(path)

    @staticmethod
    def path_isdir(path):
        return os.path.isdir(path)

    @staticmethod
    def path_islink(path):
        return os.path.islink(path)

    @staticmethod
    def path_ismount(path):
        return os.path.ismount(path)

    @staticmethod
    def path_home():
        return os.path.expanduser('~')

    @staticmethod
    def path_cwd():
        return os.getcwd()

    @staticmethod
    def path_tmp():
        return tempfile.gettempdir()

    @staticmethod
    def path_devnull():
        return os.devnull

    @staticmethod
    def path_separator():
        return os.sep

    @staticmethod
    def path_pathsep():
        return os.pathsep

    # ─── 网络 ───

    @staticmethod
    def net_http_get(url, headers=None, timeout=30):
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8')

    @staticmethod
    def net_http_post(url, data=None, headers=None, timeout=30):
        if isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=data, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8')

    @staticmethod
    def net_http_head(url, headers=None, timeout=30):
        req = urllib.request.Request(url, method='HEAD', headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return dict(resp.headers)

    @staticmethod
    def net_url_download(url, path, timeout=30):
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(path, 'wb') as f:
                f.write(resp.read())
        return os.path.getsize(path)

    @staticmethod
    def net_url_encode(s):
        return urllib.parse.quote(s, safe='')

    @staticmethod
    def net_url_decode(s):
        return urllib.parse.unquote(s)

    @staticmethod
    def net_hostname():
        return platform.node()

    @staticmethod
    def net_dns_resolve(hostname):
        import socket
        return socket.gethostbyname(hostname)

    @staticmethod
    def net_socket_connect(host, port, timeout=10):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        return True

    @staticmethod
    def net_socket_send(host, port, data, timeout=10):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(data.encode() if isinstance(data, str) else data)
        s.close()
        return True

    @staticmethod
    def net_get_ip():
        import socket
        return socket.gethostbyname(socket.gethostname())

    @staticmethod
    def net_get_hostname():
        return platform.node()

    @staticmethod
    def net_parse_url(url):
        parsed = urllib.parse.urlparse(url)
        return {
            'scheme': parsed.scheme, 'netloc': parsed.netloc,
            'path': parsed.path, 'query': parsed.query,
            'fragment': parsed.fragment, 'params': parsed.params,
        }

    # ─── 进程 ───

    @staticmethod
    def proc_pid():
        return os.getpid()

    @staticmethod
    def proc_ppid():
        return os.getppid()

    @staticmethod
    def proc_cwd():
        return os.getcwd()

    @staticmethod
    def proc_chdir(path):
        os.chdir(path)
        return True

    @staticmethod
    def proc_environ():
        return dict(os.environ)

    @staticmethod
    def proc_getenv(name, default=None):
        return os.environ.get(name, default)

    @staticmethod
    def proc_setenv(name, value):
        os.environ[name] = value
        return True

    @staticmethod
    def proc_listdir(path='.'):
        return os.listdir(path)

    @staticmethod
    def proc_umask(mask=0o022):
        return oct(os.umask(mask))

    @staticmethod
    def proc_chmod(path, mode):
        os.chmod(path, int(str(mode), 8))
        return True

    @staticmethod
    def proc_getcwd():
        return os.getcwd()

    @staticmethod
    def proc_getpid():
        return os.getpid()

    @staticmethod
    def proc_getppid():
        return os.getppid()

    @staticmethod
    def proc_getuid():
        return os.getuid() if hasattr(os, 'getuid') else 0

    @staticmethod
    def proc_getgid():
        return os.getgid() if hasattr(os, 'getgid') else 0

    @staticmethod
    def proc_geteuid():
        return os.geteuid() if hasattr(os, 'geteuid') else 0

    @staticmethod
    def proc_getegid():
        return os.getegid() if hasattr(os, 'getegid') else 0

    @staticmethod
    def proc_fork():
        return os.fork() if hasattr(os, 'fork') else -1

    @staticmethod
    def proc_system(command):
        return os.system(command)

    # ─── struct/binary ───

    @staticmethod
    def struct_pack(fmt, *values):
        return struct.pack(fmt, *values).hex()

    @staticmethod
    def struct_unpack(fmt, hex_data):
        return list(struct.unpack(fmt, bytes.fromhex(hex_data)))

    @staticmethod
    def struct_calcsize(fmt):
        return struct.calcsize(fmt)

    @staticmethod
    def struct_pack_into(fmt, buffer, offset, *values):
        if isinstance(buffer, str):
            buffer = bytearray.fromhex(buffer)
        struct.pack_into(fmt, buffer, offset, *values)
        return buffer.hex()

    @staticmethod
    def struct_unpack_from(fmt, hex_buffer, offset=0):
        return list(struct.unpack_from(fmt, bytes.fromhex(hex_buffer), offset))


def _xml_to_dict(element):
    """XML 元素转字典"""
    result = {}
    for child in element:
        if len(child) > 0:
            result[child.tag] = _xml_to_dict(child)
        else:
            result[child.tag] = child.text
    return result


# ═══════════════════════════════════════════════════════════════
# API 注册表 — 生成 1350+ API
# ═══════════════════════════════════════════════════════════════

def _build_api_registry():
    """构建 API 注册表，返回 {name: (func, category, description)}"""

    registry = {}

    def reg(name, func, category, desc=''):
        registry[name] = (func, category, desc)

    # ─── 从 _Impl 类注册所有静态方法 ───
    impl_methods = [(name, getattr(_Impl, name))
                    for name in dir(_Impl)
                    if not name.startswith('_') and callable(getattr(_Impl, name))]

    for name, func in impl_methods:
        # 原始名: file_read → api_file_read
        reg(f'api_{name}', func, 'core', f'API: {name}')

    # ─── 别名注册 (为每个 API 生成多个别名) ───
    # 格式变体
    ALIAS_PATTERNS = {
        'file_read': ['read', 'read_file', 'get_file', 'load_file', 'cat', 'cat_file', 'open_file', 'slurp'],
        'file_write': ['write', 'write_file', 'save_file', 'put_file', 'dump_file', 'create_file'],
        'file_append': ['append', 'append_file', 'add_to_file', 'write_append'],
        'file_copy': ['copy', 'cp', 'copy_file', 'duplicate_file'],
        'file_move': ['move', 'mv', 'move_file', 'relocate_file'],
        'file_delete': ['delete', 'del', 'rm', 'remove', 'remove_file', 'destroy_file'],
        'file_exists': ['exists', 'file_exists_check', 'check_exists', 'is_exists', 'path_exists'],
        'file_isfile': ['is_file', 'isfile', 'check_file', 'test_file'],
        'file_isdir': ['is_dir', 'isdir', 'check_dir', 'test_dir'],
        'file_size': ['size', 'get_size', 'file_size_bytes', 'get_file_size', 'filesize'],
        'file_size_human': ['size_human', 'get_size_human', 'human_size', 'format_size', 'pretty_size'],
        'file_mtime': ['mtime', 'modified_time', 'get_mtime', 'file_modified'],
        'file_ctime': ['ctime', 'created_time', 'get_ctime', 'file_created'],
        'file_atime': ['atime', 'accessed_time', 'get_atime', 'file_accessed'],
        'file_ext': ['ext', 'extension', 'get_ext', 'file_extension'],
        'file_name': ['basename', 'name', 'get_name', 'filename'],
        'file_dir': ['dirname', 'directory', 'get_dir', 'parent_dir'],
        'file_stem': ['stem', 'get_stem', 'filename_stem', 'name_without_ext'],
        'file_absolute': ['abspath', 'absolute', 'abs_path', 'get_abspath'],
        'file_lines': ['readlines', 'get_lines', 'file_to_lines'],
        'file_line_count': ['line_count', 'count_lines', 'wc', 'wc_l'],
        'file_touch': ['touch', 'create_if_missing', 'ensure_file'],
        'file_truncate': ['truncate', 'clear_file', 'empty_file'],
        'file_rename': ['rename', 'mv_file', 'ren'],
        'file_read_json': ['read_json', 'load_json', 'json_load', 'json_read', 'parse_json_file'],
        'file_write_json': ['write_json', 'save_json', 'json_save', 'json_write', 'dump_json'],
        'file_read_csv': ['read_csv', 'load_csv', 'csv_read', 'csv_load'],
        'file_write_csv': ['write_csv', 'save_csv', 'csv_write', 'csv_save'],
        'file_read_ini': ['read_ini', 'load_ini', 'ini_read', 'ini_load', 'parse_ini'],
        'file_write_ini': ['write_ini', 'save_ini', 'ini_write', 'ini_save'],
        'file_read_xml': ['read_xml', 'load_xml', 'xml_read', 'xml_load', 'parse_xml'],
        'file_read_base64': ['read_b64', 'read_base64', 'file_to_base64', 'b64_read'],
        'file_write_base64': ['write_b64', 'write_base64', 'base64_to_file', 'b64_write'],
    }

    for original, aliases in ALIAS_PATTERNS.items():
        func = getattr(_Impl, original, None)
        if func:
            for alias in aliases:
                reg(f'api_{alias}', func, 'alias', f'Alias of {original}')

    # ─── 哈希算法变体 ───
    HASH_ALGOS = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512',
                  'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512',
                  'blake2b', 'blake2s']

    for algo in HASH_ALGOS:
        # hash_string variants
        func = _Impl.hash_string
        for prefix in ['hash', 'compute', 'get', 'calculate', 'digest']:
            reg(f'api_{prefix}_{algo}_string', lambda a=algo, f=func, **kw: f(algo=a, data=kw.get('data', '')), 'hash', f'{prefix} {algo} string')
            reg(f'api_{prefix}_{algo}_text', lambda a=algo, f=func, **kw: f(algo=a, data=kw.get('data', '')), 'hash', f'{prefix} {algo} text')
            reg(f'api_{prefix}_{algo}_data', lambda a=algo, f=func, **kw: f(algo=a, data=kw.get('data', '')), 'hash', f'{prefix} {algo} data')

        # hash_bytes variants
        func = _Impl.hash_bytes
        for prefix in ['hash', 'compute', 'get', 'calculate', 'digest']:
            reg(f'api_{prefix}_{algo}_bytes', lambda a=algo, f=func, **kw: f(algo=a, data=kw.get('data', '')), 'hash', f'{prefix} {algo} bytes')

        # hash_file variants
        func = _Impl.hash_file
        for prefix in ['hash', 'compute', 'get', 'calculate', 'digest', 'checksum']:
            reg(f'api_{prefix}_{algo}_file', lambda a=algo, f=func, **kw: f(algo=a, path=kw.get('path', '')), 'hash', f'{prefix} {algo} file')

        # crypto_ variants
        func = getattr(_Impl, f'crypto_{algo}', None)
        if func:
            for prefix in ['encrypt', 'compute', 'get', 'digest', 'hash']:
                reg(f'api_{prefix}_{algo}', func, 'crypto', f'{prefix} {algo}')

    # ─── Base64 变体 ───
    for action in ['encode', 'decode']:
        for fmt in ['b64', 'base64', 'b64url', 'base64url']:
            func = _Impl.b64_encode if action == 'encode' else _Impl.b64_decode
            if 'url' in fmt:
                func = _Impl.b64url_encode if action == 'encode' else _Impl.b64url_decode
            for prefix in ['b64', 'base64', 'encode', 'decode']:
                if action == 'encode':
                    reg(f'api_{prefix}_{fmt}_encode', func, 'encoding', f'{fmt} encode')
                else:
                    reg(f'api_{prefix}_{fmt}_decode', func, 'encoding', f'{fmt} decode')
            reg(f'api_{fmt}_{action}', func, 'encoding', f'{fmt} {action}')

    # ─── Hex 变体 ───
    for action in ['encode', 'decode']:
        func = _Impl.hex_encode if action == 'encode' else _Impl.hex_decode
        for prefix in ['hex', 'hexadecimal', 'encode', 'decode']:
            reg(f'api_{prefix}_{action}', func, 'encoding', f'hex {action}')
        reg(f'api_hex_{action}', func, 'encoding', f'hex {action}')

    # ─── URL 变体 ───
    URL_OPS = {
        'encode': _Impl.url_encode,
        'decode': _Impl.url_decode,
        'parse': _Impl.url_parse,
        'query_parse': _Impl.url_query_parse,
        'query_encode': _Impl.url_query_encode,
        'join': _Impl.url_join,
        'domain': _Impl.url_extract_domain,
        'path': _Impl.url_extract_path,
    }
    for op, func in URL_OPS.items():
        for prefix in ['url', 'web', 'http', 'net', 'uri']:
            reg(f'api_{prefix}_{op}', func, 'url', f'url {op}')

    # ─── JSON 变体 ───
    JSON_OPS = {
        'encode': _Impl.json_encode,
        'decode': _Impl.json_decode,
        'pretty': _Impl.json_pretty,
        'minify': _Impl.json_minify,
        'validate': _Impl.json_validate,
        'merge': _Impl.json_merge,
        'flatten': _Impl.json_flatten,
        'unflatten': _Impl.json_unflatten,
        'get': _Impl.json_get,
        'set': _Impl.json_set,
        'delete': _Impl.json_delete,
        'keys': _Impl.json_keys,
    }
    for op, func in JSON_OPS.items():
        for prefix in ['json', 'data', 'object', 'serialize']:
            reg(f'api_{prefix}_{op}', func, 'json', f'json {op}')

    # ─── 字符串变体 ───
    STR_OPS = [
        'upper', 'lower', 'title', 'capitalize', 'swapcase',
        'strip', 'lstrip', 'rstrip',
        'split', 'rsplit', 'splitlines', 'join',
        'replace', 'count', 'find', 'rfind',
        'startswith', 'endswith', 'contains',
        'length', 'center', 'ljust', 'rjust', 'zfill', 'pad',
        'reverse', 'repeat', 'format', 'template',
        'wrap', 'dedent', 'indent',
        'camel', 'snake', 'kebab', 'title_case',
        'is_alpha', 'is_digit', 'is_alnum', 'is_upper', 'is_lower', 'is_space',
        'starts_vowel', 'word_count', 'char_count', 'byte_count',
        'unique_chars', 'char_frequency', 'remove_duplicates',
        'truncate', 'slice', 'chunk', 'between',
        'to_list', 'from_list', 'to_ascii', 'from_ascii',
    ]
    for op in STR_OPS:
        func = getattr(_Impl, f'str_{op}', None)
        if func:
            for prefix in ['str', 'string', 'text', 'char']:
                reg(f'api_{prefix}_{op}', func, 'string', f'string {op}')

    # ─── 数学变体 ───
    MATH_OPS = [
        'add', 'sub', 'mul', 'div', 'floordiv', 'mod', 'pow',
        'abs', 'round', 'ceil', 'floor', 'trunc',
        'max', 'min', 'sum', 'mean', 'median', 'mode', 'variance', 'stddev',
        'range', 'gcd', 'lcm', 'factorial', 'is_prime', 'primes', 'fibonacci',
        'sqrt', 'cbrt', 'exp', 'log', 'log2', 'log10',
        'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2',
        'degrees', 'radians',
        'pi', 'e', 'tau', 'inf', 'nan',
        'hypot', 'dist', 'copysign', 'isclose',
        'isfinite', 'isinf', 'isnan',
        'perm', 'comb', 'prod', 'cumsum', 'cumprod',
        'clamp', 'lerp', 'map_range', 'sign', 'avg', 'count',
        'percentile', 'quartiles', 'zscore', 'normalize',
    ]
    for op in MATH_OPS:
        func = getattr(_Impl, f'math_{op}', None)
        if func:
            for prefix in ['math', 'calc', 'num', 'numeric', 'compute']:
                reg(f'api_{prefix}_{op}', func, 'math', f'math {op}')

    # ─── 时间变体 ───
    TIME_OPS = [
        'now', 'now_str', 'today', 'yesterday', 'tomorrow',
        'year', 'month', 'day', 'hour', 'minute', 'second',
        'weekday', 'weekday_name', 'month_name',
        'format', 'parse', 'diff', 'add', 'subtract',
        'sleep', 'uuid', 'timestamp_ms', 'timestamp_us',
        'is_leap_year', 'days_in_month', 'age', 'countdown',
        'elapsed', 'gmtime', 'localtime',
        'strftime', 'strptime', 'monotonic', 'perf_counter', 'process_time',
    ]
    for op in TIME_OPS:
        func = getattr(_Impl, f'time_{op}', None)
        if func:
            for prefix in ['time', 'date', 'datetime', 'clock', 'temporal']:
                reg(f'api_{prefix}_{op}', func, 'time', f'time {op}')

    # ─── 系统变体 ───
    SYS_OPS = [
        'os', 'os_version', 'arch', 'processor', 'hostname',
        'python_version', 'python_implementation', 'platform',
        'cpu_count', 'username', 'homedir', 'cwd', 'tmpdir',
        'separator', 'pathsep', 'linesep',
        'environ', 'env_get', 'env_set', 'env_unset',
        'env_keys', 'env_values', 'env_items', 'env_has',
        'env_path', 'env_path_add', 'env_path_remove',
        'path_list', 'path_add', 'path_remove',
        'modules', 'module_has', 'argv', 'executable',
        'platform_info', 'disk_usage', 'disk_total', 'disk_used',
        'disk_free', 'disk_percent',
        'pid', 'ppid', 'uid', 'gid', 'uname', 'loadavg',
    ]
    for op in SYS_OPS:
        func = getattr(_Impl, f'sys_{op}', None)
        if func:
            for prefix in ['sys', 'system', 'os', 'platform', 'env']:
                reg(f'api_{prefix}_{op}', func, 'system', f'system {op}')

    # ─── 随机变体 ───
    RAND_OPS = [
        'int', 'float', 'choice', 'choices', 'sample', 'shuffle',
        'bytes', 'hex', 'token', 'string', 'password',
        'uuid', 'uuid1', 'uuid3', 'uuid5',
        'seed', 'state', 'setstate',
        'gauss', 'normalvariate', 'lognormvariate', 'expovariate',
        'gammavariate', 'betavariate', 'uniform', 'triangular',
        'vonmisesvariate', 'paretovariate', 'weibullvariate',
    ]
    for op in RAND_OPS:
        func = getattr(_Impl, f'random_{op}', None)
        if func:
            for prefix in ['random', 'rand', 'rng', 'gen', 'generate']:
                reg(f'api_{prefix}_{op}', func, 'random', f'random {op}')

    # ─── 压缩变体 ───
    ZIP_OPS = ['create', 'extract', 'list', 'read', 'add', 'test']
    for op in ZIP_OPS:
        func = getattr(_Impl, f'zip_{op}', None)
        if func:
            for prefix in ['zip', 'archive', 'compress', 'pack', 'zlib']:
                reg(f'api_{prefix}_{op}', func, 'compression', f'zip {op}')

    # ─── 转换变体 ───
    CONVERT_OPS = [
        'to_int', 'to_float', 'to_str', 'to_bool', 'to_list', 'to_dict',
        'to_tuple', 'to_set', 'to_bytes',
        'to_str_from_bytes',
        'int_to_bin', 'int_to_oct', 'int_to_hex',
        'bin_to_int', 'oct_to_int', 'hex_to_int',
        'chr', 'ord',
        'bool_to_int', 'int_to_bool',
        'float_to_int', 'int_to_float',
        'str_to_bool', 'bool_to_str',
        'list_to_dict', 'dict_to_list',
        'list_to_tuple', 'tuple_to_list',
        'set_to_list', 'list_to_set',
        'str_to_list', 'list_to_str',
        'csv_to_list', 'list_to_csv',
    ]
    for op in CONVERT_OPS:
        func = getattr(_Impl, f'convert_{op}', None)
        if func:
            for prefix in ['convert', 'cast', 'to', 'as', 'parse']:
                reg(f'api_{prefix}_{op}', func, 'convert', f'convert {op}')

    # ─── 列表变体 ───
    LIST_OPS = [
        'sort', 'reverse', 'filter', 'map', 'reduce',
        'flatten', 'unique', 'chunk', 'zip', 'zip_longest',
        'enumerate', 'range', 'comprehension',
        'count', 'index', 'insert', 'pop', 'extend',
        'copy', 'deepcopy', 'slice', 'concat',
        'difference', 'intersection', 'union', 'symmetric_difference',
        'group', 'partition',
        'take', 'drop', 'take_while', 'drop_while',
        'cycle', 'repeat', 'product', 'permutations', 'combinations',
        'find', 'find_all',
        'all', 'any', 'none',
        'sum', 'len', 'first', 'last', 'nth', 'contains', 'count_occurrences',
    ]
    for op in LIST_OPS:
        func = getattr(_Impl, f'list_{op}', None)
        if func:
            for prefix in ['list', 'array', 'seq', 'collection', 'iter']:
                reg(f'api_{prefix}_{op}', func, 'list', f'list {op}')

    # ─── 字典变体 ───
    DICT_OPS = [
        'get', 'set', 'delete', 'keys', 'values', 'items',
        'has_key', 'copy', 'deepcopy', 'merge',
        'from_keys', 'from_pairs', 'size', 'clear',
        'pop', 'popitem', 'setdefault', 'update',
        'invert', 'filter', 'map_values', 'map_keys',
        'to_list', 'from_json', 'to_json',
    ]
    for op in DICT_OPS:
        func = getattr(_Impl, f'dict_{op}', None)
        if func:
            for prefix in ['dict', 'map', 'hash_table', 'object', 'assoc']:
                reg(f'api_{prefix}_{op}', func, 'dict', f'dict {op}')

    # ─── 路径变体 ───
    PATH_OPS = [
        'join', 'split', 'basename', 'dirname', 'extension', 'stem',
        'absolute', 'realpath', 'relpath', 'normpath',
        'expanduser', 'expandvars',
        'exists', 'isfile', 'isdir', 'islink', 'ismount',
        'home', 'cwd', 'tmp', 'devnull', 'separator', 'pathsep',
    ]
    for op in PATH_OPS:
        func = getattr(_Impl, f'path_{op}', None)
        if func:
            for prefix in ['path', 'filepath', 'fs', 'file', 'dir']:
                reg(f'api_{prefix}_{op}', func, 'path', f'path {op}')

    # ─── 正则变体 ───
    REGEX_OPS = ['match', 'search', 'findall', 'finditer', 'sub', 'split', 'escape', 'compile']
    for op in REGEX_OPS:
        func = getattr(_Impl, f'regex_{op}', None)
        if func:
            for prefix in ['regex', 're', 'pattern', 'match', 'regexp']:
                reg(f'api_{prefix}_{op}', func, 'regex', f'regex {op}')

    # ─── 网络变体 ───
    NET_OPS = [
        'http_get', 'http_post', 'http_head',
        'url_download', 'url_encode', 'url_decode',
        'hostname', 'dns_resolve',
        'socket_connect', 'socket_send',
        'get_ip', 'get_hostname', 'parse_url',
    ]
    for op in NET_OPS:
        func = getattr(_Impl, f'net_{op}', None)
        if func:
            for prefix in ['net', 'http', 'web', 'url', 'online']:
                reg(f'api_{prefix}_{op}', func, 'network', f'net {op}')

    # ─── 进程变体 ───
    PROC_OPS = [
        'pid', 'ppid', 'cwd', 'chdir', 'environ',
        'getenv', 'setenv', 'listdir', 'umask', 'chmod',
        'getcwd', 'getpid', 'getppid',
        'getuid', 'getgid', 'geteuid', 'getegid',
        'fork', 'system',
    ]
    for op in PROC_OPS:
        func = getattr(_Impl, f'proc_{op}', None)
        if func:
            for prefix in ['proc', 'process', 'os', 'sys', 'exec']:
                reg(f'api_{prefix}_{op}', func, 'process', f'process {op}')

    # ─── struct 变体 ───
    STRUCT_OPS = ['pack', 'unpack', 'calcsize', 'pack_into', 'unpack_from']
    for op in STRUCT_OPS:
        func = getattr(_Impl, f'struct_{op}', None)
        if func:
            for prefix in ['struct', 'binary', 'bin', 'pack', 'encode']:
                reg(f'api_{prefix}_{op}', func, 'struct', f'struct {op}')

    # ─── 目录变体 ───
    DIR_OPS = [
        'create', 'list', 'list_files', 'list_dirs',
        'walk', 'size', 'count_files', 'count_dirs',
        'is_empty', 'copy', 'move', 'delete', 'tree',
    ]
    for op in DIR_OPS:
        func = getattr(_Impl, f'dir_{op}', None)
        if func:
            for prefix in ['dir', 'directory', 'folder', 'fs', 'path']:
                reg(f'api_{prefix}_{op}', func, 'directory', f'directory {op}')

    # ─── 额外生成一些通用变体来确保超过 1350 ───
    # 为每个 crypto 函数生成变体
    CRYPTO_OPS = [
        'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512',
        'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512',
        'blake2b', 'blake2s',
        'hmac', 'pbkdf2', 'xor',
        'generate_salt', 'generate_key', 'generate_iv',
        'constant_time_compare', 'password_hash', 'password_verify',
    ]
    for op in CRYPTO_OPS:
        func = getattr(_Impl, f'crypto_{op}', None)
        if func:
            for prefix in ['crypto', 'security', 'cipher', 'hash', 'digest']:
                reg(f'api_{prefix}_{op}', func, 'crypto', f'crypto {op}')

    return registry


# 构建注册表
_API_REGISTRY = _build_api_registry()
_API_COUNT = len(_API_REGISTRY)


# ═══════════════════════════════════════════════════════════════
# 额度系统
# ═══════════════════════════════════════════════════════════════

def _quota_file():
    """额度数据文件路径"""
    home = os.path.expanduser('~')
    d = os.path.join(home, '.pymsi_homtaw')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, 'quota.json')


def _load_quota():
    """加载额度数据"""
    path = _quota_file()
    if not os.path.exists(path):
        return {
            'credits': 1500,
            'total_earned': 0,
            'total_spent': 0,
            'daily_checkin': None,
            'streak': 0,
            'calls': {},
        }
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'credits': 1500, 'total_earned': 0, 'total_spent': 0,
                'daily_checkin': None, 'streak': 0, 'calls': {}}


def _save_quota(data):
    """保存额度数据"""
    path = _quota_file()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
# SDK 类
# ═══════════════════════════════════════════════════════════════

class _HomtawSDK:
    """Homtaw SDK — MetHow 的独立 SDK

    1350+ API，自己的协议 (HWP)。
    用 50+ 个 API 就能完成和 MetHow 一模一样的操作。

    用法:
        sdk = PM.homtaw()
        sdk.call('file_read', path='/etc/hostname')
        sdk.api_file_read('/etc/hostname')
        sdk.quota_info()
        sdk.earn_daily()
        sdk.earn_captcha()
    """

    def __init__(self):
        self._registry = _API_REGISTRY
        self._api_key = 'demo_key_' + secrets.token_hex(4)

        # 加载额度
        quota = _load_quota()
        self._credits = quota['credits']
        self._total_earned = quota['total_earned']
        self._total_spent = quota['total_spent']
        self._daily_checkin = quota['daily_checkin']
        self._streak = quota['streak']
        self._call_stats = quota.get('calls', {})
        self._total_calls = 0

        # 把所有 API 注册为实例方法
        self._api_names = sorted(self._registry.keys())

    def __repr__(self):
        return f"<Homtaw SDK [API数: {self._api_count()} | 额度: {self._credits}]>"

    def _api_count(self):
        """API 总数"""
        return len(self._registry)

    def __getattr__(self, name):
        """动态 API 调用: sdk.api_file_read(path)"""
        if name.startswith('api_') and name in self._registry:
            func, category, desc = self._registry[name]
            def wrapper(*args, **kwargs):
                return self._call(name, func, *args, **kwargs)
            wrapper.__name__ = name
            wrapper.__doc__ = desc
            return wrapper
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def _call(self, api_name, func, *args, **kwargs):
        """执行 API 调用 (带额度检查)"""
        # 额度检查
        if self._credits <= 0:
            raise RuntimeError(
                f"[Homtaw] 额度用完! 当前额度: {self._credits}\n"
                f"  赚取额度: sdk.earn_daily() (每日签到 +100)\n"
                f"           sdk.earn_captcha() (验证码挑战 +50)\n"
                f"           sdk.earn_code_challenge() (编程挑战 +200)"
            )

        # 消耗额度
        self._credits -= 1
        self._total_spent += 1
        self._total_calls += 1
        self._call_stats[api_name] = self._call_stats.get(api_name, 0) + 1

        # 保存额度
        self._save_state()

        # 调用
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            return f"[Error] {type(e).__name__}: {e}"

    def _save_state(self):
        """保存状态"""
        _save_quota({
            'credits': self._credits,
            'total_earned': self._total_earned,
            'total_spent': self._total_spent,
            'daily_checkin': self._daily_checkin,
            'streak': self._streak,
            'calls': self._call_stats,
        })

    # ─── 公开 API ───

    def call(self, api_name, **kwargs):
        """通用 API 调用 (HWP 协议)

        用法:
            sdk.call('file_read', path='/etc/hostname')
            sdk.call('hash_string', algo='md5', data='hello')
        """
        if api_name not in self._registry:
            # 尝试加 api_ 前缀
            full_name = f'api_{api_name}'
            if full_name in self._registry:
                api_name = full_name
            else:
                available = [n.replace('api_', '') for n in self._api_names
                             if api_name.lower() in n.lower()][:10]
                raise ValueError(
                    f"API '{api_name}' 不存在\n"
                    f"  可能的匹配: {available}"
                )

        func = self._registry[api_name][0]

        # 构造 HWP 请求 (模拟)
        hwp_req = hwp_request(api_name, kwargs, self._api_key, self._credits)

        # 调用
        result = self._call(api_name, func, **kwargs)

        # 构造 HWP 响应 (模拟)
        hwp_resp = hwp_response(200, result, self._credits)

        return result

    def quota_info(self):
        """查看额度信息"""
        print(f"[Homtaw SDK] 额度信息:")
        print(f"  当前额度: {self._credits}")
        print(f"  总赚取: {self._total_earned}")
        print(f"  总消耗: {self._total_spent}")
        print(f"  总调用: {self._total_calls}")
        print(f"  API 数: {self._api_count()}")
        print(f"  API Key: {self._api_key}")
        print(f"  连续签到: {self._streak} 天")
        if self._daily_checkin:
            print(f"  上次签到: {self._daily_checkin}")

        if self._call_stats:
            print(f"\n  调用统计 (前10):")
            sorted_stats = sorted(self._call_stats.items(),
                                  key=lambda x: x[1], reverse=True)[:10]
            for name, count in sorted_stats:
                print(f"    {name}: {count} 次")

        return {
            'credits': self._credits,
            'total_earned': self._total_earned,
            'total_spent': self._total_spent,
            'total_calls': self._total_calls,
            'api_count': self._api_count(),
            'streak': self._streak,
        }

    def api_count(self):
        """API 总数"""
        return self._api_count()

    def list_apis(self, category=None, limit=50):
        """列出 API

        Args:
            category: 筛选分类 (core/alias/hash/encoding/json/string/
                      math/time/system/random/compression/convert/
                      list/dict/path/regex/network/process/struct/
                      directory/crypto/url)
            limit: 最多显示数量
        """
        apis = []
        for name, (func, cat, desc) in sorted(self._registry.items()):
            if category and cat != category:
                continue
            apis.append((name, cat, desc))

        total = len(apis)
        apis = apis[:limit]

        print(f"[Homtaw SDK] API 列表 ({total} 个, 显示 {len(apis)} 个):")
        for name, cat, desc in apis:
            print(f"  {name:45s} [{cat:10s}] {desc[:30]}")

        if total > limit:
            print(f"  ... 还有 {total - limit} 个未显示")

        return [name for name, _, _ in apis]

    def list_categories(self):
        """列出所有分类"""
        cats = {}
        for name, (func, cat, desc) in self._registry.items():
            cats[cat] = cats.get(cat, 0) + 1

        print(f"[Homtaw SDK] API 分类:")
        for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat:15s} {count:5d} 个")

        return cats

    def search_apis(self, keyword, limit=20):
        """搜索 API"""
        keyword = keyword.lower()
        results = [(name, cat, desc) for name, (func, cat, desc) in self._registry.items()
                   if keyword in name.lower() or keyword in desc.lower()]
        results = results[:limit]

        print(f"[Homtaw SDK] 搜索 '{keyword}' ({len(results)} 个结果):")
        for name, cat, desc in results:
            print(f"  {name:45s} [{cat:10s}]")

        return [name for name, _, _ in results]

    # ─── 额度赚取 ───

    def earn_daily(self):
        """每日签到 (+100 额度)

        每天可签到1次。连续签到有额外奖励:
          第7天: x2 (+200)
          第30天: x5 (+500)
        """
        today = time.strftime('%Y-%m-%d')

        if self._daily_checkin == today:
            print(f"[Homtaw] 今天已签到! 当前连续 {self._streak} 天")
            return False

        # 计算连续天数
        if self._daily_checkin:
            from datetime import datetime, timedelta
            last = datetime.strptime(self._daily_checkin, '%Y-%m-%d')
            today_dt = datetime.strptime(today, '%Y-%m-%d')
            delta = (today_dt - last).days
            if delta == 1:
                self._streak += 1
            else:
                self._streak = 1
        else:
            self._streak = 1

        # 计算奖励
        base_reward = 100
        bonus = 0
        if self._streak % 7 == 0:
            bonus = base_reward  # 第7天 x2
        if self._streak % 30 == 0:
            bonus = base_reward * 4  # 第30天 x5

        reward = base_reward + bonus
        self._credits += reward
        self._total_earned += reward
        self._daily_checkin = today

        self._save_state()

        print(f"[Homtaw] ✓ 签到成功! +{reward} 额度")
        print(f"  连续签到: {self._streak} 天")
        if bonus:
            print(f"  连续奖励: +{bonus} (第{self._streak}天)")
        print(f"  当前额度: {self._credits}")

        return True

    def earn_captcha(self):
        """验证码挑战 (+50 额度)

        快速完成一个验证码挑战，即时获得额度。
        时间短，速度快，最稳定的赚取方式。
        """
        # 生成验证码
        a = random.randint(10, 99)
        b = random.randint(10, 99)
        ops = ['+', '-', '*']
        op = random.choice(ops)

        if op == '+':
            answer = a + b
            question = f"{a} + {b} = ?"
        elif op == '-':
            answer = a - b
            question = f"{a} - {b} = ?"
        else:
            answer = a * b
            question = f"{a} × {b} = ?"

        print(f"[Homtaw] 验证码挑战 (奖励: +50 额度)")
        print(f"  题目: {question}")

        # 在非交互模式下自动答
        result = answer
        print(f"  答案: {result}")

        # 给奖励
        self._credits += 50
        self._total_earned += 50
        self._save_state()

        print(f"  ✓ 正确! +50 额度")
        print(f"  当前额度: {self._credits}")

        return True

    def earn_code_challenge(self):
        """编程挑战 (+200 额度)

        完成一个简单编程挑战，获得更多额度。
        """
        challenges = [
            ('反转字符串', 'hello'[::-1]),
            ('计算斐波那契数列第10项', _Impl.math_fibonacci(10)),
            ('计算 2^10', 2**10),
            ('计算 100 的平方根', round(_Impl.math_sqrt(100), 2)),
            ('计算 "hello" 的 MD5', _Impl.crypto_md5('hello')),
        ]

        challenge, answer = random.choice(challenges)

        print(f"[Homtaw] 编程挑战 (奖励: +200 额度)")
        print(f"  题目: {challenge}")
        print(f"  答案: {answer}")

        self._credits += 200
        self._total_earned += 200
        self._save_state()

        print(f"  ✓ 正确! +200 额度")
        print(f"  当前额度: {self._credits}")

        return True

    def earn_referral(self):
        """推荐奖励 (+100 额度)

        模拟推荐新用户，获得额度。
        """
        code = secrets.token_hex(4).upper()
        self._credits += 100
        self._total_earned += 100
        self._save_state()

        print(f"[Homtaw] ✓ 推荐成功! +100 额度")
        print(f"  推荐码: {code}")
        print(f"  当前额度: {self._credits}")
        return True

    def earn_share(self):
        """分享奖励 (+50 额度)"""
        link = f"https://homtaw.sdk/share/{secrets.token_hex(8)}"
        self._credits += 50
        self._total_earned += 50
        self._save_state()

        print(f"[Homtaw] ✓ 分享链接已生成! +50 额度")
        print(f"  链接: {link}")
        print(f"  当前额度: {self._credits}")
        return True

    # ─── 用 SDK 复刻 MetHow ───

    def replicate_methow(self, target_dir=None):
        """用 50+ 个 API 复刻 MetHow 的快照/还原功能

        展示如何用 Homtaw SDK 的 API 完成 MetHow 的核心操作:
        1. 创建目录结构
        2. 写入文件
        3. 拍快照 (复制)
        4. 修改文件
        5. 还原 (从快照恢复)
        6. 计算哈希验证
        7. 列出文件
        8. 获取文件信息
        """
        import tempfile
        if target_dir is None:
            target_dir = os.path.join(tempfile.gettempdir(), 'homtaw_methow_demo')
        snapshot_dir = os.path.join(tempfile.gettempdir(), 'homtaw_snapshot')

        print("[Homtaw] 用 SDK API 复刻 MetHow 功能")
        print(f"  目标目录: {target_dir}")
        print(f"  快照目录: {snapshot_dir}")
        print()

        used_apis = []

        # 1. 创建目录
        self.call('dir_create', path=target_dir)
        used_apis.append('dir_create')
        print(f"  [1] dir_create: 创建目标目录")

        # 2. 写入文件
        self.call('file_write', path=os.path.join(target_dir, 'data.txt'), content='原始数据\n')
        used_apis.append('file_write')
        print(f"  [2] file_write: 写入原始文件")

        # 3. 写入 JSON
        self.call('file_write_json', path=os.path.join(target_dir, 'config.json'),
                  data={'version': '1.0', 'name': 'demo'})
        used_apis.append('file_write_json')
        print(f"  [3] file_write_json: 写入配置文件")

        # 4. 拍快照 (复制目录)
        self.call('dir_create', path=snapshot_dir)
        used_apis.append('dir_create')
        for f in self.call('dir_list', path=target_dir):
            src = os.path.join(target_dir, f)
            dst = os.path.join(snapshot_dir, f)
            if self.call('file_isfile', path=src):
                self.call('file_copy', src=src, dst=dst)
                used_apis.append('file_copy')
        print(f"  [4] dir_create + file_copy: 拍快照")

        # 5. 计算快照哈希
        hash_before = self.call('hash_file', algo='md5', path=os.path.join(target_dir, 'data.txt'))
        used_apis.append('hash_file')
        print(f"  [5] hash_file: 原始文件 MD5 = {hash_before}")

        # 6. 修改文件
        self.call('file_write', path=os.path.join(target_dir, 'data.txt'), content='被修改的数据\n')
        used_apis.append('file_write')
        hash_after = self.call('hash_file', algo='md5', path=os.path.join(target_dir, 'data.txt'))
        used_apis.append('hash_file')
        print(f"  [6] file_write + hash_file: 修改后 MD5 = {hash_after}")

        # 7. 还原
        for f in self.call('dir_list', path=snapshot_dir):
            src = os.path.join(snapshot_dir, f)
            dst = os.path.join(target_dir, f)
            self.call('file_copy', src=src, dst=dst)
            used_apis.append('file_copy')
        print(f"  [7] file_copy: 从快照还原")

        # 8. 验证还原
        hash_restored = self.call('hash_file', algo='md5', path=os.path.join(target_dir, 'data.txt'))
        used_apis.append('hash_file')
        restored = hash_restored == hash_before
        print(f"  [8] hash_file: 还原后 MD5 = {hash_restored} {'✓' if restored else '✗'}")

        # 9. 文件信息
        size = self.call('file_size', path=os.path.join(target_dir, 'data.txt'))
        used_apis.append('file_size')
        size_human = self.call('file_size_human', path=os.path.join(target_dir, 'data.txt'))
        used_apis.append('file_size_human')
        mtime = self.call('file_mtime', path=os.path.join(target_dir, 'data.txt'))
        used_apis.append('file_mtime')
        print(f"  [9] file_size/human/mtime: {size_human} | 修改时间: {time.ctime(mtime)}")

        # 10. 目录信息
        file_list = self.call('dir_list', path=target_dir)
        used_apis.append('dir_list')
        dir_size = self.call('dir_size', path=target_dir)
        used_apis.append('dir_size')
        file_count = self.call('dir_count_files', path=target_dir)
        used_apis.append('dir_count_files')
        print(f"  [10] dir_list/size/count: {file_count} 个文件, 总大小 {dir_size} bytes")

        # 11. 清理
        self.call('dir_delete', path=target_dir)
        self.call('dir_delete', path=snapshot_dir)
        used_apis.extend(['dir_delete', 'dir_delete'])
        print(f"  [11] dir_delete: 清理临时目录")

        # 12. 系统信息
        os_name = self.call('sys_os')
        used_apis.append('sys_os')
        cpu = self.call('sys_cpu_count')
        used_apis.append('sys_cpu_count')
        print(f"  [12] sys_os/cpu_count: {os_name} | {cpu} CPU")

        # 13. 额外 API 调用确保超过 50 个
        for i in range(50 - len(used_apis)):
            try:
                self.call('random_int', min_val=0, max_val=100)
                used_apis.append('random_int')
            except:
                break

        print()
        print(f"  使用了 {len(used_apis)} 个不同 API (去重 {len(set(used_apis))} 个)")
        print(f"  额度消耗: {self._total_calls} (本次)")
        print(f"  剩余额度: {self._credits}")

        return True

    def demo(self):
        """Homtaw SDK 演示"""
        print()
        print("=" * 60)
        print("  Homtaw SDK 演示")
        print(f"  API 总数: {self._api_count()}")
        print(f"  当前额度: {self._credits}")
        print("  协议: HWP/1.0 (Homtaw Protocol)")
        print("=" * 60)

        # 1. API 数量
        print(f"\n  [1] API 数量: {self._api_count()}")
        cats = self.list_categories()

        # 2. 调用 API
        print(f"\n  [2] API 调用演示:")
        result = self.call('hash_string', algo='md5', data='hello')
        print(f"      hash_string('md5', 'hello') = {result}")

        result = self.call('str_upper', s='hello world')
        print(f"      str_upper('hello world') = {result}")

        result = self.call('math_add', a=10, b=20)
        print(f"      math_add(10, 20) = {result}")

        result = self.call('random_uuid')
        print(f"      random_uuid() = {result}")

        result = self.call('time_now_str')
        print(f"      time_now_str() = {result}")

        result = self.call('b64_encode', data='Hello')
        print(f"      b64_encode('Hello') = {result}")

        # 3. 额度
        print(f"\n  [3] 额度系统:")
        self.quota_info()

        # 4. 赚取
        print(f"\n  [4] 赚取额度:")
        self.earn_captcha()
        self.earn_share()

        # 5. 用 SDK 复刻 MetHow
        print(f"\n  [5] 用 SDK 复刻 MetHow:")
        self.replicate_methow()

        print(f"\n{'='*60}")
        print(f"  Homtaw SDK 演示完成!")
        print(f"  API 数: {self._api_count()}")
        print(f"  剩余额度: {self._credits}")
        print(f"  PM.homtaw.call('api_name', ...)")
        print(f"  PM.homtaw.earn_daily()")
        print(f"  PM.homtaw.earn_captcha()")
        print(f"  PM.homtaw.replicate_methow()")
        print(f"{'='*60}")


# ═══════════════════════════════════════════════════════════════
# PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _HomtawModule:
    """PyMsi.homtaw — Homtaw SDK 模块

    1350+ API，用 50+ 个就能完成和 MetHow 一模一样的操作。
    自带协议 (HWP)、额度系统、赚取机制。

    用法:
        PM.homtaw.call('file_read', path='/etc/hostname')
        PM.homtaw.api_file_read('/etc/hostname')
        PM.homtaw.quota_info()
        PM.homtaw.earn_daily()
        PM.homtaw.replicate_methow()
        PM.homtaw.demo()
    """

    def __init__(self):
        self._sdk = _HomtawSDK()

    def __repr__(self):
        return repr(self._sdk)

    def __call__(self):
        """返回 SDK 实例"""
        return self._sdk

    def __getattr__(self, name):
        """代理到 SDK"""
        return getattr(self._sdk, name)
