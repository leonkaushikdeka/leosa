import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.ml.serving import MLModelManager


@pytest.fixture
def ml_manager():
    manager = MLModelManager()
    return manager


@pytest.mark.asyncio
async def test_ml_model_manager_initialization(ml_manager):
    assert ml_manager.loaded is False
    assert len(ml_manager.models) == 0


@pytest.mark.asyncio
async def test_ensemble_score_calculation(ml_manager):
    anomaly_score = 0.7
    behavior_score = 0.6
    signature_score = 0.8

    ensemble_score = ml_manager._compute_ensemble_score(
        anomaly_score, behavior_score, signature_score
    )

    expected = 0.35 * 0.7 + 0.35 * 0.6 + 0.30 * 0.8
    assert ensemble_score == pytest.approx(expected, abs=0.01)


@pytest.mark.asyncio
async def test_detection_type_determination(ml_manager):
    assert ml_manager._determine_detection_type(0.9, 0.8, 0.85) == "signature"
    assert ml_manager._determine_detection_type(0.8, 0.8, 0.3) == "anomaly_behavioral"
    assert ml_manager._determine_detection_type(0.3, 0.8, 0.3) == "behavioral"
    assert ml_manager._determine_detection_type(0.7, 0.3, 0.3) == "anomaly"
    assert ml_manager._determine_detection_type(0.3, 0.3, 0.3) == "normal"


@pytest.mark.asyncio
async def test_indicator_extraction(ml_manager):
    event_data = {
        "file_path": "C:\\Users\\victim\\Documents\\file.encrypted",
        "process_name": "vssadmin.exe",
        "event_type": "mass_file_modification",
    }

    indicators = ml_manager._extract_indicators(event_data)

    assert len(indicators) >= 1
    assert any("Shadow copy deletion" in ind or "Suspicious" in ind for ind in indicators)


@pytest.mark.asyncio
async def test_confidence_calculation(ml_manager):
    high_confidence = ml_manager._compute_confidence(0.9, 0.9, 0.9)
    low_confidence = ml_manager._compute_confidence(0.3, 0.3, 0.3)

    assert high_confidence > low_confidence
    assert 0 <= high_confidence <= 1
    assert 0 <= low_confidence <= 1


@pytest.mark.asyncio
async def test_recommended_actions_for_high_risk(ml_manager):
    actions = ml_manager._get_recommended_actions(0.9, "signature")

    assert len(actions) >= 4
    assert any("isolate" in action.lower() for action in actions)
    assert any("terminate" in action.lower() for action in actions)


@pytest.mark.asyncio
async def test_recommended_actions_for_low_risk(ml_manager):
    actions = ml_manager._get_recommended_actions(0.3, "normal")

    assert len(actions) == 2
    assert any("document" in action.lower() for action in actions)


@pytest.mark.asyncio
async def test_heuristic_behavior_analysis(ml_manager):
    suspicious_event = {
        "event_type": "mass_file_encryption",
        "process_name": "encryptor.exe",
        "file_path": "data.encrypted",
    }

    score = ml_manager._heuristic_behavior_analysis(suspicious_event)

    assert score > 0.5

    normal_event = {
        "event_type": "file_read",
        "process_name": "notepad.exe",
        "file_path": "document.txt",
    }

    normal_score = ml_manager._heuristic_behavior_analysis(normal_event)

    assert score > normal_score
