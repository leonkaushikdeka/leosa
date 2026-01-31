# ForensicSight v2.0

Production-grade real-time forensic analysis system using YOLOv8 and OpenCV with MSc-level forensic science capabilities.

## Features

### Core Architecture
- **YOLOv8s/m** object detection for real-time analysis
- **Multi-threaded design**: Capture Thread → Inference Thread → Main Thread
- Thread-safe evidence logging with queues
- Real-time webcam feed (1280x720, 30fps target)

### Forensic Categorization System
- **PRIMARY EVIDENCE** (Red): sports ball, bottle, cell phone, knife, scissors, clock, vase
- **SEARCH ZONES** (Blue): bed, couch, chair, dining table, refrigerator, oven, suitcase, microwave
- **ANOMALIES** (Yellow): handbag, backpack, suitcase, box, book, laptop

### MSc-Level Forensic Analysis Modules
- **Bloodstain Pattern Analysis (BPA)** - HSV dual-range detection, spatter classification
- **Gunshot Residue (GSR) Detection** - Stippling patterns, distance estimation
- **Latent Fingerprint Enhancement** - CLAHE, Gabor filters, minutiae extraction
- **Tool Mark Analysis** - Sobel edge detection, striation pattern classification
- **Trace Evidence (ALS Simulation)** - UV/Blue light fluorescence detection

### Evidence Management (ISO 17025 Compliant)
- Organized directory structure with 6 evidence categories
- Master CSV evidence registry
- SHA-256 image integrity verification
- Contamination risk detection (DNA + GSR proximity)
- Evidence numbering: `[CASE_ID]-[TYPE]-[###]`

## Installation

```bash
pip install ultralytics opencv-python numpy scipy scikit-image
```

## Usage

```bash
# Run with live camera
python ForensicSight_v2.py

# Run in demo mode (no camera required)
python ForensicSight_v2.py --demo
```

### Controls
- `q` - Quit
- `s` - Manual screenshot
- `d` - Toggle demo mode

## Output Structure

```
forensic_case_files/[CASE_ID]/
├── 01_Biology_DNA/
├── 02_Trace_Evidence/
├── 03_Impressions/
├── 04_Ballistics/
├── 05_Crime_Scene_Photography/
│   ├── *[evidence_id]_macro_[hash].png    (close-up)
│   └── *[evidence_id]_context_[hash].jpg  (context view)
├── 06_Chain_of_Custody/
└── master_evidence_registry.csv
```

## Forensic Standards Compliance
- **ISO 17025** - General requirements for testing laboratories
- **ASTM E2917** - Forensic photography scale standards
- Chain of custody documentation
- SHA-256 digital evidence integrity

## Requirements
- Python 3.8+
- Webcam (optional, demo mode available)
- 4GB+ RAM recommended
- CUDA-compatible GPU (optional, for faster inference)

## License
MIT License

## Author
ForensicSight Development Team
