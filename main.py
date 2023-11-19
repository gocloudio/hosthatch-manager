from hosthatch_manager.manager import main
from dotenv import load_dotenv
import os.path

if __name__ == "__main__":
    env_file_path = os.getenv("ENV_FILE_PATH", ".envfile")
    if os.path.exists(env_file_path):
        load_dotenv(env_file_path)
    main()