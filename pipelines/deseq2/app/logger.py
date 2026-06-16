import logging
import os

def setup_logger(log_dir: str):
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, "pipeline.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger("DESEQ2_PIPELINE")