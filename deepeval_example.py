
# 1. DeepEval with Ollama Integration
# First, install: pip install deepeval

from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, BiasMetric, GEval, LLMTestCaseParams
from deepeval import assert_test, evaluate
import requests
import json

# Custom Ollama Model Class for DeepEval
class OllamaModel(DeepEvalBaseLLM):
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def load_model(self):
        return self

    def generate(self, prompt: str) -> str:
        """Generate response using Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            return response.json()["response"]
        except Exception as e:
            return f"Error: {str(e)}"

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model_name

# Setup DeepEval with local Ollama model
def setup_local_model():
    """Setup DeepEval to use local Ollama model"""
    # Alternative method using CLI command:
    # deepeval set-local-model --model-name=llama3.1:8b --base-url="http://localhost:11434/v1/" --api-key="ollama"
    return OllamaModel()

# Example evaluation using DeepEval
def evaluate_with_deepeval():
    """Comprehensive evaluation using DeepEval with multiple metrics"""

    # Initialize local model
    local_model = setup_local_model()

    # Create test cases
    test_cases = [
        LLMTestCase(
            input="What are the benefits of renewable energy?",
            actual_output="Renewable energy sources like solar and wind power help reduce carbon emissions, create jobs, and provide sustainable electricity generation.",
            expected_output="Renewable energy offers environmental benefits through reduced greenhouse gas emissions, economic advantages through job creation, and energy security through sustainable power generation.",
            context=["Renewable energy includes solar, wind, hydro, and geothermal power sources that naturally replenish."]
        ),
        LLMTestCase(
            input="Explain machine learning in simple terms",
            actual_output="Machine learning is when computers learn to make predictions or decisions by finding patterns in data, without being explicitly programmed for each task.",
            expected_output="Machine learning is a subset of AI where algorithms learn from data to make predictions or decisions automatically."
        )
    ]

    # Initialize metrics with local model
    metrics = [
        AnswerRelevancyMetric(threshold=0.7, model=local_model),
        FaithfulnessMetric(threshold=0.7, model=local_model),
        BiasMetric(threshold=0.5, model=local_model),
        GEval(
            name="Accuracy",
            criteria="Determine if the actual output is factually accurate and complete",
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            threshold=0.7,
            model=local_model
        )
    ]

    # Run evaluation
    for test_case in test_cases:
        print(f"\nEvaluating: {test_case.input[:50]}...")
        for metric in metrics:
            try:
                metric.measure(test_case)
                print(f"{metric.__class__.__name__}: {metric.score:.3f} - {metric.reason[:100]}...")
            except Exception as e:
                print(f"{metric.__class__.__name__}: Error - {str(e)}")

    # Bulk evaluation
    results = evaluate(test_cases=test_cases, metrics=metrics)
    return results

if __name__ == "__main__":
    # Make sure Ollama is running: ollama serve
    # And model is available: ollama pull llama3.1:8b
    results = evaluate_with_deepeval()
    print("DeepEval evaluation completed!")
