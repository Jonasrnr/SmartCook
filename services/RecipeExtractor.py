import json
import langextract as lx
from langextract.data import ExampleData, Extraction


class RecipeExtractor:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

        # Beispiele aus JSON laden
        with open("services/prompt/examples.json", "r", encoding="utf-8") as f:
            raw_examples = json.load(f)

        self.examples = []
        for ex in raw_examples:
            extractions = [
                Extraction(
                    extraction_class=e["extraction_class"],
                    extraction_text=json.dumps(e["extraction_text"]),
                )
                for e in ex["extractions"]
            ]
            self.examples.append(ExampleData(text=ex["text"], extractions=extractions))

        # Prompt laden
        with open("services/prompt/prompt.txt", "r", encoding="utf-8") as f:
            self.prompt = f.read()

    def extract_recipe(self, text: str):
        # Perform extraction
        result = lx.extract(
            text_or_documents=text,
            prompt_description=self.prompt,
            model_id=self.model,
            examples=self.examples,
            api_key=self.api_key,
        )

        return result
