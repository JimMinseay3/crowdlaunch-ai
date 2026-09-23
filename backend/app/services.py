from __future__ import annotations

from collections import Counter

from .schemas import AdMetric, BackerRequest, ResearchRequest


def reward_margin(price: float, unit_cost: float, shipping_cost: float, fee_rate: float) -> float:
    fees = price * fee_rate
    margin = (price - unit_cost - shipping_cost - fees) / price
    return round(margin * 100, 1)


def run_research(payload: ResearchRequest) -> dict:
    rewards = [
        {
            "name": reward.name,
            "price": reward.price,
            "margin_percent": reward_margin(
                reward.price,
                reward.unit_cost,
                reward.shipping_cost,
                reward.platform_fee_rate,
            ),
        }
        for reward in payload.rewards
    ]
    healthy_rewards = sum(item["margin_percent"] >= 30 for item in rewards)
    evidence_score = min(payload.evidence_count * 1.4, 25)
    margin_score = min(healthy_rewards * 8, 24)
    score = round(min(100, 35 + evidence_score + margin_score), 0)
    warnings = [
        "锂电池跨境运输与危险品路线仍需物流供应商确认。",
        "任何具体到货日期承诺均应在最终排期验证后发布。",
    ]
    return {
        "readiness_score": int(score),
        "decision": "GO" if score >= 75 else "ADJUST",
        "target_market": payload.target_market,
        "platform": payload.platform,
        "reward_options": rewards,
        "citations": payload.evidence_count,
        "warnings": warnings,
        "human_review_required": True,
    }


def diagnose_growth(metrics: list[AdMetric]) -> dict:
    rows = []
    recommendations = []
    for metric in metrics:
        cpc = metric.spend / metric.clicks if metric.clicks else 0
        cvr = metric.backers / metric.clicks if metric.clicks else 0
        roas = metric.revenue / metric.spend if metric.spend else 0
        cpc_change = (cpc - metric.previous_cpc) / metric.previous_cpc
        row = {
            "ad_group": metric.ad_group,
            "cpc": round(cpc, 2),
            "cvr_percent": round(cvr * 100, 2),
            "roas": round(roas, 2),
            "cpc_change_percent": round(cpc_change * 100, 1),
        }
        rows.append(row)
        if cvr < 0.02 and cpc_change > 0.2:
            recommendations.append(
                {
                    "id": f"budget-{len(recommendations) + 1}",
                    "ad_group": metric.ad_group,
                    "action": "pause_and_reallocate",
                    "reason": "CPC 连续偏高且支持转化率低于 2%",
                    "approval_status": "pending",
                    "external_action_executed": False,
                }
            )
    return {"metrics": rows, "recommendations": recommendations, "human_review_required": bool(recommendations)}


def analyze_backers(payload: BackerRequest) -> dict:
    keywords = {
        "delivery": ["delivery", "ship", "shipping", "arrive"],
        "battery_transport": ["battery", "lithium", "canada", "airline"],
        "charging": ["charge", "charging", "solar"],
        "refund": ["refund", "cancel", "money back"],
    }
    counter: Counter[str] = Counter()
    high_risk = []
    for index, message in enumerate(payload.messages):
        lower = message.lower()
        matches = [theme for theme, words in keywords.items() if any(word in lower for word in words)]
        counter.update(matches or ["other"])
        if "refund" in matches or "delivery" in matches:
            high_risk.append(index)
    return {
        "message_count": len(payload.messages),
        "themes": [{"theme": name, "count": count} for name, count in counter.most_common()],
        "high_risk_message_indexes": high_risk,
        "draft_only": True,
        "human_review_required": True,
    }
