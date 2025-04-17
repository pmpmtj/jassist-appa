# 🎙️ JASSIST – Modular Voice Assistant Framework

**Jassist** is a modular, voice-driven assistant that organizes your life through spoken interaction. It processes voice notes and intelligently routes them to the appropriate module based on content classification.

## ✨ Features

- 🗂 **Voice Diary**: Log thoughts and notes by speaking
- 📅 **Calendar Integration**: Create calendar events through natural language
- 💰 **Accounts Tracking**: Monitor expenses and financial activities
- 📥 **Google Drive Integration**: Automatically download audio files
- 🔄 **Transcription Engine**: Convert audio to text with OpenAI Whisper
- 📊 **Daily Summaries**: Get semantic summaries of your logs
- 🔊 **Text-to-Speech**: Receive spoken responses

## 📁 Project Structure

```
jassist/
├── voice_diary/
│   ├── config/                # JSON configs and environment variables
│   ├── credentials/           # Google OAuth client files and tokens
│   ├── downloaded/            # Downloaded audio files storage
│   ├── transcriptions/        # Text transcription storage
│   ├── logger_utils/          # Centralized logging configuration
│   ├── db_utils/              # Database utilities and repositories
│   ├── download_audio_files/  # Google Drive interface and downloader
│   ├── transcribe/            # Audio-to-text conversion using OpenAI
│   ├── route_transcription/   # Content classification and routing
│   ├── diary/                 # Diary-specific processing
│   ├── calendar/              # Calendar event extraction and scheduling
│   ├── accounts/              # Financial tracking and analysis
│   ├── summary/               # Semantic summarization of logs
│   ├── voice_input/           # Speech recognition interface
│   └── tts_output/            # Text-to-speech output generation
```

## 🚀 Setup and Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Google Drive API credentials
- OpenAI API key

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/jassist.git
   cd jassist
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create configuration files:
   ```bash
   # Create the .env file in voice_diary/config/
   echo "DATABASE_URL=postgresql://username:password@localhost:5432/jassist" > voice_diary/config/.env
   echo "OPENAI_API_KEY=your_openai_api_key" >> voice_diary/config/.env
   ```

4. Set up Google API credentials:
   - Create a project in the [Google Developer Console](https://console.developers.google.com/)
   - Enable the Google Drive API
   - Create OAuth 2.0 credentials
   - Save the credentials file as `voice_diary/credentials/gdrive_credentials.json`

5. Initialize the database:
   ```bash
   python -m jassist.voice_diary.db_utils.setup_database
   ```

## 🔄 Workflow

Jassist operates through a modular workflow:

1. **Download**: Audio files are downloaded from Google Drive
   ```bash
   python -m jassist.voice_diary.download_audio_files.download_audio_files_cli
   ```

2. **Transcribe**: Audio is converted to text
   ```bash
   python -m jassist.voice_diary.transcribe.transcribe_cli
   ```

3. **Process**: Content is classified and routed to appropriate modules
   - Diary entries are stored for later retrieval
   - Calendar events are extracted and added to your calendar
   - Expenses are tracked in the accounts module

4. **Summarize**: Get daily or weekly summaries
   ```bash
   python -m jassist.voice_diary.summary.summarize_cli
   ```

## ⚙️ Configuration

Each module has its own configuration file in `voice_diary/config/` or within its module directory:

- **Download**: `download_config.json`
- **Transcription**: `transcribe/config/config_transcribe.json`
- **Calendar**: `calendar/config/calendar_config.json`
- **Database**: Environment variables in `.env`

## 📚 Documentation

Detailed module documentation is available for:

- [Google Drive Download Flow](google_drive_download_flow.md)
- [Transcription Process](transcribe_audio_flow.md)
- [Calendar Integration](calendar_flow.md)
- [Database Utilities Design](db_utils.md)

## 🧩 Extending Jassist

Jassist is designed to be modular and extensible:

1. Create a new module directory in `voice_diary/`
2. Implement the module's core functionality
3. Add a repository in `db_utils/` if database storage is needed
4. Register the module in `route_transcription.py` with appropriate tag

## 📝 License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on the GitHub repository.

