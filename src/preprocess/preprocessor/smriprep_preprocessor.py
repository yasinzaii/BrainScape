# src/preprocess/preprocessor/smriprep_preprocessor.py
import os
import shutil
import logging
import threading
import subprocess

import docker
from docker.errors import DockerException, ImageNotFound, APIError

from pathlib import Path
from preprocess.preprocessor.base_plugin import PreprocessorPlugin

from utils.common_utils import find_path_upwards

class SMRIPrepPreprocessor(PreprocessorPlugin):
    
    # Class-specific plugin name
    plugin_name = "smriprep"

    @classmethod
    def get_name(cls) -> str:
        return cls.plugin_name
    
    
    def __init__(self, dataset_settings: dict, dataset_path: Path, mapping: dict, config: dict):
        super().__init__(dataset_settings, dataset_path, mapping)
        
        self.logger = logging.getLogger(__name__)
        self.mapping = mapping

        self.download_dir_name = self.dataset_settings.get("downloadDirName")
        self.download_dir = dataset_path / self.download_dir_name

        # Unique Session Names and Group Numbers
        self.session_names = sorted(set(entry['session'] for entry in mapping))
        self.group_nums = sorted(set(entry['group'] for entry in mapping))
        # Just Discard Other Groups. Because the Preprocessed data 
        # From the other groups will override the main group anyways.
        self.group_nums = [self.group_nums[0]]

        # Temperory Directory
        self.temp_download_dir = dataset_path  / f"Temp{self.download_dir_name}" 
        
        # Acquire Modalities
        modalities =  self.dataset_settings["mapping"]["regex"]["modality"].keys()

        # Check if the Session Directory Consists of Multiple Parts
        self.output_dir_name =  self.dataset_settings.get("preprocessedDirName", "preprocessed")
        self.output_dir = dataset_path / self.output_dir_name
        self.temp_output_dir = dataset_path / f'Temp{self.dataset_settings.get("preprocessedDirName", "preprocessed")}'

        # SMRIprep Settings
        self.smriprep_config = self.dataset_settings["preprocess"]["smriprep"]

        self.work_dir = dataset_path / self.smriprep_config.get("workDirName", "work")
        self.image_name  = self.smriprep_config.get("dockerImageName", "nipreps/smriprep:latest") 
        self.num_threads  = self.smriprep_config.get("nThreads", 8) 
        self.license_file = find_path_upwards(
            starting_path=Path(__file__), 
            target_relative_path = self.smriprep_config.get("freesurferLic", "Docker/license.txt")
        )
        
        # Initialize Docker client
        self.docker_client = docker.from_env()

        # Check if Docker is running
        try:
            self.docker_client.ping()
            self.logger.info("- SMRIPrepPreprocessor - Docker is running and accessible.")
        except DockerException as e:
            self.logger.error("- SMRIPrepPreprocessor - Docker is not running or not accessible.")
            raise RuntimeError("Docker is not running or not accessible.") from e
        
        # Check if the Target Pipeline Output Directoy is present
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
            self.logger.info(f"- SMRIPrepPreprocessor - Created Output Directory {self.output_dir} for Preprocessing Pipeline")
        else:
            if any(self.output_dir.iterdir()):
                self.logger.info(f"- SMRIPrepPreprocessor - Output Directory {self.output_dir} already present by not Empty, Deleting Directory")          
                shutil.rmtree(self.output_dir)
            self.output_dir.mkdir(exist_ok=True)      

        # Pull the Docker image if it's not available
        try:
            self.docker_client.images.get(self.image_name)
            self.logger.info(f"- SMRIPrepPreprocessor - Docker image '{self.image_name}' found locally.")
        except ImageNotFound:
            self.logger.info(f"- SMRIPrepPreprocessor - Docker image '{self.image_name}' not found locally. Pulling...")
            self.docker_client.images.pull(self.image_name)
            self.logger.info(f"- SMRIPrepPreprocessor - Docker image '{self.image_name}' pulled successfully.")
        except APIError as e:
            self.logger.error(f"- SMRIPrepPreprocessor - Error accessing Docker image '{self.image_name}': {e}")
            return False
        return

    # Function to stream logs
    def _stream_logs(self, container):
        try:
            # Attach to the container's output streams
            for line in container.attach(stdout=True, stderr=True, stream=True, logs=True):
                # Simply Printing to Console
                print(line.strip().decode('utf-8'))
        except Exception as e:
            self.logger.error(f"- SMRIPrepPreprocessor - Error streaming logs: {e}")

    def run(self) -> bool:
        
        # looping through sessions and groups
        for session in self.session_names: 
            for group in self.group_nums:
                
                # Remove the folder if it already exists
                if os.path.exists(self.temp_download_dir):
                    shutil.rmtree(self.temp_download_dir)
                if os.path.exists(self.temp_output_dir):
                    shutil.rmtree(self.temp_output_dir)
                os.mkdir(self.temp_download_dir)
                os.mkdir(self.temp_output_dir)

                # looping throught mapping and matching for session and groups
                for entry in self.mapping:
                    if entry['session'] == session and entry['group'] == group:
                        
                        entry['temp'] = {}
                        temp_path = self.temp_download_dir / entry["subject"] / session/entry["type"]
                        presense_check = False
                        for mod in entry['download']:
                            entry['temp'][mod] = str(temp_path / entry['mris'][mod])
                            presense_check = True

                        # Copy the Selected Session and Group Data into Temp Folder.
                        if presense_check:
                            # Ensure the destination directory exists
                            try:
                                temp_path.mkdir(parents=True, exist_ok=True)
                            except Exception as e:
                                self.logger.error(f"Failed to create directory {temp_path}: {e}")
                                continue 

                            # Copying Each MRI Modailty
                            for mod in entry['download']:
                                download_path = str(self.download_dir / entry['download'][mod])
                                temp_path = entry['temp'][mod]
                                shutil.copy(download_path, temp_path)
                
                # Run SMRIPrep Docker
                status = self.run_docker()
                if not status:
                    self.logger.critical(f"Docker Running Failed, Dataset:{self.dataset_path}, session:{session}, group:{group}")
                    raise

                # looping throught mapping and matching for session and groups
                smriprep_dir = self.temp_output_dir / 'smriprep'
                smriprep_dir_list = list(smriprep_dir.iterdir())
                for entry in self.mapping:
                    if entry['session'] == session and entry['group'] == group:
                        entry[self.output_dir_name] = {}

                        for file_path in smriprep_dir_list:
                            file_path_str = str(file_path)
                            if entry['subject'] in file_path_str and \
                                entry['session'] in file_path_str and \
                                't1w.nii.gz' in str(file_path_str).lower() and \
                                self.smriprep_config["outputSpaces"] in file_path_str:
                                
                                entry[self.output_dir_name]['t1w'] = file_path_str

                # Move The Files from Temp Output Directory to The Output Directory
                shutil.copytree(smriprep_dir, self.output_dir, dirs_exist_ok=True)


    def run_docker(self):
        
        try:
            # Ensure the output and work directories exist
            self.temp_output_dir.mkdir(parents=True, exist_ok=True)
            self.work_dir.mkdir(parents=True, exist_ok=True)

            # Set up volume bindings
            volumes = {
                str(self.temp_download_dir.resolve()): {'bind': '/data', 'mode': 'ro'},
                str(self.temp_output_dir.resolve()): {'bind': '/out', 'mode': 'rw'},
                str(self.work_dir.resolve()): {'bind': '/work', 'mode': 'rw'},
                str(self.license_file.resolve()): {'bind': '/opt/freesurfer/license.txt', 'mode': 'ro'}
            }

            # Construct the SMRIPrep command
            cmd = [
                "/data", # Path to Data Directory
                "/out",  # Path to the Output Directory
                "participant", 
                "--work-dir", '/work', # Path to work Directory 
                "--output-spaces", self.smriprep_config["outputSpaces"],
                "--nthreads", str(self.num_threads),
                "--no-submm-recon", # disable sub-millimeter (hires) reconstruction
                "--no-msm", # Disable Multimodal Surface Matching surface registration.
                "--fs-no-reconall", # disable FreeSurfer surface preprocessing.
                "--stop-on-first-crash"
            ]

            container = self.docker_client.containers.run(
                image=self.image_name,
                command=cmd,
                user=self.smriprep_config["userIdGroudId"],
                volumes=volumes,
                auto_remove=True,
                detach=True, # Running in detached mode
                stderr=True,
                stdout=True,
                tty=False,
            )

            # Start the log streaming thread
            log_thread = threading.Thread(target=self._stream_logs, args=(container,))
            log_thread.start()

            # Wait for the container to finish
            result = container.wait()

            # Wait for the log thread to finish
            log_thread.join()

            self.logger.info("SMRIPrep completed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"SMRIPrep failed with error: {e.stderr.decode()}")
            return False
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            return False

    def _get_additional_options(self):
        """
        Constructs additional command-line options based on the dataset settings
        to include or exclude certain preprocessing steps.
        """
        options = []

        # Add options to exclude surface reconstruction and segmentation
        options.append("--no-submm-recon")
        options.append("--skull-strip-fixed-seed")

        # Add any other options you need
        # For example, if you have custom settings in dataset_settings

        return options
