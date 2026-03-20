# TODO: Create a job to clean data from temp files on startup.
import os
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clean_temp_files():
    shutil.rmtree(os.path.join(ROOT_DIR, "temp_storage"))
    os.makedirs(os.path.join(ROOT_DIR, "temp_storage"))

if __name__ == "__main__":
    clean_temp_files()