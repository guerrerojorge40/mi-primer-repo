from omega_audit_generator import SmartIDResolver, WebIntelAgent, retry


class FakeAPI:
    def search_team_exact(self, team_name):
        return []

    def search_team_fuzzy(self, team_name):
        return [{"team_id": 2875, "team_name": "Al Ahli SC", "country": "Saudi Arabia", "league": "Saudi Pro League"}]

    def list_teams_by_country(self, country):
        return []

    def get_team_context(self, team_id):
        return {"team_name": "Al Ahli SC", "country": "Saudi Arabia", "league": "Saudi Pro League"}


class FakeWeb:
    def search_web(self, query):
        return "API Football team ID: 2875"


def test_smart_resolver_fuzzy_then_validate():
    resolver = SmartIDResolver(FakeAPI(), FakeWeb())
    result = resolver.resolve("Al-Ahli Jeddah", league="Saudi Pro League", country="Saudi Arabia")
    assert result.team_id == 2875
    assert result.source == "api_fuzzy"


def test_web_intel_detect_and_enrich():
    agent = WebIntelAgent(FakeWeb())
    full_data = {"coach": None, "injuries": "", "weather": "?", "referee": "{{WEB_REQUIRED}}"}
    context = {"team_name": "Al Ahli", "team_a": "Al Ahli", "team_b": "Al Hilal", "stadium": "King Abdullah", "city": "Jeddah"}
    gaps = agent.detect_gaps(full_data)
    assert set(gaps) == {"coach", "injuries", "weather", "referee"}
    enriched = agent.enrich(full_data, context)
    assert enriched["coach"]
    assert enriched["injuries"]


def test_retry_decorator():
    state = {"count": 0}

    @retry(max_attempts=3, delay_s=0)
    def flaky():
        state["count"] += 1
        if state["count"] < 3:
            raise ValueError("fail")
        return "ok"

    assert flaky() == "ok"
    assert state["count"] == 3
