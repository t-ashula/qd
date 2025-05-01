# QD - Audio Transcription and Search

QD is a web application that allows users to upload audio files, transcribe them, vectorize the segments, and search through them using Qdrant vector database.

## Features

- Upload audio files (MP3, WAV, M4A)
- Transcribe audio using Kotoba Whisper v2.2
- Vectorize segments using multilingual-e5-base and sentence-bert-base-ja-mean-tokens-v2
- Search through transcriptions using vector search
- View and play audio segments

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL
- Qdrant
- Hugging Face Transformers
- Sentence Transformers
- Bootstrap 5

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.12
- Poetry

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/qd.git
cd qd
```

2. Install dependencies:

```bash
poetry install
```

3. Start PostgreSQL and Qdrant using Docker Compose:

```bash
docker-compose up -d
```

4. Run the application:

```bash
poetry run python -m app.main
```

The application will be available at <http://localhost:8000>.

## Project Structure

```
qd/
├── app/
│   ├── api/
│   │   ├── api.py
│   │   ├── episodes.py
│   │   ├── main.py
│   │   ├── media.py
│   │   └── upload.py
│   ├── db/
│   │   └── database.py
│   ├── models/
│   │   └── models.py
│   ├── services/
│   │   ├── embedding.py
│   │   ├── episode.py
│   │   ├── search.py
│   │   ├── storage.py
│   │   └── upload.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   ├── templates/
│   │   ├── base.html
│   │   ├── episode.html
│   │   ├── index.html
│   │   ├── search.html
│   │   └── upload.html
│   ├── transcriber/
│   │   └── transcriber.py
│   ├── vectorstore/
│   │   └── qdrant.py
│   └── main.py
├── docker-compose.yml
├── pyproject.toml
├── .env
└── README.md
```

## Usage

1. **Home Page**: The home page provides a search form and a link to upload new audio files.

2. **Upload Page**: Upload an audio file for transcription. The file will be processed in the following steps:
   - Upload audio file
   - Transcribe audio using Kotoba Whisper v2.2
   - Vectorize segments using E5 and SBERT models
   - Store in database and vector search index

3. **Search Page**: Search for specific content within the transcribed audio files. The search results will show the most relevant segments from all uploaded files.

4. **Episode Page**: View the details of a specific audio file, including its transcription segments. You can play the audio and navigate through the segments.

## Models

### Transcription Model

- [kotoba-tech/kotoba-whisper-v2.2](https://huggingface.co/kotoba-tech/kotoba-whisper-v2.2)

### Embedding Models

- [intfloat/multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base)
- [sonoisa/sentence-bert-base-ja-mean-tokens-v2](https://huggingface.co/sonoisa/sentence-bert-base-ja-mean-tokens-v2)

## License

MIT
