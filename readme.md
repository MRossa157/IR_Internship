# Internship Search Engine

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-green.svg)](https://www.elastic.co/elasticsearch/)
[![Poetry](https://img.shields.io/badge/Poetry-✓-blueviolet.svg)](https://python-poetry.org/)
[![CUDA](https://img.shields.io/badge/CUDA-Recommended-9cf.svg)](https://developer.nvidia.com/cuda-toolkit)

This project is an intelligent search engine for internships that combines traditional Elasticsearch-based search with BERT-based semantic search capabilities. It allows users to search through internship listings using either keyword-based search or more advanced semantic search powered by BERT.

## 🚀 Features

- 🔍 Web scraping of internship listings
- 📊 Elasticsearch-based indexing and search
- 🤖 Optional BERT-based semantic search
- ⌨️ Command-line interface for interactive searching
- 📝 Results display with detailed internship information

## 📋 Prerequisites

- Python 3.12+
- Poetry (Python package manager)
- Elasticsearch 8.x
- BERT model weights (optional, for semantic search)
- CUDA-compatible GPU (recommended for BERT-based search)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/MRossa157/IR_Internship
cd IR_Internship
```

2. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```
or
```bash
pip install poetry
```

3. Install project dependencies using Poetry:
```bash
poetry install
```

4. Set up Elasticsearch (choose one of the options):

   Option 1 - Using Docker (recommended):
   ```bash
   make app
   ```
   This will start Elasticsearch in a Docker container with all necessary configurations.

   Option 2 - Manual setup:
   - Install and start Elasticsearch on your machine
   - Make sure Elasticsearch is running on the default port (9200)

## 🤖 BERT Model Training

By default, the BERT model is not trained. To use BERT-based semantic search, you need to train the model first:

1. Train the BERT model:
```bash
python src/bert/trainer.py
```

2. The training process will:
   - Use the default pre-trained model (`sberbank-ai/sbert_large_mt_nlu_ru`)
   - Train for `5` epochs with a batch size of `4`
   - Save the best model based on validation loss and NDCG metrics

3. You can customize the training parameters in `src/constants.py`:
   - `BERT_TRAINING_BATCH_SIZE`: Batch size for training
   - `BERT_TRAINING_EPOCHS`: Number of training epochs
   - `BERT_PRETRAINED_MODEL_NAME`: Pre-trained model to use

## 💻 Usage

1. Run the main script:
```bash
poetry run src/main.py
```

2. The script will:
   - Scrape internship data (if not already cached)
   - Create an Elasticsearch index
   - Index the internship data
   - Prompt you to choose between BERT-based search or regular search

3. For BERT-based search:
   - When prompted, enter the path to your trained BERT model weights
   - The system will load the BERT model for semantic search

4. Enter your search query when prompted
   - Type "exit" to quit the program

## 📁 Project Structure

```
src/
├── main.py              # Entry point of the application
├── parser.py            # Web scraping functionality
├── elastic_search.py    # Elasticsearch integration
├── bert/               # BERT model implementation
├── utils.py            # Utility functions
├── constants.py        # Project constants
├── config.py           # Configuration settings
├── eval/              # Evaluation scripts
└── analysis/          # Analysis tools
```

## 📝 Notes

- ⏳ The first run will take longer as it needs to scrape and index the internship data
- 🔄 Subsequent runs will use cached data for faster startup
- 🤖 BERT-based search requires a trained model weights file
- 🚀 For optimal performance with BERT, a CUDA-compatible GPU is recommended
- 🛠️ Development tools like ruff and scikit-learn **are included in the dev dependencies**

## 🔗 Links

- [Elasticsearch Documentation](https://www.elastic.co/guide/index.html)
- [BERT Documentation](https://huggingface.co/docs/transformers/index)
- [Poetry Documentation](https://python-poetry.org/docs/)
