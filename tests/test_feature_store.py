import unittest
from datetime import datetime
from uuid import UUID

from services.feature_store_service import FeatureStoreService
from services.market_workspace_service import WorkspaceQueryError


class FakeRepository:
    def __init__(self): self.stored = []
    def source_observations(self, limit, after_at=None, after_id=None):
        if after_at is not None: return []
        return [{"analytics": {"analytics_id":"11111111-1111-4111-8111-111111111111",
                 "underlying_symbol":"RELIANCE", "expiry":"2026-07-30",
                 "source_captured_at":"2026-07-14T12:00:00", "spot_price":"100"},
                 "changes": None, "ranking": {"ranking_id":"22222222-2222-4222-8222-222222222222", "total_score":"0.8"}}][:limit]
    def upsert_vector(self, vector, values): self.stored.append((vector, values))
    def list_vectors(self, symbol, expiry, limit): return [{"underlying_symbol":symbol}]
    def get_vector(self, vector_id): return {"vector_id":vector_id}


class FeatureStoreServiceTest(unittest.TestCase):
    def setUp(self):
        self.repository=FakeRepository()
        self.service=FeatureStoreService(self.repository, clock=lambda:datetime(2026,7,14,13))

    def test_materializes_all_defined_features_with_lineage_and_quality(self):
        result=self.service.materialize(10)
        vector, values=self.repository.stored[0]
        self.assertEqual(result["materialized_count"],1)
        self.assertEqual(vector["analytics_id"],UUID("11111111-1111-4111-8111-111111111111"))
        self.assertEqual(vector["ranking_id"],"22222222-2222-4222-8222-222222222222")
        self.assertEqual(vector["quality_state"],"PARTIAL")
        mapped={value["name"]:value["value"] for value in values}
        self.assertEqual(mapped["spot_price"],"100")
        self.assertEqual(mapped["total_score"],"0.8")
        self.assertEqual(mapped["time_to_expiry_days"],16)
        self.assertEqual(len(values),len(self.service.definitions()))

    def test_vector_id_is_deterministic_and_materialization_is_bounded(self):
        self.service.materialize()
        first=self.repository.stored[-1][0]["vector_id"]
        self.service.materialize()
        self.assertEqual(first,self.repository.stored[-1][0]["vector_id"])
        with self.assertRaises(ValueError): self.service.materialize(0)

    def test_read_validation_and_detail(self):
        self.assertEqual(self.service.list({"symbol":"reliance"})["count"],1)
        for query in ({}, {"symbol":"R","limit":"bad"}, {"symbol":"R","limit":"201"}, {"symbol":"R","expiry":"bad"}):
            with self.subTest(query=query), self.assertRaises(WorkspaceQueryError): self.service.list(query)
