#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦麦点餐搭子 · 逻辑级端到端实测 (Mock Harness)
================================================
目的：在无真实 MCP Token 的情况下，用真实结构的 mock 数据，
忠实复刻 SKILL.md 定义的「8 工具编排 + 决策逻辑 + 输出模板」，
验证技能大脑（营养优先筛选 → 价格最优 → 券叠加 → 积分提醒 → 受控下单）是否正确。

说明：本脚本不连网、不调用真实麦当劳 MCP；所有 tool_* 函数模拟 MCP Tool 返回。
切换真实环境只需把 tool_* 换成对 mcd-mcp 的 tools/call 调用即可。
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field

# ----------------------------------------------------------------------------
# 1) Mock 数据层（结构对齐麦当劳 MCP 各 Tool 返回）
# ----------------------------------------------------------------------------

# list-nutrition-foods: 常见餐品营养成分
NUTRITION = {
    "板烧鸡腿堡":   {"energy": 450, "protein": 28, "fat": 19, "carbs": 38, "sodium": 950, "calcium": 120},
    "吉士蛋堡":     {"energy": 300, "protein": 15, "fat": 14, "carbs": 28, "sodium": 650, "calcium": 150},
    "麦辣鸡腿堡":   {"energy": 500, "protein": 24, "fat": 26, "carbs": 44, "sodium": 1000, "calcium": 100},
    "玉米杯":       {"energy": 100, "protein": 3,  "fat": 1,  "carbs": 22, "sodium": 10,  "calcium": 0},
    "薯条(中)":     {"energy": 320, "protein": 4,  "fat": 16, "carbs": 41, "sodium": 230, "calcium": 0},
    "苹果片":       {"energy": 35,  "protein": 0,  "fat": 0,  "carbs": 9,  "sodium": 0,   "calcium": 0},
    "无糖可乐":     {"energy": 0,   "protein": 0,  "fat": 0,  "carbs": 0,  "sodium": 0,   "calcium": 0},
    "鲜煮咖啡":     {"energy": 5,   "protein": 0,  "fat": 0,  "carbs": 0,  "sodium": 5,   "calcium": 0},
    "麦旋风":       {"energy": 350, "protein": 7,  "fat": 14, "carbs": 50, "sodium": 150, "calcium": 200},
}

# query-meals: 当前门店可售餐品（编码/价格/标签）
MENU = {
    "板烧鸡腿堡": {"code": "M01", "price": 25, "tags": ["汉堡", "主打"]},
    "吉士蛋堡":   {"code": "M02", "price": 15, "tags": ["汉堡", "早餐"]},
    "麦辣鸡腿堡": {"code": "M03", "price": 22, "tags": ["汉堡"]},
    "玉米杯":     {"code": "S01", "price": 7,  "tags": ["小食", "低钠"]},
    "薯条(中)":   {"code": "S02", "price": 12, "tags": ["小食"]},
    "苹果片":     {"code": "S03", "price": 9,  "tags": ["小食", "低钠"]},
    "无糖可乐":   {"code": "D01", "price": 7,  "tags": ["饮品", "无糖"]},
    "鲜煮咖啡":   {"code": "D02", "price": 13, "tags": ["饮品"]},
    "麦旋风":     {"code": "D03", "price": 14, "tags": ["甜品"]},
}

# query-meal-detail: 套餐组成与可替换项（降热量/降钠）
MEAL_DETAIL = {
    "板烧鸡腿堡套餐": {
        "base": ["板烧鸡腿堡", "薯条(中)", "无糖可乐"],
        "replaceable": {"薯条(中)": ["玉米杯", "苹果片"], "无糖可乐": ["鲜煮咖啡"]},
    }
}

# query-store-coupons: 当前门店可用优惠券
COUPONS = [
    {"id": "C1", "name": "满30减5", "type": "threshold", "threshold": 30, "amount": 5},
    {"id": "C2", "name": "板烧套餐立减8", "type": "item", "item": "板烧鸡腿堡", "amount": 8},
]

# query-my-account: 积分账户（含即将过期积分）
ACCOUNT = {"total": 5600, "available": 5600, "frozen": 0, "expiring_soon": 1200, "expiring_date": "2026-10-15"}

# create-order: 模拟下单返回
ORDER_RESULT = {"order_id": "MCD20261009XXXX", "pay_url": "https://mcd.cn/pay/MCD20261009XXXX", "status": "待支付"}


# ----------------------------------------------------------------------------
# 2) 模拟 MCP Tool 调用（替换为真实 tools/call 即可上线）
# ----------------------------------------------------------------------------

def tool_now_time_info():       return {"time": "2026-10-09 12:30", "meal_period": "午餐"}
def tool_query_meals():         return MENU
def tool_list_nutrition_foods():return NUTRITION
def tool_query_meal_detail(name): return MEAL_DETAIL.get(name, {})
def tool_query_store_coupons(): return COUPONS
def tool_query_my_account():    return ACCOUNT
def tool_calculate_price(items, coupon=None):
    original = sum(MENU[i]["price"] for i in items)
    discount = 0
    if coupon:
        if coupon["type"] == "threshold" and original >= coupon["threshold"]:
            discount = coupon["amount"]
        elif coupon["type"] == "item" and coupon["item"] in items:
            discount = coupon["amount"]
    return {"original": original, "discount": discount, "final": original - discount}
def tool_create_order(items):
    return ORDER_RESULT


# ----------------------------------------------------------------------------
# 3) 技能决策逻辑（对齐 SKILL.md 第 5 节）
# ----------------------------------------------------------------------------

@dataclass
class Intent:
    mode: str = "控卡"          # 控卡/高蛋白/低钠/控糖/均衡
    meal: str = "午餐"
    energy_max: int = 550
    protein_min: int = 0
    use_coupon: bool = True
    check_points: bool = True
    confirm_order: bool = False

# 候选组合（模拟"在营养约束内枚举单品与套餐替换项"）
CANDIDATES = [
    ["板烧鸡腿堡", "玉米杯", "无糖可乐"],           # 方案A: 控卡+高蛋白
    ["吉士蛋堡", "鲜煮咖啡"],                        # 方案B: 轻量
    ["麦辣鸡腿堡", "苹果片", "无糖可乐"],            # 方案C: 高钠偏高
]


def nutrition_of(items):
    agg = {"energy": 0, "protein": 0, "fat": 0, "carbs": 0, "sodium": 0, "calcium": 0}
    for it in items:
        for k, v in NUTRITION[it].items():
            agg[k] += v
    return agg


def best_coupon(items, original):
    best, best_d = None, 0
    for c in tool_query_store_coupons():
        d = tool_calculate_price(items, c)["discount"]
        if d > best_d:
            best, best_d = c, d
    return best


def run(intent: Intent):
    # 1. 时间
    t = tool_now_time_info()
    # 2-3. 菜单 + 营养
    menu, nutri = tool_query_meals(), tool_list_nutrition_foods()
    # 4. 营养优先筛选 + 排名（满足能量/蛋白约束，优先高蛋白、再低价）
    feasible = []
    for items in CANDIDATES:
        n = nutrition_of(items)
        if n["energy"] <= intent.energy_max and n["protein"] >= intent.protein_min:
            feasible.append((items, n))
    if not feasible:
        return "⚠️ 当前约束下无可行组合，请放宽热量/蛋白要求。"
    feasible.sort(key=lambda x: (-x[1]["protein"], x[1]["energy"]))
    ranked = feasible[:3]

    # 5-6. 价格最优 + 券叠加
    plans = []
    for items, n in ranked:
        if intent.use_coupon:
            coupon = best_coupon(items, 0)
            price = tool_calculate_price(items, coupon)
            coupon_name = coupon["name"] if coupon else "无可用券"
        else:
            coupon = None
            price = tool_calculate_price(items)
            coupon_name = "未用券"
        plans.append((items, n, price, coupon_name))

    # 7. 积分到期提醒
    points_tip = ""
    if intent.check_points:
        acc = tool_query_my_account()
        if acc["expiring_soon"] > 0:
            points_tip = f"💡 积分提醒：你有 {acc['expiring_soon']} 积分将于 {acc['expiring_date']} 到期，可顺手去麦麦商城兑换或抽奖"

    # 8. 输出（对齐 SKILL.md 第 6 节模板）
    lines = [f"🍔 麦麦点餐搭子 · {intent.mode} · {intent.meal}", "———————————————"]
    for idx, (items, n, price, cname) in enumerate(plans, 1):
        tag = "（推荐）" if idx == 1 else ""
        lines.append(f"方案{chr(64+idx)}{tag}：{' + '.join(items)}")
        lines.append(f"  能量 {n['energy']} kcal | 蛋白 {n['protein']} g | 脂肪 {n['fat']} g | 碳水 {n['carbs']} g | 钠 {n['sodium']} mg")
        if price["discount"] > 0:
            lines.append(f"  原价 ¥{price['original']} → 优惠后 ¥{price['final']}（省 ¥{price['discount']}，用了{cname}）")
        else:
            lines.append(f"  原价 ¥{price['original']}（{cname}）")
    lines.append(points_tip)
    lines.append("💡 小贴士：把薯条换玉米杯，同时降热量和钠，饱腹感也不差。")
    lines.append("⚠️ 仅供参考，以麦当劳实时信息为准；特殊饮食请遵医嘱。")
    lines.append("———————————————")

    if intent.confirm_order and plans:
        order = tool_create_order(plans[0][0])
        lines.append(f"✅ 已为您下单：订单号 {order['order_id']} | 支付链接 {order['pay_url']}（{order['status']}）")
    else:
        lines.append('如确认，回复"下单"即可一键生成订单与支付链接。')
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# 4) 执行实测
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    print(">>> 场景：热量别超550、蛋白尽量高、用券最划算、看快过期积分、合适就直接下单\n")
    intent = Intent(mode="控卡+高蛋白", meal="午餐", energy_max=550, protein_min=0,
                    use_coupon=True, check_points=True, confirm_order=True)
    print(run(intent))

    print("\n>>> 仅推荐不下单（确认环节未触发）\n")
    intent2 = Intent(confirm_order=False)
    print(run(intent2))

    print("\n>>> 验证：约束过滤（能量上限设为 400，应排除板烧套餐）\n")
    intent3 = Intent(mode="控卡", energy_max=400, use_coupon=False, check_points=False, confirm_order=False)
    print(run(intent3))
