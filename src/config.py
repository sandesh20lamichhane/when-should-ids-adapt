"""Central configuration. Every notebook does: from src.config import CFG

All paths point into Google Drive so nothing is lost when the Colab VM dies.
All randomness flows from CFG.SEEDS — no other seeds anywhere in the project.
"""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    # ---------- storage (Google Drive) ----------
    DRIVE_ROOT: Path = Path("/content/drive/MyDrive/ids-adapt")
    REPO_ROOT: Path = Path("/content/repo")

    # ---------- pre-registered experimental constants ----------
    SEEDS: tuple = (11, 23, 37, 51, 73)
    LABEL_BUDGETS: tuple = (0.01, 0.02, 0.05, 0.10, 0.20)  # fraction of stream
    ZERO_DAY_ONSET: float = 0.40          # injection at 40% of stream
    GRADUAL_RAMP_LEN: float = 0.10        # linear ramp over 10% of stream
    RECOVERY_RECALL: float = 0.70         # "recovered" when family recall >= 0.7
    WINDOW_SIZE: int = 5_000              # flows per monitoring window
    PERIODIC_INTERVAL: float = 0.10       # S1 retrains every 10% of stream
    MIN_FAMILY_FLOWS: int = 5_000         # families below this are skipped

    # ---------- dataset registry ----------
    DATASETS: dict = field(default_factory=lambda: {
        "cicids2017": {
            "role": "primary",
            "note": "Use the Engelen-corrected version (WTMC 2021 release).",
            "url": "https://intrusion-detection.distrinet-research.be/WTMC2021/",
        },
        "cse_cic_ids2018": {
            "role": "primary",
            "note": "Use the Liu-corrected labels where available.",
            "url": "https://www.unb.ca/cic/datasets/ids-2018.html",
        },
        "unsw_nb15": {
            "role": "primary",
            "url": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        },
        "luflow": {
            "role": "secondary",
            "url": "https://github.com/ruzzzzz/LUFlow",
        },
        "ton_iot": {
            "role": "secondary",
            "url": "https://research.unsw.edu.au/projects/toniot-datasets",
        },
        "ciciot2023": {
            "role": "secondary",
            "url": "https://www.unb.ca/cic/datasets/iotdataset-2023.html",
        },
    })

    # ---------- derived paths ----------
    @property
    def DATA_RAW(self) -> Path: return self.DRIVE_ROOT / "data" / "raw"
    @property
    def DATA_PROC(self) -> Path: return self.DRIVE_ROOT / "data" / "processed"
    @property
    def MODELS(self) -> Path: return self.DRIVE_ROOT / "models"
    @property
    def RESULTS(self) -> Path: return self.REPO_ROOT / "results"
    @property
    def FIGURES(self) -> Path: return self.REPO_ROOT / "figures"

    def make_dirs(self):
        for p in (self.DATA_RAW, self.DATA_PROC, self.MODELS,
                  self.RESULTS, self.FIGURES):
            p.mkdir(parents=True, exist_ok=True)


CFG = Config()


def git_hash() -> str:
    """Current repo commit hash — embedded in every results filename."""
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "-C", str(CFG.REPO_ROOT), "rev-parse", "--short", "HEAD"],
            text=True).strip()
    except Exception:
        return "nogit"


def results_path(experiment: str, dataset: str, seed: int) -> Path:
    """Canonical results filename: experiment__dataset__seed__githash.csv"""
    return CFG.RESULTS / f"{experiment}__{dataset}__s{seed}__{git_hash()}.csv"
