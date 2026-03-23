import os
import logging

print("=" * 50)
print(f"Current working directory: {os.getcwd()}")
print(f"Python is looking for log file at:")
print(f"  {os.path.join(os.getcwd(), 'test_log.log')}")
print("=" * 50)

# Try with absolute path
log_path = os.path.join(os.getcwd(), "test_absolute.log")
print(f"Trying absolute path: {log_path}")

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Test message with absolute path")

print("Check the directory above for test_absolute.log")
input("Press Enter to exit...")
