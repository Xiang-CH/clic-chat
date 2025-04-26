# CLIC Chat

Enhancing Legal Information Accessibility Through Advanced Language Models

## Project Overview
CLIC Chat is a comprehensive legal information system that leverages advanced language models to make legal information more accessible. The project combines web application development, data processing, and legal document management to provide an intuitive interface for legal research and consultation.

## Quick Start
- Download the database from [here](https://clic-files.s3.ap-southeast-1.amazonaws.com/lancedb.zip), extract the zip file and place `lancedb` in the `db` directory. (This db will only work for CUDA enabled devices)
- Set environment variables: create a `.env` file, and add the following:
    ```
    AZURE_OPENAI_ENDPOINT = <Your-endpoint>
    AZURE_OPENAI_API_KEY = <Your-api-key>
    DB_PATH = <Your-path-to>/db/lancedb
    ```
- Start Web App locally
    ``` bash
    # install dependencies
    pnpm i

    # run app
    pnpm dev
    ```

## Directory Structure

### Core Directories
- `webapp/` - Next.js web application
  - `app/` - Next.js app router pages and layouts
  - `components/` - Reusable React components
  - `api/` - API routes and endpoints
  - `lib/` - Utility functions and shared code
  - `hooks/` - Custom React hooks
  - `public/` - Static assets
  - `assets/` - Application assets

### Data Processing
- `dataProcessing/` - Scripts for processing legal documents
- `raw_legislations/` - Original legislative documents
- `legislations/` - Processed legislative documents
- `raw_judgments/` - Original court judgments
- `judgements/` - Processed court judgments
- `legislations_chunks/` - Chunked legislative documents with embedding
- `judgements_chunks/` - Chunked judgements documents with embedding

### Database and Evaluation
- `db/` - Database related files and configurations
- `eval/` - Evaluation scripts and metrics
- `lqb/` - Legal question bank and related resources

### Development Tools
- `demo/` - Demo and example files
- `qa_editor.py` - UI fo checking eval results
- `organize_raw_judgements.py` - Script for organizing downloaded judgment documents

### Configuration Files
- `requirements.txt` - Python dependencies