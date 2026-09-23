def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["external_writes"] is False


def test_research_calculates_reward_margin_and_records_run(client):
    response = client.post(
        "/api/research",
        json={
            "project_name": "Portable Power Station",
            "target_market": "US / CA",
            "platform": "Kickstarter",
            "evidence_count": 18,
            "rewards": [
                {
                    "name": "Early Bird",
                    "price": 599,
                    "unit_cost": 326,
                    "shipping_cost": 40,
                    "platform_fee_rate": 0.08,
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["output"]["reward_options"][0]["margin_percent"] == 30.9
    assert body["output"]["human_review_required"] is True
    assert client.get("/api/runs").json()[0]["agent_type"] == "research"


def test_growth_flags_only_high_cpc_low_conversion_group(client):
    response = client.post(
        "/api/growth/diagnose",
        json={
            "project_name": "Portable Power Station",
            "metrics": [
                {"ad_group": "Broad B2", "spend": 1000, "clicks": 500, "backers": 5, "revenue": 1200, "previous_cpc": 1.4},
                {"ad_group": "Lookalike", "spend": 800, "clicks": 800, "backers": 48, "revenue": 4000, "previous_cpc": 0.95},
            ],
        },
    )
    assert response.status_code == 200
    recommendations = response.json()["output"]["recommendations"]
    assert len(recommendations) == 1
    assert recommendations[0]["ad_group"] == "Broad B2"
    assert recommendations[0]["external_action_executed"] is False


def test_backer_analysis_marks_delivery_and_refund_for_review(client):
    response = client.post(
        "/api/backers/analyze",
        json={
            "messages": [
                "Can you guarantee delivery before October?",
                "Will the solar charging cable be included?",
                "I need a refund if shipping is delayed.",
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()["output"]
    assert body["draft_only"] is True
    assert body["high_risk_message_indexes"] == [0, 2]


def test_approval_is_idempotency_guarded(client):
    first = client.post("/api/approvals/budget-1", json={"approved_by": "demo-user"})
    second = client.post("/api/approvals/budget-1", json={"approved_by": "demo-user"})
    assert first.status_code == 200
    assert first.json()["external_action_executed"] is False
    assert second.status_code == 409


def test_model_enrichment_has_no_key_fallback(client, monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    response = client.post(
        "/api/model/enrich",
        json={"task": "Improve this draft", "deterministic_result": "Verified draft"},
    )
    assert response.status_code == 200
    assert response.json()["provider"] == "fallback"
    assert response.json()["content"] == "Verified draft"
