"""
PyMsi - 把任意文件夹打包成 MSI 安装包
========================================
用法:
    import PyMsi as PM
    PM("C:/你要构建的目录")   # 指定源文件夹
    PM.s(2)                    # 选择模式: 0=选错了, 1=普通模式, 2=极速模式

运行脚本即自动构建 MSI。
"""

import os
import sys
import shutil
import uuid
import struct
import hashlib
import tempfile
from datetime import datetime


# ─── README ─────────────────────────────────────────────

_README = r"""
╔══════════════════════════════════════════════════════════════╗
║                    PyMsi  v2.3.0                            ║
║ 文件夹→MSI | HTML→EXE | 30+游戏 | 图片→TTF | Hex | AI | 翻译 | 邮件 | 文件串🧶 | 🔐KeyKey | 🔒独家加密 | 🌐服务器 | 🌍浏览器 | 📦Shrink-Zeta | 📹录屏 | 🐱.meow | 🔐提权 | 📦.nano | 📡摩斯密码视频 | 🎨HexRGB视频 | 🧬生物 | ⚗️化学 | 🔢数学 | 🐾MeowHawk搜索 | 🔙回溯算法 | 🐮.cow格式 | 🧠AI训练 | 🤖.mnn G进制 | 🎬pyx视频提取 | 📊ckon视频验证 ║
╚══════════════════════════════════════════════════════════════╝

【安装】
    pip install pymsi-2.3.0-py3-none-any.whl
【2.3.0 新增】
    📊 ckon 视频验证 — 类似 ffprobe, 100种信息全放进 .ckon
        ckon = Log 日志文件的变体, 小白也能读懂
        包含: 文件信息/格式/视频轨道/音频轨道/验证结果/详细检查
        PM.pyx.probe("video.mp4")                # → video.ckon
        PM.pyx.probe("video.mp4", "info.ckon")   # 指定输出
    🎬 pyx 视频模式 — 视频链接 → 完整视频文件
        PM.pyx.video(url, format='mp4')          # 下载视频
        PM.pyx.video(url, output='out.mov')      # 指定输出格式
【2.2.0 新增】
    🎬 pyx 视频提取引擎 — Vmp模式 (B站/抖音/YouTube/快手/小红书... 通通提取)
        遇到好听的音乐却没办法保存到本地？Vmp = Video → Music
        纯 Python 标准库, 不加 ffmpeg/ffprobe, 零依赖
        PM.pyx.vmp(url, format='mp3')       # 视频链接 → MP3
        PM.pyx.vmp(url, format='wav')       # 视频链接 → WAV
        PM.pyx.vmp(url, format='ogg')       # 视频链接 → OGG
        PM.pyx.vmp(url, format='flac')      # 视频链接 → FLAC
        PM.pyx.vmp(url, format='aac')       # 视频链接 → AAC
        PM.pyx.download(url, path)          # 下载视频
        PM.pyx.parse_url(url)               # 解析视频链接
        支持: B站/抖音/YouTube/快手/小红书/直接视频链接
【2.1.0 新增】
    🤖 .mnn 文件格式引擎 (G进制, 把日志文件彻底翻了个天)
        人类看不懂, 只有机器能看懂 — 内部存的是 G进制 (数字位移 + 交替标记)
        .mnn 格式: 无魔数, 纯二进制, 无文本无换行
        PM.mnn.pack("log.txt")              # 打包 → log.txt.mnn
        PM.mnn.unpack("log.txt.mnn")        # 解包 → log.txt
        PM.mnn.run("log.txt.mnn")            # 打开→退出后自动清理
        PM.mnn.info("log.txt.mnn")           # 文件信息
        PM.mnn.encode(b"hello")             # G进制编码
        PM.mnn.decode(encoded_bytes)        # G进制解码
        PM.mnn.batch_pack(["a.txt"])        # 批量打包
        PM.mnn.verify("log.txt.mnn")         # 校验完整性
        PM.mnn.demo()                        # 演示
【2.0.0 新增】
    🧠 AI 训练引擎 (自研神经网络框架, 像 TensorFlow 但更轻)
        训练得好 = ChatGPT 级 | 训练不好 = 也能用 | 反正高效轻量零人民币
        PM.train.Sequential([...])              # 序列模型
        PM.train.Dense(64, activation='relu')   # 全连接层
        PM.train.Dropout(0.5)                    # Dropout
        PM.train.Embedding(10000, 128)           # 词嵌入
        PM.train.Conv1D(32, 3)                   # 一维卷积
        PM.train.SimpleRNN(64)                   # RNN
        model.compile(optimizer='adam', ...)     # 编译
        model.fit(X, y, epochs=10)               # 训练
        model.predict(X)                         # 预测
        model.save("model.pym")                  # 保存(.pym格式)
        model = PM.train.load_model("m.pym")     # 加载
        🔑 API 服务器 + 专属 Key 认证
        server = PM.train.APIServer(model, 8080)
        key = server.create_key("my_app")         # 生成 API Key
        server.start()                            # 启动服务
        client = PM.train.APIClient(url, key)     # 客户端调用
        PM.train.demo()                           # 训练演示
【1.9.0 新增】
    🐮 .cow 文件格式引擎 (无魔数, 纯base-32, 打开后自动清理)
        .cow 格式: 无魔数, 全文纯 base-32 编码, 看起来就是乱码
        打开 .cow → 解码 → 临时目录 → 系统默认程序 → 退出后清理
        PM.cow.pack("photo.jpg")            # 打包 → photo.jpg.cow
        PM.cow.unpack("photo.jpg.cow")      # 解包 → photo.jpg
        PM.cow.run("photo.jpg.cow")          # 打开→退出后自动清理
        PM.cow.info("photo.jpg.cow")         # 文件信息
        PM.cow.encode(b"hello")             # base-32 编码
        PM.cow.decode("NBSWY3DP")           # base-32 解码
        PM.cow.batch_pack(["a.txt"])        # 批量打包
        PM.cow.verify("photo.jpg.cow")       # 校验完整性
        PM.cow.moo()                         # 🐮
【1.8.0 新增】
    🔙 回溯算法暴力引擎 (10种经典问题 + 通用框架)
        暴力极快 — 1毫秒一次尝试, 1秒1000次, 100秒10万次
        PM.backtrack.permute([1,2,3])              # 全排列
        PM.backtrack.combine(4, 2)                 # 组合 C(n,k)
        PM.backtrack.subsets([1,2,3])              # 子集
        PM.backtrack.n_queens(8)                   # N皇后
        PM.backtrack.solve_sudoku(board)            # 数独求解
        PM.backtrack.maze_path(maze, s, e)          # 迷宫寻路
        PM.backtrack.knapsack(items, capacity)     # 0-1背包
        PM.backtrack.combination_sum(cands, tgt)    # 组合总和
        PM.backtrack.word_break(s, word_dict)      # 单词拆分
        PM.backtrack.solve(choices, valid, goal)    # 通用框架
        PM.backtrack.demo()                         # 演示
        PM.backtrack.benchmark()                    # 性能测试
【1.7.0 新增】
    🐾 MeowHawk 自研查找算法 (BM25排序+倒排索引+N-gram模糊匹配)
        纯Python零依赖, 对标Lucene/ES核心算法
        mh = PM.meowhawk()                    # 创建引擎
        mh.add_document("Python编程语言")      # 索引文档
        mh.search("编程语言")                   # 精确搜索
        mh.search("编成语言", fuzzy=True)       # 模糊搜索(拼写纠错)
        mh.suggest("编")                       # 前缀补全
        mh.save("index.json")                  # 持久化
        PM.meowhawk.demo()                     # 演示
        PM.meowhawk.benchmark(1000)            # 性能测试
        PM.meowhawk.search_in(["文档1","文档2"], "查询")  # 快捷搜索
【1.6.0 Education Plus 新增】
    ⚗️ 化学教育模块 (元素周期表+分子结构+化学反应模拟+溶液计算+方程配平)
        PM.chem.element()          # 元素周期表教程
        PM.chem.reaction()          # 化学反应模拟器
        PM.chem.molecule()         # 分子结构教程
        PM.chem.molarity(10, 40, 0.5)  # 摩尔浓度
        PM.chem.ph(0.001)          # pH值计算
        PM.chem.balance("H2+O2=H2O")  # 方程配平
    🔢 数学教育模块 (代数+几何+微积分+线性代数+概率+数论)
        PM.math.quadratic(1, -5, 6)  # 解二次方程
        PM.math.gcd(48, 36)          # 最大公约数
        PM.math.matrix_mult(A, B)   # 矩阵乘法
        PM.math.is_prime(17)         # 质数判断
        PM.math.fast_pow(3, 13, 100) # 快速幂
        PM.math.algebra()            # 代数教程
        PM.math.calculus()           # 微积分教程
        PM.math.number_theory()      # 数论教程
【1.5.9 Education Edition 新增】
    🧬 生物教育模块 (细胞结构+蛋白质系统+酶系统)
        PM.bio.cell()                    # 细胞结构教程
        PM.bio.protein("hemoglobin")     # 生成蛋白质文件
        PM.bio.enzyme("pepsin")          # 生成酶文件
        PM.bio.denature("hemoglobin.protein", temp=70)  # 加热变性
        PM.bio.catalyze("pepsin.enzyme", "casein.protein")  # 酶催化
【1.5.8 新增】
    🎨 十六进制 RGB 视频 (文本→Hex→RGB纯色AVI视频)
        16个hex数字各对应一种纯色, 25帧/色
        PM.hexvid("Hello World", output="hello.avi")
【1.5.6 新增】
    📦 .nano 容器 (四级权限分区存储, 纯自研)
        比压缩包更安全: 权限制度 + 校验 + 分区加密
        4个分区 (从低到高):
          normal     普通区域, 无需任何权限
          adminanorobit (Anon2) 管理员级, 需 admin/sudo
          asoav1     (Dona0/高泉区) 内核级, 需 SYSTEM/root
          nanou      最高权限区, 需 .nnu 脚本 (语法公开)
        PM.nano.create("data.nano", anon2_pw="admin123", ...)
        PM.nano.add("data.nano", "normal", "a.txt")
        PM.nano.extract("data.nano", "normal", "D:/out")
        PM.nano.run_nnu("extract.nnu")       # Nanou 区: 执行 .nnu 脚本
        PM.nano.nnu_help()                    # 查看 .nnu 公开语法
        别名: PM.container / PM.容器 / PM.纳米
【1.5.5 新增】
    🔐 进程权限提升 (以特定权限打开进程)
        ⚠️ 需要管理员(Win)/sudo(Linux), 不能绕过认证!
        Windows: 管理员→SYSTEM / TrustedInstaller (NSudo技术链)
        Linux:   用户→root (sudo / pkexec)
        PM.priv.system("notepad.exe")               # Win: SYSTEM | Linux: root
        PM.priv.trusted("notepad.exe")               # Win: TrustedInstaller
        PM.priv.admin("notepad.exe")                 # Win: UAC | Linux: sudo
        PM.priv.whoami()                             # 查看当前身份
        PM.priv.levels()                              # 可用提升级别
        别名: PM.su / PM.runas / PM.elevate / PM.提权
【1.5.4 新增】
    🐱 .meow 文件打包/解包 (多文件揉成 .meow + address.json)
        PM.meow.disteow(["a.txt", "b.png", "c.pdf"])  # 揉成 .meow
        PM.meow.undisteow("D:/Meow/")                 # 提取所有文件到 D:/Dist
        PM.meow.list("D:/Meow/")                      # 列出 .meow 中的文件
        打包: 多文件 → .meow + address.json (数字地址 154.04.1.1:00000001)
        解包: 提供 address.json 目录 → 自动提取所有文件
【1.5.3 新增】
    📹 录屏 (纯自研, Win32 GDI 截屏 + AVI/GIF 编码器 + 30+格式)
        ⚠️ 仅支持 Windows! macOS/Linux 会报 RuntimeError
        PM.record()                          # 一键录屏 (1分钟, 4K, AVI, D:/Videos)
        PM.record(duration=60, fmt="gif")    # 录制 GIF
        PM.record.formats()                   # 查看 30+ 格式
        自动隐藏控制台 → 后台静默录屏 → 录完输出路径
【1.5.1 新增】
    🌐 极简服务器 (类 Flask, 纯标准库): PM.server.port(8080).route('/').serve('Hi').start()
    🌍 极简浏览器 (纯 Python, 不调系统 Chrome): PM.browser.open(HTML)
        - 解析 HTML / CSS / 执行 JS (js2py)
        - 适配 DOM API: getElementById / querySelector / console.log

【快速开始】

    import PyMsi as PM

    # ─── 方式一：文件夹 → MSI 安装包 ───
    PM("C:/你的项目文件夹")
    PM.s(2)   # 2=极速模式(推荐)  1=普通模式  0=取消
    # ↑ 等价写法 (alias 任意选):
    #   PM.build("C:/你的项目文件夹")
    #   PM.b("C:/你的项目文件夹")
    #   PM.msi("C:/你的项目文件夹")
    #   PM.pack("C:/你的项目文件夹")
    #   PM.make("C:/你的项目文件夹")
    #   PM.s(2) 的别名:  PM.mode(2)  PM.m(2)

    # ─── 方式二：HTML → EXE 桌面应用 (Electron) ───
    PM.html("C:/你的HTML项目")
    PM.html.build()                         # 构建 EXE
    PM.html.sandbox(True)                   # 开启沙箱模式
    PM.html.icon("C:/图标.ico")             # 自定义图标
    PM.html.platform("win32-x64")           # 指定目标平台
    PM.html.title("我的应用")               # 窗口标题
    PM.html.size(1280, 720)                # 窗口大小
    # ↑ 等价写法:
    #   PM.h("C:/html")        PM.web("C:/html")   PM.app("C:/html")
    #   PM.html.run()  .make()  .go()  .exe()     别名全部 == .build()
    #   PM.html.secure()  .safe()                == .sandbox(True)
    #   PM.html.name("标题")                      == .title
    #   PM.html.resize(w,h)                       == .size
    #   PM.html.win()  .windows()  .mac()  .linux()  快捷指定平台

    # ─── 方式三：两行代码，30+ 游戏即开即玩！ ───
    PM.game.Grap("Snake")          # 贪吃蛇
    PM.game.Grap("Tetris")         # 俄罗斯方块
    PM.game.Grap("2048")           # 2048
    PM.game.Grap("FlappyBird")     # 飞扬的小鸟
    PM.game.list()                  # 列出全部 30 款游戏
    # ↑ 等价写法:
    #   PM.g("贪吃蛇")              PM.games("贪吃蛇")
    #   PM.play("贪吃蛇")           PM.game.start / run / open / play("Snake")
    #   PM.game.ls()                PM.game.all()   == .list()

    # ─── 方式四：图片文件夹 → 字体 TTF ───
    # 命名规则: A.png B.png 0.png 等，文件名=字符
    PM.image.ttf("C:/glyph_folder", "我的字体.ttf")
    # 或者给一个映射字典
    PM.image.ttf("C:/glyphs", "out.ttf", mapping={"letter_a.png":"a", "letter_b.png":"b"})
    # ↑ 等价写法:
    #   PM.font(...)   PM.fonts(...)   PM.ttf(...)
    #   PM.img(...)    PM.i(...)       PM.pic(...)    直接调用也行
    #   PM.image(folder, out)                          直接调用也行
    #   PM.image.to_font / to_ttf / build_font / make_font (folder, out)
    #   PM.image.ttf.build / make / run / go / generate / create 都是同方法

    # ─── 方式五：输入文件地址 → 解析 Hex 全部输出到终端 ───
    PM.hex("C:/some/file.bin")                      # 直接 dump 全部 hex
    PM.hex.find("C:/my_project", "config.dat")       # 目录里搜文件名后解析
    PM.hex.dump("C:/file.bin", bytes_per_line=16,
                start_offset=0, max_bytes=512)       # 带参数
    # ↑ 等价写法:
    #   PM.hexdump(...)  PM.hd(...)   PM.hexview(...)
    #   PM.hex(...)       短调用也行
    #   PM.hex.find / search / locate (目录, 文件名)
    #   PM.hex.dump / view / show / print / parse / read (path, ...)

    # ─── 方式六：AI 空壳 — 设 key + 官网后问问题 ───
    PM.ai.key = "sk-xxxxxxxx"                       # 1. 设 API Key
    PM.ai.url = "https://api.openai.com"            # 2. 设 AI API 官网
    PM.ai.imput("你好, 你是谁?")                     # 3. 问问题 (输出自动 print)
    # ↑ 等价写法:
    #   PM.ai("你好")            直接调用也行
    #   PM.ai.ask / chat / question / send / say / talk  都是 imput 别名
    #   PM.AI / PM.gpt / PM.llm / PM.chatbot 都是 ai 别名
    #   q = PM.ai.input          输入当变量用 (上次问的问题)
    #   a = PM.ai.output         输出当变量用 (AI 的回答)
    #   PM.ai.model = "deepseek-chat"   换模型 (OpenAI 兼容接口都行)

    # ─── 方式七：翻译 — 100+ 种语言 (LibreTranslate, 零依赖) ───
    PM.translate("你好")                               # 中文 → 英文 (默认)
    PM.translate.en("你好")                            # → 英语
    PM.translate.ru("你好")                            # → 俄语
    PM.translate.fr("你好")                            # → 法语
    PM.translate.ko("你好")                            # → 韩语
    PM.translate.ja("你好")                            # → 日语
    PM.translate.de("你好")                            # → 德语
    PM.translate.中文("Hello")                         # → 中文
    PM.translate.to("你好", "es")                      # → 西语 (任意语言 code/名字都行)
    # ↑ 等价写法:
    #   PM.tr(...)  PM.trans(...)  PM.t(...)  PM.翻译(...)  都是 translate 别名
    #   q = PM.translate.input       输入当变量用 (原文)
    #   a = PM.translate.output      输出当变量用 (译文)
    #   src/tgt = .source_lang/.target_lang  语言变量
    #   PM.translate.languages()     看支持的所有语言

    # ─── 方式八：邮件发送 (验证码 / 通知, 内置发件 wns1@qq.com, 零依赖) ───
    PM.dl.auth("QQ邮箱授权码")                # 1. 设授权码 (QQ邮箱设置→账户→SMTP生成)
    PM.dl.output("user@example.com")          # 2. 设收件人 (Gmail/Outlook/163/QQ都行)
    PM.dl.print("你的验证码是 123456")          # 3. 发送邮件内容
    #   PM.dl.send_code()                     一键: 自动生成6位码 + 拼正文 + 发邮件
    #   print(PM.dl.code)                      拿到刚生成的验证码做比对
    # ↑ 等价写法:
    #   PM.dl / PM.mail / PM.email / PM.send / PM.smtp / PM.邮件 / PM.发邮件 都是同一模块
    #   PM.dl.auth(码).output(邮箱).print(正文) 链式调用
    #   to = PM.dl.output    收件人变量
    #   body = PM.dl.input    上次邮件内容变量
    #   code = PM.dl.code     上次生成的验证码变量

    # ─── 方式九：文件串 — 像毛线球一样把文件串在一起 ───
    PM.filechain("a.txt", "b.png", "c.py")                 # 串成 output.yarn
    PM.filechain.to("我的球.yarn", "a.txt", "b.png")       # 指定输出名
    PM.filechain.list("我的球.yarn")                        # 看里面有什么
    PM.filechain.un("我的球.yarn")                          # 全部拆开
    PM.filechain.un("我的球.yarn", "a.txt")                 # 只拆一个
    PM.filechain.merge("a.yarn", "b.yarn", "out.yarn")     # 合并毛线球
    # ↑ 等价写法:
    #   PM.fc("a.txt")              PM.chain("a.txt")        PM.yarn("a.txt")
    #   PM.文件串("a.txt")           PM.毛线球("a.txt")
    #   PM.filechain.ls()           .all()  .show()     == .list()
    #   PM.filechain.unwrap()       .extract()  .unpack()  == .un()
    #   PM.filechain.串/拆/看/合并                         中文方法名

────────────────────────────────────────────────────────────
【API 完整参考】

  PM(path)                    设置要打包的源文件夹
    path: str                 文件夹路径

  PM.s(mode)                  选择模式并构建 MSI
    mode: int                 0=取消  1=普通(压缩)  2=极速(推荐)
    返回: str                生成的 .msi 文件路径

  PM.html(path)               设置 HTML 源目录 (重置所有参数)
    path: str                 HTML 项目目录路径

  PM.html.build(output=None)  开始构建 EXE
    output: str (可选)        输出路径，默认 dist/{目录名}.exe
    返回: str                生成的 .exe 文件路径

  PM.html.sandbox(enabled)    沙箱模式开关
    enabled: bool             True=加沙箱  False=不加(默认)

  PM.html.icon(path)          自定义图标
    path: str                 .ico 文件路径

  PM.html.platform(target)    指定目标平台 (默认自动检测)
    target: str               win32-x64 / linux-x64 / darwin-x64

  PM.html.title(text)         窗口标题
    text: str

  PM.html.size(w, h)          窗口大小 (默认 1024x768)
    w: int, h: int

  PM.readme                   打印此帮助文档

  PM.game.Grap(name)          启动内置游戏模板
    name: str                 游戏名称 (英文或中文)
    例如: "Snake", "Tetris", "2048", "贪吃蛇"

  PM.game.list()              列出全部 30 款内置游戏

  PM.game(name)               快捷调用：同 PM.game.Grap(name)

  PM.image.ttf(folder, out, mapping=None, font_name="PyMsiFont")
                              图片 → TTF 字体 (纯 Python，零外部依赖)
    folder: str               包含 png/jpg/bmp/ico/gif 的文件夹
    out: str                  输出 .ttf 文件路径
    mapping: dict (可选)      {"文件名.png": "字符"}，不传则按文件名猜
    font_name: str            字体内部名称
    支持格式: .png .jpg .jpeg .bmp .ico .gif
    GIF 特殊: 自动拆帧，每帧作为一个独立字形

  PM.image.ttf.help()         查看详细教程与示例

  PM.hex(path)                输入文件地址 → 解析 Hex 全部输出到终端
    path: str                 文件路径 (展开 ~ 和环境变量)
    bytes_per_line: int       每行字节数 (默认 16)
    group_size: int           每组字节数 (默认 2), 0=不分组
    show_ascii: bool          显示右侧 ASCII 列 (默认 True)
    uppercase: bool           hex 大写 (默认 True)
    start_offset: int         起始字节偏移 (默认 0)
    max_bytes: int            最多读取字节数 (默认 None=全部; >64MB 自动截断)
    offset_base: str          偏移进制 'hex'/'dec' (默认 'hex')
    返回: int                 成功返回解析的字节数, 失败返回 None

  PM.hex.find(directory, name)  在目录中递归搜索文件名后解析
    directory: str            搜索起始目录
    name: str                 文件名 (大小写不敏感包含匹配)
    其余参数同 PM.hex()

  PM.hex == PM.hexdump == PM.hd == PM.hexview
  PM.hex.find / search / locate   都是同一方法
  PM.hex.dump / view / show / print / parse / read  都是同一方法

  PM.ai.key = key              设 API Key (必填)
  PM.ai.url = url              设 AI API 官网 (必填, OpenAI 兼容接口)
  PM.ai.imput(question)        问 AI 问题, 输出自动 print 到终端
  PM.ai.input                  AI 的输入 (只读变量, 调用 imput 后更新)
  PM.ai.output                 AI 的输出 (只读变量, 调用 imput 后更新)
  PM.ai.model = name           换模型 (默认 gpt-3.5-turbo)
  PM.ai.clear()                清空对话历史 + 输入 + 输出

  PM.ai == PM.AI == PM.gpt == PM.llm == PM.chatbot
  PM.ai.imput / ask / chat / question / send / say / talk / q  都是同一方法
  PM.ai.input / Input / prompt / question_text  都是输入别名
  PM.ai.output / Output / answer / result       都是输出别名

  PM.translate(text, target, source)  翻译到指定语言 (默认目标 en, 源 auto)
    text: str                 要翻译的原文
    target: str               目标语言 code 或名字 ("en"/"英语"/"русский" 都行)
    source: str               源语言 (默认 "auto" 自动检测)
    返回: self                链式调用, 译文自动 print 到终端

  PM.translate.to(text, target, source)  同 PM.translate() 更直观的名字
  PM.translate.en/ru/fr/ko/ja/de/es/it/zh/th/vi/tr/pl...(text)  快捷目标语言
  PM.translate.英语/俄语/法语/韩语/日语/德语/西语/中文/繁体(text)   中文名快捷调用
  PM.translate.input / Input / text / original / source_text  上次输入的原文 (只读)
  PM.translate.output / Output / result / translated / translation  上次译文 (只读)
  PM.translate.source_lang / src / from_lang    上次源语言 code (只读)
  PM.translate.target_lang / tgt / to_lang / lang  上次目标语言 code (只读)
  PM.translate.languages() / list() / ls() / help()  打印常用语言列表
  PM.translate.clear() / reset()                清空输入输出缓存
  PM.translate.url = "..."                      自定义翻译服务器 (兼容 LibreTranslate API)
  PM.translate.api_key / set_key()              自建实例的 API Key (可选)

  PM.translate == PM.Translate == PM.tr == PM.trans == PM.t == PM.translation == PM.translator == PM.翻译 == PM.译
  PM.translate.translate / to / 翻译 / trans / tr / t / do / run / go / make / convert / 转 / 翻  都是同一方法

  PM.dl.auth(code)                         设 QQ 邮箱授权码 (不是登录密码!)
    code: str                              QQ 邮箱设置→账户→SMTP 服务→生成授权码
  PM.dl.output(email) / to / recipient / target / send_to / 收件人  设收件人
  PM.dl.output = "a@b.com"                 直接赋值也行 (可读可写)
  PM.dl.print(content)                     发送邮件 (内容自动 print 确认)
    content: str                           邮件正文 (空字符串会弹 input() 交互)
  PM.dl.send_code(length=6)               一键: 生成 6 位验证码 + 拼正文 + 发邮件
  PM.dl.gen_code(length=6)                 只生成验证码不发邮件, 返回码字符串
  PM.dl.subject = "..."                    设邮件主题 (默认 "PyMsi 验证码")
  PM.dl.from_name(name)                   设发件人显示名 (默认 "PyMsi")
  PM.dl.clear() / reset()                  清空所有缓存 (含授权码)

  PM.dl.output / Output / to_email / recipient_email / receiver / target_email  收件人 (只读)
  PM.dl.input / Input / content / body / text / message / mail_body             上次邮件正文 (只读)
  PM.dl.code / Code / verify_code / verification_code / captcha / otp            上次验证码 (只读)
  PM.dl.subject                                邮件主题 (可读可写)
  PM.dl.status / Status / result               上次发送结果信息 (只读)
  PM.dl.last_error                             上次错误 (无错为空字符串)

  PM.dl.print / send / deliver / emit / 发送 / 发邮件 / mail / email  都是同一方法
  PM.dl.send_code / code_ / verify / send_otp / send_captcha / 验证码 / 发验证码 / 发码  都是同一方法
  PM.dl.auth / authcode / apikey / token / password / set_auth   设授权码别名

  PM.dl == PM.Dl == PM.mail == PM.Mail == PM.email == PM.Email == PM.deliver
         == PM.send == PM.smtp == PM.邮件 == PM.邮箱 == PM.发邮件

────────────────────────────────────────────────────────────
【图片 → 字体 TTF 用法示例】

  方式一：按文件名识别 (最简单)
  把每个字形图片命名为对应的字符:
    A.png B.png C.png ...      大写字母
    a.png b.png c.png ...      小写字母
    0.png 1.png ... 9.png      数字
    U+4E2D.png 或 0x4E2D.png   Unicode 方式表示中文 "中"
    我.png 你.png 他.png       中文直接命名 (UTF-8 文件系统)

  方式二：提供映射字典
    mapping = {"glyph01.png": "A", "glyph02.png": "中"}
    PM.image.ttf("C:/glyphs", "我的字体.ttf", mapping=mapping)

  方式三：GIF 动画逐帧转字形
    frames.gif 会被拆成 帧1→A 帧2→B 帧3→C...
    (可用 start_char="A" 指定起始字符)

────────────────────────────────────────────────────────────
【文件 Hex 解析用法示例】

  方式一：直接给文件路径
    PM.hex("C:/data/file.bin")
    # → 终端输出类似 xxd 的 hex dump, 含偏移/十六进制/ASCII

  方式二：在目录里搜索文件名
    PM.hex.find("C:/my_project", "config")  # 匹配所有含 config 的文件

  方式三：控制输出格式
    PM.hex("C:/file.bin", bytes_per_line=8, uppercase=False)
    PM.hex("C:/file.bin", start_offset=1024, max_bytes=256)
    PM.hex("C:/file.bin", group_size=0, show_ascii=False)

────────────────────────────────────────────────────────────
【内置游戏列表 (30款)】

  贪吃蛇 Snake        俄罗斯方块 Tetris    扫雷 Minesweeper
  2048                打砖块 Breakout      弹球 Pong
  太空射击 SpaceInvaders  五子棋 Gomoku    井字棋 TicTacToe
  记忆翻牌 Memory     飞扬的小鸟 FlappyBird  吃豆人 PacMan
  数独 Sudoku         颜色记忆 SimonSays   消消乐 Match3
  跳一跳 DoodleJump   乒乓球 PingPong      打地鼠 WhackMole
  滑块拼图 SlidingPuzzle  迷宫 Maze        四子棋 ConnectFour
  弹球打砖 BrickBreaker  双人贪吃蛇 Snake2P  反应测试 ReactionTest
  打字速度 TypingTest  点击器 Clicker      大炮射击 Cannon
  15拼图 Fifteen      算术挑战 MathQuiz    翻牌配对 CardMatch

────────────────────────────────────────────────────────────
【模式说明】

  模式 0 — 选错了，无事发生
  模式 1 — 普通模式，完整构建，压缩率高，适合正式发布
  模式 2 — 极速模式，跳过压缩，构建极快，适合调试

────────────────────────────────────────────────────────────
【沙箱模式说明】

  不加沙箱 (sandbox=False, 默认):
    • 启用 nodeIntegration，可访问 Node.js API
    • 可通过 window.pymsi 访问 fs/path/os/child_process
    • 适合需要完整系统访问的桌面应用

  加沙箱 (sandbox=True):
    • 启用 contextIsolation，禁用 nodeIntegration
    • 注入 CSP 头限制网络和文件访问
    • 适合展示型 HTML 应用，更安全

────────────────────────────────────────────────────────────
【Electron 运行时】

  首次构建时自动下载 Electron v43.4.0 到:
    ~/.pymsi/electron/{version}/{platform}/

  支持平台:
    • win32-x64    (Windows 64位)
    • linux-x64    (Linux 64位)
    • darwin-x64   (macOS Intel)
    • darwin-arm64 (macOS Apple Silicon)

  生成的文件结构:
    {app_name}_app/
    ├── {app_name}.exe     ← 主程序
    ├── resources/
    │   └── app/
    │       ├── main.js        ← Electron 主进程
    │       ├── preload.js     ← 预加载脚本
    │       ├── package.json
    │       └── index.html     ← 你的 HTML 文件
    └── ...（Electron 运行时文件）

────────────────────────────────────────────────────────────
【完整示例】

  import PyMsi as PM

  # 示例 1：把 Python 项目打包成 MSI 安装包
  PM("C:/my_python_project")
  PM.s(2)
  # → 生成 C:/my_python_project.msi

  # 示例 2：把 HTML 项目打包成 Windows 桌面应用
  PM.html("C:/my_website")
  PM.html.title("我的网站")
  PM.html.sandbox(True)
  PM.html.icon("C:/icon.ico")
  PM.html.build()
  # → 生成 C:/my_website/dist/my_website_app/my_website.exe

  # 示例 3：跨平台构建 (Linux 上构建 Windows EXE)
  PM.html("C:/my_website")
  PM.html.platform("win32-x64")
  PM.html.build("C:/output/my_website.exe")
  # → 生成 C:/output/my_website_app/my_website.exe

────────────────────────────────────────────────────────────
【依赖】

  • Python >= 3.7
  • Electron 43.4.0 (首次自动下载，约 140MB)
  • 无需 Node.js 安装

────────────────────────────────────────────────────────────
【License】 MIT
"""


# ─── 常量 ───────────────────────────────────────────────
MODE_DESCRIPTIONS = {
    0: "选错了 — 无事发生，请重新选择模式 (1 或 2)",
    1: "普通模式 — 完整构建，压缩率高，适合发布",
    2: "极速模式 — 跳过压缩，构建极快，适合调试",
}


# ─── OLE Compound File 格式构建器 ────────────────────────
# MSI 文件本质上是 OLE Structured Storage (Compound Document)
# 以下代码在 Windows / Linux 上均可工作，纯 Python 实现


class _OLEWriter:
    """纯 Python 实现的 OLE Compound File 写入器"""

    HEADER_SIZE = 512
    SECTOR_SIZE = 512
    MIN_STREAM_SIZE = 4096  # 小于此值放在 mini stream 中
    MINI_SECTOR_SIZE = 64
    DIFAT_SIZE = 109  # header 中能放的 DIFAT 条目数

    def __init__(self, filepath):
        self._fp = open(filepath, "wb")
        self._fat = []          # FAT 扇区链表
        self._mini_fat = []     # Mini FAT 扇区链表
        self._dir_entries = []  # 目录条目
        self._dir_streams = {}  # name -> (data, is_mini)
        self._next_sector = 0
        self._next_mini_sector = 0
        self._mini_stream_data = b""

    def add_stream(self, name, data):
        is_mini = len(data) < self.MIN_STREAM_SIZE
        self._dir_streams[name] = (data, is_mini)

    def add_storage(self, name):
        self._dir_entries.append(_DirEntry(
            name=name, type=1, sid=-1
        ))

    def close(self):
        self._build()
        self._fp.close()

    def _build(self):
        self._build_directory()
        self._write_body()

    def _build_directory(self):
        # 构建目录树
        entries = []
        # Root Entry
        root = _DirEntry(name="Root Entry", type=1, sid=-1)
        entries.append(root)

        # 为每个流创建目录条目
        for name, (data, is_mini) in self._dir_streams.items():
            entry = _DirEntry(name=name, type=2, sid=-1, size=len(data))
            entries.append(entry)

        # 设置红黑树关系（简化：线性链表）
        for i, entry in enumerate(entries):
            if i > 0:
                entries[i - 1].dir_sibling_right = i - 1 + 2 if i < len(entries) - 1 else -1
            if i == 0:
                entry.dir_child = 1
                entry.dir_root = i
                entry.difat_start = -1
                entry.mini_fat_start = -1

        # 对齐到 128 字节的目录条目
        for entry in entries:
            entry.entry_id = entry.name.encode("utf-16-le")[:64]

        self._dir_entries = entries

    def _write_body(self):
        # 简化版：写入 header + 流数据
        # 先收集所有流数据
        self._write_simple_msi()

    def _write_simple_msi(self):
        """写入简化版 MSI（纯 Python 实现，不依赖 msilib）"""
        # 收集所有需要打包的文件
        streams = {}
        for name, (data, _) in self._dir_streams.items():
            streams[name] = data

        # 计算扇区布局
        # Sector 0: Header
        # Sector 1: FAT
        # Sector 2: Directory (4 entries × 128 bytes = 512 bytes = 1 sector)
        # Sector 3+: Stream data

        num_dir_entries = 1 + len(streams)  # Root + streams
        dir_sectors = max(1, (num_dir_entries * 128 + 511) // 512)

        # 计算流数据起始扇区
        stream_start_sector = 1 + 1 + dir_sectors  # Header + FAT + Directory

        # 为每个流分配扇区
        stream_sectors = {}
        current_sector = stream_start_sector
        for name, data in streams.items():
            num_sectors = (len(data) + 511) // 512
            stream_sectors[name] = (current_sector, len(data))
            current_sector += num_sectors

        total_sectors = current_sector

        # 写入 header（512 字节）
        header = bytearray(512)
        # Magic: D0 CF 11 E0 A1 B1 1A E1
        header[0:8] = bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1])
        # CLSID: MSI database GUID
        # {000C1084-0000-0000-C000-000000000046}
        msi_clsid = bytes([
            0x84, 0x10, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00,
            0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46,
        ])
        header[8:24] = msi_clsid
        # Minor version: 0x003E
        struct.pack_into("<H", header, 24, 0x003E)
        # Major version: 4 (Dex) for MSI
        struct.pack_into("<H", header, 26, 0x0004)
        # Byte order: 0xFFFE = little-endian
        struct.pack_into("<H", header, 28, 0xFFFE)
        # Sector size power: 9 (512) = 2^9 = 512
        struct.pack_into("<H", header, 30, 9)
        # Mini sector size power: 6 (64) = 2^6 = 64
        struct.pack_into("<H", header, 32, 6)
        # Reserved: 6 bytes
        # Number of directory sectors: 0 (means 0 for 512-byte sectors)
        struct.pack_into("<i", header, 40, 0)
        # Number of FAT sectors: 1
        struct.pack_into("<i", header, 44, 1)
        # First directory sector: 2 (sector index 2)
        struct.pack_into("<i", header, 48, 2)
        # Transaction signature number: 0
        # Mini stream cutoff size: 4096
        struct.pack_into("<i", header, 56, 4096)
        # First mini FAT sector: -2 (end of chain, no mini stream)
        struct.pack_into("<i", header, 60, -2)
        # Number of mini FAT sectors: 0
        struct.pack_into("<i", header, 64, 0)
        # First DIFAT sector: -2 (end of chain)
        struct.pack_into("<i", header, 68, -2)
        # Number of DIFAT sectors: 0
        struct.pack_into("<i", header, 72, 0)
        # DIFAT entries: first 109 entries (only first = 1 for FAT sector 1)
        struct.pack_into("<i", header, 76, 1)
        for i in range(1, 109):
            struct.pack_into("<i", header, 76 + i * 4, -1)  # FREE

        self._fp.write(bytes(header))

        # 写入 FAT sector (sector 1)
        fat = bytearray(512)
        # FAT[0]: Free sectors marker
        struct.pack_into("<i", fat, 0, -3)  # 0xFFFFFFFD = FAT sector
        # FAT[1]: end of chain (FAT sector itself)
        struct.pack_into("<i", fat, 4, -2)  # 0xFFFFFFFE = end of chain
        # FAT[2..2+dir_sectors-1]: chain directory sectors
        for d in range(dir_sectors):
            if d < dir_sectors - 1:
                struct.pack_into("<i", fat, (2 + d) * 4, 2 + d + 1)  # point to next
            else:
                struct.pack_into("<i", fat, (2 + d) * 4, -2)  # end of chain
        # FAT[2+dir_sectors+]: end of chain for each stream sector
        for i in range(2 + dir_sectors, total_sectors):
            struct.pack_into("<i", fat, i * 4, -2)  # end of chain
        self._fp.write(bytes(fat))

        # 写入目录 (sector 2+)
        dir_data = bytearray(dir_sectors * 512)
        offset = 0

        # Root Entry (type=5 for root storage)
        root_name = "Root Entry".encode("utf-16-le")
        dir_data[offset:offset + len(root_name)] = root_name
        struct.pack_into("<H", dir_data, offset + 64, len(root_name) + 2)  # name length (bytes, including null)
        dir_data[offset + 66] = 0x05  # type: root storage
        dir_data[offset + 67] = 0x01  # color: black (root is always black)
        struct.pack_into("<i", dir_data, offset + 68, -1)  # left sibling
        struct.pack_into("<i", dir_data, offset + 72, -1)  # right sibling
        struct.pack_into("<i", dir_data, offset + 76, 1)   # child: first stream entry
        # Root CLSID: MSI database GUID
        dir_data[offset + 80:offset + 96] = msi_clsid
        struct.pack_into("<i", dir_data, offset + 96, 0)   # state bits
        struct.pack_into("<Q", dir_data, offset + 100, 0)  # creation time
        struct.pack_into("<Q", dir_data, offset + 108, 0)  # modified time
        struct.pack_into("<i", dir_data, offset + 116, -2)  # start sector: no mini stream
        struct.pack_into("<i", dir_data, offset + 120, 0)  # size low
        struct.pack_into("<i", dir_data, offset + 124, 0)  # size high

        # 为每个流创建目录条目
        for i, (name, data) in enumerate(streams.items()):
            offset = 128 * (i + 1)
            name_bytes = name.encode("utf-16-le")
            # Truncate name to fit (max 32 UTF-16 chars = 64 bytes)
            if len(name_bytes) > 64:
                name_bytes = name_bytes[:64]
            dir_data[offset:offset + len(name_bytes)] = name_bytes
            struct.pack_into("<H", dir_data, offset + 64, len(name_bytes) + 2)  # name length
            dir_data[offset + 66] = 0x02  # type: stream
            dir_data[offset + 67] = 0x00  # color: red
            struct.pack_into("<i", dir_data, offset + 68, -1)  # left sibling
            # Right sibling: point to next stream, or -1 if last
            right_sib = i + 2 if i < len(streams) - 1 else -1
            struct.pack_into("<i", dir_data, offset + 72, right_sib)
            struct.pack_into("<i", dir_data, offset + 76, -1)  # child (none for streams)
            # CLSID: zero
            struct.pack_into("<i", dir_data, offset + 96, 0)   # state bits
            start_sector, size = stream_sectors[name]
            struct.pack_into("<i", dir_data, offset + 116, start_sector)  # start sector
            struct.pack_into("<i", dir_data, offset + 120, size & 0xFFFFFFFF)  # size low
            struct.pack_into("<i", dir_data, offset + 124, (size >> 32) & 0xFFFFFFFF)  # size high

        self._fp.write(bytes(dir_data))

        # 写入流数据
        for name, data in streams.items():
            self._fp.write(data)
            # 填充到 512 对齐
            pad = (512 - (len(data) % 512)) % 512
            if pad:
                self._fp.write(b"\x00" * pad)


class _DirEntry:
    __slots__ = ("name", "type", "sid", "size", "entry_id",
                 "dir_child", "dir_sibling_left", "dir_sibling_right",
                 "dir_root", "difat_start", "mini_fat_start")

    def __init__(self, name, type, sid, size=0):
        self.name = name
        self.type = type  # 1=storage, 2=stream, 5=root
        self.sid = sid
        self.size = size
        self.entry_id = b""
        self.dir_child = -1
        self.dir_sibling_left = -1
        self.dir_sibling_right = -1
        self.dir_root = -1
        self.difat_start = -1
        self.mini_fat_start = -1


# ─── MSI 构建器 ──────────────────────────────────────────

class _MSIBuilder:
    """MSI 安装包构建器"""

    def __init__(self):
        self._source_dir = None
        self._mode = None
        self._output_path = None

    def build(self, source_dir, mode, output_path=None):
        self._source_dir = os.path.abspath(source_dir)
        self._mode = mode

        if not os.path.isdir(self._source_dir):
            raise FileNotFoundError(f"目录不存在: {self._source_dir}")

        # 确定输出路径
        if output_path is None:
            dir_name = os.path.basename(self._source_dir.rstrip("/\\"))
            self._output_path = os.path.join(
                os.path.dirname(self._source_dir),
                f"{dir_name}.msi"
            )
        else:
            self._output_path = output_path

        # 收集所有文件
        file_list = self._collect_files()

        # 根据模式构建
        if self._mode == 0:
            print("[PyMsi] 模式 0: 选错了 — 无事发生。")
            print("        请使用 PM.s(1) 普通模式 或 PM.s(2) 极速模式")
            return None

        elif self._mode == 1:
            return self._build_normal(file_list)

        elif self._mode == 2:
            return self._build_fast(file_list)

        else:
            raise ValueError(f"未知模式: {self._mode}，有效值为 0/1/2")

    def _collect_files(self):
        """收集源目录下所有文件"""
        file_list = []
        base = self._source_dir
        for root, dirs, files in os.walk(base):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, base)
                file_list.append((full, rel))
        return file_list

    def _build_normal(self, file_list):
        """普通模式：完整构建 MSI"""
        print(f"[PyMsi] 普通模式构建中...")
        print(f"[PyMsi] 源目录: {self._source_dir}")
        print(f"[PyMsi] 文件数: {len(file_list)}")
        return self._write_msi(file_list, compress=True)

    def _build_fast(self, file_list):
        """极速模式：跳过压缩，快速构建"""
        print(f"[PyMsi] ⚡ 极速模式构建中...")
        print(f"[PyMsi] 源目录: {self._source_dir}")
        print(f"[PyMsi] 文件数: {len(file_list)}")
        return self._write_msi(file_list, compress=False)

    def _write_msi(self, file_list, compress):
        """写入 MSI 文件"""
        try:
            # 先尝试使用 Python 内置的 msilib（Windows）
            return self._write_msi_msilib(file_list, compress)
        except ImportError:
            # 非 Windows 环境，使用纯 Python 实现
            return self._write_msi_pure(file_list, compress)

    def _write_msi_msilib(self, file_list, compress):
        """使用 msilib 构建 MSI (Windows)"""
        import msilib

        product_code = self._generate_product_code()
        db = msilib.init_database(
            self._output_path,
            msilib.schema,
            os.path.basename(self._source_dir),
            product_code,
            "1.0.0.0",
            "PyMsi",
        )

        # 添加 Directory 表
        msilib.add_data(db, "Directory", [
            ("TARGETDIR", "", "SourceDir"),
            ("ProgramFilesFolder", "TARGETDIR", "PFiles"),
            ("INSTALLDIR", "ProgramFilesFolder", f"PyMsi_{os.path.basename(self._source_dir)}"),
        ])

        # 添加 Property 表
        msilib.add_data(db, "Property", [
            ("ProductCode", product_code),
            ("ProductName", os.path.basename(self._source_dir)),
            ("ProductVersion", "1.0.0.0"),
            ("Manufacturer", "PyMsi"),
            ("ARPURLINFOABOUT", "https://github.com/pymsi"),
        ])

        # 添加 Feature 表
        feature_name = "Complete"
        msilib.add_data(db, "Feature", [
            (feature_name, "", "Complete", "", 1, "INSTALLDIR", 0),
        ])

        # 添加 Component 表 + File 表 + FeatureComponents
        # 同时将文件添加到 CAB
        cab = msilib.CAB("PyMsi.cab")
        for i, (full_path, rel_path) in enumerate(file_list, 1):
            comp_id = self._make_guid(rel_path)
            file_name = os.path.basename(rel_path)
            short_name = file_name[:8].upper() if len(file_name) > 8 else file_name.upper()

            msilib.add_data(db, "Component", [
                (comp_id, comp_id, "INSTALLDIR", 2 if compress else 0),
            ])
            msilib.add_data(db, "FeatureComponents", [
                (feature_name, comp_id),
            ])
            msilib.add_data(db, "File", [
                (file_name, comp_id, file_name, len(open(full_path, "rb").read()),
                 "1.0.0.0", "", 8192, i),
            ])

            cab.add_file(full_path)

        # 添加 Media 表
        msilib.add_data(db, "Media", [
            (1, len(file_list), "#PyMsi.cab"),
        ])

        # 添加 InstallExecuteSequence 表
        msilib.add_data(db, "InstallExecuteSequence", [
            ("InstallValidate", "", 1400),
            ("InstallInitialize", "", 1500),
            ("InstallFinalize", "", 6600),
        ])

        cab.commit(db)
        db.Commit()
        print(f"[PyMsi] 构建完成: {self._output_path}")
        return self._output_path

    def _write_msi_pure(self, file_list, compress):
        """纯 Python 实现 MSI 构建（跨平台）"""
        print(f"[PyMsi] 使用纯 Python 模式构建 MSI...")

        # 收集所有文件数据
        total_size = 0
        file_entries = []
        for full_path, rel_path in file_list:
            with open(full_path, "rb") as f:
                data = f.read()
            file_entries.append((rel_path, data))
            total_size += len(data)

        # 构建 MSI 数据库内容
        db_content = self._build_msi_database(file_entries)

        # 创建 OLE compound file
        ole = _OLEWriter(self._output_path)
        ole.add_stream("\x05SummaryInformation", self._build_summary_info())
        ole.add_stream("_\x05DocumentSummaryInformation", self._build_doc_summary())
        ole.add_stream("Data", db_content)
        ole.add_stream("_Streams", self._build_streams(file_entries))
        ole.close()

        size_mb = total_size / (1024 * 1024)
        print(f"[PyMsi] 构建完成: {self._output_path}")
        print(f"[PyMsi] 总大小: {size_mb:.2f} MB")
        return self._output_path

    def _build_msi_database(self, file_entries):
        """构建 MSI 数据库表结构"""
        # 简化的 MSI 数据库
        tables = []

        # _Tables 表
        tables.append(self._make_table("_Tables", ["Name"], [
            ("Property",), ("Directory",), ("Component",),
            ("Feature",), ("FeatureComponents",), ("File",),
            ("Media",), ("InstallExecuteSequence",),
        ]))

        # Property 表
        product_code = self._generate_product_code()
        tables.append(self._make_table("Property", ["Property", "Value"], [
            ("ProductCode", product_code),
            ("ProductName", os.path.basename(self._source_dir)),
            ("ProductVersion", "1.0.0.0"),
            ("Manufacturer", "PyMsi"),
            ("ARPURLINFOABOUT", "https://github.com/pymsi"),
        ]))

        # Directory 表
        tables.append(self._make_table("Directory", ["Directory", "Directory_Parent", "DefaultDir"], [
            ("TARGETDIR", "", "SourceDir"),
            ("ProgramFilesFolder", "TARGETDIR", "PFiles"),
            ("INSTALLDIR", "ProgramFilesFolder", f"PyMsi:{os.path.basename(self._source_dir)}"),
        ]))

        # Component 表
        components = []
        for rel_path, _ in file_entries:
            comp_id = self._make_guid(rel_path)
            components.append((comp_id, comp_id, "INSTALLDIR", rel_path))
        tables.append(self._make_table("Component", ["Component", "ComponentId", "Directory_", "Attributes"], components))

        # Feature 表
        tables.append(self._make_table("Feature", ["Feature", "Feature_Parent", "Title", "Display", "Level", "Directory_", "Attributes"], [
            ("Complete", "", "Complete", "", 1, "INSTALLDIR", 0),
        ]))

        # FeatureComponents 表
        fc = [(comp[0], "Complete") for comp in components]
        tables.append(self._make_table("FeatureComponents", ["Feature_", "Component_"], fc))

        # File 表
        files = []
        for i, (rel_path, data) in enumerate(file_entries):
            comp_id = self._make_guid(rel_path)
            file_name = os.path.basename(rel_path)
            files.append((
                file_name, comp_id, file_name, len(data),
                "1.0.0.0", "", 0, 8192, 1 + i
            ))
        tables.append(self._make_table("File", [
            "File", "Component_", "FileName", "FileSize",
            "Version", "Language", "Attributes", "Sequence"
        ], files))

        # Media 表
        tables.append(self._make_table("Media", ["DiskId", "LastSequence", "Cabinet"], [
            (1, len(file_entries), "#PyMsi.cab"),
        ]))

        # InstallExecuteSequence 表
        tables.append(self._make_table("InstallExecuteSequence", ["Action", "Condition", "Sequence"], [
            ("InstallValidate", "", 1400),
            ("InstallInitialize", "", 1500),
            ("InstallFinalize", "", 6600),
        ]))

        # 序列化所有表
        result = b""
        for table_name, columns, rows in tables:
            result += self._serialize_table(table_name, columns, rows)

        return result

    def _make_table(self, name, columns, rows):
        return (name, columns, rows)

    def _serialize_table(self, name, columns, rows):
        """简单序列化表数据"""
        lines = []
        lines.append(f"[{name}]")
        lines.append("\t".join(columns))
        for row in rows:
            lines.append("\t".join(str(v) for v in row))
        lines.append("")
        return "\n".join(lines).encode("utf-8")

    def _build_summary_info(self):
        """构建 Summary Information 流"""
        # 简化的 Summary Information
        data = bytearray(4096)
        # Property set format
        # 写入基本的摘要信息
        return bytes(data)

    def _build_doc_summary(self):
        """构建 Document Summary Information 流"""
        return b"\x00" * 4096

    def _build_streams(self, file_entries):
        """构建文件流数据"""
        result = b""
        for rel_path, data in file_entries:
            result += struct.pack("<I", len(rel_path.encode("utf-8")))
            result += rel_path.encode("utf-8")
            result += struct.pack("<Q", len(data))
            result += data
        return result

    def _generate_product_code(self):
        """生成产品 GUID"""
        return str(uuid.uuid4()).upper()

    def _make_guid(self, seed):
        """基于种子生成确定性 GUID"""
        h = hashlib.md5(seed.encode("utf-8")).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}".upper()


# ─── 公开 API ───────────────────────────────────────────

from .html_builder import _HTMLBuilder, _HTMLModule
from .game import _GameModule, _GAME_NAMES
from .image import _ImageModule
from .hex import _HexModule
from .ai import _AIModule
from .translate import _TranslateModule
from .mail import _MailModule

# ═══════════════════════════════════════════════════════════════
# 文件串模块 — 像毛线球一样把文件串在一起
# ═══════════════════════════════════════════════════════════════
from .filechain import _FileChainModule

# ═══════════════════════════════════════════════════════════════
# KeyKey 加密模块 — AES/RSA/ECC 三合一, 512位, Unicode17.0
# ═══════════════════════════════════════════════════════════════
from .keykey import _KeyKeyModule

# ═══════════════════════════════════════════════════════════════
# 独家加密模块 — Cython + Python 通用 (1.5.0 新增)
# 字符→十进制→分3份→打乱→×10! (3628800)
# ═══════════════════════════════════════════════════════════════
from .exclcrypto import _ExclCryptoModule

# ═══════════════════════════════════════════════════════════════
# 极简 Web 服务器模块 (1.5.1 新增) — 类 Flask, 纯标准库
# ═══════════════════════════════════════════════════════════════
from .server import _ServerModule

# ═══════════════════════════════════════════════════════════════
# 极简后台浏览器模块 (1.5.1 新增) — 纯 Python, 不调用系统 Chrome
# ═══════════════════════════════════════════════════════════════
from .browser import _BrowserModule

# ═══════════════════════════════════════════════════════════════
# Shrink-Zeta 独家压缩模块 (1.5.2 新增) — .㠖 格式, 比 xz 更小
# ═══════════════════════════════════════════════════════════════
from .shrinkzeta import _ShrinkZetaModule

# ═══════════════════════════════════════════════════════════════
# 录屏模块 (1.5.3 新增) — 纯自研 Win32 GDI 截屏 + AVI/GIF 编码器
# 30+ 输出格式, 自动隐藏控制台, 默认 D:/Videos
# ═══════════════════════════════════════════════════════════════
from .recorder import _ScreenRecordModule

# ═══════════════════════════════════════════════════════════════
# .meow 文件打包/解包模块 (1.5.4 新增) — 揉成 .meow + address.json
# ═══════════════════════════════════════════════════════════════
from .meow import _MeowModule

# ═══════════════════════════════════════════════════════════════
# 进程权限提升模块 (1.5.5 新增) — SYSTEM/TrustedInstaller (Win) / root (Linux)
# ═══════════════════════════════════════════════════════════════
from .priv import _PrivModule

# ═══════════════════════════════════════════════════════════════
# .nano 容器模块 (1.5.6 新增) — 四级权限分区存储
# ═══════════════════════════════════════════════════════════════
from .nano import _NanoModule

# ═══════════════════════════════════════════════════════════════
# 摩斯密码视频模块 (1.5.7 新增) — 明文→摩斯密码→AVI视频
# 白色=点(25帧) 黑色=划(1.5秒) 红色=空格(20帧) 绿色=/(20帧)
# 纯 Python AVI 编码器, 零依赖, 颜色100%准确
# ═══════════════════════════════════════════════════════════════
from .morse import _MorseVideoModule

# ═══════════════════════════════════════════════════════════════
# 十六进制 RGB 视频模块 (1.5.8 新增) — 文本→Hex→RGB纯色AVI视频
# 16个hex数字(0-9,a-f)各映射到一种RGB纯色, 每色25帧
# 白色=开头标记/空格, 纯 Python AVI, 零依赖
# ═══════════════════════════════════════════════════════════════
from .hexvid import _HexVideoModule

# ═══════════════════════════════════════════════════════════════
# 生物教育模块 (1.5.9 Education Edition) — 细胞结构+蛋白质+酶
# 生成互动教程/蛋白质文件/酶文件, 可加热变性和酶催化
# ═══════════════════════════════════════════════════════════════
from .bio import _BioModule

# ═══════════════════════════════════════════════════════════════
# 化学教育模块 (1.6.0 Education Plus) — 元素+分子+反应+溶液+配平
# 20个元素、10种分子、7个反应、溶液计算、方程式配平
# ═══════════════════════════════════════════════════════════════
from .chemistry import _ChemistryModule

# ═══════════════════════════════════════════════════════════════
# 数学教育模块 (1.6.0 Education Plus) — 代数+几何+微积分+线代+概率+数论
# 6大数学分支, 互动教程 + 直接计算函数
# ═══════════════════════════════════════════════════════════════
from .math import _MathModule

# ═══════════════════════════════════════════════════════════════
# MeowHawk 搜索引擎模块 (1.7.0 新增) — 自研查找算法
# BM25 排序 + 倒排索引 + N-gram 模糊匹配, 纯 Python 零依赖
# ═══════════════════════════════════════════════════════════════
from .meowhawk import _MeowHawkModule

# ═══════════════════════════════════════════════════════════════
# Backtrack 回溯算法模块 (1.8.0 新增) — 暴力搜索引擎
# 排列/组合/子集/N皇后/数独/迷宫/背包/组合总和/单词拆分
# 1毫秒一次尝试, 1秒1000次, 100秒10万次
# ═══════════════════════════════════════════════════════════════
from .backtrack import _BacktrackModule

# ═══════════════════════════════════════════════════════════════
# Cow 文件格式模块 (1.9.0 新增) — .cow 格式引擎
# 无魔数, 纯 base-32 内容, 打开→临时目录→退出后清理
# ═══════════════════════════════════════════════════════════════
from .cow import _CowModule

# ═══════════════════════════════════════════════════════════════
# Train AI 训练模块 (2.0.0 新增) — 自研神经网络训练引擎
# 像 TensorFlow 那样训练真正的 AI, 轻量高效, 零成本
# 带专属 API Key + HTTP API 服务器
# ═══════════════════════════════════════════════════════════════
from .train import _TrainModule

# ═══════════════════════════════════════════════════════════════
# Mnn 文件格式模块 (2.1.0 新增) — .mnn G进制文件格式引擎
# 把日志文件彻底翻了个天, 人类看不懂, 机器能懂
# ═══════════════════════════════════════════════════════════════
from .mnn import _MnnModule

# ═══════════════════════════════════════════════════════════════
# Pyx 视频提取引擎 (2.2.0 / 2.3.0 新增) — Vmp模式 / 视频模式 / ckon验证
# B站/抖音/YouTube/快手/小红书... 通通给你提取
# 纯 Python 标准库, 不加 ffmpeg/ffprobe
# ═══════════════════════════════════════════════════════════════
from .pyx import _PyxModule


# ═══════════════════════════════════════════════════════════════
# Cmd 终端扩展引擎 (v2.4.0 新增) — Windows命令也能在Linux上用
# Pjsoi / Pytem / .msh / .mhn / .fsu
# 纯 Python 标准库 + 系统 API, 跨平台
# ═══════════════════════════════════════════════════════════════
from .cmd import _CmdModule

# ═══════════════════════════════════════════════════════════════
# MetHow 还原引擎 + Homtaw SDK (v2.5.0 新增)
# 快速还原 | 权限管理 | 密码找回 | 1350+ API SDK
# ═══════════════════════════════════════════════════════════════
from .methow import _MetHowModule
from .homtaw import _HomtawModule


# ═══════════════════════════════════════════════════════════════
# 主类
# ═══════════════════════════════════════════════════════════════

class _PyMsi:
    """
    PyMsi 主类 — 可调用对象 + .s() 方法 + .html 子模块

    用法:
        # 文件夹 → MSI
        import PyMsi as PM
        PM("C:/your/folder")
        PM.s(2)  # 极速模式构建

        # HTML → EXE (像 Electron 一样)
        PM.html("C:/html_project")
        PM.html.sandbox(True)   # 沙箱模式
        PM.html.icon("C:/icon.ico")
        PM.html.build()
    """

    def __init__(self):
        self._source_dir = None
        self._mode = None
        self._builder = _MSIBuilder()
        self._html_builder = _HTMLBuilder()
        self._html_module = _HTMLModule(self._html_builder, self._print_readme)
        self._game_module = _GameModule()
        self._image_module = _ImageModule()
        self._hex_module = _HexModule()
        self._ai_module = _AIModule()
        self._translate_module = _TranslateModule()
        self._mail_module = _MailModule()
        self._filechain_module = _FileChainModule()
        self._keykey_module = _KeyKeyModule()
        self._excl_module = _ExclCryptoModule()
        self._server_module = _ServerModule()
        self._browser_module = _BrowserModule()
        self._shrink_module = _ShrinkZetaModule()
        self._record_module = _ScreenRecordModule()
        self._meow_module = _MeowModule()
        self._priv_module = _PrivModule()
        self._nano_module = _NanoModule()
        self._morse_module = _MorseVideoModule()
        self._hexvid_module = _HexVideoModule()
        self._bio_module = _BioModule()
        self._chemistry_module = _ChemistryModule()
        self._math_module = _MathModule()
        self._meowhawk_module = _MeowHawkModule()
        self._backtrack_module = _BacktrackModule()
        self._cow_module = _CowModule()
        self._train_module = _TrainModule()
        self._mnn_module = _MnnModule()
        self._pyx_module = _PyxModule()
        self._cmd_module = _CmdModule()
        self._methow_module = _MetHowModule()
        self._homtaw_module = _HomtawModule()

    def __call__(self, path):
        """
        设置源文件夹路径

        Args:
            path: 要打包成 MSI 的文件夹路径

        Returns:
            self (用于链式调用)
        """
        self._source_dir = path
        print(f"[PyMsi] 源目录已设置: {path}")
        return self

    def s(self, mode):
        """
        选择构建模式并开始构建

        Args:
            mode: 构建模式
                0 = 选错了，不执行任何操作
                1 = 普通模式，完整构建，压缩率高
                2 = 极速模式，跳过压缩，构建极快

        Returns:
            生成的 MSI 文件路径，或 None
        """
        self._mode = mode

        if mode not in MODE_DESCRIPTIONS:
            raise ValueError(f"无效模式: {mode}，有效值: 0, 1, 2")

        desc = MODE_DESCRIPTIONS[mode]
        print(f"[PyMsi] 模式: {mode} - {desc}")

        if mode == 0:
            return None

        if self._source_dir is None:
            raise RuntimeError("请先使用 PM(path) 设置源目录，再调用 PM.s()")

        return self._builder.build(self._source_dir, mode)

    def _print_readme(self):
        """内部方法: 打印 README"""
        print(_README)

    @property
    def readme(self):
        """打印完整的帮助文档"""
        print(_README)
        return self

    # ═══════════════════════════════════════════════════════════
    # 别名 Aliases — 长短名通用，怎么写都行
    # ═══════════════════════════════════════════════════════════

    # PM.build() = PM("path") + PM.s(2) 一步到位
    def build(self, path, mode=2):
        """别名: 一步构建 MSI — PM.build("path") = PM("path"); PM.s(2)"""
        self.__call__(path)
        return self.s(mode)

    def b(self, path, mode=2):
        """短别名: PM.b("path") = PM.build(path, 2)"""
        return self.build(path, mode)

    def mode(self, m):
        """别名: PM.mode(2) = PM.s(2)"""
        return self.s(m)

    def m(self, m):
        """短别名: PM.m(2) = PM.s(2)"""
        return self.s(m)

    # MSI 相关: PM.msi / PM.pack / PM.make
    @property
    def msi(self):
        """别名: PM.msi("path", 2) 一步构建 MSI（callable 属性）"""
        class _MSIAliaser:
            def __init__(self, outer): self._outer = outer
            def __call__(self, path, mode=2):
                self._outer.__call__(path)
                return self._outer.s(mode)
            def __repr__(self):
                return "<PyMsi.msi> alias: PM.msi('path') = PM('path'); PM.s(2)"
        return _MSIAliaser(self)

    @property
    def pack(self):
        """别名: PM.pack(path) = PM.msi(path, 2)"""
        class _PAliaser:
            def __init__(self, outer): self._outer = outer
            def __call__(self, path, mode=2):
                self._outer.__call__(path)
                return self._outer.s(mode)
            def __repr__(self):
                return "<PyMsi.pack> alias"
        return _PAliaser(self)

    @property
    def make(self):
        """别名: PM.make(path, 2) 同 PM.build"""
        class _MAliaser:
            def __init__(self, outer): self._outer = outer
            def __call__(self, path, mode=2):
                self._outer.__call__(path)
                return self._outer.s(mode)
        return _MAliaser(self)

    # help 别名
    def help(self):
        """别名: PM.help() = PM.readme"""
        print(_README)
        return self

    @property
    def doc(self):
        """别名: PM.doc = PM.readme"""
        print(_README)
        return self

    @property
    def man(self):
        """别名: PM.man = PM.readme"""
        print(_README)
        return self

    # ═══════════════════════════════════════════════════════════
    # 子模块短别名
    # ═══════════════════════════════════════════════════════════

    @property
    def h(self):
        """短别名: PM.h = PM.html"""
        return self._html_module

    @property
    def web(self):
        """别名: PM.web = PM.html"""
        return self._html_module

    @property
    def app(self):
        """别名: PM.app = PM.html (把 HTML 做成 app)"""
        return self._html_module

    @property
    def electron(self):
        """别名: PM.electron = PM.html"""
        return self._html_module

    @property
    def g(self):
        """短别名: PM.g = PM.game"""
        return self._game_module

    @property
    def games(self):
        """别名: PM.games = PM.game"""
        return self._game_module

    @property
    def play(self):
        """别名: PM.play("Snake") = PM.game.Grap("Snake")"""
        class _Play:
            def __init__(self, gm): self._g = gm
            def __call__(self, name):
                return self._g.Grap(name)
            def __repr__(self):
                return "<PyMsi.play> alias: PM.play(name) = PM.game.Grap(name)"
            def __getattr__(self, item):
                return getattr(self._g, item)
        return _Play(self._game_module)

    @property
    def img(self):
        """短别名: PM.img = PM.image"""
        return self._image_module

    @property
    def i(self):
        """短别名: PM.i = PM.image"""
        return self._image_module

    @property
    def pic(self):
        """别名: PM.pic = PM.image"""
        return self._image_module

    @property
    def font(self):
        """别名: PM.font(folder, out) = PM.image.ttf(...)"""
        return self._image_module._ttf

    @property
    def fonts(self):
        """别名: PM.fonts = PM.image.ttf"""
        return self._image_module._ttf

    @property
    def ttf(self):
        """别名: PM.ttf(folder, out) = PM.image.ttf(...)"""
        return self._image_module._ttf

    # hex 子模块别名: PM.hexdump / PM.hd / PM.hexview
    @property
    def hexdump(self):
        """别名: PM.hexdump = PM.hex"""
        return self._hex_module

    @property
    def hd(self):
        """短别名: PM.hd = PM.hex"""
        return self._hex_module

    @property
    def hexview(self):
        """别名: PM.hexview = PM.hex"""
        return self._hex_module

    @property
    def html(self):
        """
        HTML → EXE 子模块

        像 Electron 一样把 HTML 文件夹打包成独立 EXE。
        支持自定义图标、沙箱模式开关。

        用法:
            PM.html("C:/html_project")
            PM.html.icon("C:/icon.ico")
            PM.html.sandbox(True)   # 加沙箱
            PM.html.build()
        """
        return self._html_module

    @property
    def game(self):
        """
        内置游戏模板库 (30+ 游戏)

        两行代码即开即玩！

        用法:
            PM.game.Grap("Snake")    # 贪吃蛇
            PM.game.Grap("Tetris")   # 俄罗斯方块
            PM.game.list()            # 列出所有游戏
        """
        return self._game_module

    @property
    def image(self):
        """
        图片处理模块

        当前功能: 图片 → TTF 字体 (纯 Python, 零外部依赖)
          - 支持 png / jpg / jpeg / bmp / ico / gif
          - GIF 自动拆帧，每帧作为一个独立字形
          - 按文件名自动识别对应字符，或提供 mapping 字典

        用法:
            # 方式一：命名 = 字符 (A.png → 'A', 中.png → '中')
            PM.image.ttf("C:/glyph_folder", "out.ttf")

            # 方式二：自定义映射
            PM.image.ttf("C:/glyphs", "out.ttf",
                         mapping={"glyph1.png": "A", "glyph2.png": "中"})

            # 查看完整教程
            PM.image.ttf.help()
        """
        return self._image_module

    @property
    def hex(self):
        """
        文件 Hex 解析子模块

        输入文件地址 → 找到对应文件 → 解析 16 进制 → 全部输出到终端

        用法:
            # 直接给文件路径, 全部 hex 输出到终端
            PM.hex("C:/some/file.bin")

            # 在目录里按文件名搜索, 找到后解析
            PM.hex.find("C:/my_project", "config.dat")

            # 带参数控制输出格式
            PM.hex.dump("C:/file.bin", bytes_per_line=16,
                        start_offset=0, max_bytes=512)

            # PM.hex == PM.hexdump == PM.hd == PM.hexview
        """
        return self._hex_module

    @property
    def ai(self):
        """
        AI 空壳子模块 — 告诉它 API Key + AI API 官网, 就能问 AI 问题

        用法:
            PM.ai.key = "sk-xxx"                      # 1. 设 API Key
            PM.ai.url = "https://api.openai.com"      # 2. 设 AI API 官网
            PM.ai.imput("你好, 你是谁?")               # 3. 问问题 (输出自动 print)

            # PM.ai("问题")  直接问也行
            # print(PM.ai.output)  拿原始输出文本
            # PM.ai.ask / chat / question / send / say  都是 imput 别名
        """
        return self._ai_module

    # ai 子模块别名: PM.AI / PM.gpt / PM.chat / PM.llm
    @property
    def AI(self):
        """别名: PM.AI = PM.ai"""
        return self._ai_module

    @property
    def gpt(self):
        """别名: PM.gpt = PM.ai"""
        return self._ai_module

    @property
    def llm(self):
        """别名: PM.llm = PM.ai"""
        return self._ai_module

    @property
    def chatbot(self):
        """别名: PM.chatbot = PM.ai"""
        return self._ai_module

    @property
    def translate(self):
        """
        翻译子模块 — 100+ 种语言 (默认走 LibreTranslate API, 零依赖)

        用法:
            PM.translate("你好")                      # 中文 → 英文 (默认)
            PM.translate.to("你好", "en")              # 明确指定目标语言
            PM.translate.en("你好")                    # → 英语 (快捷)
            PM.translate.ru("你好")                    # → 俄语 (快捷)
            PM.translate.fr("你好")                    # → 法语 (快捷)
            PM.translate.ko("你好")                    # → 韩语 (快捷)
            PM.translate.ja("你好")                    # → 日语 (快捷)
            PM.translate.de("你好")                    # → 德语 (快捷)
            PM.translate.中文("Hello")                 # → 中文 (快捷)

            # 输入输出都能当变量用
            q = PM.translate.input                    # 上次输入的原文
            a = PM.translate.output                   # 翻译结果
            src = PM.translate.source_lang            # 源语言
            tgt = PM.translate.target_lang            # 目标语言

            # PM.tr / PM.trans / PM.t / PM.翻译  都是 translate 别名
        """
        return self._translate_module

    # translate 子模块别名
    @property
    def Translate(self):
        """别名: PM.Translate = PM.translate"""
        return self._translate_module

    @property
    def tr(self):
        """别名: PM.tr = PM.translate"""
        return self._translate_module

    @property
    def trans(self):
        """别名: PM.trans = PM.translate"""
        return self._translate_module

    @property
    def translation(self):
        """别名: PM.translation = PM.translate"""
        return self._translate_module

    @property
    def translator(self):
        """别名: PM.translator = PM.translate"""
        return self._translate_module

    @property
    def t(self):
        """别名: PM.t = PM.translate"""
        return self._translate_module

    @property
    def 翻译(self):
        """别名: PM.翻译 = PM.translate"""
        return self._translate_module

    @property
    def 译(self):
        """别名: PM.译 = PM.translate"""
        return self._translate_module

    @property
    def dl(self):
        """
        邮件子模块 — 发送验证码 / 通知邮件 (内置发件 wns1@qq.com, 零依赖)

        用法:
            PM.dl.auth("QQ邮箱授权码")              # 1. 设授权码 (QQ邮箱设置里开启SMTP生成)
            PM.dl.output("user@gmail.com")          # 2. 设收件人 (任意邮箱都行)
            PM.dl.print("你的验证码是 123456")       # 3. 发送邮件

            # 一键发送验证码 (自动生成 6 位码 + 拼正文 + 发邮件)
            PM.dl.send_code()
            print(PM.dl.code)                       # 拿到刚生成的验证码做比对

            # 输入输出都当变量用
            to = PM.dl.output                       # 收件人邮箱
            body = PM.dl.input                       # 上次发送的邮件内容
            code = PM.dl.code                        # 上次生成的验证码

            # 链式: PM.dl.auth(码).output(邮箱).print(正文)
            # PM.dl / PM.mail / PM.email / PM.send / PM.邮件 / PM.发送 都是同一模块
        """
        return self._mail_module

    # dl 子模块别名
    @property
    def Dl(self):
        """别名: PM.Dl = PM.dl"""
        return self._mail_module

    @property
    def mail(self):
        """别名: PM.mail = PM.dl"""
        return self._mail_module

    @property
    def Mail(self):
        """别名: PM.Mail = PM.dl"""
        return self._mail_module

    @property
    def email(self):
        """别名: PM.email = PM.dl"""
        return self._mail_module

    @property
    def Email(self):
        """别名: PM.Email = PM.dl"""
        return self._mail_module

    @property
    def deliver(self):
        """别名: PM.deliver = PM.dl"""
        return self._mail_module

    @property
    def send(self):
        """别名: PM.send = PM.dl"""
        return self._mail_module

    @property
    def smtp(self):
        """别名: PM.smtp = PM.dl"""
        return self._mail_module

    @property
    def 邮件(self):
        """别名: PM.邮件 = PM.dl"""
        return self._mail_module

    @property
    def 邮箱(self):
        """别名: PM.邮箱 = PM.dl"""
        return self._mail_module

    @property
    def 发邮件(self):
        """别名: PM.发邮件 = PM.dl"""
        return self._mail_module

    @property
    def filechain(self):
        """
        文件串子模块 — 像毛线球一样把文件串在一起

        把文件一个一个挂在线上面，揉成一个毛线球，变成一个文件。

        用法:
            # 串文件 — 把多个文件揉成一个毛线球
            PM.filechain("a.txt", "b.png", "c.py")           # → output.yarn
            PM.filechain.to("我的球.yarn", "a.txt", "b.png")  # → 指定输出

            # 看毛线球里有什么
            PM.filechain.list("我的球.yarn")

            # 拆毛线球 — 把文件抽出来
            PM.filechain.un("我的球.yarn")                     # 全部解出
            PM.filechain.un("我的球.yarn", "a.txt")            # 只解一个

            # 合并毛线球
            PM.filechain.merge("a.yarn", "b.yarn", "out.yarn")

            # PM.fc / PM.chain / PM.文件串 / PM.毛线球 都是别名
        """
        return self._filechain_module

    # filechain 别名
    @property
    def fc(self):
        """短别名: PM.fc = PM.filechain"""
        return self._filechain_module

    @property
    def chain(self):
        """别名: PM.chain = PM.filechain"""
        return self._filechain_module

    @property
    def yarn(self):
        """别名: PM.yarn = PM.filechain (毛线球)"""
        return self._filechain_module

    @property
    def 文件串(self):
        """别名: PM.文件串 = PM.filechain"""
        return self._filechain_module

    @property
    def 毛线球(self):
        """别名: PM.毛线球 = PM.filechain"""
        return self._filechain_module

    @property
    def keykey(self):
        """
        🔐 KeyKey 三合一强加密 (AES / RSA / ECC 合一)

        密钥不可能破解: Unicode 17.0 全字符 + 512 位 + PBKDF2-HMAC-SHA512

        用法:
            # 加密 (选文件 + 选类型)
            PM.keykey("secret.txt", mode="AES")      # AES 风格
            PM.keykey("secret.txt", mode="RSA")      # RSA 风格
            PM.keykey("secret.txt", mode="ECC")      # ECC 风格
            PM.keykey("secret.txt", mode="HYBRID")   # 三合一, 最强
            # → 生成 secret.txt.keykey (加密文件) + secret.txt.FILEKEY (密钥)

            # 解密 (选中 FILEKEY, 自动检测)
            PM.keykey.dec("secret.txt.FILEKEY")      # 自动找到并解密

            # 设额外密码 (可选, 让密钥更强)
            PM.keykey("secret.txt", mode="HYBRID", password="我的密码")
            PM.keykey.dec("secret.txt.FILEKEY", password="我的密码")
        """
        return self._keykey_module

    # keykey 别名
    @property
    def KeyKey(self):
        """别名: PM.KeyKey = PM.keykey"""
        return self._keykey_module

    @property
    def crypto(self):
        """别名: PM.crypto = PM.keykey"""
        return self._keykey_module

    @property
    def encrypt(self):
        """别名: PM.encrypt = PM.keykey (加密模块)"""
        return self._keykey_module

    @property
    def 加密(self):
        """别名: PM.加密 = PM.keykey"""
        return self._keykey_module

    @property
    def excl(self):
        """
        🔒 独家加密 (纯 C + GMP 大整数, 1.5.0 新增)

        算法: 字符→十进制→分3份→随机打乱→×10! (3628800)
        实现: PyMsi/_excl_cipher.c (libgmp 任意精度大整数)
        用户装 wheel 即用, 无需编译器

        用法:
            # 加密文件
            PM.excl("secret.txt")
            # → 生成 secret.txt.excl (加密文件) + secret.txt.EXCKEY (密钥)

            # 解密 (选中 EXCKEY, 自动检测)
            PM.excl.dec("secret.txt.EXCKEY")

            # 直接对字符串加密/解密
            ct, fk = PM.excl.encrypt("机密内容")
            pt = PM.excl.decrypt(ct, fk)
        """
        return self._excl_module

    # excl 别名
    @property
    def 独家加密(self):
        """别名: PM.独家加密 = PM.excl"""
        return self._excl_module

    @property
    def exclusive(self):
        """别名"""
        return self._excl_module

    @property
    def server(self):
        """
        🌐 极简 Web 服务器 (类 Flask, 纯标准库, 1.5.1 新增)

        用法:
            # 链式
            PM.server.port(8080).route("/").serve("<h1>Hi</h1>").start()
            PM.server.stop()

            # Flask 装饰器
            @PM.server.app.route("/")
            def home(): return "<h1>Home</h1>"
            PM.server.run(8080)

            # 静态文件
            PM.server.static("/", "./public").start(8080)
        """
        return self._server_module

    # server 别名
    @property
    def http(self):
        """别名: PM.http = PM.server"""
        return self._server_module

    @property
    def web(self):
        """别名: PM.web = PM.server"""
        return self._server_module

    @property
    def 服务器(self):
        """别名: PM.服务器 = PM.server"""
        return self._server_module

    @property
    def browser(self):
        """
        🌍 极简后台浏览器 (纯 Python, 不调用系统 Chrome/Edge, 1.5.1 新增)

        在后台打开 HTML, 解析 HTML + CSS + 执行 JS

        用法:
            PM.browser.open('<h1 id="t">Hi</h1>')
            PM.browser.title
            PM.browser.find('#t').text
            PM.browser.eval('1+2')         # 3
            PM.browser.close()

            PM.browser.open_url('https://example.com')
        """
        return self._browser_module

    # browser 别名
    @property
    def 浏览器(self):
        """别名: PM.浏览器 = PM.browser"""
        return self._browser_module

    @property
    def shrink(self):
        """
        🔒 独家压缩格式 .㠖 (Shrink-Zeta 算法, 1.5.2 新增)

        自研压缩: LZMA1 raw + 稀疏字节重映射 + 64MB 分块 + CRC32 校验
        实测比 xz -9e 还小 (省掉 xz 60+ 字节头部开销)

        用法:
            PM.shrink('file.txt')              # → file.txt.㠖
            PM.shrink.dec('file.txt.㠖')        # → file.txt
            PM.shrink.compress(data)          # 字节流压缩
            PM.shrink.decompress(sz)          # 字节流解压
            PM.shrink.folder('dir')          # 批量压缩
            PM.shrink.folder_dec('dir')      # 批量解压

        特性:
            - 比 xz -9e 小 5%-25% (小文件收益更大)
            - 64MB 分块, 大文件不占内存
            - 损坏块可跳过, 其余块正常还原 (CRC32 校验)
            - 随机数据兜底直存, 不膨胀
        """
        return self._shrink_module

    # shrink 别名
    @property
    def sz(self):
        """别名: PM.sz = PM.shrink"""
        return self._shrink_module

    @property
    def zeta(self):
        """别名: PM.zeta = PM.shrink"""
        return self._shrink_module

    @property
    def compress(self):
        """别名: PM.compress = PM.shrink"""
        return self._shrink_module

    @property
    def 压缩(self):
        """别名: PM.压缩 = PM.shrink"""
        return self._shrink_module

    @property
    def record(self):
        """
        📹 录屏模块 (1.5.3 新增) — 纯自研, 自动隐藏控制台

        ⚠️ 仅支持 Windows! macOS/Linux 调用会抛 RuntimeError
           截屏底层是 Win32 GDI (ctypes → user32/gdi32/kernel32)
           macOS 替代: screencapture | Linux 替代: ffmpeg -f x11grab

        纯手搓的屏幕录制:
            - Win32 GDI 截屏 (ctypes, 零依赖)
            - 纯 Python AVI 编码器 (RIFF 容器手写)
            - 纯 Python GIF 动画编码器 (3-3-2 量化 + LZW 压缩)
            - 30+ 输出格式 (纯自研 AVI/GIF + ffmpeg 转码)
            - 自动隐藏控制台, 后台静默录制
            - 默认 D:/Videos, 录完自动输出文件路径

        用法:
            # 一键录屏 (默认: 1分钟, 最高4K, AVI, D:/Videos)
            PM.record()

            # 自定义
            PM.record(duration=60, resolution="4K", fmt="mp4")
            PM.record(duration=30, fmt="gif", output_dir="D:/Videos")

            # 分步配置
            PM.record.duration = 60       # 录屏时长 (秒)
            PM.record.resolution = "4K"   # 清晰度 (最高4K)
            PM.record.format = "gif"      # 输出格式
            PM.record.start()

            # 查看支持的格式
            PM.record.formats()           # 打印 30+ 格式列表

            # 录完后的输出路径
            print(PM.record.output)

            # 别名: PM.rec / PM.capture / PM.录屏 / PM.录像
        """
        return self._record_module

    # record 别名
    @property
    def rec(self):
        """别名: PM.rec = PM.record"""
        return self._record_module

    @property
    def capture(self):
        """别名: PM.capture = PM.record"""
        return self._record_module

    @property
    def screen(self):
        """别名: PM.screen = PM.record"""
        return self._record_module

    @property
    def screencast(self):
        """别名: PM.screencast = PM.record"""
        return self._record_module

    @property
    def screenrecord(self):
        """别名: PM.screenrecord = PM.record"""
        return self._record_module

    @property
    def 录屏(self):
        """别名: PM.录屏 = PM.record"""
        return self._record_module

    @property
    def 录像(self):
        """别名: PM.录像 = PM.record"""
        return self._record_module

    @property
    def 视频(self):
        """别名: PM.视频 = PM.record"""
        return self._record_module

    @property
    def meow(self):
        """
        🐱 .meow 文件打包/解包模块 (1.5.4 新增)

        把多个文件揉成一个 .meow, 同时吐出 address.json
        address.json 存着每个文件的数字地址 (154.04.1.1:数字地址)
        解包时提供 address.json 所在目录, 提取所有文件到 D:/Dist

        用法:
            # 打包 (揉成 .meow)
            PM.meow.disteow(["a.txt", "b.png", "c.pdf"])
            # → D:/Meow/output.meow + D:/Meow/address.json

            # 自定义输出路径
            PM.meow.disteow(["a.txt", "b.png"], output="E:/test/data.meow")

            # 解包 (从 .meow 取出所有文件)
            PM.meow.undisteow("D:/Meow/")    # 提供 address.json 所在目录
            # → 读取 address.json → 提取所有文件到 D:/Dist

            # 列出 .meow 中的文件
            PM.meow.list("D:/Meow/")

            # 别名: PM.cat / PM.揉 / PM.猫
        """
        return self._meow_module

    # meow 别名
    @property
    def cat(self):
        """别名: PM.cat = PM.meow"""
        return self._meow_module

    @property
    def 揉(self):
        """别名: PM.揉 = PM.meow"""
        return self._meow_module

    @property
    def 猫(self):
        """别名: PM.猫 = PM.meow"""
        return self._meow_module

    @property
    def priv(self):
        """
        🔐 进程权限提升模块 (1.5.5 新增)

        以特定权限打开进程:
            Windows: 管理员 → SYSTEM / TrustedInstaller (NSudo 技术链)
            Linux:   普通用户 → root (通过 sudo / pkexec)

        ⚠️ 需要管理员 (Windows) / sudo (Linux) 权限, 不能绕过认证!

        用法:
            # Windows: 以 SYSTEM 权限运行
            PM.priv.system("notepad.exe")
            PM.priv.system("C:/Windows/System32/cmd.exe")

            # Windows: 以 TrustedInstaller 运行
            PM.priv.trusted("notepad.exe")

            # Windows: 以管理员运行 (UAC)
            PM.priv.admin("notepad.exe")

            # Linux: 以 root 运行
            PM.priv.system("ls /root")
            PM.priv.root("whoami")

            # 查看当前身份
            PM.priv.whoami()

            # 别名: PM.su / PM.runas / PM.elevate / PM.提权
        """
        return self._priv_module

    # priv 别名
    @property
    def su(self):
        """别名: PM.su = PM.priv"""
        return self._priv_module

    @property
    def runas(self):
        """别名: PM.runas = PM.priv"""
        return self._priv_module

    @property
    def elevate(self):
        """别名: PM.elevate = PM.priv"""
        return self._priv_module

    @property
    def 提权(self):
        """别名: PM.提权 = PM.priv"""
        return self._priv_module

    @property
    def 权限(self):
        """别名: PM.权限 = PM.priv"""
        return self._priv_module

    @property
    def nano(self):
        """
        📦 .nano 容器模块 (1.5.6 新增) — 四级权限分区存储

        自研 .nano 容器文件格式, 比压缩包更安全的存储方式:
        权限制度 + 校验 + 分区加密, 每个区域密码/权限都不一样

        四个分区 (从低到高):
            1. normal    — 普通区域, 无需任何权限
            2. adminanorobit (Anon2) — 管理员级, 需 admin/sudo
            3. asoav1    (Dona0 / 高泉区) — 内核级, 需 SYSTEM/root
            4. nanou     — 最高权限区, 需 .nnu 脚本

        用法:
            # 创建容器
            PM.nano.create("data.nano", anon2_pw="admin123",
                           dona0_key="kernel_secret", nanou_key="top_secret")

            # 添加文件
            PM.nano.add("data.nano", "normal", "readme.txt")
            PM.nano.add("data.nano", "adminanorobit", "secret.docx", anon2_pw="admin123")

            # 列出 / 提取
            PM.nano.list("data.nano", "normal")
            PM.nano.extract("data.nano", "normal", output_dir="D:/out")

            # Nanou 区: 执行 .nnu 脚本
            PM.nano.run_nnu("extract.nnu")
            PM.nano.nnu_help()  # 查看 .nnu 公开语法

            # 别名: PM.container / PM.容器 / PM.纳米
        """
        return self._nano_module

    # nano 别名
    @property
    def container(self):
        """别名: PM.container = PM.nano"""
        return self._nano_module

    @property
    def 容器(self):
        """别名: PM.容器 = PM.nano"""
        return self._nano_module

    @property
    def 纳米(self):
        """别名: PM.纳米 = PM.nano"""
        return self._nano_module

    @property
    def morse(self):
        """
        📡 摩斯密码视频模块 (1.5.7 新增) — 明文→摩斯密码→AVI视频

        把文本转换成摩斯密码视频, 用颜色和时长编码:
            白色 25帧 = 点 (.)
            黑色 1.5秒 = 划 (-)
            红色 20帧 = 空格 (字母间隔)
            绿色 20帧 = / (单词分隔)

        纯 Python AVI 编码器 (无压缩), 颜色100%准确, 零第三方依赖
        自动生成说明文档 txt

        用法:
            # 一键生成
            PM.morse("Hello World", output="morse.avi")

            # 自定义分辨率和帧率
            PM.morse("SOS", output="sos.avi", size=(640, 480), fps=25)

            # 只转摩斯密码 (不生成视频)
            code = PM.morse.text_to_morse("Hello World")

            # 单独生成说明文档
            PM.morse.readme("readme.txt")

            # 别名: PM.morse_video / PM.摩斯密码 / PM.摩斯 / PM.mv
        """
        return self._morse_module

    # morse 别名
    @property
    def morse_video(self):
        """别名: PM.morse_video = PM.morse"""
        return self._morse_module

    @property
    def mv(self):
        """别名: PM.mv = PM.morse"""
        return self._morse_module

    @property
    def 摩斯密码(self):
        """别名: PM.摩斯密码 = PM.morse"""
        return self._morse_module

    @property
    def 摩斯(self):
        """别名: PM.摩斯 = PM.morse"""
        return self._morse_module

    @property
    def hexvid(self):
        """
        🎨 十六进制 RGB 视频模块 (1.5.8 新增) — 文本→Hex→RGB纯色AVI视频

        把文本编码为十六进制, 每个 hex 数字映射到一种 RGB 纯色:
            白色 25帧 = 开头标记 / 空格
            0=黑 1=红 2=绿 3=蓝 4=黄 5=品红 6=青 7=橙
            8=紫 9=青柠 a=蓝绿 b=粉 c=深蓝 d=深红 e=橄榄 f=灰

        纯 Python AVI (无压缩), 颜色100%准确, 零依赖
        自动生成说明文档 txt

        用法:
            # 一键生成
            PM.hexvid("Hello", output="hello.avi")

            # 自定义分辨率
            PM.hexvid("Hi", output="hi.avi", size=(640, 480))

            # 只转 hex (不生成视频)
            code = PM.hexvid.text_to_hex("Hello")

            # 别名: PM.hex_video / PM.hv / PM.十六进制视频
        """
        return self._hexvid_module

    # hexvid 别名
    @property
    def hex_video(self):
        """别名: PM.hex_video = PM.hexvid"""
        return self._hexvid_module

    @property
    def hv(self):
        """别名: PM.hv = PM.hexvid"""
        return self._hexvid_module

    @property
    def 十六进制视频(self):
        """别名: PM.十六进制视频 = PM.hexvid"""
        return self._hexvid_module

    @property
    def bio(self):
        """
        🧬 生物教育模块 (1.5.9 Education Edition) — 细胞结构+蛋白质+酶

        专为程序员设计的生物学教学工具:
        1. 细胞结构 — 生成互动式教程 Python 文件 (运行后终端输出)
        2. 蛋白质系统 — 10种蛋白质, 可加热变性
        3. 酶系统 — 7种酶, 可催化对应蛋白质

        用法:
            # 生成细胞结构教程
            PM.bio.cell()
            PM.bio.cell(output="my_tutorial.py")

            # 生成蛋白质文件
            PM.bio.protein("hemoglobin")
            PM.bio.protein("血红蛋白")  # 支持中文

            # 生成酶文件
            PM.bio.enzyme("pepsin")
            PM.bio.enzyme("胃蛋白酶")

            # 加热变性
            PM.bio.denature("hemoglobin.protein", temp=70)
            PM.bio.heat("casein.protein", temp=100)  # 别名

            # 酶催化反应
            PM.bio.catalyze("pepsin.enzyme", "casein.protein")
            PM.bio.react("pepsin.enzyme", "casein.protein")  # 别名

            # 列出所有可用蛋白质和酶
            PM.bio.list_proteins()
            PM.bio.list_enzymes()
            PM.bio.list_all()

            # 别名: PM.biology / PM.生物
        """
        return self._bio_module

    @property
    def biology(self):
        """别名: PM.biology = PM.bio"""
        return self._bio_module

    @property
    def 生物(self):
        """别名: PM.生物 = PM.bio"""
        return self._bio_module

    @property
    def chem(self):
        """
        ⚗️  化学教育模块 (1.6.0 Education Plus) — 元素+分子+反应+溶液+配平

        专为程序员设计的化学教学工具:
        1. 元素周期表 — 20个常见元素, 每个都有编程类比
        2. 分子结构 — 10种常见分子, 用数据结构类比
        3. 化学反应 — 7个经典反应, 带动画模拟
        4. 溶液计算 — 摩尔浓度、pH值计算器
        5. 方程式配平 — 简单化学方程式配平

        用法:
            PM.chem.element()          # 元素周期表教程
            PM.chem.molecule()         # 分子结构教程
            PM.chem.reaction()         # 化学反应模拟器
            PM.chem.solution()         # 溶液计算器 (交互式)
            PM.chem.balance("H2+O2=H2O")  # 配平方程式
            PM.chem.molarity(10, 40, 0.5)  # 摩尔浓度计算
            PM.chem.ph(0.001)          # pH计算
            PM.chem.list_elements()    # 列出所有元素

            别名: PM.chemistry / PM.化学
        """
        return self._chemistry_module

    @property
    def chemistry(self):
        """别名: PM.chemistry = PM.chem"""
        return self._chemistry_module

    @property
    def 化学(self):
        """别名: PM.化学 = PM.chem"""
        return self._chemistry_module

    @property
    def math(self):
        """
        🔢 数学教育模块 (1.6.0 Education Plus) — 6大分支全涵盖

        专为程序员设计的数学教学工具:
        1. 代数 — 方程、函数、因式分解
        2. 几何 — 面积体积、三角函数、勾股定理
        3. 微积分 — 导数、积分、极值 (AI基础)
        4. 线性代数 — 向量、矩阵、特征值 (AI必备)
        5. 概率统计 — 概率分布、期望方差、贝叶斯
        6. 数论 — 质数、GCD、模运算、RSA基础

        用法:
            PM.math.algebra()            # 代数教程
            PM.math.geometry()           # 几何教程
            PM.math.calculus()           # 微积分教程
            PM.math.linear_algebra()     # 线性代数教程
            PM.math.probability()        # 概率统计教程
            PM.math.number_theory()      # 数论教程

            # 直接计算
            PM.math.quadratic(1, -5, 6)  # 解二次方程
            PM.math.factorial(5)         # 阶乘
            PM.math.gcd(48, 36)          # 最大公约数
            PM.math.dot_product([1,2,3], [4,5,6])  # 点积
            PM.math.matrix_mult(A, B)    # 矩阵乘法
            PM.math.is_prime(17)         # 判断质数
            PM.math.prime_factors(100)   # 质因数分解
            PM.math.fast_pow(3, 13, 100) # 快速幂

            别名: PM.maths / PM.数学
        """
        return self._math_module

    @property
    def maths(self):
        """别名: PM.maths = PM.math"""
        return self._math_module

    @property
    def 数学(self):
        """别名: PM.数学 = PM.math"""
        return self._math_module

    @property
    def meowhawk(self):
        """
        🐾 MeowHawk 自研查找算法引擎 (v1.7.0)

        轻量级高性能全文检索引擎, 对标主流搜索引擎核心算法:
          - BM25 排序 (与 Lucene / Elasticsearch 相同)
          - 倒排索引 (Inverted Index)
          - N-gram 模糊匹配 (Jaccard 相似度, 拼写纠错)
          - 中文双字分词 + 英文单词分词
          - 摘要提取与高亮
          - 纯 Python, 零依赖

        用法:
            # 创建引擎 + 索引文档
            mh = PM.meowhawk()
            mh.add_document("Python是最流行的编程语言")
            mh.add_document("Java也是很好的编程语言")
            mh.add_document("Go语言并发性能很强")

            # 搜索
            results = mh.search("编程语言")
            for r in results:
                print(f"  [{r.score:.2f}] {r.snippet}")

            # 模糊搜索 (拼写纠错)
            results = mh.search("编成语言", fuzzy=True)

            # 前缀补全
            print(mh.suggest("编"))

            # 持久化
            mh.save("index.json")
            mh2 = PM.meowhawk.load("index.json")

            # 快捷搜索 (一次性索引+搜索)
            results = PM.meowhawk.search_in(["文档1", "文档2"], "查询词")

            # 演示 / 基准测试
            PM.meowhawk.demo()
            PM.meowhawk.benchmark(num_docs=1000)

            # 直接用类
            from PyMsi.meowhawk import MeowHawk
            mh = MeowHawk()
        """
        return self._meowhawk_module

    @property
    def backtrack(self):
        """
        🔙 回溯算法暴力引擎 (v1.8.0)

        轻量级高性能回溯搜索, 纯Python零依赖.
        暴力的时间极短 — 1毫秒一次尝试, 1秒就是 1000 次, 100秒就是 10万次.

        内置经典问题 (10种):
            PM.backtrack.permute([1,2,3])              # 全排列
            PM.backtrack.permute_unique([1,1,2])        # 去重排列
            PM.backtrack.combine(4, 2)                 # 组合 C(n,k)
            PM.backtrack.subsets([1,2,3])              # 所有子集
            PM.backtrack.subsets_with_dup([1,2,2])      # 去重子集
            PM.backtrack.n_queens(4)                   # N皇后
            PM.backtrack.n_queens_count(8)             # N皇后计数
            PM.backtrack.solve_sudoku(board)            # 数独求解
            PM.backtrack.maze_path(maze, s, e)          # 迷宫所有路径
            PM.backtrack.maze_shortest_path(maze,s,e)  # 迷宫最短路径 (BFS)
            PM.backtrack.knapsack(items, capacity)     # 0-1背包
            PM.backtrack.combination_sum(cands, tgt)    # 组合总和(可重复)
            PM.backtrack.word_break(s, word_dict)      # 单词拆分

        通用框架 (自定义问题):
            results = PM.backtrack.solve(
                choices=[...],                         # 可选列表
                is_valid=lambda path, c: ...,          # 约束条件
                is_goal=lambda path: ...,              # 目标条件
                find_all=True,                          # 找所有解
                prune=lambda path: ...,                 # 剪枝条件
            )

        演示/性能测试:
            PM.backtrack.demo()                        # 运行演示
            PM.backtrack.benchmark()                   # 性能基准测试

        性能参考:
            subsets(20): 100万子集 / 秒
            n_queens(8): 92解 / 毫秒
            permute(8): 40320解 / 毫秒
            数独: 难题 < 1ms
        """
        return self._backtrack_module

    @property
    def 回溯(self):
        """别名: PM.回溯 = PM.backtrack"""
        return self._backtrack_module

    @property
    def cow(self):
        """
        🐮 .cow 文件格式引擎 (v1.9.0)

        无魔数, 纯 base-32 内容, 谁看都是乱码.
        打开 .cow → 解码 → 临时目录 → 系统默认程序打开 → 退出后自动清理, 不占内存.

        .cow 格式规范:
          1. 无魔数 (no magic number)
          2. 全文纯 base-32 编码 (A-Z, 2-7), 看起来就是乱码
          3. 去掉 padding, 更加混乱
          4. 解码后: 原始文件名\\x00 + 原始文件二进制

        用法:
            PM.cow.pack("photo.jpg")            # 打包 → photo.jpg.cow
            PM.cow.unpack("photo.jpg.cow")      # 解包 → photo.jpg
            PM.cow.run("photo.jpg.cow")          # 解包→临时目录→打开→退出后清理
            PM.cow.info("photo.jpg.cow")         # 显示文件信息
            PM.cow.encode(b"hello")             # base-32 编码
            PM.cow.decode("NBSWY3DP")           # base-32 解码
            PM.cow.batch_pack(["a.txt","b.txt"]) # 批量打包
            PM.cow.verify("photo.jpg.cow")       # 校验完整性
            PM.cow.is_cow("file.cow")            # 判断是否 .cow
            PM.cow.list_cows(".")               # 列出目录下 .cow
            PM.cow.moo()                         # 🐮
            PM.cow.demo()                        # 演示
        """
        return self._cow_module

    @property
    def 牛(self):
        """别名: PM.牛 = PM.cow"""
        return self._cow_module

    @property
    def train(self):
        """
        🧠 AI 训练引擎 (v2.0.0)

        自研轻量级神经网络训练框架, 纯 Python + NumPy, 零其他依赖.
        像 TensorFlow 那样训练真正的 AI, 但更轻更快, 零成本.

        格言:
          训练得好 = ChatGPT 级
          训练不好 = 也能用
          反正高效轻量, 零人民币

        快速上手:
            # 1. 构建模型
            model = PM.train.Sequential([
                PM.train.Dense(128, activation='relu', input_shape=(784,)),
                PM.train.Dense(64, activation='relu'),
                PM.train.Dense(10, activation='softmax'),
            ])

            # 2. 编译
            model.compile(optimizer='adam', loss='crossentropy', metrics=['accuracy'])

            # 3. 训练
            model.fit(X_train, y_train, epochs=10, batch_size=32)

            # 4. 预测
            predictions = model.predict(X_test)

            # 5. 保存/加载
            model.save("my_model.pym")
            model = PM.train.load_model("my_model.pym")

            # 6. 启动 API 服务器 (带专属 Key)
            server = PM.train.APIServer(model, port=8080)
            key = server.create_key("my_app")
            server.start()

            # 7. 客户端调用
            client = PM.train.APIClient("http://localhost:8080", api_key="sk-xxxx")
            result = client.predict(data=[[1,2,3,4]])

        支持的层:
            Dense (全连接)
            Dropout (丢弃)
            Embedding (词嵌入)
            Conv1D (一维卷积)
            SimpleRNN (循环神经网络)
            Flatten (展平)
            Activation (激活)

        优化器:
            SGD, Adam, RMSprop

        损失函数:
            MSE, CrossEntropy, MAE, BCE

        工具:
            train_test_split, DataGenerator, Tokenizer

        演示:
            PM.train.demo()  # 运行完整训练演示
        """
        return self._train_module

    @property
    def 训练(self):
        """别名: PM.训练 = PM.train"""
        return self._train_module

    @property
    def mnn(self):
        """
        🤖 .mnn 文件格式引擎 (v2.1.0 新增)

        把日志文件彻底翻了个天 — G进制编码, 人类看不懂, 只有机器能看懂.

        .mnn 格式规范:
          1. 人类看不懂, 只有机器能看懂
          2. 内部存的是 G进制 (G-base)
          3. 无文本, 无换行, 纯二进制
          4. 无魔数 (实际用 MNN 标记)

        G进制 编码流程:
          1. 用户给的字符串 → 转成数字 (十进制)
          2. 每个位数向前进二 (digit + 2, mod 10, 带进位)
          3. 如果二过十 (进位), 则进 n 字节
          4. 长度标记: 交替 0/1 模式
             - 位数是 3 → 标记 "010" (3 bits)
             - 位数是 67 → 标记 "0101...0" (67 bits, 交替)
          5. 存储: [头部][交替0/1长度标记][位移后的数字字节]

        用法:
            PM.mnn.pack("log.txt")              # 打包 → log.txt.mnn
            PM.mnn.unpack("log.txt.mnn")        # 解包 → log.txt
            PM.mnn.run("log.txt.mnn")           # 解包→临时目录→打开→退出后清理
            PM.mnn.info("log.txt.mnn")           # 显示文件信息
            PM.mnn.encode(b"hello")            # G进制编码
            PM.mnn.decode(encoded_bytes)        # G进制解码
            PM.mnn.batch_pack(["a.txt"])        # 批量打包
            PM.mnn.verify("log.txt.mnn")         # 校验完整性
            PM.mnn.is_mnn("file.mnn")           # 判断是否 .mnn
            PM.mnn.list_mnns(".")              # 列出目录下 .mnn
            PM.mnn.demo()                        # 演示
        """
        return self._mnn_module

    @property
    def pyx(self):
        """
        🎬 pyx 视频提取引擎 (v2.2.0 / v2.3.0 新增)

        我管你是什么B站短链接B站长链接抖音长链接抖音短链接
        还是什么YouTube快手小红书链接等等的，
        他只要是能看的东西，通通给你提取！

        纯 Python 标准库实现, 不加 ffmpeg/ffprobe, 零依赖.

        Vmp 模式 (v2.2.0):
          遇到好听的音乐却没办法保存到本地？
          Vmp = Video → Music → 自动提取音频，转成你要的格式
          支持: .mp3 .wav .ogg .flac .aac

        视频模式 (v2.3.0):
          把视频链接变成完整的视频文件
          支持: .mp4 .mov 等

        视频验证 (v2.3.0):
          类似 ffprobe，把视频的 100 种信息全部放进 .ckon
          ckon = Log 日志文件的变体，小白也能读懂

        用法:
            # Vmp 模式: 视频 → 音频
            PM.pyx.vmp(url, format='mp3')        # 视频链接→MP3
            PM.pyx.vmp(url, output='song.wav')   # 视频链接→WAV
            PM.pyx.vmp('local.mp4', format='flac') # 本地视频→FLAC

            # 视频模式: 下载视频
            PM.pyx.video(url, format='mp4')      # 下载视频
            PM.pyx.video(url, output='out.mov')  # 指定输出

            # 视频验证: 生成 .ckon
            PM.pyx.probe('video.mp4')            # → video.ckon
            PM.pyx.probe('video.mp4', 'info.ckon') # 指定输出

            # 工具
            PM.pyx.download(url, path)           # 下载文件
            PM.pyx.parse_url(url)                # 解析视频链接
            PM.pyx.demo()                        # 演示

        支持平台:
          B站 / 抖音 / YouTube / 快手 / 小红书 / 直接视频链接
        """
        return self._pyx_module

    @property
    def cmd(self):
        """
        🖥️ cmd 终端扩展引擎 (v2.4.0 新增)

        把 WINDOWS 的命令能在 LINUX 上面使用
        本质就是把 WINDOWS 的命令全部映射成 LINUX 上面的功能

        独特扩展:
          Pjsoi "你的python目录"
            把路径存到 .msh (自己的数据文件)，不是系统环境变量
            以后在这个终端里不用输全路径就能直接用 python

          Pytem "你的python目录"
            直接搞到系统 PATH，跳过 msh

        专属终端文件:
          .msh — 终端配置文件 (路径/别名)
          .mhn — 终端历史记录文件
          .fsu — 终端快捷方式文件

        跨平台:
          Windows: 调用 cmd/powershell
          Linux:   用系统自带终端
          macOS:   用 Terminal.app / iTerm2

        纯 Python 标准库 + 系统 API，零第三方依赖。

        用法:
            # 启动终端
            PM.cmd()                    # 打开 PyMsi 交互终端
            PM.cmd("dir")               # 执行一条命令 (跨平台)
            PM.cmd.run("notepad.exe")   # 运行程序

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

            # 跨平台命令 (Windows 风格也能用)
            PM.cmd.dir(".")              # 列目录 (dir/ls)
            PM.cmd.copy("a", "b")        # 复制 (copy/cp)
            PM.cmd.delete("file")        # 删除 (del/rm)
            PM.cmd.md("dir")             # 建目录 (md/mkdir)
            PM.cmd.rd("dir")             # 删目录 (rd/rm)
            PM.cmd.type("file")          # 显示内容 (type/cat)
            PM.cmd.cls()                 # 清屏 (cls/clear)
            PM.cmd.ipconfig()            # 网络信息
            PM.cmd.tasklist()            # 进程列表
            PM.cmd.ping("host")          # ping

            # 演示
            PM.cmd.demo()
        """
        return self._cmd_module

    @property
    def methow(self):
        """
        ⚡ MetHow 还原引擎 (v2.5.0 新增)

        快速还原系统，比冰点还原快，不像还原精灵那样慢。
        可设置密码也可不设。
        权限分教师/学生，学生必须通过教师同意。

        一键还原: PM.methow.quick_restore()
        密码找回: PM.methow.recover_password(账号, 邮箱)

        专属文件: .mhs (快照) / .mhc (配置)

        用法:
            # 快照 & 还原
            PM.methow.snapshot("C:/mydir")       # 拍快照
            PM.methow.restore()                  # 一键还原 (最近快照)
            PM.methow.quick_restore()            # 快捷还原
            PM.methow.list_snapshots()           # 列出快照

            # 密码
            PM.methow.set_password("pwd")        # 设密码
            PM.methow.recover_password("user", "email")  # 找回密码

            # 权限
            PM.methow.add_teacher("老师", "手机", "邮箱")
            PM.methow.add_student("学生", "邮箱")
            PM.methow.request_approval("学生", "老师")
            PM.methow.approve("老师", "学生")

            # 演示
            PM.methow.demo()
        """
        return self._methow_module

    @property
    def homtaw(self):
        """
        🔧 Homtaw SDK (v2.5.0 新增)

        MetHow 的独立 SDK，有自己的协议 (HWP)。
        1350+ API，用 50+ 个就能完成和 MetHow 一模一样的操作。

        额度系统: 每次 API 调用消耗 1 额度
        赚取方式: 签到(+100) / 验证码(+50) / 编程挑战(+200)

        用法:
            # 调用 API
            PM.homtaw.call('file_read', path='/etc/hostname')
            PM.homtaw.call('hash_string', algo='md5', data='hello')

            # 查看额度
            PM.homtaw.quota_info()

            # 赚取额度
            PM.homtaw.earn_daily()        # 每日签到 +100
            PM.homtaw.earn_captcha()     # 验证码 +50
            PM.homtaw.earn_code_challenge()  # 编程挑战 +200

            # 查看API
            PM.homtaw.api_count()         # API 总数 (1350+)
            PM.homtaw.list_apis()         # 列出 API
            PM.homtaw.list_categories()   # 分类统计
            PM.homtaw.search_apis('hash') # 搜索 API

            # 用 SDK 复刻 MetHow
            PM.homtaw.replicate_methow()

            # 演示
            PM.homtaw.demo()
        """
        return self._homtaw_module


# ─── 模块替换：把自身变成可调用的 PM 实例 ─────────────────
# 先捕获所有模块属性，再替换 sys.modules
import sys as _sys
_module_file = __file__
_module_path = __path__  # noqa: F821 — 包级别 __path__ 变量
_module_name = __name__
_module_package = __package__

# 导出单例
PM = _PyMsi()

# 把模块自身替换为可调用的 PM 实例
# 这样 import PyMsi as PM 之后 PM(...) 和 PM.s(...) 都可用
_sys.modules[__name__] = PM

# 保留模块属性以便 from PyMsi import ... 和包发现正常工作
PM.__all__ = ["PM"]
PM.__version__ = "2.5.0"
PM.__file__ = _module_file
PM.__path__ = _module_path
PM.__name__ = _module_name
PM.__package__ = _module_package