import os
import csv
import json
import re
import html
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def clean_html(text: str) -> str:
    """Removes HTML tags and decodes HTML entities."""
    if not text:
        return ""
    # Decode html entities
    text = html.unescape(text)
    # Remove HTML tags (simple regex, robust enough for cleanup)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def preprocess_stackoverflow_data(questions_path: str, answers_path: str, output_path: str, max_records: int = 2000):
    """Parses Stack Overflow Questions.csv and Answers.csv to extract high-quality Python Q&A pairs."""
    if not os.path.exists(questions_path) or not os.path.exists(answers_path):
        logger.warning(
            f"Kaggle Stack Overflow dataset files not found at {questions_path} or {answers_path}.\n"
            f"Please download the dataset from https://www.kaggle.com/datasets/stackoverflow/pythonquestions and place them in the data/ folder.\n"
            f"Skipping preprocess. The system will fall back to using default high-quality Q&As."
        )
        return False

    logger.info("Starting preprocessing of Stack Overflow CSV dataset...")

    # Load questions (filter by score and get python tags if not already filtered)
    # The Kaggle dataset already contains Python-specific questions
    questions = {}
    logger.info("Reading Questions CSV...")
    with open(questions_path, 'r', encoding='latin1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                q_id = int(row['Id'])
                score = int(row['Score'])
                title = row['Title']
                body = row['Body']
                
                # Filter for high-score questions to get the most representative Python queries
                if score >= 10:  # Adjust threshold as needed
                    questions[q_id] = {
                        "id": q_id,
                        "title": title,
                        "question_body": clean_html(body),
                        "score": score,
                        "answers": []
                    }
            except Exception as e:
                continue

    logger.info(f"Loaded {len(questions)} high-score questions. Reading Answers CSV...")

    # Load answers and associate them with questions
    with open(answers_path, 'r', encoding='latin1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                q_id = int(row['ParentId'])
                score = int(row['Score'])
                body = row['Body']
                
                if q_id in questions:
                    questions[q_id]["answers"].append({
                        "score": score,
                        "body": clean_html(body)
                    })
            except Exception as e:
                continue

    # Compile the final clean Q&A format
    cleaned_data = []
    logger.info("Compiling Q&A documents...")
    for q_id, q_data in questions.items():
        if not q_data["answers"]:
            continue
            
        # Select the best answer (highest score)
        best_answer = max(q_data["answers"], key=lambda x: x["score"])
        
        # Combine Question + Answer into a single document structure
        doc_text = (
            f"Question: {q_data['title']}\n"
            f"Description: {q_data['question_body']}\n\n"
            f"Answer:\n{best_answer['body']}"
        )
        
        cleaned_data.append({
            "id": q_id,
            "text": doc_text,
            "metadata": {
                "title": q_data["title"],
                "score": q_data["score"],
                "url": f"https://stackoverflow.com/questions/{q_id}"
            }
        })

    # Sort by score descending and take the top max_records
    cleaned_data.sort(key=lambda x: x["metadata"]["score"], reverse=True)
    final_dataset = cleaned_data[:max_records]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=4, ensure_ascii=False)

    logger.info(f"Successfully preprocessed and saved {len(final_dataset)} Q&A pairs to {output_path}")
    return True

if __name__ == "__main__":
    # Default local paths for Kaggle data
    data_dir = "data"
    questions_csv = os.path.join(data_dir, "Questions.csv")
    answers_csv = os.path.join(data_dir, "Answers.csv")
    output_json = os.path.join(data_dir, "cleaned_qa.json")
    
    preprocess_stackoverflow_data(questions_csv, answers_csv, output_json)
