from dataclasses import dataclass
from datetime import date
from decimal import Decimal

STATES={'ELIGIBLE','INSUFFICIENT_EVIDENCE','UNCERTAIN','UNCALIBRATED','NEGATIVE_CONSERVATIVE_EV','CONCENTRATED_EVIDENCE','OUT_OF_DISTRIBUTION','DATA_QUALITY_FAILURE','DRIFT_SUSPENDED','ILLIQUID','INELIGIBLE'}
@dataclass(frozen=True)
class CalibrationPeriod:
 name:str; start:date; end:date
@dataclass(frozen=True)
class CalibrationPolicyV2:
 policy_id:object; policy_version:str; strategy:str; direction:str; holding_horizon:str
 liquidity_regime:str; volatility_regime:str; market_regime:str; periods:tuple[CalibrationPeriod,...]
 purge_days:int=45; embargo_days:int=7; minimum_sample_size:int=30; minimum_effective_sample_size:Decimal=Decimal(30)
 calibration_error_threshold:Decimal=Decimal('.10'); uncertainty_threshold:Decimal=Decimal('.30'); concentration_threshold:Decimal=Decimal('.50')
 out_of_distribution_threshold:Decimal=Decimal('.75'); minimum_data_quality:Decimal=Decimal('.90'); maximum_drift:Decimal=Decimal('.10')
 conservative_ev_threshold:Decimal=Decimal(0); method:str='MONOTONIC_BINNING'; bin_count:int=5; bootstrap_samples:int=200; seed:int=37
 def __post_init__(self):
  if not self.policy_version or self.method not in {'EMPIRICAL_BINNING','MONOTONIC_BINNING'} or self.bin_count<2:raise ValueError('Invalid calibration policy.')
  if tuple(p.name for p in self.periods)!=('TRAIN','VALIDATION','CALIBRATION','TEST'):raise ValueError('Four ordered research periods are required.')
  if any(p.start>p.end for p in self.periods) or any(a.end>=b.start for a,b in zip(self.periods,self.periods[1:])):raise ValueError('Research periods must be ordered and disjoint.')
  if self.purge_days<0 or self.embargo_days<0 or self.minimum_sample_size<1 or self.bootstrap_samples<1:raise ValueError('Invalid sample/split policy.')
@dataclass(frozen=True)
class CalibrationResultV2:
 run_id:object; state:str; sample_size:int
@dataclass(frozen=True)
class RecommendationResultV2:
 evaluation_id:object; state:str; eligible:bool
