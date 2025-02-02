import logging
import sys

def setup_logging(file_name):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(f"{file_name}", mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )