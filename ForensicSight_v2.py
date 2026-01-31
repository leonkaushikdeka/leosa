"""
ForensicSight v2.0 - Real-time Forensic Analysis System (Improved Detection)
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


class ForensicConfig:
    WIDTH = 1280
    HEIGHT = 720
    FPS_TARGET = 30
    CONF_THRESHOLD = 0.25

    WEAPONS = {"knife", "scissors", "gun", "firearm", "knife set", "dagger"}
    BIOLOGICAL = {"person", "face", "blood"}
    ELECTRONICS = {"cell phone", "laptop", "computer", "phone", "mobile"}
    CONTAINERS = {"suitcase", "backpack", "handbag", "bag", "box", "trunk"}
    FURNITURE = {"bed", "couch", "chair", "table", "dining table", "desk", "bench"}
    KITCHEN = {"refrigerator", "oven", "microwave", "sink", "stove", "toaster"}
    DOCUMENTS = {"book", "paper", "newspaper", "document", "letter"}
    CLOTHING = {"tie", "shirt", "pants", "jacket", "coat", "dress", "shoe"}
    TOOLS = {"scissors", "knife", "screwdriver", "hammer", "wrench", "drill"}
    VALUABLES = {"watch", "ring", "jewelry", "necklace", "earring", "bracelet"}
    TRAFFIC = {"car", "truck", "vehicle", "bicycle", "motorcycle", "bus"}

    ALL_CATEGORIES = (
        WEAPONS
        | BIOLOGICAL
        | ELECTRONICS
        | CONTAINERS
        | FURNITURE
        | KITCHEN
        | DOCUMENTS
        | CLOTHING
        | TOOLS
        | VALUABLES
        | TRAFFIC
    )

    COLOR_WEAPON = (0, 0, 255)
    COLOR_BIOLOGICAL = (0, 0, 200)
    COLOR_ELECTRONIC = (0, 255, 255)
    COLOR_CONTAINER = (255, 165, 0)
    COLOR_FURNITURE = (255, 0, 0)
    COLOR_TOOL = (0, 255, 0)
    COLOR_OTHER = (128, 128, 128)

    GRID_SIZE = 50
    DUPLICATE_COOLDOWN = 1.0


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
        lower_red1 = np.array([0, 100, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 50])
        upper_red2 = np.array([180, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)
        return mask

    def analyze_pattern(self, mask: np.ndarray, image_area: int) -> Dict[str, Any]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_stains = len(contours)
        blood_ratio = total_stains / (image_area / 10000) if image_area > 0 else 0

        patterns = {"drip": 0, "spatter": 0, "pool": 0, "transfer": 0}
        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if area > 500:
                    patterns["pool"] += 1
                elif circularity > 0.7:
                    patterns["drip"] += 1
                elif area < 50:
                    patterns["spatter"] += 1
                else:
                    patterns["transfer"] += 1

        dominant = max(patterns, key=patterns.get) if patterns else "none"

        return {
            "total_stains": total_stains,
            "blood_ratio": blood_ratio,
            "dominant_pattern": dominant,
            "patterns": patterns,
            "requires_forensic": blood_ratio > 5 or total_stains > 10,
        }


class GunshotResidueDetector:
    def detect_gsr(self, roi: np.ndarray) -> Dict[str, Any]:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        gsr_particles = []
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 5 <= area <= 100:
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.5:
                        gsr_particles.append(cnt)

        count = len(gsr_particles)
        density = count / max(1, roi.shape[0] * roi.shape[1] / 1000)

        if count > 100:
            distance = "Contact-6 inches"
        elif count > 50:
            distance = "6-12 inches"
        elif count > 20:
            distance = "12-24 inches"
        else:
            distance = ">24 inches"

        return {
            "gsr_particles": count,
            "density": density,
            "estimated_distance": distance,
            "is_gsr_present": count > 10,
            "contamination_risk": count > 50,
        }


class FingerprintDetector:
    def enhance_fingerprint(self, roi: np.ndarray) -> Dict[str, Any]:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        sobelx = cv2.Sobel(enhanced, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(enhanced, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        edges = np.uint8(255 * magnitude / max(1, np.max(magnitude)))

        _, binary = cv2.threshold(edges, 30, 255, cv2.THRESH_BINARY)
        skeleton = morphology.skeletonize(binary > 127)

        ridges = measure.label(skeleton)
        regions = measure.regionprops(ridges)

        minutiae = 0
        for region in regions:
            for coord in region.coords:
                y, x = coord
                nb = skeleton[
                    max(0, y - 1) : min(y + 2, skeleton.shape[0]),
                    max(0, x - 1) : min(x + 2, skeleton.shape[1]),
                ]
                pixels = np.sum(nb > 0)
                if pixels == 3 or pixels > 4:
                    minutiae += 1

        return {
            "minutiae_count": minutiae,
            "quality": np.std(enhanced) / 128,
            "is_latent": minutiae > 5 and np.std(enhanced) > 30,
            "requires_afis": minutiae > 15,
        }


class ToolMarkAnalyzer:
    def analyze_tool_marks(self, roi: np.ndarray) -> Dict[str, Any]:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(sobelx**2 + sobely**2)

        edges = np.uint8(255 * magnitude / max(1, np.max(magnitude)))
        _, binary = cv2.threshold(edges, 40, 255, cv2.THRESH_BINARY)

        lines = cv2.HoughLinesP(
            binary, 1, np.pi / 180, threshold=30, minLineLength=20, maxLineGap=5
        )

        angles = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 != x1:
                    angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                    angles.append(angle)

        variance = np.std(angles) if len(angles) > 1 else 0

        if variance < 30:
            tool_type = "Screwdriver"
        elif variance < 100:
            tool_type = "Pliers/Wrench"
        elif variance < 200:
            tool_type = "Hammer"
        else:
            tool_type = "Unknown/Impact"

        return {
            "tool_type": tool_type,
            "striation_lines": len(angles),
            "angle_variance": variance,
            "is_tool_mark": len(angles) > 5,
        }


class TraceEvidenceAnalyzer:
    def analyze_trace(self, roi: np.ndarray) -> Dict[str, Any]:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        uv_mask = cv2.inRange(hsv, np.array([130, 50, 0]), np.array([170, 255, 100]))
        blue_mask = cv2.inRange(hsv, np.array([100, 50, 0]), np.array([140, 255, 255]))

        uv_count = np.sum(uv_mask > 0)
        blue_count = np.sum(blue_mask > 0)

        fiber_mask = cv2.inRange(hsv, np.array([0, 50, 100]), np.array([180, 150, 255]))
        fiber_count = np.sum(fiber_mask > 0)

        return {
            "uv_fluorescent": uv_count > 50,
            "blue_enhancement": blue_count > 100,
            "fibers_detected": fiber_count > 20,
            "fiber_count": fiber_count,
            "particle_density": (uv_count + blue_count) / max(1, roi.size / 1000),
        }


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

    def _create_structure(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for d in self.structure_dirs:
            (self.base_dir / d).mkdir(exist_ok=True)

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

    def _gen_id(self, ev_type: str) -> str:
        prefix_map = {
            "biological": "BIO",
            "trace": "TRC",
            "impression": "IMP",
            "ballistics": "BAL",
            "weapon": "BAL",
            "electronic": "PHY",
        }
        prefix = prefix_map.get(ev_type[:10].lower(), "GEN")
        self.evidence_counter[prefix] += 1
        return f"{self.case_id}-{prefix}-{self.evidence_counter[prefix]:03d}"

    def _sha256(self, img: np.ndarray) -> str:
        _, enc = cv2.imencode(".png", img)
        return hashlib.sha256(enc.tobytes()).hexdigest()

    def create_evidence(
        self,
        ev_type: str,
        subclass: str,
        bbox: Tuple,
        dims: Tuple,
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
        self._save_evidence(ev, img)
        self._append_csv(ev)
        self.registered_evidence.append(ev)
        logger.info(
            f"EVIDENCE: {ev.evidence_id} - {ev.evidence_type} | {ev.subclassification}"
        )
        return ev

    def _save_evidence(self, ev: ForensicEvidence, img: np.ndarray):
        try:
            photo_dir = self.base_dir / "05_Crime_Scene_Photography"
            hash_short = ev.image_hash_sha256[:12]
            macro_path = photo_dir / f"{ev.evidence_id}_macro_{hash_short}.png"
            context_path = photo_dir / f"{ev.evidence_id}_context_{hash_short}.jpg"
            cv2.imwrite(str(macro_path), img)

            context_img = np.zeros(
                (ForensicConfig.HEIGHT, ForensicConfig.WIDTH, 3), dtype=np.uint8
            )
            context_img[:] = (15, 15, 20)
            bx, by, bw, bh = ev.location_bbox
            by2 = min(by + bh + 80, ForensicConfig.HEIGHT - 80)
            bx2 = min(bx + bw + 80, ForensicConfig.WIDTH - 30)
            roi_resized = cv2.resize(img, (max(10, bx2 - bx), max(10, by2 - by)))
            context_img[by:by2, bx:bx2] = roi_resized
            cv2.rectangle(context_img, (bx, by), (bx2, by2), (0, 255, 0), 2)
            cv2.putText(
                context_img,
                ev.evidence_id,
                (bx, by - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                context_img,
                f"Type: {ev.evidence_type}",
                (bx, by2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
            )
            cv2.putText(
                context_img,
                f"Priority: {ev.collection_priority}",
                (bx, by2 + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 200, 100),
                1,
            )
            cv2.imwrite(str(context_path), context_img)
        except Exception as e:
            logger.error(f"Save error: {e}")

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
        except:
            pass


class ForensicSightSystem:
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.model = YOLO("yolov8s.pt")
        self.cap = None
        self.running = False
        self.fps = 0
        self.frame_count = 0
        self.last_time = time.time()
        self.demo_mode = False
        self.evidence_manager = ForensicEvidenceManager(case_id)
        self.bpa = BloodstainPatternAnalysis()
        self.gsr = GunshotResidueDetector()
        self.fingerprint = FingerprintDetector()
        self.tool = ToolMarkAnalyzer()
        self.trace = TraceEvidenceAnalyzer()
        self.tracked = {}
        self.logged = set()
        logger.info(f"ForensicSight v2.0 initialized: {case_id}")

    def init_camera(self) -> bool:
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, ForensicConfig.WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ForensicConfig.HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, ForensicConfig.FPS_TARGET)
        if not self.cap.isOpened():
            logger.warning("Camera not available - demo mode")
            self.demo_mode = True
        return True

    def gen_demo_frame(self):
        frame = np.random.randint(
            0, 40, (ForensicConfig.HEIGHT, ForensicConfig.WIDTH, 3), dtype=np.uint8
        )
        frame[100:400, 300:700] = (30, 30, 45)
        cv2.putText(
            frame,
            "DEMO MODE - ForensicSight v2.0",
            (380, 350),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (100, 120, 150),
            2,
        )

        demo_objs = [
            {"bbox": [350, 180, 500, 350], "cls": 41, "conf": 0.85},
            {"bbox": [700, 80, 950, 320], "cls": 59, "conf": 0.92},
            {"bbox": [80, 380, 280, 580], "cls": 0, "conf": 0.75},
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

    def process_detection(self, frame, box):
        bbox = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
        cls_id = int(box[5])
        conf = float(box[4])
        name = self.model.names[cls_id] if cls_id < len(self.model.names) else "unknown"

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
        priority = 3
        analysis = {}
        risks = []

        name_lower = name.lower()

        if name_lower in ForensicConfig.WEAPONS or any(
            w in name_lower for w in ["knife", "gun", "scissor", "weapon"]
        ):
            ev_type = "weapon"
            subclass = f"WEAPON: {name}"
            priority = 5
            analysis = {"weapon_type": name, "threat_level": "HIGH"}
            risks.append("Handle with extreme caution")

        elif (
            name_lower in ForensicConfig.BIOLOGICAL
            or "blood" in name_lower
            or "face" in name_lower
        ):
            ev_type = "biological_blood"
            subclass = f"BIOLOGICAL: {name}"
            priority = 5
            bpa = self.bpa.analyze_pattern(self.bpa.detect_blood(roi), roi.size)
            analysis = {"biological": name, "bpa": bpa}
            risks.append("Biohazard - use PPE")

        elif name_lower in ForensicConfig.ELECTRONICS or any(
            e in name_lower for e in ["phone", "laptop", "computer", "mobile"]
        ):
            ev_type = "electronic"
            subclass = f"ELECTRONIC: {name}"
            priority = 4
            analysis = {"electronic": name, "digital_forensics": True}

        elif name_lower in ForensicConfig.CONTAINERS or any(
            c in name_lower for c in ["bag", "box", "suitcase", "backpack", "container"]
        ):
            ev_type = "trace_evidence"
            subclass = f"CONTAINER: {name}"
            priority = 4
            trace = self.trace.analyze_trace(roi)
            fp = self.fingerprint.enhance_fingerprint(roi)
            analysis = {"container": name, "trace": trace, "fingerprint": fp}
            if fp["is_latent"]:
                analysis["latent_print"] = True
                priority = 5

        elif (
            name_lower in ForensicConfig.FURNITURE
            or name_lower in ForensicConfig.KITCHEN
        ):
            ev_type = "search_zone"
            subclass = f"SEARCH ZONE: {name}"
            priority = 2
            bpa = self.bpa.analyze_pattern(self.bpa.detect_blood(roi), roi.size)
            gsr = self.gsr.detect_gsr(roi)
            analysis = {"zone": name, "blood_check": bpa, "gsr_check": gsr}
            if bpa["requires_forensic"]:
                analysis["blood_detected"] = True
                risks.append("Possible biological evidence")
            if gsr["is_gsr_present"]:
                analysis["gsr_detected"] = True
                risks.append("GSR contamination")

        elif name_lower in ForensicConfig.TOOLS or any(
            t in name_lower for t in ["knife", "scissor", "screwdriver", "hammer"]
        ):
            ev_type = "impression_tool_mark"
            subclass = f"TOOL: {name}"
            priority = 4
            tool_analysis = self.tool.analyze_tool_marks(roi)
            analysis = {"tool": name, "tool_analysis": tool_analysis}

        elif name_lower in ForensicConfig.DOCUMENTS:
            ev_type = "trace_evidence"
            subclass = f"DOCUMENT: {name}"
            priority = 3
            analysis = {"document": name}

        elif name_lower in ForensicConfig.CLOTHING:
            ev_type = "biological_blood"
            subclass = f"CLOTHING: {name}"
            priority = 3
            bpa = self.bpa.analyze_pattern(self.bpa.detect_blood(roi), roi.size)
            analysis = {"clothing": name, "blood_check": bpa}
            if bpa["requires_forensic"]:
                risks.append("Possible biological evidence")

        else:
            ev_type = "contextual"
            subclass = f"OBJECT: {name}"
            priority = 1
            analysis = {"object": name}

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

    def draw(self, frame, results):
        ann = frame.copy()

        cv2.rectangle(ann, (0, 0), (ForensicConfig.WIDTH, 65), (0, 0, 0), -1)
        status = "DEMO" if self.demo_mode else "LIVE"
        color = (255, 165, 0) if self.demo_mode else (0, 255, 0)
        cv2.putText(
            ann,
            f"FORENSIC SIGHT v2.0 [{status}] - {self.case_id}",
            (10, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
        )

        if results.boxes is not None:
            try:
                for box in results.boxes.data.cpu().numpy():
                    bbox = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
                    cls_id = int(box[5])
                    name = (
                        self.model.names[cls_id]
                        if cls_id < len(self.model.names)
                        else "unknown"
                    )
                    name_lower = name.lower()

                    if (
                        name_lower in ForensicConfig.WEAPONS
                        or "knife" in name_lower
                        or "gun" in name_lower
                    ):
                        color = ForensicConfig.COLOR_WEAPON
                        label = f"⚠️ WEAPON: {name} | PRIORITY: 5"
                    elif (
                        name_lower in ForensicConfig.BIOLOGICAL or "blood" in name_lower
                    ):
                        color = ForensicConfig.COLOR_BIOLOGICAL
                        label = f"🩸 BIOLOGICAL: {name} | PRIORITY: 5"
                    elif (
                        name_lower in ForensicConfig.ELECTRONICS
                        or "phone" in name_lower
                        or "laptop" in name_lower
                    ):
                        color = ForensicConfig.COLOR_ELECTRONIC
                        label = f"📱 {name} | DIGITAL EVIDENCE"
                    elif name_lower in ForensicConfig.CONTAINERS or any(
                        c in name_lower for c in ["bag", "box", "suitcase"]
                    ):
                        color = ForensicConfig.COLOR_CONTAINER
                        label = f"📦 {name} | CHECK CONTENTS"
                    elif (
                        name_lower in ForensicConfig.FURNITURE
                        or name_lower in ForensicConfig.KITCHEN
                    ):
                        color = ForensicConfig.COLOR_FURNITURE
                        label = f"🪑 SEARCH ZONE: {name}"
                    elif name_lower in ForensicConfig.TOOLS:
                        color = ForensicConfig.COLOR_TOOL
                        label = f"🔧 TOOL: {name}"
                    else:
                        color = ForensicConfig.COLOR_OTHER
                        label = f"📍 {name}"

                    cv2.rectangle(ann, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                    (tw, th), _ = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                    )
                    cv2.rectangle(
                        ann,
                        (bbox[0], bbox[1] - th - 12),
                        (bbox[0] + tw + 5, bbox[1]),
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

                    bx, by, bw, bh = bbox
                    rw = min(80, bw)
                    ry = min(bh + 20, ForensicConfig.HEIGHT - 50)
                    if rw > 15:
                        cv2.rectangle(
                            ann, (bx, ry), (bx + rw, ry + 12), (255, 255, 255), -1
                        )
                        cv2.rectangle(ann, (bx, ry), (bx + rw, ry + 12), (0, 0, 0), 1)
                        for i in range(0, rw, 10):
                            h = 5 if i % 20 == 0 else 3
                            cv2.line(
                                ann,
                                (bx + i, ry + 12),
                                (bx + i, ry + 12 - h),
                                (0, 0, 0),
                                1,
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
        trace = len(
            [
                e
                for e in self.evidence_manager.registered_evidence
                if "trace" in e.evidence_type
            ]
        )
        weapon = len(
            [
                e
                for e in self.evidence_manager.registered_evidence
                if "weapon" in e.evidence_type
            ]
        )
        cv2.putText(
            ann,
            f"BIO: {bio} | TRACE: {trace} | WEAPON: {weapon} | TOT: {len(self.logged)}",
            (10, ForensicConfig.HEIGHT - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            ann,
            f"FPS: {self.fps:.1f}",
            (ForensicConfig.WIDTH - 120, 45),
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
            capture_q = queue.Queue(maxsize=2)
            result_q = queue.Queue(maxsize=2)

            def capture_worker():
                while self.running:
                    if self.cap and self.cap.isOpened():
                        ret, f = self.cap.read()
                        if ret:
                            try:
                                if capture_q.full():
                                    capture_q.get_nowait()
                                capture_q.put(f)
                            except:
                                pass
                    time.sleep(0.01)

            def inference_worker():
                while self.running:
                    try:
                        f = capture_q.get(timeout=0.5)
                        r = self.model(
                            f,
                            conf=ForensicConfig.CONF_THRESHOLD,
                            iou=0.45,
                            verbose=False,
                        )
                        if result_q.full():
                            result_q.get_nowait()
                        result_q.put((f, r[0]))
                    except:
                        pass

            threading.Thread(target=capture_worker, daemon=True).start()
            threading.Thread(target=inference_worker, daemon=True).start()

        last_time = time.time()

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
                        frame, results = result_q.get(timeout=0.2)
                    except:
                        continue

                ann = self.draw(frame, results)
                self.current_frame = frame
                cv2.imshow("ForensicSight v2.0", ann)

                if results.boxes is not None:
                    try:
                        for box in results.boxes.data.cpu().numpy():
                            self.process_detection(frame, box)
                    except:
                        pass

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    self.running = False
                    break
                elif key == ord("s"):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    cv2.imwrite(f"screenshot_{self.case_id}_{ts}.jpg", frame)
                elif key == ord("d"):
                    self.demo_mode = not self.demo_mode
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(0.05)

        self.cleanup()

    def start(self):
        self.init_camera()
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

    demo = "--demo" in sys.argv
    case_id = f"CASE-{datetime.now().strftime('%Y-%m-%d')}-001"

    print("=" * 60)
    print("  FORENSIC SIGHT v2.0 - Enhanced Detection")
    print("  Press 'q' to quit, 's' for screenshot, 'd' for demo mode")
    print("=" * 60)

    system = ForensicSightSystem(case_id)
    system.demo_mode = demo

    try:
        system.start()
    except KeyboardInterrupt:
        system.stop()


if __name__ == "__main__":
    main()
