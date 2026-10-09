# 麦麦点餐搭子 · 真实 MCP 实测报告

> 测试时间：2026-10-09
> 测试环境：真实 `mcd-mcp`（Token 已配置于 `~/.workbuddy/mcp.json`），直连 `https://mcp.mcd.cn`
> 测试范围：核心 8 工具链中 **7 个真实调用**；`create-order` 按受控红线**未调**（避免真实扣款）

---

## 一、实测结论

- ✅ **核心链路全部真实可用**：营养筛选（160 条真实数据）、菜单 / 价格、算价、积分查询、门店查询均返回真实数据。
- ⚠️ **真实环境两个"空值"场景需注意**：当前账号无可用门店券（`data:[]`）、无即将过期积分（`currentMouthExpirePoint=0`）——技能已做兼容。
- 🔒 **`create-order` 未真实调用**（受控红线，避免花钱）；其前置参数 `takeWayCode` 已从 `calculate-price` 的 `takeWayList` 确认可取。

---

## 二、逐工具实测记录

| 工具 | 真实返回摘要 | 验证点 |
|------|--------------|--------|
| `now-time-info` | `2026-10-09 20:59:53 GMT+08:00` | 链路通、鉴权生效 |
| `query-my-account` | `availablePoint=0, accumulativePoint=868.7, currentMouthExpirePoint=0, expiredPoint=843.7` | 积分可能为空，提醒需兼容 |
| `list-nutrition-foods` | 160 条真实营养数据（`[160]{...}` 格式） | 营养筛选数据源，已解析出控卡+高蛋白 Top10 |
| `query-nearby-stores` | 上海人民广场 5 家门店，`storeCode=1450713` 等 | 到店场景拿 `storeCode` |
| `query-meals` | 完整菜单（分类+餐品映射表，含 code/现价/折扣） | 板烧鸡腿堡 `1406` ¥23.5 等 |
| `query-store-coupons` | `data:[]`（当前无可用券） | 需兼容空券场景 |
| `calculate-price` | 板烧+玉米杯 = ¥36.50（3650 分），`takeWayList=[eat-in, locker-out]` | 价格单位=分；`takeWayCode` 必需 |
| `create-order` | **未调（受控）** | 前置 `takeWayCode` 已确认可取 |

---

## 三、真实营养筛选示例（控卡 ≤550kcal + 高蛋白 ≥20g Top5）

| 餐品 | 热量 | 蛋白 | 脂肪 | 钠 |
|------|------|------|------|-----|
| 蜜汁BBQ薄皮脆汁鸡(带骨里脊) | 152 | 20g | 5g | 635 |
| 蜜汁快乐 | 258 | 22g | 9g | 721 |
| 果然多肉 | 478 | 36g | 17g | 1343 |
| 麦麦脆汁鸡(带骨里脊) | 332 | 22g | 18g | 812 |
| 双层原味板烧鸡腿麦满分 | 355 | 23g | 17g | 984 |

> 完整 Top10 由 `real_nutrition_probe.py` 直连真实 MCP 跑出（160 条全部解析成功）。

---

## 四、关键校准点（已固化进 SKILL.md §4.5）

1. `calculate-price` 价格单位 = **分**，展示 ÷100；返回 `takeWayList` → `create-order` 必须带 `takeWayCode`。
2. `list-nutrition-foods` 数据需从 `data` 字符串解析，首列中文名、第 4 列 kcal、第 5 列蛋白。
3. `query-store-coupons` 可能返回 `[]`，需兼容。
4. `query-my-account` 即将过期积分可能为 0，提醒需兼容空值。

---

## 五、下一步

- **真实下单**：用户明确说"下单"后，用 `takeWayCode` + 商品 `code` 调 `create-order`（受控）。
- **拉 Star**：10/25 前发 Public 仓库 + 发 Issue 报名，用公众号 / 小红书 / 抖音导流。
- **提交 workbuddy.md**：本目录 `workbuddy.md` 已更新为真实开发记录（Token 脱敏），用于参与 WorkBuddy 专项奖励。
