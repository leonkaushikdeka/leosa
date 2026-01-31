"""
ForensicSight v2.0 - Real-time Forensic Analysis System
"""

import cv2
import numpy as np
from ultralytics import YOLO
import threading
import queue
import dataclasses
import json
import csv
import hashlib
import pathlib
from datetime import datetime, timezone
from typing import Tuple, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from scipy import ndimage
from skimage import filters, morphology, measure
import time
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - FORENSIC_LOG - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("forensic_operations.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    pass


class ForensicConfig:
    WIDTH = 1280
    HEIGHT = 720
    FPS_TARGET = 30

    PRIMARY = {
        "sports ball",
        "bottle",
        "cell phone",
        "knife",
        "scissors",
        "clock",
        "vase",
    }
    ZONES = {
        "bed",
        "couch",
        "chair",
        "dining table",
        "refrigerator",
        "oven",
        "suitcase",
        "microwave",
    }
    ANOMALIES = {"handbag", "backpack", "suitcase", "box", "book", "laptop"}

    COLOR_PRIMARY = (0, 0, 255)
    COLOR_ZONE = (255, 0, 0)
    COLOR_ANOMALY = (0, 255, 255)
    GRID_SIZE = 50
    DUPLICATE_COOLDOWN = 2.0


@dataclass
class ForensicEvidence:
    evidence_id: str
    timestamp_utc: str
    evidence_type: str
    subclassification: str
    location_bbox: Tuple[int, int, int, int]
    pixel_dimensions: Tuple[int, int]
    image_hash_sha256: str
    forensic_analysis: Dict = field(default_factory=dict)
    collection_priority: int = 1
    contamination_risks: List[str] = field(default_factory=list)
    custodian_id: str = "SYSTEM_AUTO"

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


class BloodstainPatternAnalysis:
    def __init__(self):
        self.kernel = np.ones((5, 5), np.uint8)

    def detect_blood(self, image: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 100, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([160, 100, 50]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(mask1, mask2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)
        return mask

    def analyze_pattern(self, mask: np.ndarray, image_area: int) -> Dict[str, Any]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_stains = len(contours)
        blood_ratio = total_stains / (image_area / 10000)
        return {
            "total_stain_count": total_stains,
            "blood_ratio": blood_ratio,
            "automatic_log_required": blood_ratio > 10,
        }


class GunshotResidueDetector:
    def detect_stippling(self, roi: np.ndarray) -> Dict[str, Any]:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        particles = []
        for c in contours:
            area = cv2.contourArea(c)
            if 10 <= area <= 100:
                per = cv2.arcLength(c, True)
                if per > 0 and (4 * np.pi * area / (per * per)) > 0.7:
                    particles.append(c)

        count = len(particles)
        return {
            "gsr_particle_count": count,
            "estimated_distance": 'contact-6"'
            if count > 100
            else '6-12"'
            if count > 50
            else '12-24"'
            if count > 20
            else '>24"',
            "contamination_risk": count > 50,
        }


class LatentFingerprintEnhancer:
    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        self.gabor_angles = [0, 45, 90, 135]

    def create_gabor_kernels(self) -> List[np.ndarray]:
        kernels = []
        for angle in self.gabor_angles:
            kernel = cv2.getGaborKernel(
                (31, 31), 5.0, np.radians(angle), 10.0, 0.5, 0, cv2.CV_32F
            )
            kernels.append(kernel)
        return kernels

    def enhance_fingerprint(self, roi: np.ndarray) -> Dict[str, Any]:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        clahe_enhanced = self.clahe.apply(gray)
        kernels = self.create_gabor_kernels()
        gabor_combined = np.zeros_like(gray, dtype=np.float32)
        for kernel in kernels:
            filtered = cv2.filter2D(clahe_enhanced, -1, kernel)
            gabor_combined = np.maximum(gabor_combined, filtered)
        gabor_uint8 = np.uint8(255 * gabor_combined / max(1, np.max(gabor_combined)))
        _, binary = cv2.threshold(
            gabor_uint8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        skeleton = morphology.skeletonize(binary > 127)
        skeleton_uint8 = np.uint8(skeleton * 255)
        ridges = measure.label(skeleton_uint8 > 0)
        regions = measure.regionprops(ridges)
        minutiae = 0
        for region in regions:
            for coord in region.coords:
                y, x = coord
                nb = skeleton_uint8[max(0, y - 1) : y + 2, max(0, x - 1) : x + 2]
                if np.sum(nb > 0) == 3 or np.sum(nb > 0) > 4:
                    minutiae += 1
        return {
            "minutiae_count": minutiae,
            "quality_score": min(1.0, np.std(clahe_enhanced) / 128.0),
            "is_suitable": minutiae > 10,
        }


class ToolMarkAnalyzer:
    def analyze_tool_mark(self, roi: np.ndarray) -> Dict[str, Any]:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        edges = np.uint8(255 * magnitude / max(1, np.max(magnitude)))
        _, edges_binary = cv2.threshold(edges, 50, 255, cv2.THRESH_BINARY)
        lines = cv2.HoughLinesP(
            edges_binary, 1, np.pi / 180, threshold=50, minLineLength=30, maxLineGap=10
        )
        angles = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angles.append(abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi))
        variance = np.std(angles) if len(angles) > 1 else 0
        return {
            "tool_classification": "screwdriver"
            if variance < 50
            else "pliers/wrench"
            if variance < 200
            else "irregular",
            "is_striation": variance < 100 and len(angles) > 10,
        }


class TraceEvidenceAnalyzer:
    def __init__(self):
        self.uv_range = ((130, 50, 0), (170, 255, 100))
        self.blue_range = ((100, 50, 0), (140, 255, 255))

    def detect_uv_fluorescence(self, roi: np.ndarray) -> Dict[str, Any]:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(self.uv_range[0]), np.array(self.uv_range[1]))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return {"uv_detected": len(contours) > 5, "particle_count": len(contours)}

    def detect_blue_enhancement(self, roi: np.ndarray) -> Dict[str, Any]:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv, np.array(self.blue_range[0]), np.array(self.blue_range[1])
        )
        return {"blue_applied": True, "intensity": np.sum(mask > 0)}


class ForensicEvidenceManager:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.base_dir = pathlib.Path(f"./forensic_case_files/{case_id}")
        self.structure_dirs = [
            "01_Biology_DNA",
            "02_Trace_Evidence",
            "03_Impressions",
            "04_Ballistics",
            "05_Crime_Scene_Photography",
            "06_Chain_of_Custody",
        ]
        self.evidence_counter = {
            "BIO": 0,
            "TRC": 0,
            "IMP": 0,
            "BAL": 0,
            "PHY": 0,
            "GEN": 0,
        }
        self.registered_evidence = []
        self._create_structure()
        self._init_csv()
        self.csv_path = self.base_dir / "master_evidence_registry.csv"

    def _create_structure(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for d in self.structure_dirs:
            (self.base_dir / d).mkdir(exist_ok=True)
        logger.info(f"Case dir: {self.base_dir}")

    def _init_csv(self):
        self.csv_path = self.base_dir / "master_evidence_registry.csv"
        with open(self.csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Evidence_ID",
                    "Case_Number",
                    "Date_Time",
                    "Type",
                    "Description",
                    "Priority",
                ]
            )

    def _append_csv(self, ev: ForensicEvidence):
        try:
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        ev.evidence_id,
                        self.case_id,
                        ev.timestamp_utc,
                        ev.evidence_type,
                        ev.subclassification,
                        ev.collection_priority,
                    ]
                )
        except Exception as e:
            logger.error(f"CSV append error: {e}")

    def _gen_id(self, ev_type: str) -> str:
        prefix = {
            "biological": "BIO",
            "trace": "TRC",
            "impression": "IMP",
            "ballistics": "BAL",
        }.get(ev_type[:10], "GEN")
        self.evidence_counter[prefix] += 1
        return f"{self.case_id}-{prefix}-{self.evidence_counter[prefix]:03d}"

    def _sha256(self, img: np.ndarray) -> str:
        _, enc = cv2.imencode(".png", img)
        return hashlib.sha256(enc.tobytes()).hexdigest()

    def check_contamination(self, new_ev: ForensicEvidence) -> List[str]:
        risks = []
        if "gsr" in new_ev.evidence_type.lower():
            for existing in self.registered_evidence:
                if "biological" in existing.evidence_type.lower():
                    nb = new_ev.location_bbox
                    eb = existing.location_bbox
                    nc = ((nb[0] + nb[2]) // 2, (nb[1] + nb[3]) // 2)
                    ec = ((eb[0] + eb[2]) // 2, (eb[1] + eb[3]) // 2)
                    dist = np.sqrt((nc[0] - ec[0]) ** 2 + (nc[1] - ec[1]) ** 2)
                    if dist < 200:
                        risks.append(
                            f"PROXIMITY: {dist:.0f}px from {existing.evidence_id}"
                        )
        return risks

    def create_evidence(
        self,
        ev_type: str,
        subclass: str,
        bbox: Tuple[int, int, int, int],
        dims: Tuple[int, int],
        img: np.ndarray,
        analysis: Dict,
        priority: int = 3,
        risks: List[str] = None,
    ) -> ForensicEvidence:
        ev = ForensicEvidence(
            evidence_id=self._gen_id(ev_type),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            evidence_type=ev_type,
            subclassification=subclass,
            location_bbox=bbox,
            pixel_dimensions=dims,
            image_hash_sha256=self._sha256(img),
            forensic_analysis=analysis,
            collection_priority=priority,
            contamination_risks=risks or [],
        )
        all_risks = self.check_contamination(ev)
        if all_risks:
            ev.contamination_risks.extend(all_risks)

        self._save_evidence_images(ev, img)
        self._append_csv(ev)
        self.registered_evidence.append(ev)
        logger.info(f"EVIDENCE: {ev.evidence_id} - {ev.evidence_type}")
        return ev

    def _save_evidence_images(self, ev: ForensicEvidence, img: np.ndarray):
        """Save macro and context images for evidence"""
        try:
            photo_dir = self.base_dir / "05_Crime_Scene_Photography"
            hash_short = ev.image_hash_sha256[:12]

            macro_path = photo_dir / f"{ev.evidence_id}_macro_{hash_short}.png"
            context_path = photo_dir / f"{ev.evidence_id}_context_{hash_short}.jpg"

            cv2.imwrite(str(macro_path), img)

            context_img = np.zeros(
                (ForensicConfig.HEIGHT, ForensicConfig.WIDTH, 3), dtype=np.uint8
            )
            context_img[:] = (20, 20, 20)
            bx, by, bw, bh = ev.location_bbox
            by2 = min(by + bh + 50, ForensicConfig.HEIGHT - 100)
            bx2 = min(bx + bw + 50, ForensicConfig.WIDTH - 50)
            context_img[by:by2, bx:bx2] = cv2.resize(img, (bx2 - bx, by2 - by))
            cv2.rectangle(context_img, (bx, by), (bx2, by2), (0, 255, 0), 2)
            cv2.putText(
                context_img,
                ev.evidence_id,
                (bx, by - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )
            cv2.putText(
                context_img,
                f"Type: {ev.evidence_type}",
                (bx, by2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (200, 200, 200),
                1,
            )

            cv2.imwrite(str(context_path), context_img)
            logger.info(f"Saved: {macro_path.name}, {context_path.name}")
        except Exception as e:
            logger.error(f"Error saving evidence images: {e}")


class ForensicSightSystem:
    def __init__(self, case_id: str, model_size: str = "s"):
        self.case_id = case_id
        self.model = YOLO(f"yolov8{model_size}.pt")
        self.cap = None
        self.running = False
        self.fps = 0
        self.frame_count = 0
        self.last_time = time.time()
        self.demo_mode = False
        self.demo_idx = 0

        self.evidence_manager = ForensicEvidenceManager(case_id)
        self.bpa = BloodstainPatternAnalysis()
        self.gsr = GunshotResidueDetector()
        self.fp = LatentFingerprintEnhancer()
        self.tool = ToolMarkAnalyzer()
        self.trace = TraceEvidenceAnalyzer()

        self.tracked = {}
        self.logged = set()

        self.zone_prompts = {
            "bed": "ZONE: Under Mattress | COLLECT: Bedding DNA",
            "couch": "ZONE: Between Cushions | LIFT: Frame weapons",
            "chair": "ZONE: Seat & Legs | EXAMINE: Upholstery",
            "refrigerator": "ZONE: Door & Contents | EXAMINE: Contamination",
            "oven": "ZONE: Interior | COLLECT: Residue samples",
            "suitcase": "ZONE: Hidden compartments | SEARCH: Drugs",
        }

        logger.info(f"ForensicSight v2.0 initialized: {case_id}")

    def init_camera(self) -> bool:
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, ForensicConfig.WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ForensicConfig.HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, ForensicConfig.FPS_TARGET)

        if not self.cap.isOpened():
            logger.warning("Camera not available - using DEMO mode")
            self.demo_mode = True
            return True
        return True

    def gen_demo_frame(self) -> Tuple[np.ndarray, Any]:
        frame = np.random.randint(
            0, 50, (ForensicConfig.HEIGHT, ForensicConfig.WIDTH, 3), dtype=np.uint8
        )
        frame[200:520, 400:880] = [30, 30, 40]
        cv2.putText(
            frame,
            "DEMO MODE - NO CAMERA",
            (450, 360),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (100, 100, 150),
            2,
        )

        demo_objs = [
            {"bbox": [350, 200, 550, 400], "cls": 41, "conf": 0.85},  # suitcase
            {"bbox": [700, 100, 950, 350], "cls": 59, "conf": 0.90},  # bed
            {"bbox": [100, 400, 300, 600], "cls": 0, "conf": 0.75},  # person
        ]

        class MockBoxes:
            def __init__(self, data):
                self.data = data

        import torch

        boxes = []
        for obj in demo_objs:
            x1, y1, x2, y2 = obj["bbox"]
            boxes.append([x1, y1, x2, y2, obj["conf"], obj["cls"]])

        class MockResults:
            def __init__(self, boxes_data):
                self.boxes = MockBoxes(boxes_data)

        return frame, MockResults(torch.tensor(boxes))

    def process(self, frame: np.ndarray, box) -> None:
        bbox = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
        cls_id = int(box[5])
        conf = float(box[4])
        name = self.model.names[cls_id]

        grid = (
            bbox[0] // ForensicConfig.GRID_SIZE,
            bbox[1] // ForensicConfig.GRID_SIZE,
        )
        now = time.time()

        if (
            grid in self.tracked
            and now - self.tracked[grid] < ForensicConfig.DUPLICATE_COOLDOWN
        ):
            return
        self.tracked[grid] = now

        roi = frame[bbox[1] : bbox[3], bbox[0] : bbox[2]]
        if roi.size == 0:
            return

        ev_type = "contextual"
        subclass = name
        priority = 1
        analysis = {}
        risks = []

        if name in ForensicConfig.PRIMARY:
            ev_type = "contextual"
            subclass = name
            priority = 3
            analysis = {"class": name, "type": "primary"}

        elif name in ForensicConfig.ZONES:
            ev_type = "contextual"
            subclass = f"ZONE: {name}"
            analysis = {"class": name, "type": "zone"}

            bpa = self.bpa.analyze_pattern(self.bpa.detect_blood(roi), roi.size)
            if bpa["automatic_log_required"]:
                ev_type = "biological_blood"
                subclass = f"BLOOD in {name}"
                priority = 5
                analysis.update(bpa)
                risks.append("Biological hazard")

            gsr = self.gsr.detect_stippling(roi)
            if gsr["contamination_risk"]:
                analysis["gsr_warning"] = gsr["estimated_distance"]

        elif name in ForensicConfig.ANOMALIES:
            ev_type = "trace"
            subclass = f"ANOMALY: {name}"
            priority = 4
            uv = self.trace.detect_uv_fluorescence(roi)
            analysis = {"class": name, "type": "anomaly", "uv": uv}

            fp = self.fp.enhance_fingerprint(roi)
            if fp["is_suitable"]:
                ev_type = "trace_fingerprint"
                subclass = f"FINGERPRINT on {name}"
                priority = 5
                analysis.update(fp)

        if name in ForensicConfig.PRIMARY:
            bpa = self.bpa.analyze_pattern(self.bpa.detect_blood(roi), roi.size)
            if bpa["automatic_log_required"]:
                ev_type = "biological_blood"
                subclass = f"BLOOD on {name}"
                priority = 5
                analysis.update(bpa)
                risks.append("Biological hazard")

            gsr = self.gsr.detect_stippling(roi)
            if gsr["gsr_particle_count"] > 0:
                analysis["gsr"] = gsr
                if gsr["contamination_risk"]:
                    ev_type = "trace_gunshot_residue"
                    subclass = f"GSR on {name}"
                    priority = 5
                    risks.append("GSR contamination")

            tool = self.tool.analyze_tool_mark(roi)
            if tool["is_striation"]:
                analysis["tool"] = tool
                ev_type = "impression_tool_mark"
                subclass = f"TOOL MARK on {name}"
                priority = 4

        ev = self.evidence_manager.create_evidence(
            ev_type,
            subclass,
            tuple(bbox),
            (frame.shape[1], frame.shape[0]),
            roi,
            analysis,
            priority,
            risks,
        )
        self.logged.add(ev.evidence_id)

    def draw(self, frame: np.ndarray, results) -> np.ndarray:
        ann = frame.copy()

        cv2.rectangle(ann, (0, 0), (ForensicConfig.WIDTH, 60), (0, 0, 0), -1)
        status = "DEMO" if self.demo_mode else "LIVE"
        color = (255, 165, 0) if self.demo_mode else (0, 255, 0)
        cv2.putText(
            ann,
            f"FORENSIC SIGHT v2.0 [{status}] - {self.case_id}",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

        try:
            for box in results.boxes.data.cpu().numpy():
                bbox = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
                cls_id = int(box[5])
                name = self.model.names[cls_id]

                if name in ForensicConfig.PRIMARY:
                    color = ForensicConfig.COLOR_PRIMARY
                    label = f"EVIDENCE: {name} | PRIORITY: 5"
                elif name in ForensicConfig.ZONES:
                    color = ForensicConfig.COLOR_ZONE
                    label = f"ZONE: {name}"
                elif name in ForensicConfig.ANOMALIES:
                    color = ForensicConfig.COLOR_ANOMALY
                    label = f"ANOMALY: {name}"
                else:
                    continue

                cv2.rectangle(ann, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(
                    ann,
                    (bbox[0], bbox[1] - th - 10),
                    (bbox[0] + tw, bbox[1]),
                    color,
                    -1,
                )
                cv2.putText(
                    ann,
                    label,
                    (bbox[0], bbox[1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    2,
                )

                x1, y1, x2, y2 = bbox
                rw = min(100, x2 - x1)
                ry = min(y2 + 10, ForensicConfig.HEIGHT - 30)
                if rw > 20:
                    cv2.rectangle(
                        ann, (x1, ry), (x1 + rw, ry + 15), (255, 255, 255), -1
                    )
                    cv2.rectangle(ann, (x1, ry), (x1 + rw, ry + 15), (0, 0, 0), 1)
                    for i in range(0, rw, 10):
                        h = 5 if i % 20 == 0 else 3
                        cv2.line(
                            ann, (x1 + i, ry + 15), (x1 + i, ry + 15 - h), (0, 0, 0), 1
                        )
        except Exception as e:
            pass

        bio = len(
            [
                e
                for e in self.evidence_manager.registered_evidence
                if "biological" in e.evidence_type
            ]
        )
        trc = len(
            [
                e
                for e in self.evidence_manager.registered_evidence
                if "trace" in e.evidence_type
            ]
        )
        cv2.putText(
            ann,
            f"BIO: {bio} | TRACE: {trc} | TOTAL: {len(self.logged)}",
            (10, ForensicConfig.HEIGHT - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        zones = []
        try:
            for box in results.boxes.data.cpu().numpy():
                name = self.model.names[int(box[5])]
                if name in self.zone_prompts and name not in zones:
                    zones.append(name)
        except:
            pass

        yoff = 80
        for z in zones[:3]:
            cv2.putText(
                ann,
                self.zone_prompts.get(z, "")[:50],
                (10, yoff),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                1,
            )
            yoff += 20

        cv2.putText(
            ann,
            f"FPS: {self.fps:.1f}",
            (ForensicConfig.WIDTH - 120, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        return ann

    def main(self):
        logger.info("Main loop started")
        self.running = True

        if not self.demo_mode:
            capture_t = threading.Thread(target=self._cap_worker, daemon=True)
            inference_t = threading.Thread(target=self._inf_worker, daemon=True)
            capture_t.start()
            inference_t.start()

        last_time = time.time()
        last_fps_update = last_time
        frame_counter = 0

        while self.running:
            try:
                now = time.time()
                delta = now - last_time
                last_time = now

                if delta > 0:
                    self.fps = (
                        0.9 * self.fps + 0.1 * (1.0 / delta) if self.fps > 0 else 30.0
                    )

                if self.demo_mode:
                    frame, results = self.gen_demo_frame()
                else:
                    try:
                        frame, results = self.result_queue.get(timeout=0.1)
                    except:
                        continue

                ann = self.draw(frame, results)
                cv2.imshow("ForensicSight v2.0", ann)
                self.current_frame = frame

                try:
                    for box in results.boxes.data.cpu().numpy():
                        self.process(frame, box)
                except:
                    pass

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    self.running = False
                    break
                elif key == ord("s"):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    cv2.imwrite(f"screenshot_{self.case_id}_{ts}.jpg", frame)
                    logger.info("Screenshot saved")
                elif key == ord("d"):
                    self.demo_mode = not self.demo_mode
                    logger.info(f"Demo mode: {self.demo_mode}")

                frame_counter += 1

            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(0.05)

        self.cleanup()

    def _cap_worker(self):
        self.capture_queue = queue.Queue(maxsize=2)
        while self.running:
            if self.cap and self.cap.isOpened():
                ret, f = self.cap.read()
                if ret:
                    try:
                        if self.capture_queue.full():
                            self.capture_queue.get_nowait()
                        self.capture_queue.put(f)
                    except:
                        pass
            time.sleep(0.01)

    def _inf_worker(self):
        self.result_queue = queue.Queue(maxsize=2)
        while self.running:
            try:
                f = self.capture_queue.get(timeout=0.5)
                r = self.model(f, conf=0.5, iou=0.45, verbose=False)
                if self.result_queue.full():
                    self.result_queue.get_nowait()
                self.result_queue.put((f, r[0]))
            except:
                pass

    def start(self):
        if not self.init_camera():
            return False
        self.running = True
        self.main()
        return True

    def stop(self):
        self.running = False
        self.cleanup()

    def cleanup(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        logger.info(f"Stopped. Evidence logged: {len(self.logged)}")


def main():
    import sys

    demo = "--demo" in sys.argv or "-d" in sys.argv
    case_id = f"CASE-{datetime.now().strftime('%Y-%m-%d')}-001"

    print("=" * 50)
    print("  FORENSIC SIGHT v2.0")
    print("  Press 'q' to quit, 's' for screenshot, 'd' for demo")
    print("=" * 50)

    system = ForensicSightSystem(case_id, "s")
    system.demo_mode = demo

    try:
        system.start()
    except KeyboardInterrupt:
        system.stop()


if __name__ == "__main__":
    main()
