
# 5. Hugging Face evaluate library
# Install: pip install evaluate datasets

import evaluate
from datasets import Dataset
import pandas as pd

def evaluate_with_hf_metrics():
    """Evaluate text generation using BLEU, ROUGE, and METEOR"""

    # Sample data
    data = {
        'prediction': [
            "The quick brown fox jumps over the lazy dog.",
            "A cat sat on the mat.",
            "Artificial intelligence is transforming industries."
        ],
        'reference': [
            "A quick brown fox jumps over the lazy dog.",
            "The cat sat on the mat.",
            "AI is transforming various industries."
        ]
    }

    # Create dataset
    ds = Dataset.from_pandas(pd.DataFrame(data))

    # Load metrics
    bleu = evaluate.load("bleu")
    rouge = evaluate.load("rouge")
    meteor = evaluate.load("meteor")

    # Compute metrics
    bleu_score = bleu.compute(predictions=ds['prediction'], references=[[ref] for ref in ds['reference']])
    rouge_score = rouge.compute(predictions=ds['prediction'], references=ds['reference'])
    meteor_score = meteor.compute(predictions=ds['prediction'], references=ds['reference'])

    print("BLEU Score: ", bleu_score['bleu'] * 100)
    print("ROUGE-L F1 Score: ", rouge_score['rougeL'] * 100)
    print("METEOR Score: ", meteor_score['meteor'] * 100)

    return bleu_score, rouge_score, meteor_score

if __name__ == "__main__":
    evaluate_with_hf_metrics()
