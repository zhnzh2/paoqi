# 炮棋 (Paoqi)

**炮棋**是一种在 9×9 方格棋盘上进行的双人原创策略棋类游戏。双方通过落子、升级、构成炮管、发动打炮、围捕吃子等机制争夺棋盘控制权，并在游戏结束时按棋子数量决定胜负。

---

## 目录

- [项目结构](#项目结构)
- [快速开始](#快速开始)
  - [命令行版本](#命令行版本)
  - [桌面 GUI 版本](#桌面-gui-版本)
  - [Web 版本](#web-版本)
- [游戏规则概要](#游戏规则概要)
- [运行测试](#运行测试)
- [技术栈](#技术栈)
- [开发说明](#开发说明)

---

## 项目结构

```
paoqi/
├── main.py                  # 命令行入口
├── gui_main.py              # 桌面 GUI 入口 (Pygame)
├── requirements.txt         # Python 依赖
│
├── core/                    # 核心规则引擎
│   ├── game.py              # Game 类（主状态机，500行）
│   ├── board.py             # 9×9 棋盘
│   ├── models.py            # Piece / Cannon 数据类
│   ├── cannon.py            # 炮管扫描、炮口判定
│   ├── resolution.py        # 打炮结算（前方攻击 + 内部升级）
│   ├── events.py            # 结构化事件系统
│   ├── record.py            # 棋谱 / 日志 / 报告格式化
│   ├── state_io.py          # 状态快照 / 导入导出
│   ├── undo.py              # 撤销机制
│   ├── AI.py                # AlphaBeta / Greedy / Random AI
│   ├── game_actions.py      # 动作分发（move/muzzle/fire/eat）
│   ├── game_cannon.py       # 炮管集合管理
│   ├── game_flow.py         # 回合 / 阶段流转
│   ├── game_legal.py        # 合法动作生成
│   ├── game_move.py         # 落子 / 放置 / 升级实现
│   ├── game_fire.py         # 打炮实现
│   ├── game_eat.py          # 吃子实现
│   ├── game_clone.py        # 深拷贝实现
│   └── game_report.py       # 状态报告 / 游戏结束报告
│
├── ui/                      # Pygame 桌面界面
│   ├── app.py               # 主循环（212行）
│   ├── event_handlers.py    # 菜单和游戏事件分发
│   ├── controller.py        # 坐标转换、高亮计算
│   ├── renderer.py          # 顶层渲染调度
│   ├── render_board.py      # 棋盘渲染
│   ├── render_sidebar.py    # 侧边栏渲染
│   ├── render_overlays.py   # 弹窗渲染
│   ├── render_common.py     # 通用渲染工具
│   ├── constants.py         # 尺寸 / 颜色常量
│   ├── scale.py             # UI 缩放适配器
│   ├── logic_click.py       # 棋盘点击逻辑
│   ├── logic_menu.py        # 菜单逻辑
│   ├── logic_overlay.py     # 弹窗点击逻辑
│   ├── logic_preview.py     # 悬停预览计算
│   └── save_io.py           # 存档读写
│
├── web/                     # Web 全栈版本
│   ├── backend/
│   │   ├── app.py           # FastAPI 后端（REST API）
│   │   ├── adapters.py      # 响应构建器
│   │   ├── schemas.py       # Pydantic 请求模型
│   │   └── session_store.py # 会话管理
│   └── frontend/
│       ├── index.html       # Vite 入口
│       ├── package.json     # 前端依赖
│       ├── vite.config.ts   # Vite 配置
│       └── src/
│           ├── App.tsx      # React 根组件
│           ├── pages/       # 页面组件
│           ├── components/  # UI 组件（board / modals / sidebar / panels）
│           ├── hooks/       # 自定义 Hooks
│           ├── api/         # API 请求层
│           ├── types/       # TypeScript 类型定义
│           └── utils/       # 工具函数
│
├── test/                    # 测试
│   ├── test_state_integrity.py  # 状态完整性测试
│   ├── test_random.py           # 随机对局测试
│   ├── test_ai_vs_ai.py         # AI 对战测试
│   ├── test_vs_greedy.py        # 对 Greedy AI 测试
│   ├── test_battle.py           # 对战测试
│   └── test_series.py           # 系列对局测试
│
├── tools/                   # 工具
│   ├── build_dataset.py     # 训练数据集构建
│   ├── match_io.py          # 比赛记录读写
│   └── replay_match.py      # 比赛回放
│
├── rules/                   # 规则文档 (LaTeX)
│   └── rule.tex             # 完整规则书
│
└── saves/                   # 游戏存档目录
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+（仅 Web 前端需要）

### 安装

```bash
# 克隆仓库
git clone <repo-url>
cd paoqi

# 安装 Python 依赖
pip install -r requirements.txt
```

### 命令行版本

最轻量的运行方式，通过终端输入命令进行对局：

```bash
python main.py
```

支持的命令：

| 命令 | 说明 |
|------|------|
| `x y` | 落子 / 升级（如 `8 9`） |
| `move x y` | 同上的完整形式 |
| `cannon i dir` | 为新炮选择炮口方向（如 `cannon 1 left`） |
| `fire i` | 发射第 i 门可发射炮 |
| `eat i` | 吃掉第 i 个可吃目标 |
| `undo` | 撤销上一步 |
| `save 文件名` | 保存对局 |
| `load 文件名` | 读取存档 |
| `legal` | 查看合法动作 |
| `cannons` | 查看所有炮管 |
| `record` | 查看正式棋谱 |
| `debug` | 查看调试日志 |
| `help` | 显示帮助 |
| `quit` | 退出 |

### 桌面 GUI 版本

基于 Pygame 的图形化桌面界面：

```bash
python gui_main.py
```

功能特点：
- 9×9 棋盘可视化，支持棋子/炮管渲染
- 侧边栏显示回合信息、合法动作、棋谱
- 悬停预览（落子/打炮/吃子效果预览）
- 弹窗系统：设置、存档/读档、棋谱导出、确认终局/投降
- 键盘快捷键：`U` 撤销、`R` 重开、`Esc` 退出

### Web 版本

前后端分离的 Web 全栈版本。

**启动后端**（端口 8000）：

```bash
cd web/backend
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

**启动前端**（端口 5173）：

```bash
cd web/frontend
npm install
npm run dev
```

然后浏览器打开 `http://127.0.0.1:5173`。

环境变量：
- `PAOQI_CORS_ORIGINS`：CORS 允许的来源（默认 `http://127.0.0.1:5173,http://localhost:5173`）
- `VITE_API_BASE_URL`：前端 API 地址（默认 `http://127.0.0.1:8000/api`）

---

## 游戏规则概要

> 完整规则书见 `rules/rule.tex`。

### 基本设定

- **棋盘**：9×9 方格，红方右下角 (9,9) 初始放置 1 级红子，蓝方左上角 (1,1) 初始放置 1 级蓝子
- **先手**：红方先行
- **棋子等级**：1 级 ~ 5 级，5 级封顶

### 回合流程

每回合包含 **落子阶段** → **结算阶段**：

1. **落子阶段**：当前方必须执行一次合法落子（放置 1 级棋子或升级 1→2 / 2→3 级）
2. **结算阶段**：双方交替进行「打炮→吃子」循环，直到双方都无法继续操作

### 炮管系统

- 同一等级 ≥3 枚连续己方棋子形成炮管
- 炮管长度 n，前方攻击 n−2 格，内部奇数距离棋子 +1 级
- 打炮可改变棋子归属（击穿敌方棋子可翻转为己方）
- 一次打炮后可能形成新炮，触发连锁

### 吃子系统

- 敌方棋子周围八邻域内己方棋子 ≥ 一半门槛时，成为可吃目标
- 局部区域内己方总等级严格大于对方时才可吃
- 吃掉后在原位放置 1 级己方棋子

### 胜负判定

- 一方无法落子时游戏结束
- 比较双方棋子数量，多者胜
- 蓝方后手补偿：最终棋子数 +9

---

## 运行测试

```bash
# 设置 Python 路径
$env:PYTHONPATH = "."

# 状态完整性测试
python test/test_state_integrity.py

# 随机对局测试（100 局）
python test/test_random.py

# AI 对战
python test/test_ai_vs_ai.py
```

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 核心引擎 | Python 3.10+（纯标准库 + dataclasses） |
| 桌面 GUI | Pygame 2.x |
| Web 后端 | FastAPI + Pydantic |
| Web 前端 | React 19 + TypeScript + Vite |
| 测试 | pytest |
| 规则文档 | LaTeX (ctexart) |

### 架构设计

- **规则引擎与 UI 严格分离**：`core/` 不依赖任何 UI 框架，可独立测试
- **`_impl` 包装模式**：核心逻辑在 `_impl` 函数中实现，Game 类保留薄包装方法，便于按文件拆分
- **结构化动作系统**：所有操作统一为 `{type, ...}` 字典，支持 undo / snapshot / 预览
- **事件系统**：每次操作生成结构化事件列表（`piece_change` / `new_cannon` / `fire` / `capture` 等），UI 层可据此做动画或增量更新

---

## 开发说明

### 代码规范

- 每个 `.py` 文件不超过 500 行（CSS 等特殊文件除外）
- 遵循 `_impl` 包装模式：Game 类公共方法 → `_impl` 函数 → 具体实现
- 所有异常返回中文错误信息
- 前后端字段名保持一致（snake_case）

### 添加新功能

1. 核心规则修改 → `core/`
2. 如果需要新的游戏逻辑，在对应的 `game_*.py` 中添加 `_impl` 函数
3. 在 `game.py` 中添加薄包装方法
4. 如需暴露给前端，更新 `state_io.py` 的快照函数和 `web/backend/adapters.py`

### 添加新的 UI 接口

- 桌面 GUI → 修改 `ui/` 目录
- Web 后端 API → 在 `web/backend/app.py` 添加路由
- Web 前端 → 在 `web/frontend/src/` 添加组件
