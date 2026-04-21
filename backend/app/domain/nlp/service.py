"""
NLP ESG scoring service — reusable logic for analyzing ESG report text.

Loads pre-trained NLP artifacts once and exposes a `score_text()` function
that can be called from any endpoint (document analysis, standalone NLP, etc.).
"""
from pathlib import Path
import json
import zipfile
import re
import logging
from typing import Dict, List, Optional

import numpy as np
import joblib

logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path("artifacts/nlp_text")
ARTIFACT_ZIP = Path("esg_nlp_artifacts_20260409_083250.zip")


def _resolve_artifact_zip() -> Path:
    """
    Prefer explicitly configured ZIP if present; otherwise fallback to newest
    esg_nlp_artifacts_*.zip in project root.
    """
    if ARTIFACT_ZIP.exists():
        return ARTIFACT_ZIP

    candidates = sorted(
        Path(".").glob("esg_nlp_artifacts_*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]

    return ARTIFACT_ZIP

# ---------------------------------------------------------------------------
# Keyword dictionaries (must match training)
# ---------------------------------------------------------------------------
E_KEYWORDS = [
    'emission', 'ghg', 'carbon', 'co2', 'scope', 'climate', 'greenhouse',
    'renewable', 'energy', 'solar', 'wind', 'electricity', 'fossil', 'coal',
    'water', 'waste', 'recycle', 'biodiversity', 'deforestation', 'land',
    'pollution', 'net zero', 'carbon neutral', 'paris', 'temperature',
    'methane', 'refrigerant', 'coolant', 'effluent', 'wastewater'
]
S_KEYWORDS = [
    'employee', 'worker', 'staff', 'workforce', 'labor', 'labour',
    'safety', 'injury', 'accident', 'trir', 'fatality', 'health',
    'diversity', 'inclusion', 'gender', 'women', 'minority', 'discrimination',
    'training', 'development', 'skill', 'education',
    'community', 'local', 'human rights', 'supply chain', 'modern slavery',
    'wage', 'benefit', 'turnover', 'retention', 'wellbeing'
]
G_KEYWORDS = [
    'board', 'director', 'independent', 'governance', 'committee',
    'audit', 'risk management', 'internal control', 'compliance',
    'executive', 'compensation', 'remuneration', 'shareholder', 'voting',
    'anti-corruption', 'bribery', 'whistleblower', 'ethics',
    'transparency', 'disclosure', 'policy', 'accountability', 'esg committee'
]

ZONE_KEYWORDS: Dict[str, List[str]] = {
    'E_Emissions':    ['emission', 'ghg', 'carbon', 'co2', 'scope 1', 'scope 2', 'scope 3',
                       'greenhouse', 'net zero', 'carbon neutral', 'methane', 'refrigerant'],
    'E_Energy':       ['energy', 'renewable', 'solar', 'wind', 'electricity', 'fossil',
                       'coal', 'natural gas', 'kwh', 'mwh', 'gigajoule', 'petajoule'],
    'E_Water':        ['water', 'withdrawal', 'consumption', 'discharge', 'recycled water',
                       'wastewater', 'effluent', 'drought', 'aquifer', 'stormwater'],
    'E_Waste':        ['waste', 'recycle', 'landfill', 'hazardous', 'circular economy',
                       'single use', 'packaging', 'disposal', 'reuse', 'diversion'],
    'E_Biodiversity': ['biodiversity', 'ecosystem', 'deforestation', 'land use', 'habitat',
                       'species', 'nature', 'forest', 'wetland', 'restoration'],
    'S_Labor':        ['employee', 'worker', 'workforce', 'labor', 'labour', 'trade union',
                       'collective', 'wage', 'benefit', 'turnover', 'retention', 'hiring'],
    'S_Safety':       ['safety', 'injury', 'accident', 'trir', 'ltir', 'fatality',
                       'health', 'wellbeing', 'ppe', 'incident', 'recordable', 'near miss'],
    'S_Diversity':    ['diversity', 'inclusion', 'gender', 'women', 'minority', 'disability',
                       'lgbtq', 'pay gap', 'representation', 'equity', 'belonging'],
    'S_Community':    ['community', 'local', 'investment', 'volunteer', 'philanthropy',
                       'charitable', 'social impact', 'foundation', 'donation', 'outreach'],
    'S_SupplyChain':  ['supply chain', 'supplier', 'procurement', 'vendor', 'sourcing',
                       'modern slavery', 'human rights', 'audit', 'due diligence', 'conflict'],
    'G_Board':           ['board', 'director', 'independent', 'chair', 'committee',
                          'governance', 'tenure', 'diversity', 'nomination', 'oversight'],
    'G_ExecutivePay':    ['executive', 'compensation', 'remuneration', 'ceo pay', 'bonus',
                          'stock option', 'pay ratio', 'incentive', 'clawback', 'say on pay'],
    'G_AntiCorruption':  ['corruption', 'bribery', 'ethics', 'conduct', 'anti-fraud',
                          'whistleblower', 'speak up', 'misconduct', 'sanctions', 'facilitation'],
    'G_Transparency':    ['disclosure', 'reporting', 'transparency', 'stakeholder', 'materiality',
                          'gri', 'sasb', 'tcfd', 'assurance', 'third party', 'verified'],
    'G_RiskManagement':  ['risk', 'audit', 'internal control', 'compliance', 'regulatory',
                          'legal', 'liability', 'crisis', 'scenario', 'stress test']
}


def _build_pattern(keywords: List[str]) -> re.Pattern:
    return re.compile('|'.join(re.escape(k) for k in keywords), re.IGNORECASE)


KW_PATTERNS = {
    'E': _build_pattern(E_KEYWORDS),
    'S': _build_pattern(S_KEYWORDS),
    'G': _build_pattern(G_KEYWORDS),
    **{k: _build_pattern(v) for k, v in ZONE_KEYWORDS.items()}
}
QUANT_PATTERN = re.compile(
    r'\d[\d,\.]+\s*(?:tco2|co2e|kgco2|ghg|kwh|mwh|gwh|gj|tj|tonne|ton|kg|litre|liter|gallon|cubic|percent|%|employee|worker|staff)'
    r'|\$[\d,\.]+\s*(?:million|billion)',
    re.IGNORECASE
)
TARGET_PATTERN = re.compile(
    r'by\s+20[23]\d|target|goal|commitment|pledge|net\s+zero|achieve|reduce\s+by|increase\s+to',
    re.IGNORECASE
)


def compute_keyword_features(texts: List[str]) -> np.ndarray:
    zone_order = list(ZONE_KEYWORDS.keys())
    rows: List[List[float]] = []

    for text in texts:
        if not isinstance(text, str) or not text.strip():
            rows.append([0.0] * 21)
            continue

        wc = len(text.split())
        if wc == 0:
            rows.append([0.0] * 21)
            continue

        row = [
            len(KW_PATTERNS['E'].findall(text)) / wc * 1000,
            len(KW_PATTERNS['S'].findall(text)) / wc * 1000,
            len(KW_PATTERNS['G'].findall(text)) / wc * 1000,
        ]
        for zone in zone_order:
            row.append(len(KW_PATTERNS[zone].findall(text)) / wc * 1000)

        row.append(float(bool(QUANT_PATTERN.search(text))))
        row.append(min(len(TARGET_PATTERN.findall(text)) / 6.0, 1.0))
        row.append(min(wc / 20000.0, 1.0))
        rows.append(row)

    return np.array(rows, dtype=np.float32)


def compute_zone_breakdown(text: str) -> Dict[str, float]:
    """Return per-zone keyword density (hits per 1000 words)."""
    wc = len(text.split())
    if wc == 0:
        return {z: 0.0 for z in ZONE_KEYWORDS}
    return {
        zone: round(len(KW_PATTERNS[zone].findall(text)) / wc * 1000, 3)
        for zone in ZONE_KEYWORDS
    }


# ---------------------------------------------------------------------------
# Artifact loading (lazy singleton)
# ---------------------------------------------------------------------------
_artifacts: Optional[dict] = None


def _load_artifacts() -> dict:
    global _artifacts
    if _artifacts is not None:
        return _artifacts

    artifact_zip = _resolve_artifact_zip()

    if not ARTIFACT_DIR.exists():
        if not artifact_zip.exists():
            raise FileNotFoundError(
                "NLP artifacts not found. Place an esg_nlp_artifacts_*.zip "
                "in project root or extract to artifacts/nlp_text/"
            )
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(artifact_zip) as zf:
            zf.extractall(ARTIFACT_DIR)
        logger.info("Extracted NLP artifacts from %s to %s", artifact_zip, ARTIFACT_DIR)

    _artifacts = {
        "text_pipeline": joblib.load(ARTIFACT_DIR / "text_pipeline.joblib"),
        "model_e": joblib.load(ARTIFACT_DIR / "esg_e_model.joblib"),
        "model_s": joblib.load(ARTIFACT_DIR / "esg_s_model.joblib"),
        "model_g": joblib.load(ARTIFACT_DIR / "esg_g_model.joblib"),
        "bench_sorted": json.load(open(ARTIFACT_DIR / "benchmark_sorted_scores.json")),
        "bench_dist": json.load(open(ARTIFACT_DIR / "benchmark_distributions.json")),
        "zone_thresholds": json.load(open(ARTIFACT_DIR / "zone_thresholds.json")),
        "model_cfg": json.load(open(ARTIFACT_DIR / "model_config.json")),
    }
    return _artifacts


def _score_raw_to_scaled(raw: float, pillar: str, bench_sorted: dict, bench_dist: dict) -> Optional[float]:
    scores = bench_sorted.get(pillar, [])
    if not scores:
        return None
    arr = np.array(scores)
    invert = bench_dist.get(pillar, {}).get('invert', True)
    # Primary mapping: empirical percentile rank against benchmark distribution.
    rank = np.searchsorted(arr, raw, side='left') / len(arr)

    # When raw is far outside benchmark min/max, pure rank collapses to 0 or 1
    # and can pin scores at 0/10 for many documents. Use a z-score fallback
    # (clipped to reduce tail instability) to keep scoring informative.
    if raw < float(arr[0]) or raw > float(arr[-1]):
        mean = float(bench_dist.get(pillar, {}).get("mean", float(np.mean(arr))))
        std = float(bench_dist.get(pillar, {}).get("std", float(np.std(arr))))
        if std > 0:
            z = (raw - mean) / std
            z = float(np.clip(z, -3.0, 3.0))
            pct = 1.0 / (1.0 + float(np.exp(-z)))
            pct = 1.0 - pct if invert else pct
            return round(float(max(0.0, min(10.0, 10.0 * pct))), 2)

    pct = 1 - rank if invert else rank
    scaled = max(0.0, min(10.0, 10 * pct))
    return round(float(scaled), 2)


def _heuristic_pillar_scores(kw_row: np.ndarray) -> Dict[str, float]:
    """
    Heuristic fallback scoring from keyword/structure signals.
    Used when model raw outputs are out-of-distribution vs benchmark bounds.
    """
    env_density, soc_density, gov_density = [float(x) for x in kw_row[:3]]
    has_quant = float(kw_row[-3])       # 0/1
    targets = float(kw_row[-2])         # 0..1
    length_norm = float(kw_row[-1])     # 0..1

    def pillar_score(density: float) -> float:
        # Density contributes most; quantified metrics/targets/report depth
        # add credibility signal.
        val = (density * 0.40) + (has_quant * 1.5) + (targets * 2.0) + (length_norm * 1.5)
        return round(float(max(0.0, min(10.0, val))), 2)

    return {
        "E": pillar_score(env_density),
        "S": pillar_score(soc_density),
        "G": pillar_score(gov_density),
    }


def _pillar_evidence_strength(
    zone_breakdown: Dict[str, float],
    zone_thresholds: Dict[str, dict],
) -> Dict[str, float]:
    """
    Compute evidence strength per pillar in [0, 1] from zone densities
    relative to weak/strong thresholds.
    """
    by_pillar: Dict[str, List[float]] = {"E": [], "S": [], "G": []}
    for zone, density in zone_breakdown.items():
        zcfg = zone_thresholds.get(zone, {})
        pillar = zcfg.get("pillar")
        if pillar not in by_pillar:
            continue
        weak = float(zcfg.get("flag_weak", 0.0) or 0.0)
        strong = float(zcfg.get("flag_strong", weak + 1.0) or (weak + 1.0))
        if strong <= weak:
            strong = weak + 1.0
        strength = (float(density) - weak) / (strong - weak)
        by_pillar[pillar].append(float(np.clip(strength, 0.0, 1.0)))

    out: Dict[str, float] = {}
    for p in ("E", "S", "G"):
        vals = by_pillar[p]
        out[p] = float(np.mean(vals)) if vals else 0.0
    return out


def _apply_evidence_calibration(
    scaled: Dict[str, Optional[float]],
    zone_breakdown: Dict[str, float],
    zone_thresholds: Dict[str, dict],
    word_count: int,
) -> Dict[str, Optional[float]]:
    """
    Pull scores toward neutral when textual evidence is weak.
    This reduces overconfident high scores for sparse/short documents.
    """
    strengths = _pillar_evidence_strength(zone_breakdown, zone_thresholds)
    # Ramp from 0 to 1 between 300 and 3000 words.
    wc_factor = float(np.clip((word_count - 300.0) / 2700.0, 0.0, 1.0))
    calibrated: Dict[str, Optional[float]] = {}
    for p, score in scaled.items():
        if score is None:
            calibrated[p] = None
            continue
        evidence = strengths.get(p, 0.0) * wc_factor
        calibrated_score = 5.0 + (float(score) - 5.0) * evidence
        calibrated[p] = round(float(np.clip(calibrated_score, 0.0, 10.0)), 2)
    return calibrated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _framework_weights(framework: str) -> Dict[str, float]:
    """Framework-specific pillar weights used for composite scoring."""
    fw = (framework or "gri").strip().lower()
    weights_map: Dict[str, Dict[str, float]] = {
        "gri": {"E": 1 / 3, "S": 1 / 3, "G": 1 / 3},
        "sasb": {"E": 0.35, "S": 0.25, "G": 0.40},
        "tcfd": {"E": 0.60, "S": 0.10, "G": 0.30},
        "esrs": {"E": 0.35, "S": 0.35, "G": 0.30},
    }
    return weights_map.get(fw, weights_map["gri"])


def score_text(text: str, framework: str = "gri") -> dict:
    """
    Run NLP ESG analysis on a block of text.

    Returns dict with keys: raw, scaled, composite, zone_breakdown,
    feature_dims, model_info, word_count.
    """
    arts = _load_artifacts()

    texts = [text]
    lsa = arts["text_pipeline"].transform(texts)
    kw = compute_keyword_features(texts)
    X = np.hstack([lsa, kw])

    raw = {
        'E': float(arts["model_e"].predict(X)[0]),
        'S': float(arts["model_s"].predict(X)[0]),
        'G': float(arts["model_g"].predict(X)[0]),
    }

    scaled_model = {
        k: _score_raw_to_scaled(v, k, arts["bench_sorted"], arts["bench_dist"])
        for k, v in raw.items()
    }
    heuristic = _heuristic_pillar_scores(kw[0])

    # Detect out-of-distribution predictions against benchmark support.
    # If all pillars are OOD, rely on heuristic scores (model calibration unreliable).
    ood_flags: Dict[str, bool] = {}
    for k, v in raw.items():
        arr = arts["bench_sorted"].get(k, [])
        if not arr:
            ood_flags[k] = False
            continue
        ood_flags[k] = bool(v < float(arr[0]) or v > float(arr[-1]))

    use_heuristic = all(ood_flags.values())
    scaled = heuristic if use_heuristic else scaled_model

    zone_breakdown = compute_zone_breakdown(text)
    word_count = len(text.split())
    scaled_calibrated = _apply_evidence_calibration(
        scaled,
        zone_breakdown,
        arts.get("zone_thresholds", {}),
        word_count,
    )

    weights = _framework_weights(framework)
    weighted_total = 0.0
    weight_sum = 0.0
    for pillar, score in scaled_calibrated.items():
        if score is None:
            continue
        w = float(weights.get(pillar, 0.0))
        weighted_total += score * w
        weight_sum += w
    composite = round(weighted_total / weight_sum, 2) if weight_sum > 0 else None

    return {
        'raw': raw,
        'scaled': scaled_calibrated,
        'composite': composite,
        'zone_breakdown': zone_breakdown,
        'feature_dims': {
            'lsa': int(lsa.shape[1]),
            'keywords': int(kw.shape[1]),
            'total': int(X.shape[1]),
        },
        'model_info': {
            'schema_version': arts["model_cfg"].get('schema_version'),
            'invert_score': arts["model_cfg"].get('invert_score'),
            'framework': (framework or "gri").strip().lower(),
            'framework_weights': weights,
            'scoring_mode': 'heuristic_fallback' if use_heuristic else 'model_calibrated',
            'ood_flags': ood_flags,
            'evidence_strength': _pillar_evidence_strength(zone_breakdown, arts.get("zone_thresholds", {})),
        },
        'word_count': word_count,
    }
