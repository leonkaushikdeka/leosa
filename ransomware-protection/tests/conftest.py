import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_event_data():
    return {
        "host_id": 1,
        "event_type": "file_modification",
        "process_name": "suspicious_process.exe",
        "file_path": "C:\\Users\\test\\Documents\\important.encrypted",
        "user": "testuser",
        "action": "write",
        "source_ip": "192.168.1.100",
        "destination_ip": "",
        "file_hash": "abc123def456",
        "raw_data": {"event_code": 4663, "access_mask": "0x2", "process_id": 1234},
    }


@pytest.fixture
def ransomware_event_data():
    return {
        "host_id": 1,
        "event_type": "mass_file_encryption",
        "process_name": "ransomware.exe",
        "file_path": "C:\\Users\\victim\\Documents\\file.encrypted",
        "user": "victim",
        "action": "write",
        "source_ip": "",
        "destination_ip": "",
        "file_hash": "known_ransomware_hash",
        "raw_data": {"event_code": 4663, "access_mask": "0x2", "process_id": 5678},
    }


@pytest.fixture
def normal_event_data():
    return {
        "host_id": 1,
        "event_type": "file_read",
        "process_name": "notepad.exe",
        "file_path": "C:\\Users\\test\\Documents\\report.txt",
        "user": "testuser",
        "action": "read",
        "source_ip": "",
        "destination_ip": "",
        "file_hash": "",
        "raw_data": {"event_code": 4663, "access_mask": "0x1", "process_id": 1000},
    }
