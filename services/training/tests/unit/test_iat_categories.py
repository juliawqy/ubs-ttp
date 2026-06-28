"""
Unit tests for IATCategoryCatalog.
Run: pytest services/training/tests/unit/test_iat_categories.py -v
"""
import pytest
from app.services.iat_categories import IATCategoryCatalog, IATCategory


@pytest.fixture
def catalog():
    return IATCategoryCatalog()


class TestGetCategories:
    def test_returns_at_least_one_category(self, catalog):
        categories = catalog.get_categories()
        assert len(categories) >= 1

    def test_categories_are_iat_category_instances(self, catalog):
        categories = catalog.get_categories()
        assert all(isinstance(c, IATCategory) for c in categories)

    def test_each_category_has_two_distinct_poles(self, catalog):
        categories = catalog.get_categories()
        for c in categories:
            assert c.pole_a != c.pole_b

    def test_each_category_has_a_nonempty_id_and_label(self, catalog):
        categories = catalog.get_categories()
        for c in categories:
            assert c.id.strip()
            assert c.label.strip()

    def test_category_ids_are_unique(self, catalog):
        categories = catalog.get_categories()
        ids = [c.id for c in categories]
        assert len(ids) == len(set(ids))

    def test_result_mutation_does_not_affect_defaults(self, catalog):
        categories = catalog.get_categories()
        categories.append(
            IATCategory(id="extra", label="Extra", pole_a="X", pole_b="Y")
        )
        assert len(catalog.get_categories()) == len(categories) - 1

    def test_mutating_returned_category_list_is_independent_per_call(self, catalog):
        first_call = catalog.get_categories()
        first_call[0].stimuli.append("Mutated")
        second_call = catalog.get_categories()
        assert "Mutated" not in second_call[0].stimuli
