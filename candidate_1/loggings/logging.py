import logging

# 1. Create the logger
logger = logging.getLogger("fintech_app")
logger.setLevel(logging.DEBUG)  

# 2. Create Handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("logging.logs") 

console_handler.setLevel(logging.INFO)  
file_handler.setLevel(logging.ERROR)  

# 3. Create a Formatter and attach it to handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 4. Add Handlers to the Logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
