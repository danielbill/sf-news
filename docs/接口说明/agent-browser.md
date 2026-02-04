
  agent-browser 使用方法总结

  概述

  agent-browser 是 Vercel Labs 开发的一个用于 AI 代理的浏览器自动化 CLI 工具，基于 Rust 和 Node.js，支持无头浏览器操作。

  安装方法

  推荐安装方式

  npm install -g agent-browser
  agent-browser install  # 下载 Chromium 浏览器

  Linux 系统依赖

  agent-browser install --with-deps

  核心使用流程

  1. 基本操作流程

  # 打开网页
  agent-browser open example.com

  # 获取页面快照（推荐AI使用）
  agent-browser snapshot

  # 使用快照中的引用进行交互
  agent-browser click @e2
  agent-browser fill @e3 "test@example.com"

  # 关闭浏览器
  agent-browser close

  2. AI 代理最佳工作流

  # 1. 导航并获取快照
  agent-browser open example.com
  agent-browser snapshot -i --json

  # 2. AI 解析快照中的引用（@e1, @e2等）
  # 3. 使用引用执行操作
  agent-browser click @e2
  agent-browser fill @e3 "input text"

  # 4. 页面变化后重新获取快照
  agent-browser snapshot -i --json

  主要命令分类

  导航命令

  - open <url> - 打开网页
  - back - 后退
  - forward - 前进
  - reload - 刷新

  元素交互

  - click <selector> - 点击元素
  - fill <selector> <text> - 填充文本
  - type <selector> <text> - 输入文本
  - hover <selector> - 悬停
  - scroll <direction> - 滚动

  信息获取

  - get text <selector> - 获取文本
  - get html <selector> - 获取HTML
  - get url - 获取当前URL
  - snapshot - 获取可访问性树快照（带引用）

  页面操作

  - screenshot [path] - 截图
  - pdf <path> - 保存为PDF
  - eval <js> - 执行JavaScript

  选择器类型

  1. 引用选择器（推荐）

  # 从快照中获取引用
  agent-browser snapshot
  # 输出: button "Submit" [ref=e2]

  # 使用引用
  agent-browser click @e2

  2. CSS 选择器

  agent-browser click "#submit"
  agent-browser click ".button"

  3. 语义定位器

  agent-browser find role button click --name "Submit"
  agent-browser find label "Email" fill "test@test.com"

  高级功能

  会话管理

  # 创建独立会话
  agent-browser --session agent1 open site-a.com
  agent-browser --session agent2 open site-b.com

  # 列出活动会话
  agent-browser session list

  持久化配置

  # 使用持久化配置文件
  agent-browser --profile ~/.myapp-profile open myapp.com

  云端浏览器支持

  # Browserbase
  export BROWSERBASE_API_KEY="your-key"
  agent-browser -p browserbase open example.com

  # Browser Use
  export BROWSER_USE_API_KEY="your-key"
  agent-browser -p browseruse open example.com

  iOS 模拟器支持（macOS）

  # 列出可用设备
  agent-browser device list

  # 在iOS模拟器中打开
  agent-browser -p ios --device "iPhone 16 Pro" open example.com

  配置选项
  ┌───────────────────┬──────────────────────────────┐
  │       选项        │             描述             │
  ├───────────────────┼──────────────────────────────┤
  │ --session <name>  │ 使用独立会话                 │
  ├───────────────────┼──────────────────────────────┤
  │ --profile <path>  │ 持久化配置文件目录           │
  ├───────────────────┼──────────────────────────────┤
  │ --json            │ JSON格式输出（适合AI解析）   │
  ├───────────────────┼──────────────────────────────┤
  │ --headed          │ 显示浏览器窗口（非无头模式） │
  ├───────────────────┼──────────────────────────────┤
  │ -i, --interactive │ 仅显示交互元素               │
  ├───────────────────┼──────────────────────────────┤
  │ -c, --compact     │ 紧凑模式                     │
  └───────────────────┴──────────────────────────────┘
  环境变量
  ┌────────────────────────┬───────────────────────────────────────────────┐
  │          变量          │                     描述                      │
  ├────────────────────────┼───────────────────────────────────────────────┤
  │ AGENT_BROWSER_SESSION  │ 默认会话名称                                  │
  ├────────────────────────┼───────────────────────────────────────────────┤
  │ AGENT_BROWSER_PROFILE  │ 默认配置文件路径                              │
  ├────────────────────────┼───────────────────────────────────────────────┤
  │ AGENT_BROWSER_PROVIDER │ 浏览器提供商（browserbase/browseruse/kernel） │
  └────────────────────────┴───────────────────────────────────────────────┘
  集成到 AI 工作流

  在项目中添加指导

  在项目的 CLAUDE.md 或 AGENTS.md 中添加：

  ## 浏览器自动化

  使用 `agent-browser` 进行网页自动化操作：

  1. `agent-browser open <url>` - 导航到页面
  2. `agent-browser snapshot -i --json` - 获取交互元素快照
  3. 使用快照中的引用（@e1, @e2等）进行交互
  4. 页面变化后重新获取快照

  运行 `agent-browser --help` 查看所有可用命令。

  适用场景

  1. AI 代理自动化 - 让 AI 代理能够操作网页
  2. 网页测试 - 自动化测试流程
  3. 数据抓取 - 自动化数据收集
  4. E2E 测试 - 端到端测试
  5. 网页监控 - 定期检查网页状态