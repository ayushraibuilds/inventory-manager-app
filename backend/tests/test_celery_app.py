from unittest.mock import patch


def test_send_daily_stock_summary_task_sends_whatsapp_summary():
    from celery_app import send_daily_stock_summary_task

    catalog = {
        "bpp/catalog": {
            "bpp/providers": [
                {
                    "items": [
                        {
                            "descriptor": {"name": "Rice"},
                            "price": {"value": "50"},
                            "quantity": {"available": {"count": 2}},
                        },
                        {
                            "descriptor": {"name": "Atta"},
                            "price": {"value": "40"},
                            "quantity": {"available": {"count": 10}},
                        },
                    ]
                }
            ]
        }
    }

    with patch("db.get_all_seller_ids", return_value=["seller-1"]), \
         patch("db.get_seller_profile", return_value={"phone": "+919876543210", "preferred_language": "en"}), \
         patch("db.get_catalog", return_value=catalog), \
         patch("db.log_activity") as mock_log, \
         patch("routes.auth.send_whatsapp_reply", return_value=True) as mock_send:
        send_daily_stock_summary_task()

    assert mock_send.called
    assert "Daily Stock Summary" in mock_send.call_args.args[1]
    mock_log.assert_called_once()
