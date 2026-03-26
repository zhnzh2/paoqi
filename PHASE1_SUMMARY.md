# 炮棋 AI 第一阶段总结

## 本阶段目标

完成从“已有游戏引擎”到“可用于 AI 搜索、自博弈、日志记录、训练数据生成”的基础框架搭建。

---

## 已完成内容

### 1. 环境接口
已完成以下核心接口：

- `clone()`
- `is_terminal()`
- `get_winner()`
- `get_legal_actions()`
- `apply_action()`

这意味着当前游戏已经可以被 AI 直接调用，而不再依赖人工输入。

---

### 2. 基础 AI
已实现三类对手：

- `RandomAgent`
- `GreedyAgent`
- `AlphaBetaAgent`

其中 `AlphaBetaAgent` 已支持：

- 评估函数
- Alpha-Beta 搜索
- 动作排序
- 同分随机打破平局
- 搜索日志输出（verbose）

---

### 3. 自动测试
已实现多种测试脚本：

- `test_battle.py`
- `test_series.py`
- `test_random.py`
- `test_vs_greedy.py`
- `test_ai_vs_ai.py`

支持：

- AI vs Random
- AI vs Greedy
- AI vs AI
- 步数上限自动结算

---

### 4. 对局日志
已实现：

- 自动保存每局结果到 json
- 保存终局棋盘
- 保存完整棋谱
- 保存动作列表 `action_log`
- 保存训练样本 `training_samples`

相关文件：

- `match_io.py`
- `replay_match.py`

---

### 5. 训练数据
已实现：

- 从对局日志中提取训练样本
- 棋盘字符串编码 `board`
- 棋盘数值编码 `board_numeric`
- 动作特征提取
- 动作统一编码 `action_code`
- 数据集汇总 `build_dataset.py`
- 数据集检查 `inspect_dataset.py`

输出目录：

- `match_logs/`
- `datasets/`

---

## 当前阶段产物

### 已有代理
- 随机代理
- 贪心代理
- Alpha-Beta 搜索代理

### 已有日志能力
- 单局日志
- 棋谱回放
- 训练样本生成

### 已有数据能力
- 样本筛选
- 动作编码
- 状态编码
- 数据集统计检查

---

## 当前阶段结束标志

第一阶段的目标可以视为已经完成：

- 已具备可运行的搜索 AI
- 已具备自动化对局与日志保存
- 已具备训练数据导出能力

---

## 下一阶段方向

下一阶段重点可放在以下方向之一：

### 方向 A：继续强化搜索 AI
- 优化评估函数
- 增加更强对手
- 加缓存或其他搜索优化

### 方向 B：进入学习阶段
- 使用已有数据集进行 imitation learning
- 训练策略模型预测动作
- 之后考虑 self-play / RL

### 方向 C：可视化与分析
- 做逐手回放
- 做局面分析工具
- 做对局复盘界面

---

## 推荐下一步

优先建议进入“学习阶段”：

1. 固定数据格式
2. 导出更稳定的数据集
3. 做第一个简单策略模型
4. 测试模型能否模仿 Alpha-Beta 的走法