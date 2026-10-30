import os
import shutil

import kagglehub


def download_kaggle_dataset(dataset: str, dest_dir: str = None) -> None:
    """
    Downloads a Kaggle dataset using kagglehub and copies the files to a destination directory.
    Skips download if all files already exist.

    Parameters:
    - dataset: str, dataset name in the format "user/dataset-name"
    - dest_dir: str, destination directory. If None, defaults to "data/raw" in the repository.
    """
    # Set destination directory
    if dest_dir is None:
        dest_dir = os.path.join(os.path.dirname(__file__), "../../data/raw")
    os.makedirs(dest_dir, exist_ok=True)

    # Download the dataset (kagglehub creates a temp folder)
    temp_path = kagglehub.dataset_download(dataset)
    print("Path to dataset files:", temp_path)

    # Copy only the files that aren't there yet
    for filename in os.listdir(temp_path):
        src_file = os.path.join(temp_path, filename)
        dest_file = os.path.join(dest_dir, filename)

        if os.path.exists(dest_file):
            print(f"Already exists, skipping: {dest_file}")
        else:
            shutil.copy2(src_file, dest_file)
            print(f"Copied to: {dest_file}")
