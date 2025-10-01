from cli.cli_io import main
import logging
with open("log.log", "w") as file: file.write("")
logging.basicConfig(
filename = "log.log",
level = logging.DEBUG,
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
filemode = "a",
)

main()