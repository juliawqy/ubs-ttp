"""
Unit tests for RecommendationEngine.
Run: pytest services/training/tests/unit/test_recommendation_engine.py -v
"""
import pytest
from app.services.recommendation_engine import RecommendationEngine, DEFAULT_SKILLS


@pytest.fixture
def engine():
    return RecommendationEngine()


class TestRecommend:
    def test_known_pair_returns_specific_skills(self, engine):
        skills = engine.recommend("Software Engineer", "Senior Software Engineer")
        assert "System Design" in skills

    def test_unknown_pair_returns_default_skills(self, engine):
        skills = engine.recommend("Astronaut", "Chief Astronaut")
        assert skills == DEFAULT_SKILLS

    def test_result_mutation_does_not_affect_defaults(self, engine):
        skills = engine.recommend("Astronaut", "Chief Astronaut")
        skills.append("Rocket Science")
        assert "Rocket Science" not in DEFAULT_SKILLS

    def test_matching_is_case_insensitive(self, engine):
        skills = engine.recommend("software engineer", "senior software engineer")
        assert "System Design" in skills

    def test_matching_ignores_surrounding_whitespace(self, engine):
        skills = engine.recommend("  Software Engineer  ", "  Senior Software Engineer  ")
        assert "System Design" in skills


class TestValidation:
    def test_empty_current_role_raises(self, engine):
        with pytest.raises(ValueError, match="current_role"):
            engine.recommend("", "Senior Software Engineer")

    def test_empty_next_milestone_raises(self, engine):
        with pytest.raises(ValueError, match="next_milestone"):
            engine.recommend("Software Engineer", "")
