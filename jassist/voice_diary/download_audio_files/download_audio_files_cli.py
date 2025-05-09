from pathlib import Path
from jassist.voice_diary.download_audio_files.config_loader import load_config
from jassist.voice_diary.download_audio_files.gdrive_downloader import run_download
from jassist.voice_diary.logger_utils.logger_utils import setup_logger
from jassist.voice_diary.utils.path_utils import resolve_path

logger = setup_logger("download_audio_files_cli", module="download_audio_files")

def main():
    try:
        # Get base directory paths
        script_dir = Path(__file__).resolve().parent
        voice_diary_dir = script_dir.parent.parent
        
        # Paths to config and template using consistent resolution
        config_path = resolve_path("config/download_config.json", voice_diary_dir)
        template_path = resolve_path("download_config_sample.json", script_dir)

        logger.info(f"Loading configuration from {config_path}")
        config = load_config(config_path, template_path)

        logger.info("Starting download process...")
        success = run_download(config)

        if success:
            logger.info("Download process completed successfully.")
        else:
            logger.warning("Download process finished with warnings or partial failure.")
    except Exception as e:
        logger.exception(f"Fatal error in CLI: {e}")

if __name__ == "__main__":
    main()
