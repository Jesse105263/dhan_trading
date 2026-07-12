import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from services.option_chain_models import OptionChainCollectionResult
from services.option_data_pipeline import OptionAnalyticsStage, OptionCollectionStage


class Failures:
    def __init__(self): self.items=[]
    def insert(self, item): self.items.append(item); return len(self.items)

class Collector:
    def __init__(self): self.calls={}
    def collect(self, request):
        symbol=request.underlying_symbol
        self.calls[symbol]=self.calls.get(symbol,0)+1
        if symbol == 'BAD': raise ValueError('access-token=secret')
        if symbol == 'RETRY' and self.calls[symbol] == 1: raise TimeoutError('timeout')
        return OptionChainCollectionResult(uuid4(), symbol, '1', date(2026,7,28), Decimal('100'), 2, 4, 4)

class Analytics:
    def calculate_and_persist(self, request):
        return type('A', (), {'source_run_id': request.source_run_id})()

class OptionDataPipelineTest(unittest.TestCase):
    def test_collection_isolates_failures_and_retries(self):
        failures=Failures(); sleeps=[]
        stage=OptionCollectionStage(('GOOD','BAD','RETRY'), Collector(), failures,
                                    max_attempts=2, retry_backoff_seconds=1,
                                    sleeper=sleeps.append)
        context={'run_id':'run','current_stage_started_at':datetime.now()}
        stage.run(context)
        self.assertEqual(set(context['option_collection_results']), {'GOOD','RETRY'})
        self.assertEqual(set(context['option_collection_failures']), {'BAD'})
        self.assertNotIn('secret', failures.items[0].error_message)
        self.assertEqual(sleeps, [1])
        self.assertEqual(context['stage_metric_data']['records_received'], 2)

    def test_analytics_only_uses_successful_collections(self):
        failures=Failures(); stage=OptionAnalyticsStage(Analytics(), failures,
            nearby_strikes_each_side=3, maximum_source_age=timedelta(hours=1))
        result=OptionChainCollectionResult(uuid4(),'GOOD','1',date(2026,7,28),Decimal('100'),2,4,4)
        context={'run_id':'run','current_stage_started_at':datetime.now(),
                 'option_collection_results':{'GOOD':result}}
        stage.run(context)
        self.assertEqual(set(context['option_analytics_results']), {'GOOD'})
        self.assertEqual(context['stage_metric_data']['records_written'], 1)

    def test_rejects_empty_symbols(self):
        with self.assertRaises(ValueError):
            OptionCollectionStage(tuple(), Collector(), Failures())

if __name__ == '__main__': unittest.main()
