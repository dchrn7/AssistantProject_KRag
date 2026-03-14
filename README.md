# RAG HelpDesk — Confluence Q&A Assistant

> Built on top of [BastinFlorian/RAG-Chatbot-with-Confluence](https://github.com/BastinFlorian/RAG-Chatbot-with-Confluence) (MIT License).  
> Extended and adapted for custom dataset integration.

A Retrieval-Augmented Generation (RAG) chatbot that answers questions 
over a Confluence knowledge base, with a Streamlit UI.

**Stack:** LangChain · OpenAI · Streamlit · Confluence API

---

## My contributions vs. original

| | Original (BastinFlorian) | This fork |
|---|---|---|
| Data source | Confluence only | Confluence + custom datasets |
| Environment | Local setup | Dev container (`.devcontainer`) |
| File structure | Basic | Added `PDFViewer.py`, `SourcesOrganize.py`, `project_config.py` |
| Evaluation | Generic Q&A pairs | Tuned on domain-specific data |

---

## Setup
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env  # Fill in your API keys and Confluence credentials
```

## Run
```bash
cd src
streamlit run streamlit.py
```

## Evaluate
```bash
cd src
python evaluate.py  # Replace data/evaluation_dataset.tsv with your own Q&A pairs
```

## How it works ?


    .
    ├── data/
        ├── evaluation_dataset.tsv  # Questions and answers useful for evaluation

    ├── docs/                       # Documentation files
    ├── src/                        # The main directory for computer demo
        ├── __init__.py
        ├──  PDFViewer.py           # Allow the user to view the pdf 
        ├── load_db.py              # Load data from local folder and creates smart chunks
        ├── help_desk.py            # Instantiates the LLMs, retriever and chain
        ├── main.py                 # Run the Chatbot for a simple question
        ├── streamlit.py            # Run the Chatbot in streamlit where you can ask your own questions
        ├── SourcesOrganize.py      # Organize the sources format 
        ├── evaluate.py             # Evaluate the RAG model based on questions-answers samples

    ├── notebooks/                  # Interactive code, useful for try and learn
    ├── config.py
    ├── .env.template               # Environment variables to feed
    ├── .gitignore
    ├── LICENSE                     # MIT License
    ├── README.md                   # Where to start
    └── requirements.txt            # The dependencies


The process is the following:
- Loading data from Confluence
  - You can keep the Markdown style using the `keep_markdown_format` option added in our [MR]('https://github.com/langchain-ai/langchain/pull/8246')
  - See the `help_desk.ipynb` for a more deep dive analysis
  - Otherwise you cannot split text in a smart manner using the [MarkdownHeaderTextSplitter]('https://python.langchain.com/docs/modules/data_connection/document_transformers/text_splitters/markdown_header_metadata')
- Load data
- Markdown and RecursiveCharacterTextSplitter
- LLM used: Open AI LLM and embedding
- The QARetrievalChain
- Streamlit as a data interface
