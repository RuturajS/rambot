# Excel Analysis Bot

A lightweight AI assistant for analyzing Excel files.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Copy `.env.example` to `.env` and set your `AI_API_KEY`.
    ```bash
    copy .env.example .env
    ```

## Usage

### CLI
```bash
# Upload a file
python cli.py upload path/to/file.xlsx

# List files
python cli.py list

# Query a file
python cli.py query <hash_id> "What is the total sales?"

# Edit a file
python cli.py edit <hash_id> "Add a column 'Tax' that is 10% of 'Price'"
```

### Web UI
1.  Run the web server:
    ```bash
    python web.py
    ```
2.  Open `http://localhost:8000` in your browser.
3.  Upload files, Chat with data, or **Edit** them using the new "Edit File" button.
