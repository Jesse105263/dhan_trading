from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from uuid import UUID,uuid5

from services.feature_store_v2_models import (
    FeatureAnchorV2,FeatureDefinitionV2,FeatureMaterializationResultV2,FeatureSchemaV2,FeatureValueV2,
)
from services.feature_store_v2_repository import FeatureStoreV2Repository


class FeatureStoreV2Service:
    NAMESPACE=UUID("8c27de47-9958-4e33-84f3-09b27fcd86bb")
    DEFAULT_SCHEMA=FeatureSchemaV2("canonical-market-features-v2",(
        FeatureDefinitionV2("close_price","price","anchor.close_price","REQUIRED","NONE",1,"Canonical raw close."),
        FeatureDefinitionV2("return_1_bar_pct","returns","pct(close[t-1],close[t])","PRESERVE_NULL","ZSCORE_TRAIN_WINDOW",2,"One-bar close return."),
        FeatureDefinitionV2("return_3_bar_pct","returns","pct(close[t-3],close[t])","PRESERVE_NULL","ZSCORE_TRAIN_WINDOW",4,"Three-bar close return."),
        FeatureDefinitionV2("range_pct","volatility","(high-low)/close*100","REQUIRED","ZSCORE_TRAIN_WINDOW",1,"Anchor high-low range relative to close."),
        FeatureDefinitionV2("gap_return_pct","returns","pct(close[t-1],open[t])","PRESERVE_NULL","ZSCORE_TRAIN_WINDOW",2,"Open gap from prior close."),
        FeatureDefinitionV2("realized_volatility_5","volatility","population_std(last_5_close_returns)","PRESERVE_NULL","ZSCORE_TRAIN_WINDOW",6,"Five-return realized volatility."),
        FeatureDefinitionV2("average_range_pct_5","volatility","mean(last_5_range_pct)","PRESERVE_NULL","ZSCORE_TRAIN_WINDOW",5,"Five-bar mean range."),
        FeatureDefinitionV2("volume","volume","anchor.volume","PRESERVE_NULL","LOG1P",1,"Reported volume without imputation."),
        FeatureDefinitionV2("volume_change_1_pct","volume","pct(volume[t-1],volume[t])","PRESERVE_NULL","ZSCORE_TRAIN_WINDOW",2,"One-bar volume change."),
        FeatureDefinitionV2("open_interest","derivatives","anchor.open_interest","NOT_APPLICABLE","LOG1P",1,"Reported futures/options open interest."),
        FeatureDefinitionV2("open_interest_change_1_pct","derivatives","pct(oi[t-1],oi[t])","NOT_APPLICABLE","ZSCORE_TRAIN_WINDOW",2,"One-bar open-interest change."),
        FeatureDefinitionV2("bid_ask_spread_pct","liquidity","pct(mid,bid_ask_spread)","PRESERVE_NULL","MINMAX_TRAIN_WINDOW",1,"Quoted spread relative to midpoint."),
        FeatureDefinitionV2("minute_of_day","temporal","hour*60+minute","REQUIRED","MINMAX_TRAIN_WINDOW",1,"Exchange-local encoded bar close minute."),
        FeatureDefinitionV2("day_of_week","temporal","weekday(session_date)","REQUIRED","NONE",1,"Session weekday, Monday zero."),
        FeatureDefinitionV2("days_to_expiry","temporal","expiry-session_date","NOT_APPLICABLE","MINMAX_TRAIN_WINDOW",1,"Calendar days to derivative expiry."),
        FeatureDefinitionV2("trend_regime_3","regime","sign(return_3_bar_pct)","PRESERVE_NULL","NONE",4,"Transparent three-bar trend regime."),
        FeatureDefinitionV2("volatility_regime_ratio","regime","range_pct/average_range_pct_5","PRESERVE_NULL","ZSCORE_TRAIN_WINDOW",5,"Current range relative to trailing range."),
    ),compatible_schema_versions=("option-observation-v1",))

    def __init__(self,repository=None,clock=datetime.now): self.repository=repository or FeatureStoreV2Repository(); self.clock=clock

    def materialize(self,schema:FeatureSchemaV2=DEFAULT_SCHEMA,*,as_of:datetime|None=None,limit:int|None=None,batch_size:int=250)->FeatureMaterializationResultV2:
        if limit is not None and limit<1: raise ValueError("limit must be positive.")
        if not 1<=batch_size<=1000: raise ValueError("batch_size must be between 1 and 1000.")
        cutoff=(as_of or self.clock()).replace(tzinfo=None); started=self.clock(); definition_bytes=self._canonical(asdict(schema)); definition_checksum=hashlib.sha256(definition_bytes).hexdigest()
        run_id=uuid5(self.NAMESPACE,f"run:{schema.schema_version}:{cutoff.isoformat()}:{definition_checksum}")
        anchors=[]; after_at=after_id=None
        while limit is None or len(anchors)<limit:
            size=min(batch_size,limit-len(anchors)) if limit is not None else batch_size
            page=self.repository.anchors(cutoff,size,after_at,after_id)
            if not page: break
            anchors.extend(page); after_at=page[-1].available_at; after_id=page[-1].bar_revision_id
            if len(page)<size: break
        definitions=[]
        for item in schema.definitions:
            checksum=hashlib.sha256(self._canonical(asdict(item))).hexdigest(); definitions.append({"definition_id":uuid5(self.NAMESPACE,f"definition:{schema.schema_version}:{item.name}"),
                "schema_version":schema.schema_version,"feature_name":item.name,"feature_family":item.family,"formula":item.formula,"missing_policy":item.missing_policy,
                "normalization_policy":item.normalization_policy,"minimum_history":item.minimum_history,"description":item.description,"definition_checksum":checksum})
        definition_map={item["feature_name"]:item for item in definitions}; vectors=[]; counts={"complete_count":0,"partial_count":0,"insufficient_count":0}
        for anchor in anchors:
            vector,values=self._build(anchor,self.repository.history(anchor),schema,definition_map,definition_checksum,run_id)
            vectors.append((vector,values)); counts[vector["quality_state"].lower()+"_count"]+=1
        counts["vector_count"]=len(vectors); completed=self.clock()
        self.repository.persist({"run_id":run_id,"schema_version":schema.schema_version,"definition_checksum":definition_checksum,
            "compatible_schema_versions":list(schema.compatible_schema_versions),"compatible_outcome_models":list(schema.compatible_outcome_models),
            "definitions":definitions,"as_of":cutoff,"anchor_count":len(anchors),"counts":counts,"vectors":vectors,"started_at":started,"completed_at":completed})
        return FeatureMaterializationResultV2(run_id,len(anchors),len(vectors),counts["complete_count"],counts["partial_count"],counts["insufficient_count"])

    def _build(self,anchor:FeatureAnchorV2,history:list[FeatureAnchorV2],schema:FeatureSchemaV2,definitions,definition_checksum,run_id):
        raw={
            "close_price":FeatureValueV2("close_price",Decimal(anchor.close_price) if anchor.close_price is not None else None,None if anchor.close_price is not None else "SOURCE_VALUE_MISSING",(anchor.bar_revision_id,)),
            "return_1_bar_pct":self._trailing_return("return_1_bar_pct",history,1),"return_3_bar_pct":self._trailing_return("return_3_bar_pct",history,3),
            "range_pct":self._value("range_pct",self._range(anchor),(anchor.bar_revision_id,)),"gap_return_pct":self._gap(history),
            "realized_volatility_5":self._volatility(history,5),"average_range_pct_5":self._average_range(history,5),
            "volume":self._source("volume",anchor.volume,anchor),"volume_change_1_pct":self._source_change("volume_change_1_pct",history,"volume"),
            "open_interest":self._source("open_interest",anchor.open_interest,anchor,"NOT_APPLICABLE_FOR_INSTRUMENT"),
            "open_interest_change_1_pct":self._source_change("open_interest_change_1_pct",history,"open_interest","NOT_APPLICABLE_FOR_INSTRUMENT"),
            "bid_ask_spread_pct":self._spread(anchor),"minute_of_day":self._value("minute_of_day",Decimal(anchor.bar_close_at.hour*60+anchor.bar_close_at.minute),(anchor.bar_revision_id,)),
            "day_of_week":self._value("day_of_week",Decimal(anchor.session_date.weekday()),(anchor.bar_revision_id,)),
            "days_to_expiry":self._value("days_to_expiry",Decimal((anchor.expiry-anchor.session_date).days) if anchor.expiry else None,(anchor.bar_revision_id,),"NOT_APPLICABLE_FOR_INSTRUMENT"),
        }
        ret3=raw["return_3_bar_pct"]; raw["trend_regime_3"]=self._value("trend_regime_3",Decimal(1 if ret3.value>0 else -1 if ret3.value<0 else 0) if ret3.value is not None else None,ret3.source_revision_ids,ret3.missing_reason)
        avg=raw["average_range_pct_5"]; current=raw["range_pct"]
        regime_missing=avg.missing_reason if avg.value is None else "ZERO_TRAILING_RANGE" if avg.value==0 else None
        raw["volatility_regime_ratio"]=self._value("volatility_regime_ratio",current.value/avg.value if current.value is not None and avg.value not in (None,0) else None,tuple(dict.fromkeys((*current.source_revision_ids,*avg.source_revision_ids))),regime_missing)
        values=[]; missing=0; required_missing=0; family_counts={}
        for definition in schema.definitions:
            item=raw[definition.name]; missing+=item.value is None; required_missing+=item.value is None and definition.missing_policy=="REQUIRED"
            family_counts.setdefault(definition.family,[0,0]); family_counts[definition.family][0]+=1; family_counts[definition.family][1]+=item.value is not None
            document={"name":item.name,"value":item.value,"missing_reason":item.missing_reason,"sources":[str(value) for value in item.source_revision_ids]}
            values.append({"definition_id":definitions[item.name]["definition_id"],"feature_name":item.name,"numeric_value":item.value,
                "missing_reason":item.missing_reason,"source_revision_ids":[str(value) for value in item.source_revision_ids],"value_checksum":hashlib.sha256(self._canonical(document)).hexdigest()})
        state="INSUFFICIENT" if required_missing else "PARTIAL" if missing else "COMPLETE"; present=len(schema.definitions)-missing
        lineage={"anchor":str(anchor.bar_revision_id),"history":[str(item.bar_revision_id) for item in history],"definitions":definition_checksum}
        vector={"vector_id":uuid5(self.NAMESPACE,f"vector:{schema.schema_version}:{anchor.bar_revision_id}"),"run_id":run_id,"schema_version":schema.schema_version,
            "instrument_id":anchor.instrument_id,"underlying_instrument_id":anchor.underlying_instrument_id,"subject_type":"OPTION" if anchor.instrument_class=="OPTION" else "FUTURE" if anchor.instrument_class=="FUTURE" else "UNDERLYING",
            "anchor_bar_revision_id":anchor.bar_revision_id,"anchor_manifest_id":anchor.manifest_id,"interval_code":anchor.interval_code,"observed_at":anchor.bar_close_at,
            "available_at":anchor.available_at,"quality_state":state,"feature_count":len(schema.definitions),"present_feature_count":present,"missing_feature_count":missing,
            "coverage_percentage":Decimal(present)*100/Decimal(len(schema.definitions)),"quality_metrics":{"history_observation_count":len(history),"family_coverage":{key:{"present":value[1],"total":value[0]} for key,value in family_counts.items()}},
            "definition_checksum":definition_checksum,"lineage_checksum":hashlib.sha256(self._canonical(lineage)).hexdigest(),"materialized_at":self.clock()}
        return vector,values

    @classmethod
    def _trailing_return(cls,name,history,lag):
        if len(history)<=lag:return cls._value(name,None,tuple(item.bar_revision_id for item in history),"INSUFFICIENT_HISTORY")
        subset=history[-lag-1:]; return cls._value(name,cls._pct(subset[0].close_price,subset[-1].close_price),tuple(item.bar_revision_id for item in subset))
    @classmethod
    def _gap(cls,history):
        if len(history)<2:return cls._value("gap_return_pct",None,tuple(item.bar_revision_id for item in history),"INSUFFICIENT_HISTORY")
        return cls._value("gap_return_pct",cls._pct(history[-2].close_price,history[-1].open_price),(history[-2].bar_revision_id,history[-1].bar_revision_id))
    @classmethod
    def _volatility(cls,history,count):
        if len(history)<count+1:return cls._value("realized_volatility_5",None,tuple(item.bar_revision_id for item in history),"INSUFFICIENT_HISTORY")
        subset=history[-count-1:]; returns=[cls._pct(subset[i-1].close_price,subset[i].close_price) for i in range(1,len(subset))]; mean=sum(returns,Decimal(0))/len(returns)
        return cls._value("realized_volatility_5",(sum(((item-mean)**2 for item in returns),Decimal(0))/len(returns)).sqrt(),tuple(item.bar_revision_id for item in subset))
    @classmethod
    def _average_range(cls,history,count):
        if len(history)<count:return cls._value("average_range_pct_5",None,tuple(item.bar_revision_id for item in history),"INSUFFICIENT_HISTORY")
        subset=history[-count:]; values=[cls._range(item) for item in subset]
        if any(value is None for value in values):return cls._value("average_range_pct_5",None,tuple(item.bar_revision_id for item in subset),"SOURCE_VALUE_MISSING")
        return cls._value("average_range_pct_5",sum(values,Decimal(0))/len(values),tuple(item.bar_revision_id for item in subset))
    @classmethod
    def _source_change(cls,name,history,field,not_applicable="SOURCE_VALUE_MISSING"):
        if len(history)<2:return cls._value(name,None,tuple(item.bar_revision_id for item in history),"INSUFFICIENT_HISTORY")
        previous,current=history[-2:]; a=getattr(previous,field); b=getattr(current,field)
        return cls._value(name,cls._pct(a,b) if a is not None and b is not None else None,(previous.bar_revision_id,current.bar_revision_id),None if a is not None and b is not None else not_applicable)
    @classmethod
    def _spread(cls,anchor):
        if anchor.bid_price is None or anchor.ask_price is None:return cls._value("bid_ask_spread_pct",None,(anchor.bar_revision_id,),"SOURCE_VALUE_MISSING")
        midpoint=(Decimal(anchor.bid_price)+Decimal(anchor.ask_price))/2
        return cls._value("bid_ask_spread_pct",((Decimal(anchor.ask_price)-Decimal(anchor.bid_price))/midpoint)*100 if midpoint else None,(anchor.bar_revision_id,),"ZERO_MIDPOINT" if not midpoint else None)
    @classmethod
    def _range(cls,bar): return ((Decimal(bar.high_price)-Decimal(bar.low_price))/Decimal(bar.close_price))*100 if bar.close_price not in (None,0) else None
    @staticmethod
    def _pct(a,b): return ((Decimal(b)-Decimal(a))/Decimal(a))*100 if a not in (None,0) and b is not None else None
    @staticmethod
    def _source(name,value,anchor,missing="SOURCE_VALUE_MISSING"): return FeatureStoreV2Service._value(name,Decimal(value) if value is not None else None,(anchor.bar_revision_id,),None if value is not None else missing)
    @staticmethod
    def _value(name,value,sources,missing=None): return FeatureValueV2(name,value,missing if value is None else None,tuple(sources))
    @staticmethod
    def _canonical(value): return json.dumps(value,sort_keys=True,separators=(",",":"),default=lambda item:item.isoformat() if hasattr(item,"isoformat") else str(item)).encode()
