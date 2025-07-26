
# 3. TruLens - LLM Application Evaluation and Tracking
# Install: pip install trulens-eval

from trulens_eval import Feedback, TruChain, Tru
from trulens_eval.feedback import Groundedness
from trulens_eval.feedback.provider.openai import OpenAI as TruOpenAI
from trulens_eval.feedback.provider.hugs import Huggingface
import numpy as np

def setup_trulens():
    """Initialize TruLens with feedback functions"""

    # Initialize feedback providers
    openai_provider = TruOpenAI()
    hugs_provider = Huggingface()

    # Define feedback functions
    feedback_functions = [
        # Relevance: Question/answer relevance
        Feedback(
            openai_provider.relevance_with_cot_reasons,
            name="Answer Relevance"
        ).on_input_output(),

        # Groundedness: Answer grounded in context
        Feedback(
            Groundedness(groundedness_provider=openai_provider).groundedness_measure_with_cot_reasons,
            name="Groundedness"
        ).on(context=lambda x: x['context']).on_output(),

        # Context relevance: Retrieved context relevance to question  
        Feedback(
            openai_provider.context_relevance_with_cot_reasons,
            name="Context Relevance"
        ).on(context=lambda x: x['context']).on_input(),

        # Language match feedback using HuggingFace
        Feedback(
            hugs_provider.language_match,
            name="Language Match"
        ).on_input_output(),

        # Custom sentiment feedback
        Feedback(
            lambda text: {"score": 0.8 if "positive" in text.lower() else 0.3, "reason": "Sentiment analysis"},
            name="Sentiment"
        ).on_output()
    ]

    return feedback_functions

def create_mock_llm_app():
    """Create a mock LLM application for evaluation"""

    def mock_rag_app(query: str, context: list = None):
        """Mock RAG application"""
        responses = {
            "What is machine learning?": {
                "answer": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without explicit programming.",
                "context": ["Machine learning algorithms build mathematical models based on training data.", "AI systems use ML to improve performance on tasks."]
            },
            "Benefits of renewable energy?": {
                "answer": "Renewable energy sources like solar, wind, and hydro provide clean electricity, reduce carbon emissions, and create sustainable jobs.",
                "context": ["Solar panels convert sunlight to electricity.", "Wind turbines generate power from wind.", "Renewable energy reduces greenhouse gases."]
            }
        }

        return responses.get(query, {
            "answer": "I don't have specific information about that topic.",
            "context": ["General knowledge context."]
        })

    return mock_rag_app

def evaluate_with_trulens():
    """Comprehensive evaluation using TruLens"""

    # Initialize TruLens
    tru = Tru()
    tru.reset_database()  # Start fresh

    # Setup feedback functions
    feedback_functions = setup_trulens()

    # Create mock app
    llm_app = create_mock_llm_app()

    # Wrap app with TruLens for tracking
    class TruLensWrapper:
        def __init__(self, app):
            self.app = app

        def __call__(self, query):
            result = self.app(query)
            return {
                'query': query,
                'answer': result['answer'],
                'context': result['context']
            }

    wrapped_app = TruLensWrapper(llm_app)

    # Create TruChain (TruLens app wrapper)
    tru_app = TruChain(
        wrapped_app,
        app_id="RAG_Evaluation_Demo",
        feedbacks=feedback_functions
    )

    # Test queries
    test_queries = [
        "What is machine learning?",
        "Benefits of renewable energy?",
        "How does photosynthesis work?"
    ]

    print("Running TruLens evaluation...")
    results = []

    # Run evaluations
    for query in test_queries:
        print(f"\nEvaluating: {query}")

        with tru_app as recording:
            result = tru_app.app(query)
            results.append(result)

        # Get the record
        record = recording.get()

        # Display feedback scores
        print("Feedback Scores:")
        for feedback in feedback_functions:
            try:
                feedback_result = feedback(record)
                if isinstance(feedback_result, dict):
                    score = feedback_result.get('score', 'N/A')
                    reason = feedback_result.get('reason', 'No reason provided')[:100]
                else:
                    score = feedback_result
                    reason = "Direct score"
                print(f"  {feedback.name}: {score} - {reason}")
            except Exception as e:
                print(f"  {feedback.name}: Error - {str(e)}")

    # Get leaderboard
    print("\n" + "="*50)
    print("TruLens Application Leaderboard:")
    leaderboard = tru.get_leaderboard(app_ids=[tru_app.app_id])
    if not leaderboard.empty:
        print(leaderboard[['app_id', 'Answer Relevance', 'Groundedness', 'Context Relevance']].round(3))

    return results

# Example with custom TruLens feedback function
class CustomFeedback:
    """Custom feedback function for TruLens"""

    def __init__(self):
        self.name = "Custom Technical Accuracy"

    def technical_accuracy(self, question: str, answer: str) -> dict:
        """Custom feedback function to assess technical accuracy"""

        # Simple keyword-based technical accuracy check
        technical_terms = ['algorithm', 'data', 'model', 'learning', 'neural', 'artificial', 'intelligence']

        question_lower = question.lower()
        answer_lower = answer.lower()

        # Check if question is technical
        is_technical_question = any(term in question_lower for term in technical_terms)

        if not is_technical_question:
            return {"score": 1.0, "reason": "Non-technical question - accuracy assumed"}

        # Count technical terms in answer
        technical_count = sum(1 for term in technical_terms if term in answer_lower)

        # Score based on technical term usage
        score = min(technical_count / 3.0, 1.0)  # Normalize to 3 terms = full score

        reason = f"Technical question answered with {technical_count} technical terms"

        return {"score": score, "reason": reason}

def custom_trulens_feedback():
    """Example with custom TruLens feedback"""

    custom_feedback = CustomFeedback()

    # Create custom feedback function
    technical_feedback = Feedback(
        custom_feedback.technical_accuracy,
        name="Technical Accuracy"
    ).on_input_output()

    # Test the custom feedback
    test_cases = [
        ("What is machine learning?", "Machine learning is an algorithm that learns from data to make predictions."),
        ("What's the weather?", "It's sunny today."),
        ("Explain neural networks", "Neural networks are artificial intelligence models with interconnected nodes.")
    ]

    print("Custom TruLens Feedback Results:")
    for question, answer in test_cases:
        result = custom_feedback.technical_accuracy(question, answer)
        print(f"Q: {question}")
        print(f"A: {answer}")
        print(f"Score: {result['score']:.2f} - {result['reason']}")
        print("-" * 50)

if __name__ == "__main__":
    # Requires OpenAI API key: export OPENAI_API_KEY="your-api-key"
    results = evaluate_with_trulens()
    custom_trulens_feedback()
    print("TruLens evaluation completed!")
