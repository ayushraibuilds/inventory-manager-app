from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from billing import _apply_trial_state


def test_apply_trial_state_bootstraps_trial_for_uninitialized_account():
    profile = {
        "billing_plan": "free",
        "billing_status": "active",
        "trial_started_at": None,
        "trial_ends_at": None,
        "razorpay_subscription_id": "",
    }

    with patch("billing._update_profile_billing") as update_mock, patch("billing._insert_subscription_event") as event_mock:
        result = _apply_trial_state("seller-1", profile, jwt_token=None)

    assert result["billing_plan"] == "pro"
    assert result["billing_status"] == "trialing"
    assert result["billing_provider"] == "trial"
    assert result["trial_started_at"] is not None
    assert result["trial_ends_at"] is not None
    update_mock.assert_called_once()
    event_mock.assert_called_once()


def test_apply_trial_state_expires_trial_to_free():
    past_start = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    past_end = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    profile = {
        "billing_plan": "pro",
        "billing_status": "trialing",
        "billing_provider": "trial",
        "trial_started_at": past_start,
        "trial_ends_at": past_end,
        "razorpay_subscription_id": "",
    }

    with patch("billing._update_profile_billing") as update_mock, patch("billing._insert_subscription_event") as event_mock:
        result = _apply_trial_state("seller-1", profile, jwt_token=None)

    assert result["billing_plan"] == "free"
    assert result["billing_status"] == "active"
    assert result["billing_provider"] == "trial_expired"
    update_mock.assert_called_once()
    event_mock.assert_called_once()
