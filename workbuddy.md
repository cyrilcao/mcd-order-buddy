# WorkBuddy 开发对话上下文（workbuddy.md）

> 用于核验是否真实使用腾讯 WorkBuddy 智能体开发，参与「麦当劳程序员节创意开发大赛」WorkBuddy 专项奖励。
> 本文件为真实开发记录（已脱敏 Token 为 `${MCD_MCP_TOKEN}`）。

---

## 真实开发记录（节选）

**用户：** 我要参加麦当劳开发者创新挑战赛，基于麦当劳中国 MCP 做一个以"营养达标"为核心的「麦麦点餐搭子」技能——一句话完成 营养 + 价格最优 + 券叠加 + 积分到期提醒 + 一键下单。

**WorkBuddy（我）：** 我先读活动规则与麦当劳 MCP 文档，确定差异化角度：别人只做"省钱"或只做"营养"，我做"营养优先 + 多工具融合"。随后产出 `SKILL.md`（5 种营养模式 + 8 工具编排）+ 全套参赛文件，并把仓库重命名为 `mcd-order-buddy`。

**配置 MCP：** 在 `~/.workbuddy/mcp.json` 写入 `mcd-mcp`（Streamable HTTP，`https://mcp.mcd.cn`，`Authorization: Bearer ${MCD_MCP_TOKEN}`）。

**真实实测（2026-10-09）：** 接通真实 MCP 后，依次调用：
- `now-time-info` → `2026-10-09 20:59:53`（链路通）
- `query-my-account` → 可用积分 0、本月无即将过期（兼容空值）
- `list-nutrition-foods` → 160 条真实营养数据，解析出"控卡≤550 + 高蛋白≥20g"Top10
- `query-nearby-stores` → 上海人民广场 5 家门店（`storeCode 1450713`）
- `query-meals` → 完整菜单含价格（板烧鸡腿堡 `1406` ¥23.5）
- `query-store-coupons` → `data:[]`（当前无券，兼容）
- `calculate-price` → 板烧 + 玉米杯 ¥36.50（单位分，`takeWayList` 提供 `takeWayCode`）
- `create-order` → 按受控红线**未调**（避免真实扣款）

**关键产出：**
- `SKILL.md`：5 模式 + 8 工具编排 + 受控下单 + 合规红线；实测后新增 §4.5 真实 API 行为备注（价格单位分、`takeWayCode` 必需、券/积分空值兼容）。
- `REAL_TEST_REPORT.md`：真实实测报告。
- `real_nutrition_probe.py`：直连真实 MCP 的可复现营养筛选脚本。
- `mcp-config.example.json`：仅含 `${MCD_MCP_TOKEN}` 占位符（合规）。

---

> 提交前请确认：本文件为你在 WorkBuddy 中的真实开发记录，且不含任何真实凭证。
