from typing import Dict, Any, List, Optional
from services.statistical_validator import StatisticalValidator, RiskLevel


def enrich_with_statistical_metadata(
    data: Dict[str, Any],
    sample_size: int,
    analysis_type: str = "general"
) -> Dict[str, Any]:
    validator = StatisticalValidator()
    assessment = validator.assess_sample_size(sample_size)
    
    data["statistical_meta"] = {
        "sample_size": sample_size,
        "risk_level": assessment.risk_level.value,
        "risk_description": assessment.risk_description,
        "ci_width_estimate": assessment.ci_width_estimate,
        "requires_nonparametric": assessment.requires_nonparametric,
        "analysis_type": analysis_type
    }
    
    warnings = []
    if assessment.risk_level == RiskLevel.LIMITED:
        warnings.append({
            "severity": "high",
            "message": "Begrenzte Datenbasis: Ergebnisse mit Vorsicht interpretieren",
            "details": assessment.clt_assessment
        })
    elif assessment.risk_level == RiskLevel.CONSTRAINED:
        warnings.append({
            "severity": "medium",
            "message": "Eingeschränkte Aussagekraft: Breite Konfidenzintervalle",
            "details": assessment.power_assessment
        })
    
    if warnings:
        data["statistical_meta"]["warnings"] = warnings
    
    return data


def enrich_topic_analysis_with_metadata(
    topics_data: List[Dict[str, Any]],
    total_sample_size: int
) -> List[Dict[str, Any]]:
    validator = StatisticalValidator()
    
    enriched_topics = []
    for topic in topics_data:
        enriched_topic = topic.copy()
        
        topic_n = topic.get("frequency", 0) or topic.get("count", 0) or topic.get("review_count", 0) or 0
        
        if topic_n > 0:
            assessment = validator.assess_sample_size(topic_n)
            
            enriched_topic["statistical_meta"] = {
                "sample_size": topic_n,
                "risk_level": assessment.risk_level.value,
                "risk_description": assessment.risk_description,
                "ci_width_estimate": assessment.ci_width_estimate,
                "share_of_total": round((topic_n / total_sample_size) * 100, 1) if total_sample_size > 0 else 0
            }
            
            if assessment.risk_level == RiskLevel.LIMITED:
                enriched_topic["statistical_meta"]["warning"] = (
                    f"Nur {topic_n} Reviews - statistische Aussagekraft begrenzt"
                )
        
        enriched_topics.append(enriched_topic)
    
    return enriched_topics


def enrich_comparison_with_metadata(
    data: Dict[str, Any],
    n1: int,
    n2: int,
    group1_label: str = "Gruppe 1",
    group2_label: str = "Gruppe 2"
) -> Dict[str, Any]:
    validator = StatisticalValidator()
    comparison = validator.assess_comparison(n1, n2, "two_group")
    
    data["comparison_meta"] = {
        "groups": {
            group1_label: {
                "n": n1,
                "risk_level": comparison["group1"]["risk_level"],
                "risk_description": comparison["group1"]["risk_description"]
            },
            group2_label: {
                "n": n2,
                "risk_level": comparison["group2"]["risk_level"],
                "risk_description": comparison["group2"]["risk_description"]
            }
        },
        "overall_risk": comparison["overall_risk"],
        "notes": comparison["notes"]
    }
    
    if abs(n1 - n2) > max(n1, n2) * 0.5:
        data["comparison_meta"]["warning"] = (
            f"Ungleiche Gruppengrößen ({n1} vs {n2}) - "
            "kleinere Gruppe limitiert Aussagekraft"
        )
    
    return data


def get_methodological_notes(
    sample_size: int,
    analysis_type: str = "general"
) -> List[str]:
    validator = StatisticalValidator()
    assessment = validator.assess_sample_size(sample_size)
    
    notes = [
        f"Stichprobengröße: n={sample_size} ({assessment.risk_description})",
        f"Geschätzte Margin of Error: ±{assessment.ci_width_estimate}★ (95% CI)",
    ]
    
    notes.extend(assessment.recommendations[:3])
    
    if analysis_type == "comparison":
        notes.append(
            "Effektstärken (Cohen's d) und Konfidenzintervalle werden zusätzlich zu p-Werten berichtet"
        )
    elif analysis_type == "anova":
        notes.append(
            "Bei ungleicher Topic-Verteilung sinkt die Power für kleinere Gruppen"
        )
    
    return notes


def should_use_nonparametric(sample_size: int) -> bool:
    validator = StatisticalValidator()
    return sample_size < validator.HEURISTIC_CLT


def get_ui_badge_config(risk_level: str) -> Dict[str, str]:
    configs = {
        "limited": {
            "color": "red",
            "icon": "⚠️",
            "label": "Begrenzte Datenbasis",
            "description": "Statistische Aussagekraft eingeschränkt"
        },
        "constrained": {
            "color": "orange",
            "icon": "⚡",
            "label": "Eingeschränkte Aussagekraft",
            "description": "Moderate statistische Robustheit"
        },
        "acceptable": {
            "color": "yellow",
            "icon": "✓",
            "label": "Akzeptable Basis",
            "description": "Gute statistische Basis"
        },
        "solid": {
            "color": "green",
            "icon": "✓✓",
            "label": "Solide Datenbasis",
            "description": "Robuste statistische Grundlage"
        }
    }
    
    return configs.get(risk_level, configs["limited"])


if __name__ == "__main__":
    sample_topics = [
        {"name": "Work-Life Balance", "count": 45, "avg_rating": 3.2},
        {"name": "Gehalt", "count": 28, "avg_rating": 2.8},
        {"name": "Karriere", "count": 15, "avg_rating": 3.5}
    ]
    
    enriched = enrich_topic_analysis_with_metadata(sample_topics, total_sample_size=88)
    
    print("Enriched Topic Analysis:")
    for topic in enriched:
        print(f"\n{topic['name']}:")
        print(f"  Count: {topic['count']}")
        print(f"  Risk: {topic['statistical_meta']['risk_description']}")
        if 'warning' in topic['statistical_meta']:
            print(f"  ⚠️  {topic['statistical_meta']['warning']}")
