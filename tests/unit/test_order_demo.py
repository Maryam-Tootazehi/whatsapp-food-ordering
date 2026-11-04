"""The walkthrough must be runnable without WhatsApp, API keys or a database."""

from restaurant_assistant.interfaces.demo_order import main


def test_demo_shows_customer_confirmation_and_staff_acceptance_separately(capsys) -> None:  # type: ignore[no-untyped-def]
    main()
    text = capsys.readouterr().out
    assert "EXAMPLE ONLY" in text
    assert "19,50 €" in text
    assert "awaiting_customer" in text
    assert "awaiting_kitchen" in text
    assert "accepted" in text
    assert "No messages sent. No database writes." in text
