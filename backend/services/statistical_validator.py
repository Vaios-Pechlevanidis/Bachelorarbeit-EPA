from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import math


class RiskLevel(str, Enum):
    LIMITED = "limited"
    CONSTRAINED = "constrained"
    ACCEPTABLE = "acceptable"
    SOLID = "solid"


@dataclass
class SampleSizeAssessment:
    n: int
    risk_level: RiskLevel
    risk_description: str
    clt_assessment: str
    power_assessment: str
    ci_width_estimate: float
    recommendations: list[str]
    requires_nonparametric: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_size": self.n,
            "risk_level": self.risk_level.value,
            "risk_description": self.risk_description,
            "clt_assessment": self.clt_assessment,
            "power_assessment": self.power_assessment,
            "ci_width_estimate": self.ci_width_estimate,
            "recommendations": self.recommendations,
            "requires_nonparametric": self.requires_nonparametric
        }


class StatisticalValidator:
    HEURISTIC_CLT = 30
    HEURISTIC_POWER = 64
    HEURISTIC_PRECISION = 100
    
    HEURISTIC_ANOVA_PER_GROUP = 30
    
    def __init__(self, assumed_std: float = 1.0, alpha: float = 0.05):
        self.assumed_std = assumed_std
        self.alpha = alpha
        self.z_critical = 1.96
    
    def assess_sample_size(self, n: int) -> SampleSizeAssessment:
        risk_level = self._determine_risk_level(n)
        
        clt_assessment = self._assess_clt(n)
        
        power_assessment = self._assess_power(n)
        
        ci_width = self._estimate_ci_width(n)
        
        recommendations = self._generate_recommendations(n, risk_level)
        
        requires_nonparametric = n < self.HEURISTIC_CLT
        
        risk_description = self._get_risk_description(risk_level)
        
        return SampleSizeAssessment(
            n=n,
            risk_level=risk_level,
            risk_description=risk_description,
            clt_assessment=clt_assessment,
            power_assessment=power_assessment,
            ci_width_estimate=ci_width,
            recommendations=recommendations,
            requires_nonparametric=requires_nonparametric
        )
    
    def _determine_risk_level(self, n: int) -> RiskLevel:
        if n < self.HEURISTIC_CLT:
            return RiskLevel.LIMITED
        elif n < self.HEURISTIC_POWER:
            return RiskLevel.CONSTRAINED
        elif n < self.HEURISTIC_PRECISION:
            return RiskLevel.ACCEPTABLE
        else:
            return RiskLevel.SOLID
    
    def _get_risk_description(self, risk_level: RiskLevel) -> str:
        descriptions = {
            RiskLevel.LIMITED: "Begrenzte Datenbasis",
            RiskLevel.CONSTRAINED: "Eingeschränkte Aussagekraft",
            RiskLevel.ACCEPTABLE: "Akzeptable Basis",
            RiskLevel.SOLID: "Solide Datenbasis"
        }
        return descriptions[risk_level]
    
    def _assess_clt(self, n: int) -> str:
        if n < self.HEURISTIC_CLT:
            return (
                f"CLT-Approximation unsicher bei n={n}. Bei rechtschiefen Bewertungsverteilungen "
                f"(Häufung bei 5★) kann deutlich größeres n erforderlich sein."
            )
        elif n < 50:
            return (
                f"CLT-Approximation wahrscheinlich ausreichend bei n={n} für moderate Schiefe. "
                f"Bei starken Ceiling-Effekten Vorsicht geboten."
            )
        else:
            return (
                f"CLT-Approximation robust bei n={n}. Normalverteilung der Mittelwerte "
                f"auch bei schiefen Ausgangsverteilungen plausibel."
            )
    
    def _assess_power(self, n: int) -> str:
        if n < self.HEURISTIC_POWER:
            return (
                f"Power wahrscheinlich <80% bei n={n} für mittlere Effekte (d≈0.5). "
                f"Risiko für Typ-II-Fehler erhöht. Ex-post Effektstärken berichten."
            )
        elif n < self.HEURISTIC_PRECISION:
            return (
                f"Power wahrscheinlich ≈80% bei n={n} für mittlere Effekte. "
                f"Kleine Effekte (d<0.3) möglicherweise nicht detektierbar."
            )
        else:
            return (
                f"Power wahrscheinlich >80% bei n={n} auch für mittlere bis kleine Effekte. "
                f"Gute Sensitivität für relevante Unterschiede."
            )
    
    def _estimate_ci_width(self, n: int) -> float:
        if n == 0:
            return float('inf')
        
        moe = self.z_critical * (self.assumed_std / math.sqrt(n))
        return round(moe, 2)
    
    def _generate_recommendations(self, n: int, risk_level: RiskLevel) -> list[str]:
        recommendations = []
        
        recommendations.append(
            "Effektstärken (Cohen's d) und Konfidenzintervalle zusätzlich zu p-Werten berichten"
        )
        
        if n < self.HEURISTIC_CLT:
            recommendations.append(
                "Nicht-parametrische Tests (Mann-Whitney-U, Kruskal-Wallis) bevorzugen"
            )
            recommendations.append(
                "Ergebnisse mit Vorsicht interpretieren - CLT-Approximation unsicher"
            )
        else:
            recommendations.append(
                "Nicht-parametrische Sensitivitätsanalysen parallel durchführen"
            )
        
        if n < self.HEURISTIC_POWER:
            recommendations.append(
                "Ex-post Power-Analyse durchführen und berichten"
            )
            recommendations.append(
                "Null-Befunde nicht als 'kein Effekt' interpretieren (Typ-II-Fehler möglich)"
            )
        
        if n < self.HEURISTIC_PRECISION:
            moe = self._estimate_ci_width(n)
            recommendations.append(
                f"Konfidenzintervalle breit (±{moe}★) - Schätzungen unpräzise"
            )
        
        if risk_level in [RiskLevel.LIMITED, RiskLevel.CONSTRAINED]:
            recommendations.append(
                "Bei Topic-ANOVA: Ungleiche Gruppengrößen reduzieren Power für kleine Topics"
            )
        
        return recommendations
    
    def assess_comparison(
        self, 
        n1: int, 
        n2: int,
        comparison_type: Literal["two_group", "anova"] = "two_group"
    ) -> Dict[str, Any]:
        if comparison_type == "two_group":
            assessment1 = self.assess_sample_size(n1)
            assessment2 = self.assess_sample_size(n2)
            
            overall_risk = (
                assessment1.risk_level 
                if assessment1.risk_level.value < assessment2.risk_level.value 
                else assessment2.risk_level
            )
            
            return {
                "comparison_type": "two_group",
                "group1": assessment1.to_dict(),
                "group2": assessment2.to_dict(),
                "overall_risk": overall_risk.value,
                "notes": [
                    "Ungleiche Gruppengrößen beeinflussen Power",
                    "Kleinere Gruppe limitiert Gesamtaussagekraft"
                ]
            }
        
        elif comparison_type == "anova":
            total_n = n1
            k_groups = n2 if n2 > 0 else 1
            avg_per_group = total_n / k_groups if k_groups > 0 else 0
            
            assessment = self.assess_sample_size(int(avg_per_group))
            
            anova_notes = [
                f"Durchschnittlich n≈{int(avg_per_group)} pro Gruppe bei k={k_groups} Gruppen",
                f"Maxwell & Delaney (2017): n≈{self.HEURISTIC_ANOVA_PER_GROUP} pro Gruppe empfohlen für f=0.25"
            ]
            
            if avg_per_group < self.HEURISTIC_ANOVA_PER_GROUP:
                anova_notes.append(
                    "WARNUNG: Durchschnittliche Gruppengröße unter Heuristik - Power reduziert"
                )
            
            return {
                "comparison_type": "anova",
                "total_n": total_n,
                "k_groups": k_groups,
                "avg_per_group": int(avg_per_group),
                "assessment": assessment.to_dict(),
                "notes": anova_notes
            }
        
        else:
            raise ValueError(f"Unknown comparison_type: {comparison_type}")
    
    def validate_correlation_stability(self, n: int) -> Dict[str, Any]:
        HEURISTIC_CORRELATION = 250
        
        if n < 100:
            stability = "instabil"
            confidence = "sehr niedrig"
            warning = "Korrelationen können stark variieren - nicht verallgemeinerbar"
        elif n < 150:
            stability = "niedrig"
            confidence = "niedrig"
            warning = "Korrelationen noch volatil - vorsichtige Interpretation"
        elif n < HEURISTIC_CORRELATION:
            stability = "moderat"
            confidence = "moderat"
            warning = "Korrelationen nähern sich Stabilität - moderate Verallgemeinerbarkeit"
        else:
            stability = "stabil"
            confidence = "hoch"
            warning = None
        
        return {
            "sample_size": n,
            "stability": stability,
            "confidence": confidence,
            "warning": warning,
            "reference": "Schönbrodt & Perugini (2013): Korrelationen stabilisieren sich ab n≈250"
        }


def validate_sample_size(n: int) -> Dict[str, Any]:
    validator = StatisticalValidator()
    assessment = validator.assess_sample_size(n)
    return assessment.to_dict()


if __name__ == "__main__":
    validator = StatisticalValidator()
    
    test_sizes = [15, 30, 64, 100, 250]
    
    print("Sample Size Assessment Examples")
    print("=" * 80)
    
    for n in test_sizes:
        assessment = validator.assess_sample_size(n)
        print(f"\nn = {n}")
        print(f"Risk Level: {assessment.risk_level.value}")
        print(f"Description: {assessment.risk_description}")
        print(f"CI Width: ±{assessment.ci_width_estimate}★")
        print(f"Non-parametric required: {assessment.requires_nonparametric}")
        print("Recommendations:")
        for rec in assessment.recommendations[:3]:
            print(f"  - {rec}")
