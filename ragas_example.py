
# 2. RAGAS - RAG Assessment Framework
# Install: pip install ragas

from ragas import evaluate as ragas_evaluate
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_recall,
    context_precision,
    answer_correctness,
    answer_similarity
)
from datasets import Dataset
import pandas as pd

def evaluate_with_ragas():
    """Evaluate RAG pipeline using RAGAS metrics"""

    # Sample RAG evaluation data
    data_samples = {
        'question': [
            "What is the capital of France?",
            "How does photosynthesis work?",
            "What are the benefits of exercise?"
        ],
        'answer': [
            "The capital of France is Paris, which is also the largest city in the country.",
            "Photosynthesis is the process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen.",
            "Exercise provides numerous benefits including improved cardiovascular health, stronger muscles, better mental health, and increased longevity."
        ],
        'contexts': [
            ["Paris is the capital and most populous city of France. It is located in northern France."],
            ["Photosynthesis is a process used by plants to convert light energy into chemical energy. It involves chlorophyll capturing sunlight."],
            ["Regular physical activity has many health benefits including reduced risk of heart disease, improved mood, and stronger bones."]
        ],
        'ground_truth': [
            "Paris is the capital of France.",
            "Photosynthesis converts sunlight into energy using chlorophyll in plants.",
            "Exercise improves physical and mental health."
        ]
    }

    # Convert to dataset
    dataset = Dataset.from_dict(data_samples)

    # Define metrics to evaluate
    metrics = [
        faithfulness,           # Measures factual consistency with context
        answer_relevancy,       # Measures relevance of answer to question
        context_recall,         # Measures if context contains ground truth info
        context_precision,      # Measures precision of retrieved context
        answer_correctness,     # Overall correctness considering ground truth
        answer_similarity       # Semantic similarity with ground truth
    ]

    # Run RAGAS evaluation
    print("Running RAGAS evaluation...")
    result = ragas_evaluate(
        dataset=dataset,
        metrics=metrics,
    )

    # Display results
    df = result.to_pandas()
    print("\nRAGAS Evaluation Results:")
    print(df[['question', 'faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']].round(3))

    # Summary statistics
    print("\nMetric Averages:")
    for metric in metrics:
        avg_score = df[metric.name].mean()
        print(f"{metric.name}: {avg_score:.3f}")

    return result

# Example with custom RAGAS metrics
def custom_ragas_evaluation():
    """Example with custom RAGAS metric"""
    from ragas.metrics import SingleTurnSample
    from ragas.metrics._simple_criteria import SimpleCriteriaScore

    # Custom criteria for evaluation
    custom_criteria = SimpleCriteriaScore(
        name="conciseness",
        definition="Conciseness measures how brief and to-the-point the answer is while maintaining accuracy.",
        scoring_criteria="Score 1 if answer is very concise, 0.5 if moderately concise, 0 if verbose"
    )

    # Sample data
    sample = SingleTurnSample(
        user_input="What is AI?",
        response="Artificial Intelligence (AI) refers to computer systems that can perform tasks typically requiring human intelligence.",
        reference="AI is computer systems performing human-like tasks."
    )

    # Evaluate custom metric
    score = custom_criteria.single_turn_score(sample)
    print(f"Custom Conciseness Score: {score}")

    return score

if __name__ == "__main__":
    # Requires OpenAI API key or other LLM provider
    # export OPENAI_API_KEY="your-api-key"
    results = evaluate_with_ragas()
    custom_score = custom_ragas_evaluation()
