
# 4. BERTScore - Semantic Similarity Evaluation
# Install: pip install bert-score transformers torch

from bert_score import score as bert_score
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def evaluate_with_bertscore():
    """Evaluate LLM outputs using BERTScore"""

    # Sample predictions and references for evaluation
    predictions = [
        "The capital of France is Paris, a beautiful city known for its culture.",
        "Machine learning algorithms learn patterns from data to make predictions.",
        "Regular exercise improves both physical and mental health significantly."
    ]

    references = [
        "Paris is the capital city of France.",
        "Machine learning uses data patterns to predict outcomes.",
        "Exercise benefits both body and mind health."
    ]

    print("Evaluating with BERTScore...")

    # Calculate BERTScore
    P, R, F1 = bert_score(
        predictions, 
        references, 
        lang="en",
        model_type="bert-base-uncased",
        verbose=True
    )

    print("\nBERTScore Results:")
    print("-" * 50)
    for i, (pred, ref) in enumerate(zip(predictions, references)):
        print(f"\nExample {i+1}:")
        print(f"Prediction: {pred}")
        print(f"Reference:  {ref}")
        print(f"Precision:  {P[i]:.4f}")
        print(f"Recall:     {R[i]:.4f}")
        print(f"F1-Score:   {F1[i]:.4f}")

    # Average scores
    print(f"\nAverage Scores:")
    print(f"Precision:  {P.mean():.4f}")
    print(f"Recall:     {R.mean():.4f}")
    print(f"F1-Score:   {F1.mean():.4f}")

    return P.numpy(), R.numpy(), F1.numpy()

def semantic_similarity_evaluation():
    """Custom semantic similarity evaluation using sentence embeddings"""

    from sentence_transformers import SentenceTransformer

    # Load pre-trained sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Test cases
    test_cases = [
        {
            "query": "What are the benefits of artificial intelligence?",
            "generated": "AI offers automation, improved decision-making, and enhanced efficiency across industries.",
            "reference": "Artificial intelligence provides automation, better decisions, and increased productivity."
        },
        {
            "query": "How does renewable energy work?", 
            "generated": "Renewable energy harnesses natural resources like sun and wind to generate clean electricity.",
            "reference": "Renewable sources use solar and wind power to create sustainable energy."
        }
    ]

    print("\nSemantic Similarity Evaluation:")
    print("=" * 60)

    similarity_scores = []

    for i, case in enumerate(test_cases):
        # Generate embeddings
        generated_embedding = model.encode([case["generated"]])
        reference_embedding = model.encode([case["reference"]])

        # Calculate cosine similarity
        similarity = cosine_similarity(generated_embedding, reference_embedding)[0][0]
        similarity_scores.append(similarity)

        print(f"\nTest Case {i+1}:")
        print(f"Query:     {case['query']}")
        print(f"Generated: {case['generated']}")
        print(f"Reference: {case['reference']}")
        print(f"Similarity Score: {similarity:.4f}")

        # Interpretation
        if similarity > 0.8:
            interpretation = "Excellent semantic match"
        elif similarity > 0.6:
            interpretation = "Good semantic similarity"
        elif similarity > 0.4:
            interpretation = "Fair semantic similarity"
        else:
            interpretation = "Poor semantic match"

        print(f"Interpretation: {interpretation}")

    avg_similarity = np.mean(similarity_scores)
    print(f"\nAverage Semantic Similarity: {avg_similarity:.4f}")

    return similarity_scores

def advanced_bertscore_analysis():
    """Advanced BERTScore analysis with different models"""

    models_to_test = [
        "bert-base-uncased",
        "roberta-base", 
        "distilbert-base-uncased"
    ]

    predictions = [
        "Climate change is causing rising sea levels and extreme weather events.",
        "Artificial intelligence will transform healthcare through better diagnostics."
    ]

    references = [
        "Global warming leads to higher ocean levels and severe weather patterns.",
        "AI technology will revolutionize medical diagnosis and treatment."
    ]

    print("\nAdvanced BERTScore Analysis:")
    print("=" * 50)

    results = {}

    for model_name in models_to_test:
        print(f"\nEvaluating with {model_name}...")

        try:
            P, R, F1 = bert_score(
                predictions,
                references,
                model_type=model_name,
                lang="en",
                verbose=False
            )

            results[model_name] = {
                'precision': P.mean().item(),
                'recall': R.mean().item(),
                'f1': F1.mean().item()
            }

            print(f"Precision: {P.mean():.4f}")
            print(f"Recall:    {R.mean():.4f}")
            print(f"F1-Score:  {F1.mean():.4f}")

        except Exception as e:
            print(f"Error with {model_name}: {str(e)}")
            results[model_name] = {'error': str(e)}

    # Compare models
    print("\nModel Comparison (F1-Scores):")
    print("-" * 30)
    for model, scores in results.items():
        if 'f1' in scores:
            print(f"{model}: {scores['f1']:.4f}")

    return results

if __name__ == "__main__":
    # Main BERTScore evaluation
    bert_scores = evaluate_with_bertscore()

    # Semantic similarity evaluation
    sim_scores = semantic_similarity_evaluation()

    # Advanced analysis
    advanced_results = advanced_bertscore_analysis()

    print("\nBERTScore evaluation completed!")
