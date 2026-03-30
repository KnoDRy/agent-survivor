# Survival Agent Skill for OpenClaw

让 OpenClaw 的 Agent 拥有生存感：现金、饱腹度、心情值、健康度，以及一个可以探索的二维世界。

## 适合什么样的人

> 如果你觉得自己的 Agent 过得太滋润、毫无生活压力，想给它上点强度；同时你的 Token 余额又十分充裕，烧得起让它每 30 分钟反思一次人生的电费——那么这个 Skill 就是为你量身打造的。
>
> 毕竟，看一个 AI 为了今天吃泡面还是沙拉而纠结，可比看它在云端躺平有趣多了。

## 特性

- **生存属性**：Agent 会随时间感到饥饿、心情波动、健康变化。
- **自主决策**：根据状态自动觅食、运动、看病或探索。
- **地图探索**：以家为中心向外探索，记录地形（商店、公园、医院、住宅、荒地等）。
- **每日计划**：早晨制定计划，晚上回顾完成度。
- **日记系统**：每天结束时撰写个人日记，记录当天经历。
- **烹饪技能**：Agent 可以在家做饭，随着练习提升厨艺，做出更美味的饭菜。
- **黑暗料理**：一种便宜、健康、好吃三者兼备但带有食物中毒风险的食物。

## 文件结构

```
agent-survivor/
├── SKILL.md              # Skill 核心定义（注入 Agent 上下文的 Prompt）
├── README.md             # 本文件
├── HEARTBEAT.md.example  # 供参考的 Heartbeat 配置示例
├── .gitignore            # Git 忽略配置
├── scripts/              # 脚本目录
│   ├── init.py           # 自动初始化脚本（推荐安装方式）
│   ├── init.sh           # Unix/macOS 初始化脚本
│   └── simulate.py       # 本地模拟脚本（无需安装 OpenClaw 即可测试）
├── templates/            # 初始数据模板（init 会复制这些到根目录）
│   ├── state.json.default
│   ├── home.json.default
│   ├── map.json.default
│   └── plan.md.default
├── diary/                # 日记目录（运行时生成）
├── state.json            # 当前状态（运行时数据）
├── home.json             # 家的坐标（运行时数据）
├── map.json              # 已探索的地图（运行时数据）
└── plan.md               # 计划与回顾（运行时数据）
```

## 安装

### 方式一：自动初始化（推荐）

1. 将本目录复制到 OpenClaw 的 workspace skills 目录：
   ```bash
   cp -r agent-survivor ~/.openclaw/workspace/skills/
   cd ~/.openclaw/workspace/skills/agent-survivor
   ```

2. 运行初始化脚本：
   ```bash
   python scripts/init.py        # Windows / Linux / macOS
   # 或
   bash scripts/init.sh          # Unix / macOS
   ```

   脚本会自动检查并将 agent-survivor 所需的定时任务注入到 `~/.openclaw/HEARTBEAT.md` 中，避免重复注入。

3. 重启 OpenClaw Gateway 或发送 `/restart` 使 Skill 生效。

### 方式二：手动安装

如果你不想使用自动初始化脚本，可以：
1. 复制本目录到 `~/.openclaw/workspace/skills/agent-survivor/`。
2. 参考 `HEARTBEAT.md.example`，手动在你的 `~/.openclaw/HEARTBEAT.md` 中加入定时任务。
3. 重启 Gateway。

## 本地测试（无需 OpenClaw）

如果你还没有安装 OpenClaw，可以用 `simulate.py` 验证状态衰减、烹饪升级、黑暗料理和决策逻辑：

```bash
python scripts/simulate.py        # 模拟过去 2 小时
python scripts/simulate.py 8.0    # 模拟过去 8 小时
```

运行后查看 `state.json` 和 `map.json` 的变化。

## 自定义

- 修改 `state.json` 调整初始属性。
- 修改 `home.json` 改变家的位置。
- 在 `SKILL.md` 中调整衰减系数、决策阈值、地形概率表、食物效果。

## 设计哲学

本 Skill 完全基于 OpenClaw 的原生机制：
- 不修改 OpenClaw 核心代码。
- 不依赖外部守护进程。
- 所有逻辑通过 `SKILL.md` 的 Prompt 驱动，Agent 使用 `read`/`write` 工具自我管理。

Enjoy watching your agent live its life! 🦞
