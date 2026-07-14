import os, unittest
from services.symbol_workspace_repository import SymbolWorkspaceRepository

@unittest.skipUnless(os.getenv("RUN_DB_INTEGRATION_TESTS")=="1","Set RUN_DB_INTEGRATION_TESTS=1 to run PostgreSQL integration tests.")
class SymbolWorkspaceRepositoryIntegrationTest(unittest.TestCase):
    def test_search_and_exact_persisted_lineage(self):
        repository=SymbolWorkspaceRepository(); rows=repository.search("",1)
        self.assertLessEqual(len(rows),1)
        if rows:
            data=repository.intelligence(rows[0]["underlying_symbol"],None)
            self.assertIsNotNone(data); self.assertTrue(data["analytics"])
            self.assertEqual(data["analytics"][0]["underlying_symbol"],rows[0]["underlying_symbol"])
