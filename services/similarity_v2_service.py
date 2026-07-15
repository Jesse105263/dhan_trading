from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from uuid import UUID, uuid5

from services.similarity_v2_models import SimilarityPolicyV2, SimilarityResultV2
from services.similarity_v2_repository import SimilarityV2Repository


class SimilarityV2Service:
    NAMESPACE=UUID("418bff7d-b4ce-4bc3-9699-34fdbecce491")

    def __init__(self, repository=None, clock=datetime.now): self.repository=repository or SimilarityV2Repository(); self.clock=clock

    def materialize(self, query_vector_id, policy, *, cutoff=None):
        query=self.repository.vector(query_vector_id)
        if query is None: raise ValueError("Query Feature Store V2 vector was not found.")
        effective=(cutoff or query["observed_at"]).replace(tzinfo=None)
        if effective>query["observed_at"]: raise ValueError("Similarity cutoff cannot exceed the query observation.")
        policy_doc=json.loads(json.dumps(asdict(policy),default=str)); checksum=self._hash(policy_doc)
        selected=policy.selected_features or tuple(sorted(query["features"]))
        candidates=self.repository.candidates(query,effective,policy)
        eligible=[]
        for candidate in candidates:
            if policy.same_regime and not self._same_regime(query,candidate): continue
            if policy.minimum_liquidity_value is not None:
                liquidity=candidate["features"].get("bid_ask_spread_pct")
                if liquidity is None or Decimal(liquidity)>policy.minimum_liquidity_value: continue
            eligible.append(candidate)
        scales=self._scales(eligible,selected)
        ranked=[]
        for candidate in eligible:
            item=self._distance(query,candidate,selected,scales,policy)
            if item is not None: ranked.append(item)
        ranked=self._rank(ranked,policy)[:policy.maximum_matches]
        outcomes=self.repository.outcomes([item["candidate"] for item in ranked],query["observed_at"])
        state="SUFFICIENT" if len(ranked)>=policy.minimum_candidates else "INSUFFICIENT_EVIDENCE"
        now=self.clock(); run_id=uuid5(self.NAMESPACE,f"{query_vector_id}:{effective.isoformat()}:{checksum}")
        matches=[]
        for position,item in enumerate(ranked,1):
            candidate=item.pop("candidate"); outcome=outcomes.get(candidate["anchor_bar_revision_id"])
            lineage={"query":str(query_vector_id),"candidate":str(candidate["vector_id"]),"feature_lineage":candidate["lineage_checksum"],"outcome":str(outcome["outcome_id"]) if outcome else None}
            matches.append({"match_id":uuid5(self.NAMESPACE,f"{run_id}:{candidate['vector_id']}"),"run_id":run_id,
                "rank_position":position,"matched_vector_id":candidate["vector_id"],"matched_outcome_id":outcome["outcome_id"] if outcome else None,
                "distance":item["distance"],"similarity_score":item["similarity_score"],"evidence_quality_score":item["quality"],
                "shared_feature_count":item["shared"],"feature_diagnostics":item["diagnostics"],"filter_diagnostics":item["filters"],
                "lineage_checksum":self._hash(lineage)})
        lineage={"query":str(query_vector_id),"candidates":[str(item["matched_vector_id"]) for item in matches],"policy":checksum}
        run={"run_id":run_id,"model_version":policy.model_version,"query_vector_id":query_vector_id,"query_observed_at":query["observed_at"],
            "cutoff_at":effective,"policy_checksum":checksum,"candidate_count":len(eligible),"match_count":len(matches),"evidence_state":state,
            "quality_metrics":{"selected_features":list(selected),"normalization_population":len(eligible),"outcome_count":sum(item["matched_outcome_id"] is not None for item in matches)},
            "lineage_checksum":self._hash(lineage),"started_at":now,"completed_at":self.clock()}
        self.repository.persist({"model_version":policy.model_version,"policy_checksum":checksum,"feature_schema_version":query["schema_version"],
            "compatible_outcome_model":"canonical-path-outcome-v2","policy":policy_doc,"started_at":now,"run":run,"matches":matches})
        return SimilarityResultV2(run_id,len(eligible),len(matches),state)

    @staticmethod
    def _scales(candidates,selected):
        scales={}
        for name in selected:
            values=[Decimal(item["features"][name]) for item in candidates if item["features"].get(name) is not None]
            if values: scales[name]=(min(values),max(values))
        return scales

    def _distance(self,query,candidate,selected,scales,policy):
        diagnostics={}; weighted=[]; cosine=[]
        for name in selected:
            left=query["features"].get(name); right=candidate["features"].get(name)
            if left is None or right is None or name not in scales: continue
            low,high=scales[name]; width=high-low
            q=Decimal(0) if width==0 else (Decimal(left)-low)/width; c=Decimal(0) if width==0 else (Decimal(right)-low)/width
            family=query["families"].get(name); weight=policy.feature_weights.get(name,Decimal(1))*policy.family_weights.get(family,Decimal(1))
            delta=abs(q-c); weighted.append((delta,weight)); cosine.append((q,c,weight))
            diagnostics[name]={"family":family,"weight":str(weight),"query_normalized":str(q),"candidate_normalized":str(c),"absolute_delta":str(delta)}
        if len(weighted)<policy.minimum_shared_features: return None
        if policy.distance_model=="WEIGHTED_MANHATTAN": distance=sum((d*w for d,w in weighted),Decimal(0))/sum((w for _,w in weighted),Decimal(0))
        elif policy.distance_model=="WEIGHTED_EUCLIDEAN": distance=(sum((d*d*w for d,w in weighted),Decimal(0))/sum((w for _,w in weighted),Decimal(0))).sqrt()
        else:
            dot=sum((a*b*w for a,b,w in cosine),Decimal(0)); left=sum((a*a*w for a,_,w in cosine),Decimal(0)).sqrt(); right=sum((b*b*w for _,b,w in cosine),Decimal(0)).sqrt()
            distance=Decimal(1)-(dot/(left*right) if left and right else Decimal(0))
        quality=(Decimal(query["coverage_percentage"])+Decimal(candidate["coverage_percentage"]))/Decimal(200)
        return {"candidate":candidate,"distance":distance,"similarity_score":max(Decimal(0),Decimal(1)-distance),"quality":quality,
            "shared":len(weighted),"diagnostics":diagnostics,"filters":{"regime_match":self._same_regime(query,candidate),"age_seconds":int((query["observed_at"]-candidate["observed_at"]).total_seconds())}}

    @staticmethod
    def _rank(rows,policy):
        if policy.ranking_strategy=="EVIDENCE_QUALITY": key=lambda x:(-x["quality"],x["distance"],x["candidate"]["observed_at"],str(x["candidate"]["vector_id"]))
        elif policy.ranking_strategy=="TEMPORAL_DIVERSITY": key=lambda x:(x["distance"],x["candidate"]["observed_at"].date().toordinal()//policy.temporal_bucket_days,str(x["candidate"]["vector_id"]))
        else: key=lambda x:(x["distance"],x["candidate"]["observed_at"],str(x["candidate"]["vector_id"]))
        ordered=sorted(rows,key=key)
        if policy.ranking_strategy!="TEMPORAL_DIVERSITY": return ordered
        result=[]; buckets=set()
        for item in ordered:
            bucket=item["candidate"]["observed_at"].date().toordinal()//policy.temporal_bucket_days
            if bucket in buckets: continue
            buckets.add(bucket); result.append(item)
        return result

    @staticmethod
    def _same_regime(left,right):
        regime=left["features"].get("trend_regime_3")
        return regime is not None and regime==right["features"].get("trend_regime_3")
    @staticmethod
    def _hash(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
