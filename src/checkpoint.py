
"""Resume-safe checkpointing for long Colab runs.

Two layers:
  1. done-keys ledger (JSON on Drive)  -> skip finished work units
  2. artifact store (joblib on Drive)  -> models / partial results

Usage in notebook 07:
    from src.checkpoint import CheckpointManager
    ck = CheckpointManager('s0s5_experiments')
    for unit in units:                      # unit = (corpus, family, ramp, seed, strategy)
        key = ck.key(*unit)
        if ck.is_done(key):
            continue
        result_df = run_unit(*unit)
        ck.save_artifact(key, result_df)
        ck.mark_done(key)
"""
import json, time
from pathlib import Path
import joblib

DRIVE_CK = Path('/content/drive/MyDrive/ids-adapt/checkpoints')


class CheckpointManager:
    def __init__(self, run_name: str):
        self.dir = DRIVE_CK / run_name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.dir / 'ledger.json'
        self.ledger = (json.loads(self.ledger_path.read_text())
                       if self.ledger_path.exists() else {})

    @staticmethod
    def key(*parts) -> str:
        return '|'.join(str(p) for p in parts)

    def is_done(self, key: str) -> bool:
        return self.ledger.get(key, {}).get('done', False)

    def mark_done(self, key: str):
        self.ledger[key] = {'done': True, 'ts': time.strftime('%Y-%m-%d %H:%M:%S')}
        self.ledger_path.write_text(json.dumps(self.ledger, indent=1))

    def save_artifact(self, key: str, obj):
        joblib.dump(obj, self.dir / (key.replace('|', '__') + '.joblib'))

    def load_artifact(self, key: str):
        return joblib.load(self.dir / (key.replace('|', '__') + '.joblib'))

    def progress(self) -> str:
        done = sum(1 for v in self.ledger.values() if v.get('done'))
        return f'{done} units done in {self.dir.name}'
