import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer

from src.bert.dataset import (
    InternshipDataset,
    create_training_data_from_evaluation,
)
from src.bert.model import BERTSearchEngine, BERTSearchEngineFitter
from src.constants import (
    BERT_PRETRAINED_MODEL_NAME,
    BERT_TRAINING_BATCH_SIZE,
    BERT_TRAINING_EPOCHS,
    EVALUATION_QUERIES,
    INDEX_NAME,
)
from src.eval.evaluate import SearchEvaluator


def train_bert_ranker(
    model: torch.nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 3,
    lr: float = 2e-5,
) -> torch.nn.Module:

    if torch.cuda.is_available():
        device = torch.device('cuda')
        torch.cuda.empty_cache()
    else:
        device = torch.device('cpu')

    model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)
    criterion = torch.nn.BCELoss()
    scaler = torch.GradScaler(device=device)

    best_val_loss = float('inf')
    best_ndcg = 0.0

    for epoch in range(epochs):
        # Обучение
        model.train()
        total_train_loss = 0

        for batch in tqdm(train_loader, desc=f'Training Epoch {epoch + 1}'):
            query_input_ids = batch['query_input_ids'].to(device)
            query_attention_mask = batch['query_attention_mask'].to(device)
            text_input_ids = batch['text_input_ids'].to(device)
            text_attention_mask = batch['text_attention_mask'].to(device)
            labels = batch['label'].to(device)

            optimizer.zero_grad()

            outputs = model(
                query_input_ids=query_input_ids,
                query_attention_mask=query_attention_mask,
                text_input_ids=text_input_ids,
                text_attention_mask=text_attention_mask,
            )

            loss = criterion(outputs.squeeze(), labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / len(train_loader)

        # Валидация
        model.eval()
        total_val_loss = 0

        with torch.no_grad():
            for batch in tqdm(
                val_loader,
                desc=f'Validation Epoch {epoch + 1}',
            ):
                query_input_ids = batch['query_input_ids'].to(device)
                query_attention_mask = batch['query_attention_mask'].to(device)
                text_input_ids = batch['text_input_ids'].to(device)
                text_attention_mask = batch['text_attention_mask'].to(device)
                labels = batch['label'].to(device)

                outputs = model(
                    query_input_ids=query_input_ids,
                    query_attention_mask=query_attention_mask,
                    text_input_ids=text_input_ids,
                    text_attention_mask=text_attention_mask,
                )

                loss = criterion(outputs.squeeze(), labels)

                total_val_loss += loss.item()

        avg_val_loss = total_val_loss / len(val_loader)

        # Оценка NDCG и Precision
        bert_wrapper = BERTSearchEngine(model=model)
        bert_results = {}
        for query in tqdm(
            EVALUATION_QUERIES,
            desc=f'Evaluation Epoch {epoch + 1}',
        ):
            bert_results[query] = bert_wrapper.find_internships(
                query,
                INDEX_NAME,
            )

        evaluations = SearchEvaluator.evaluate_multiple_queries(bert_results)
        current_precision = evaluations['avg_precision']
        current_ndcg = evaluations['avg_ndcg']

        print(
            f'Epoch {epoch + 1}/{epochs}: '
            f'Train Loss: {avg_train_loss:.4f} | '
            f'Val Loss: {avg_val_loss:.4f} | '
            f'Precision: {current_precision:.4f} | NDCG: {current_ndcg:.4f}',
        )

        scheduler.step()

        if current_ndcg > best_ndcg:
            best_ndcg = current_ndcg
            torch.save(model.state_dict(), 'best_bert_ranker_ndcg.pth')
            print(f'Model saved with best NDCG: {best_ndcg:.4f}')

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), 'best_bert_ranker.pth')
            print(f'Model saved with Val Loss: {best_val_loss:.4f}')

    return model


def train_model_pipeline() -> torch.nn.Module:
    """Полный пайплайн обучения: подготовка данных, обучение, сохранение"""
    queries, texts, labels = create_training_data_from_evaluation()

    (
        train_queries,
        val_queries,
        train_texts,
        val_texts,
        train_labels,
        val_labels,
    ) = train_test_split(
        queries,
        texts,
        labels,
        test_size=0.2,
        random_state=42,
    )

    model_name = BERT_PRETRAINED_MODEL_NAME
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = BERTSearchEngineFitter(model_name=model_name)

    train_dataset = InternshipDataset(
        train_queries,
        train_texts,
        train_labels,
        tokenizer,
    )
    val_dataset = InternshipDataset(
        val_queries,
        val_texts,
        val_labels,
        tokenizer,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BERT_TRAINING_BATCH_SIZE,
        shuffle=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BERT_TRAINING_BATCH_SIZE,
        shuffle=False,
    )

    trained_model = train_bert_ranker(
        model,
        train_loader,
        val_loader,
        epochs=BERT_TRAINING_EPOCHS,
        lr=2e-5,
    )

    print('Обучение завершено!')
    return trained_model


if __name__ == '__main__':
    train_model_pipeline()
