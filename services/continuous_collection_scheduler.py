from services.scheduler import PipelineScheduler


class ContinuousCollectionRunner:
    def __init__(self, service, execution_kwargs): self.service=service; self.execution_kwargs=execution_kwargs
    def start(self): return self.service.execute_pending(**self.execution_kwargs)


def build_continuous_scheduler(service, execution_kwargs, calendar, lock_repository, ttl_seconds=900):
    return PipelineScheduler(lambda: ContinuousCollectionRunner(service,execution_kwargs),calendar,lock_repository,
                             "continuous-market-collection",ttl_seconds)
