from nablaclaw.core import Doctor


def test_doctor_report_shape() -> None:
    report = Doctor().run()
    payload = report.as_dict()
    assert "ok" in payload
    assert "checks" in payload
    assert len(payload["checks"]) >= 3
