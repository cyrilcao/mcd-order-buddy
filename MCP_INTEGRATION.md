# MCP 集成说明（MCP Integration）

## 1. 使用的 MCP Server

| 项 | 值 |
|----|----|
| Server 名称 | `mcd-mcp` |
| 提供方 | 麦当劳中国（金拱门） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权 | 请求头 `Authorization: Bearer <MCP_TOKEN>` |
| 官方入口 | https://open.mcd.cn/mcp |

> 每个 Token 限流 600 次/分钟，编排时需控制调用频次，避免重复拉取同一工具。

## 2. 实际使用的 Tools 与用途（约 8 个）

| # | Tool | 在技能中的角色 |
|---|------|----------------|
| 1 | `now-time-info` | 当前时间，判断早/午/晚/夜宵场景，决定是否提示早餐卡 |
| 2 | `query-meals` | 当前门店可售餐品（分类、编码、标签），作为候选池 |
| 3 | `list-nutrition-foods` | 常见餐品营养成分（能量、蛋白、脂肪、碳水、钠、钙），营养约束数据源 |
| 4 | `query-meal-detail` | 查套餐组成与可替换项，用于"降热量/降钠"的替换建议 |
| 5 | `query-store-coupons` | 当前门店可用优惠券（价格最优） |
| 5b | `available-coupons` / `query-my-coupons` | 麦麦省可领券 / 账户已有券（可选增强） |
| 6 | `calculate-price` | 候选商品列表（+券）算应付，挑更优组合 |
| 7 | `query-my-account` | 查积分账户，重点是 **即将过期积分**，生成到期提醒 |
| 8 | `create-order` | 用户确认后创建订单，返回订单详情与支付链接（一键下单） |
| 9 | `delivery-query-addresses` | **外送专用**：查用户已存配送地址，返回 `addressId`（外卖下单前置） |
| 10 | `delivery-create-address` | **外送专用**：无地址时新建收货地址（city+详细地址+联系人+电话），拿到 `addressId` |
| 11 | `delivery-query-stores` | **外送专用**：用 `addressId` 查可配送门店，返回 `storeCode` + **`beCode`**（外卖后续工具必传） |

> 可选增强：`auto-bind-coupons`（一键领麦麦省券，有副作用，须用户同意）；`query-nearby-stores`（到店场景定位）。外卖三件套（9/10/11）已纳入 SKILL.md §4.1 正式链路，到店场景不调用。

## 3. 调用流程

```
用户自然语言需求（含营养约束 / 预算 / 是否用券 / 是否下单）
   │
   ▼
[澄清目标] 模式 + 餐次 + 预算 + 是否用券 + 是否外送 + 是否直接下单
   │
   ▼
（若用户选「外卖/麦乐送」→ 先走外送链路：delivery-query-addresses 查地址，空则 delivery-create-address 建地址拿 addressId → delivery-query-stores(beType=2) 拿 storeCode+beCode；后续 query-meals/query-store-coupons/calculate-price/create-order 均带 beCode、不传 takeWayCode、create-order 带 addressId。详见 SKILL.md §4.1）
   │
   ▼
now-time-info ──► 判断餐次场景
   │
   ▼
query-meals ──► 候选餐品池
   │
   ▼
list-nutrition-foods ──► 营养数据表
   │
   ▼
[营养优先筛选] 在能量/蛋白/钠/糖约束内枚举单品与套餐替换项
   │
   ▼
query-meal-detail（按需） ──► 套餐内替换建议
   │
   ▼
query-store-coupons / available-coupons / query-my-coupons ──► 最优券
   │
   ▼
calculate-price ──► 原价 vs 优惠后价（保留 Top 2–3）
   │
   ▼
query-my-account ──► 即将过期积分提醒
   │
   ▼
输出方案（营养明细 + 价格 + 省钱 + 积分提示 + 小贴士）
   │
   ▼
[用户确认 "下单"] ──► create-order ──► 订单号 + 支付链接
```

## 4. 业务价值

- **对健康人群**：把"想吃麦当劳但怕不健康"的纠结，变成可量化的营养方案（核心差异点）。
- **对省钱人群**：自动叠加最优券，价格透明。
- **对积分党**：到期前提醒，避免积分白白蒸发（融合积分理财思路）。
- **对品牌**：正向引导"均衡地吃、聪明地花"，契合麦当劳透明营养信息，提升点餐体验。
- **对开发者**：示范「营养数据 × 实时菜单 × 优惠 × 积分 × 下单」的多工具编排范式。

## 5. 配置示例

见 `mcp-config.example.json`（仅含 `${MCD_MCP_TOKEN}` 环境变量占位符，不含任何真实 Token）。
