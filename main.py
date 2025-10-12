from datetime import datetime
import os
import logging
from cli.cli_io import main


logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"{logs_dir}/{current_time}.log"


logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="a",
    encoding="UTF-8"
)


main()