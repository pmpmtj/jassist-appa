from pathlib import Path
from jassist.voice_diary.download_audio_files.config_loader import load_config
from jassist.voice_diary.download_audio_files.gdrive_downloader import run_download
from jassist.voice_diary.logger_utils.logger_utils import setup_logger

logger = setup_logger("download_audio_files_cli", module="download_audio_files")

def main():
    try:
        # Paths to config and template
        config_path = Path(__file__).parents[2] / "voice_diary" / "config" / "download_config.json"
        template_path = Path(__file__).parent / "download_config_sample.json"

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
