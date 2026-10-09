# WorkBuddy 真实开发对话上下文（workbuddy.md）

> 本文件用于核验是否真实使用 **腾讯 WorkBuddy 智能体**完成开发，参与「麦当劳程序员节创意开发大赛」WorkBuddy 专项奖励。
> 以下为在 WorkBuddy 中**真实发生的开发 + 使用会话记录**（已脱敏 Token / 手机号 / 家庭地址，与现实仓库 `SKILL.md` 的脱敏口径一致）。
> MCP 鉴权统一记为 `${MCD_MCP_TOKEN}`，端点 `https://mcp.mcd.cn`。

---

## 0. 背景与参赛定位

**用户：** 我要参加麦当劳开发者创新挑战赛（基于麦当劳中国 MCP）。帮我思考从哪些角度做 Skill 更适合麦当劳。

**WorkBuddy（我）：** 先读活动规则与 `README.md`（MCP 文档）。关键约束：
- 排行榜**只看 GitHub Star**，Star=0 不进榜，前 100 进获奖池；同一账号只取 Star 最高的一项。
- WorkBuddy 是官方合作伙伴，提交本文件可额外拿 3000 积分。

**差异化决策：** 别人只做"省钱"或只做"营养"，我做 **"营养达标为核心 + 价格最优 + 券叠加 + 积分到期提醒 + 受控一键下单"的融合型 Skill**（hero skill）。用户画像（控卡/金融 ROI/宝妈亲子）正好命中 MCP 最冷门也最具差异化的工具簇。最终定名 **`麦麦点餐搭子`（mcd-order-buddy）**。

---

## 1. 技能产出（在 WorkBuddy 内完成）

产出全套文件：`SKILL.md`（8 工具编排 + 5 营养模式 + 受控下单 + 合规红线）、`README.md`、`MCP_INTEGRATION.md`、`mcp-config.example.json`（仅 `${MCD_MCP_TOKEN}` 占位）、`CONTEST_DECLARATION.md`（官方原文未改）、`REAL_TEST_REPORT.md`、两个可复现测试脚本。

**配置 MCP：** 在 `~/.workbuddy/mcp.json` 写入 `mcd-mcp`（Streamable HTTP，`https://mcp.mcd.cn`，`Authorization: Bearer ${MCD_MCP_TOKEN}`），并把 `SKILL.md` 装入 `~/.workbuddy/skills/mcd-order-buddy/`。

---

## 2. 真实 MCP 实测（2026-10-09，全部为真实调用）

接通后依次调用（Token 脱敏）：

| 工具 | 真实返回（节选） | 验证点 |
|---|---|---|
| `now-time-info` | `2026-10-09 20:59:53 (GMT+08:00)` | 链路通、鉴权生效 |
| `query-my-account` | 可用 0 / 累计 868.7 / **本月即将过期 0** | ⚠️ 积分可能为空，提醒需兼容 |
| `list-nutrition-foods` | **160 条真实营养数据** | 核心数据源 |
| `query-nearby-stores` | 上海人民广场 5 家（`storeCode 1450713`…） | 拿 storeCode |
| `query-meals` | 完整菜单含价格（板烧鸡腿堡 `1406` ¥23.5） | 价格最优数据源 |
| `query-store-coupons` | `data:[]` | ⚠️ 当前无券，已做兼容 |
| `calculate-price` | 板烧+玉米杯 = `3650` 分 = ¥36.50，返回 `takeWayList` | 价格单位=**分**；`takeWayCode` 下单必需 |
| `create-order` | 按受控红线**未调**（避免无确认扣款） | 安全合规 |

**真实营养筛选（用官方 160 条数据）：** "控卡≤550kcal + 高蛋白≥20g" Top 项：蜜汁BBQ薄皮脆汁鸡-带骨里脊（152kcal/20g蛋白/5g脂肪）、果然多肉（478/36）、麦麦脆汁鸡-带骨里脊（332/22）、双层板烧麦满分（355/23）、双层吉士汉堡（429/27）。

> 实测后把发现固化进 `SKILL.md` §4.5「真实 API 行为备注」：价格单位=分、`takeWayCode` 必需、券/积分空值兼容。

---

## 3. 真实用户使用会话（在同一 WorkBuddy 对话内）

### 3.1 营养优先点餐
**用户：** 我想吃减肥餐（门店：上海人民广场 → 后改为 普陀区中环百联）

**我：** 把"减肥餐"重述为营养学更稳妥的"低热量 + 高蛋白 + 抗饿"控卡均衡餐（正向话术，不踩"少吃/发胖羞耻"合规红线）。真实链路：
1. `query-nearby-stores`（中环百联）→ `storeCode 1450319`（真光路1288号，营业至 22:00）
2. `query-meals` + `query-store-coupons`（该店无券）→ `calculate-price` 锁定两套真实到手价：
   - **方案A 轻盈版**：麦麦脆汁鸡 `9900005432` + 玉米杯 `4437` + 可乐 `9900008751` = **¥37.5**（discount 0）
   - **方案B 均衡版**：板烧鸡腿堡 `1406` + 玉米杯 `4437` + 可乐 = **¥46**
3. 输出带营养明细 + 到手价 + 取餐方式（`eat-in` 堂食 / `take-in-store` 外带），**不下单**（受控）。

### 3.2 切换麦乐送外卖（双链路实测）
**用户：** 我要点外卖。

**我：** 加载 `delivery-*` 工具，按写入技能的外卖链路执行：
1. `delivery-query-addresses` → `addresses:[]`（真实账号无地址）
2. `delivery-create-address`（用户提供脱敏信息：城市上海、地址、联系人、电话 `135****0798`）→ 拿到 `addressId`
3. `delivery-query-stores`（beType=2）→ 3 家可配送门店，选 `1450077`（beCode `145007702`，营业至 23:59）
4. `query-meals`（orderType=2）→ **关键发现：外卖商品 code 与到店完全不同**（脆汁鸡到店 `9900005432` → 外卖 `9900003021`；玉米杯 `4437`→`904437`；可乐 `9900008751`→`903071`），旧 code 算价报"不可售"
5. 用外卖 code 重算：`calculate-price` → 方案A ¥49.10（含配送¥6+打包¥1.6）、方案B ¥59.90

### 3.3 地址地理编码坑 & 修复（真实 Bug 闭环）
**用户：** 我的地址是 某小区 X 号 Y 室，你没有楼栋号，真实地址对么？

**我：** 复查发现 `delivery-create-address` 会对 `address` 字段做地理编码标准化，**把楼栋号"X号"吞掉了**（回写成"…某路 1-129 号(某小区) Y室"，楼栋号丢失）。
- **根因：** `address` 街道字段被标准化，楼栋号丢失；`addressDetail` 门牌字段原样保留。
- **修复：** 把楼栋号写进 `addressDetail`（`address="某小区"` + `addressDetail="X号Y室"` → 回写"…某小区[地铁站]X号Y室"，**"X号"保住**），新建地址并验证可解析出可配送门店。
- **固化：** 此坑 + 绕过法已写入 `SKILL.md` §4.1 建地址步骤 + §4.5。

### 3.4 预算约束再算价
**用户：** 太贵了，我要 30 元以内的套餐。

**我：** 从真实外卖菜单（119 个餐品）筛价，并 `calculate-price` 实测：标准套餐最低"辣么快乐套餐"¥28.5，但外卖配送¥6+打包¥1.6 → 到手 ¥36.4，**超 30**；唯有轻食小吃组合可到手 ≤30：
- **方案①（达标）蘸蘸炸鸡 `9900016511` ¥12.9 + 苹果片 `906102` ¥7.5** → 小计 ¥20.4 + 配送打包 ¥7.6 = **实付 ¥28.0** ✅
- 方案②③到手 ¥36~37，超预算。

### 3.5 真实下单（受控，用户明确确认）
**用户：** 下单1。

**我：** 仅在用户明确说"下单1"后调 `create-order`（beType=2/orderType=2/beCode `145007702`/storeCode `1450077`/`addressId`=新地址/**不传 takeWayCode**）：
- **订单号** `103*********88`（真实订单号已隐藏）
- **实付 ¥28.0**（真·30 以内 ✅）
- **配送地址落单为"某小区[地铁站] X号Y室"** —— 证明上一轮地址纠错生效，楼栋号"X号"真实保留 🎉
- 支付截止 `2026-10-09 22:01:23`，返回支付链接 `https://m.mcd.cn/mcp/scanToPay?orderId=...`

> 受控红线全程遵守：仅用户明确确认才调 `create-order`，绝不默认代下。技能到店 + 外卖双链路均端到端真实跑通。

---

## 4. 参赛提交（在 WorkBuddy 内执行）

**我：** 完成"推送 git + 发 Public + 发 Issue 报名"：
1. 推送前**安全清理**：清除 `real_nutrition_probe.py` 硬编码 Token（改读本地 `mcp.json`/环境变量）、`SKILL.md` 真实街道小区泛化为虚构示例、远程地址去 token 化。
2. `git init -b main` + commit（10 文件）→ 经 API 创建公开仓库 `cyrilcao/mcd-order-buddy`（`private=False` 已核验）→ `git push -u origin main`。
3. 在官方仓库 `M-China/mcd-developer-innovation-challenge` 提交参赛 Issue（按模板 `【参赛申请】/项目名称/项目地址/项目简介`），Issue #122 创建成功。

---

## 5. 本次 `workbuddy.md` 升级说明

本文件由"示例占位"升级为**真实会话记录**，覆盖：设计定位 → 技能产出 → 真实 MCP 实测（7/8 工具）→ 真实用户使用（营养筛选、门店定位、外卖双链路、地址 geocoding 修复、预算约束、真实下单）→ 参赛提交。所有凭证/手机号/家庭地址均已脱敏，与仓库内 `SKILL.md` 口径一致。

> 提交前请确认：本文件为你在 WorkBuddy 中的真实开发与使用记录，且不含任何真实凭证。
