import tasks.transfer
from classes.config import Config

CONFIG = Config()

def transfer_primary_image():
    CONFIG.nornir.run(task=tasks.transfer.transfer_image)
