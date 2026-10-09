---
name: mcd-order-buddy
description: 麦麦点餐搭子 —— 基于麦当劳中国 MCP 的一站式点餐助手。以"营养达标"为核心，一句话需求即可完成 营养达标 + 价格最优 + 券自动叠加 + 积分到期提醒 + 一键下单 的全链路，支持到店自取与麦乐送外卖两种场景。当用户说"帮我点份麦当劳/麦麦、控卡又便宜、热量别超XX、蛋白高点、用券最划算、顺便看看快过期的积分、直接下单/点外卖送到家"时使用。触发词：麦当劳、麦麦、点餐、下单、点外卖、送到家、麦乐送、控卡、热量、蛋白、优惠券、积分、最划算。
agent_created: true
---

# 麦麦点餐搭子（McDonald's Order Buddy · 营养优先的一站式点餐助手）

## 1. 概述

本技能是面向 **麦当劳中国 MCP（`mcd-mcp`）** 的一站式点餐决策 + 执行 Skill。**以"营养达标"为核心差异点**，让一句自然语言需求同时完成五件事：

1. **营养达标** —— 在用户设定的能量 / 蛋白 / 钠 / 糖约束内搭餐（融合 ① 营养膳食）。
2. **价格最优** —— 在可行组合里挑最便宜的（融合 ② 省钱）。
3. **券自动叠加** —— 找出门店券 / 麦麦省券最优组合并算价（融合 ②）。
4. **积分到期提醒** —— 下单前提示"即将过期积分"，建议顺手用掉（融合 ③ 积分）。
5. **一键下单** —— 用户确认后调用 `create-order` 生成订单与支付链接。

**支持两种订单方式（务必先判定）：**
- **到店自取（beType=1, orderType=1）**：用户说"去店里/自取/外带"。
- **麦乐送外卖（beType=2, orderType=2）**：用户说"点外卖/送到家/麦乐送/配送"。两套链路参数差异大，详见 §4.1。

**定位原则（务必遵守）：**
- 正向、倡导"均衡地吃、聪明地花"，**不贬低**麦当劳产品，不与任何友商对比。
- 营养数据仅作信息参考，**不构成医疗 / 营养专业诊断**；特殊疾病或严格医嘱请提示遵医嘱。
- 餐品、价格、供应、积分均以麦当劳官方 MCP 实时返回为准。
- **下单是高危动作**：必须等用户明确确认后才调用 `create-order`，绝不默认代下单（到店与外卖一致）。

## 2. 适用人群

| 人群 | 默认偏好 |
|------|----------|
| 健身 / 减脂期 | 控卡、高饱腹 |
| 增肌期 | 高蛋白、能量可控 |
| 控糖 / 控钠人群 | 低糖饮品、避开高钠 |
| 精打细算党 | 券叠加、价格最优 |
| 积分党 | 即将过期积分提醒 |
| 懒人 / 打工人 | 一句话搞定点单（到店或外卖） |

## 3. 核心模式（营养约束，可在对话中覆盖）

| 模式 | 默认营养约束 |
|------|--------------|
| 控卡 | 单餐能量 ≤ 550 kcal，优先高饱腹 |
| 高蛋白 | 蛋白 ≥ 30 g，能量尽量可控 |
| 低钠 | 钠尽量低，提示高钠陷阱 |
| 控糖 | 优先无糖饮品，避免甜品叠加 |
| 均衡 | 能量 + 蛋白 + 钠"中等偏好"，强调搭配多样性 |

## 4. 工具编排（必须走麦当劳 MCP，约 8 个 Tool）

调用顺序（按需，注意 600 次/分钟限流，避免重复拉同一工具）：

1. `now-time-info` —— 当前时间，判断早 / 午 / 晚 / 夜宵场景（是否早餐卡可用）。
2. `query-meals` —— 当前门店可售餐品（分类、餐品编码、标签），作为候选池。
3. `list-nutrition-foods` —— 常见餐品营养成分（能量、蛋白、脂肪、碳水、钠、钙），营养约束的数据源。
4. `query-meal-detail` —— 查套餐组成与可替换项，用于"降热量 / 降钠"的替换建议。
5. `query-store-coupons` / `available-coupons` / `query-my-coupons` —— 找可用优惠（价格最优）。
6. `calculate-price` —— 候选商品列表（+ 券）算应付，挑更优组合。
7. `query-my-account` —— 查积分账户，重点是 **即将过期积分**，生成到期提醒。
8. `create-order` —— 用户确认后创建订单，返回订单详情与支付链接（一键下单）。

> 可选增强：`auto-bind-coupons`（一键领麦麦省券，有领券副作用，**必须用户同意**后再调用）；`query-nearby-stores`（到店场景定位门店）；`delivery-query-addresses` / `delivery-create-address` / `delivery-query-stores`（**外送场景**下先查/建地址、再查可配送门店，详见 §4.1）。

### 4.1 外卖模式（麦乐送 beType=2）完整链路

当用户说"点外卖 / 送到家 / 麦乐送 / 帮我配送"时，走**外送链路**，与到店自取（beType=1）参数完全不同，务必区分：

#### 订单方式参数矩阵（到店 vs 外卖）

| 维度 | 到店自取（beType=1） | 麦乐送外卖（beType=2） |
|------|----------------------|------------------------|
| orderType | 1 | 2 |
| beCode | 不传 | **必传**，来源 `delivery-query-stores` |
| 门店来源 | `query-nearby-stores`(searchType=2) | `delivery-query-stores`(addressId) |
| 地址 | 不需要 | **必传 `addressId`**（先查/建地址） |
| takeWayCode | **必传**（取自 `calculate-price` 的 takeWayList） | **不传** |
| remark | 不填 | 选填（≤50字，如"无接触配送"） |
| 配送费 | 无 | 含在 `calculate-price` 结果中 |

#### 外卖链路步骤（beType=2, orderType=2）

1. **取 / 建配送地址**：
   - 先 `delivery-query-addresses` 查已有地址；
   - 返回 `data.addresses:[]` 时，**必须先 `delivery-create-address`**（city + 详细地址 + 联系人 + 电话）建地址，拿到 `addressId` 才能继续。建地址是写操作，需用户给出真实收货信息后再调。
   - ⚠️ **建地址时务必让用户提供楼栋号，并把楼栋号写进 `addressDetail`**（如 `addressDetail="94号501室"`），不要把楼栋号只放 `address` 字段——`address` 会被地理编码标准化而吞掉楼栋号（详见 §4.5）。建完用 `delivery-query-addresses` 复查 `fullAddress` 是否含楼栋号。
2. **查可配送门店**：`delivery-query-stores`(beType=2, addressId) → 返回可配送门店列表，取目标门店的 `storeCode` + **`beCode`**（后续必传）。
3. **拉外卖菜单**：`query-meals`(orderType=2, beType=2, storeCode, **beCode**)。
4. **查外卖券**：`query-store-coupons`(orderType=2, beType=2, storeCode, **beCode**)。
5. **算外卖到手价**：`calculate-price`(orderType=2, beType=2, storeCode, **beCode**, items) —— 返回价已含配送费，单位"分"需 ÷100。
6. **用户确认 → 下单**：`create-order`(orderType=2, storeCode, **beCode**, **addressId**, items；可选 remark)。**同样遵循受控红线：未确认不下单。**

> ⚠️ 外卖链路任何一步缺 `beCode` 或 `addressId` 都会报错；到店链路的 `takeWayCode` 在外卖场景下**不要传**。

## 4.5 真实 API 行为备注（实测校准）

下列为接通真实 `mcd-mcp` 后确认的行为，编排与解析务必遵守：

- **`list-nutrition-foods`**：返回文本被 "API Response Information … ## Original Response … {json}" 包装；真实数据在 json 的 `data` 字符串里，格式为 `[N]{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}:` 头 + 多行 `名称,描述,能量Kj,能量Kcal,蛋白,脂肪,碳水,钠,钙`。程序化解析需先取 `data` 字段再按行切分（首列名称为中文，第 4 列 `energyKcal`、第 5 列 `protein`）。
- **`calculate-price`**：返回的 `productPrice / originalPrice / discount / price` 等**单位均为"分"**，展示给用户时必须 ÷100 转"元"。同时返回 `takeWayList`（如 `eat-in 堂食` / `locker-out 外带`），**到店下单 `create-order` 必须带 `takeWayCode`**（取自 `takeWayList[].code`）；外卖场景不返回该字段、不下传。
- **外卖 code ≠ 到店 code（实测关键坑）**：同一商品在**外卖(orderType=2)**与**到店(orderType=1)**菜单中的 `productCode` 不同。例：脆汁鸡到店 `9900005432` / 外卖 `9900003021`；玉米杯到店 `4437` / 外卖 `904437`；可乐到店 `9900008751` / 外卖 `903050`(含糖)/`903071`(无糖)；板烧鸡腿堡到店 `1406` / 外卖 `901406`。**外卖算价 / 下单前必须先 `query-meals`(orderType=2, beType=2, beCode) 取外卖专属 code**，直接复用门店 code 会报 `60006 商品已售罄或不可售`。
- **外卖价格构成**：`calculate-price` 在外卖场景除 `productPrice` 外还会返回 `deliveryPrice`(配送费) + `packingPrice`(打包费)，均含在 `originalPrice / price` 中；`discount` 在无券时为 0。展示给用户时需说明"已含配送费 ¥X + 打包费 ¥Y"。
- **`query-store-coupons`**：可能返回 `data:[]`（当前账号 / 门店无可用券）。需兼容"无券"场景：不报错、提示"当前无可用券，已按原价计算"。到店与外卖均可能为空。
- **`query-my-account`**：字段含 `availablePoint / accumulativePoint / currentMouthExpirePoint（本月将过期）/ nextMouthExpirePoint（下月将过期）/ expiredPoint / usedPoint`。真实账号可能出现 `currentMouthExpirePoint=0`（无即将过期积分），到期提醒逻辑需兼容空值——**无即将过期积分时不强行提示**，避免误导。
- **`delivery-query-addresses`**：返回 `data.addresses[]`，字段 `addressId / contactName / fullAddress / phone`。**真实账号常为空数组**，此时必须先用 `delivery-create-address` 建地址（city、详细地址、联系人、电话为必填），否则外卖链路无法推进。
- **⚠️ 地址地理编码会吞掉楼栋号（实测关键坑）**：`delivery-create-address` 会对 `address` 字段做标准化（地理编码），**「街道/楼栋号」常被模糊匹配后丢弃**。实测：传入 `address="南京西路1288弄"` + `addressDetail="501室"` → 回写 `fullAddress="上海市某区某街道南京西路1288弄1-129号(示例小区) 示例楼501室"`，**"楼栋号"丢失**，外卖无法定位到楼。
  - **正确做法**：把**楼栋号写进 `addressDetail` 字段**（该字段会被原样保留，不会被地理编码吞掉）。实测：`address="示例小区"` + `addressDetail="94号501室"` → 回写 `fullAddress="地铁X号线 示例小区[地铁站]94号501室"`，**"94号"成功保留**。
  - **建地址前务必向用户确认楼栋号**，并在建完后用 `delivery-query-addresses` 复查 `fullAddress` 是否含楼栋号；若丢失，删不掉旧地址（MCP 无删除/修改地址工具），只能新建一个正确的、下单时改用新 `addressId`。
  - 注意：MCP **没有** `delivery-delete-address` / `delivery-update-address`，错误地址只能由用户在麦当劳 App 内手动删除，Agent 侧无法清理。
- **`delivery-query-stores`**：外送场景专用，入参 `beType=2` + `addressId`，返回可配送门店及其 `storeCode` + **`beCode`**。外卖后续 `query-meals / query-store-coupons / calculate-price / create-order` **全部必须带这个 beCode**，漏传会报参错。
- **外卖 `create-order`**：`orderType=2`，必填 `storeCode + beCode + addressId`，**不传 `takeWayCode`**；`remark` 选填（≤50字）。返回订单号 + 支付链接，与到店一致。
- **限流**：约 600 次 / 分钟，避免在同一轮重复拉取同一工具。

## 5. 决策逻辑（Agent 执行准则）

1. **澄清目标与场景**：先判定**订单方式**——到店自取（beType=1）还是麦乐送外卖（beType=2，用户说"点外卖 / 送到家"即触发）。再澄清模式（控卡 / 高蛋白 / 低钠 / 控糖 / 均衡）+ 餐次 + 预算 + 是否用券 + 是否直接下单。**外卖场景必须先拿到收货地址（见 §4.1）**。
2. **营养优先筛选**：拉取 `query-meals` + `list-nutrition-foods`，在营养约束内枚举单品与套餐替换项，得到候选组合。
3. **价格最优**：对每个候选调用 `calculate-price`（叠加最优券；外卖会自动含配送费），保留 Top 2–3。
4. **积分提醒**：调用 `query-my-account`，若发现"即将过期积分"或可用积分较高，在方案中加一句正向提示（如"你有一笔 X 积分将于 Y 到期，可顺手在麦麦商城兑换 / 抽奖"）。
5. **输出方案**：营养明细 + 原价 / 优惠后价 + 省钱额 + 积分提示 + 替换建议；外卖版补充配送地址与预计送达说明。
6. **确认下单**：用户说"就这个 / 下单 / 直接买 / 点外卖"且场景信息齐全后，调用 `create-order`；返回订单号与支付链接。未明确确认则只给方案不下单。

## 6. 输出模板

```
🍔 麦麦点餐搭子 · <模式> · <餐次> · [到店/外卖]
———————————————
方案A（推荐）：<餐品1> + <餐品2> + <替换说明>
  能量 X kcal | 蛋白 X g | 脂肪 X g | 碳水 X g | 钠 X mg
  原价 ¥X → 优惠后 ¥X（省 ¥Y，用了<券名>）（外卖含配送费 ¥Z）
💡 积分提醒：你的 X 积分将于 Y 到期，可顺手去麦麦商城兑换或抽奖
💡 小贴士：<一句正向健康提示>
⚠️ 仅供参考，以麦当劳实时信息为准；特殊饮食请遵医嘱。
———————————————
[到店] 取餐方式：堂食/外带；[外卖] 🛵 配送至：<fullAddress>，预计 <X> 送达（以麦当劳实时为准）
如确认，回复"下单"即可一键生成订单与支付链接。
```

## 7. 合规红线（严格遵守活动规则）

- 不得出现"垃圾食品 / 少吃 / 发胖羞耻"等贬义话术；改用"均衡搭配 / 聪明选择"。
- 不得与肯德基 / 汉堡王等任何友商对比。
- 不得植入外部链接、脚本或采集 Token。
- 营养数据仅作信息展示，不提供医疗建议。
- 下单、领券均属有副作用动作，必须用户明确确认 / 授权。

## 8. 示例对话

**示例 1 · 到店**
**用户：** 帮我点份午餐，热量别超 550、蛋白尽量高、用券最划算，顺便看看我快过期的积分，合适就直接下单。

**Agent：**（依次调用 `now-time-info → query-meals → list-nutrition-foods → query-meal-detail → query-store-coupons → calculate-price → query-my-account`，输出方案；用户回复"下单"后调用 `create-order`）

```
🍔 麦麦点餐搭子 · 控卡+高蛋白 · 午餐 · 到店
———————————————
方案A（推荐）：板烧鸡腿堡（去酱） + 玉米杯 + 无糖可乐
  能量 470 kcal | 蛋白 31 g | 脂肪 14 g | 碳水 52 g | 钠 980 mg
  原价 ¥32 → 优惠后 ¥27（省 ¥5，用了门店优惠券）
💡 积分提醒：你有 1,200 积分将于 10-15 到期，可顺手去麦麦商城兑换或抽奖
💡 小贴士：把薯条换玉米杯，同时降热量和钠，饱腹感也不差。
⚠️ 仅供参考，以麦当劳实时信息为准；特殊饮食请遵医嘱。
———————————————
取餐方式：堂食/外带；如确认，回复"下单"即可一键生成订单与支付链接。
```

**示例 2 · 外卖（麦乐送）**
**用户：** 我想吃减肥餐，点外卖送到家。

**Agent：**（识别为外卖 → `delivery-query-addresses` 发现无地址 → 请用户补收货信息 → `delivery-create-address` 建地址拿 addressId → `delivery-query-stores`(beType=2) 取门店 storeCode+beCode → `query-meals`(orderType=2,beCode) → `query-store-coupons`(orderType=2,beCode) → `calculate-price`(orderType=2,beCode,items) 含配送费 → 输出方案并请确认 → 用户回复"确认下单"后 `create-order`(orderType=2,addressId,beCode,storeCode,items)）

```
🍔 麦麦点餐搭子 · 控卡均衡 · 午餐 · 外卖
———————————————
方案A（推荐）：麦麦脆汁鸡1块 + 玉米杯 + 鲜萃咖啡（0糖）
  能量 ~230 kcal | 蛋白 ~20 g | 脂肪 ~5 g
  原价 ¥37.5 → 到手 ¥37.5（无可用券，含配送费 ¥X）
💡 小贴士：把含糖可乐换成鲜萃咖啡，单这一项少摄入约 100–140 kcal 糖。
⚠️ 仅供参考，以麦当劳实时信息为准；特殊饮食请遵医嘱。
———————————————
🛵 配送至：上海市普陀区真光路XXXX号（联系人元宝 / 138xxxx），预计 30–45 分钟送达。
确认请回复"确认下单"，我将生成订单与支付链接。
```
