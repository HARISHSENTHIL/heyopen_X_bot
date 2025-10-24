import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "signals_collection")
    DATASET_DIR = os.getenv("DATASET_DIR", "data")

    @classmethod
    def setup(cls):
        """Setup OpenAI client"""
        os.environ["OPENAI_API_KEY"] = cls.OPENAI_API_KEY
        return OpenAI(api_key=cls.OPENAI_API_KEY)


import os
import json
from pathlib import Path

class DataManager:
    def __init__(self, json_path: str, output_dir: str):
        self.json_path = json_path
        self.output_dir = Path(output_dir)

    def process_signals(self) -> str:
        """Process trading signals from JSON and save as text files"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        try:

            with open(self.json_path, "r") as file:
                trading_signals = json.load(file)

            documents = [
                {
                    "content": str(signal["content"]),
                    "metadata": {
                        "user": signal["user"],
                        "channel": signal["channel"],
                        "date": signal["date"]
                    }
                }
                for signal in trading_signals
            ]

            for i, doc in enumerate(documents):
                signal_file = self.output_dir / f"signal_{i}.txt"
                with open(signal_file, "w") as file:
                    file.write(f"Content: {doc['content']}\n")
                    file.write(f"User: {doc['metadata']['user']}\n")
                    file.write(f"Channel: {doc['metadata']['channel']}\n")
                    file.write(f"Date: {doc['metadata']['date']}\n")

            return str(self.output_dir)

        except Exception as e:
            print(f"Error processing signals: {str(e)}")
            return None

    def validate_dataset(self) -> bool:
        """Check if the dataset exists and is valid"""
        if not os.path.exists(self.json_path):
            print(f"Error: JSON file '{self.json_path}' not found")
            return False

        if not self.output_dir.exists():
            return True

        files = list(self.output_dir.glob('signal_*.txt'))
        if not files:
            return True

        return True

    def get_document_stats(self) -> dict:
        """Get statistics about the processed signals"""
        stats = {
            'total_documents': 0,
            'users': set(),
            'channels': set(),
            'total_size': 0
        }

        try:
            with open(self.json_path, "r") as file:
                signals = json.load(file)
                stats['total_documents'] = len(signals)
                stats['users'] = set(signal['user'] for signal in signals)
                stats['channels'] = set(signal['channel'] for signal in signals)
                stats['total_size'] = os.path.getsize(self.json_path)
        except Exception as e:
            print(f"Error getting stats: {str(e)}")

        return stats
        from pathlib import Path
        from typing import Optional, List
        import numpy as np
        from qdrant_client import QdrantClient
        from qdrant_client.http import models
        from qdrant_client.models import Distance, VectorParams, PointStruct
        from openai import OpenAI
        import json

        class IndexManager:
            def __init__(self, dataset_dir: str, config):
                self.dataset_dir = Path(dataset_dir)
                self.config = config
                self.client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
                self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                self.collection_name = config.COLLECTION_NAME

            def get_embedding(self, text: str) -> List[float]:
                """Get embeddings from OpenAI"""
                response = self.openai_client.embeddings.create(
                    input=text,
                    model=self.config.EMBEDDING_MODEL
                )
                return response.data[0].embedding

            def create_or_load_index(self) -> bool:
                """Create or load Qdrant collection"""
                try:
                    collections = self.client.get_collections().collections
                    exists = any(collection.name == self.collection_name for collection in collections)
                    if not exists:
                        print("Creating new Qdrant collection...")
                        # Create new collection
                        self.client.create_collection(
                            collection_name=self.collection_name,
                            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                        )
                        # Load and index documents
                        if not self.dataset_dir.exists():
                            raise FileNotFoundError(f"Dataset directory not found: {self.dataset_dir}")
                        # Process all signal files in the directory
                        for signal_file in self.dataset_dir.glob('signal_*.txt'):
                            with open(signal_file, 'r') as f:
                                content = f.read()
                                embedding = self.get_embedding(content)

                                self.client.upsert(
                                    collection_name=self.collection_name,
                                    points=[PointStruct(
                                        id=int(signal_file.stem.split('_')[1]),
                                        vector=embedding,
                                        payload={"content": content}
                                    )]
                                )
                        print("Collection created and documents indexed.")
                    else:
                        print("Using existing Qdrant collection...")

                    return True

                except Exception as e:
                    print(f"Error creating/loading index: {str(e)}")
                    return False

            def rebuild_index(self) -> bool:
                """Rebuild the Qdrant collection"""
                try:
                    # Delete existing collection if it exists
                    collections = self.client.get_collections().collections
                    if any(collection.name == self.collection_name for collection in collections):
                        self.client.delete_collection(collection_name=self.collection_name)

                    # Create new collection
                    return self.create_or_load_index()
                except Exception as e:
                    print(f"Error rebuilding index: {str(e)}")
                    return False

            def search(self, query: str, limit: int = 3) -> List[dict]:
                """Search for similar documents"""
                try:
                    query_embedding = self.get_embedding(query)

                    search_results = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=query_embedding,
                        limit=limit
                    )
                    # Format results to match your existing structure
                    results = []
                    for result in search_results:
                        results.append({
                            "text": result.payload["content"],
                            "weight": float(result.score) * 100  # Convert similarity score to percentage
                        })
                    return results
                except Exception as e:
                    print(f"Error searching index: {str(e)}")
                    return []
                    import gradio as gr
                    from typing import Tuple
                    import json
                    from src.query_engine import QueryProcessor
                    from src.visualization import Visualizer

                    class Interface:
                        def __init__(self, query_processor: QueryProcessor, data_path: str):
                            self.query_processor = query_processor
                            self.visualizer = Visualizer()
                            self.data_path = data_path

                        def handle_query(self, query: str) -> Tuple[str, str, str]:
                            """Handle user query and return formatted results"""
                            response, citations = self.query_processor.process_query(query)
                            citation_texts = "\n\n".join(
                                [f"Weight: {citation['weight']}%\nSource: {citation['text']}"
                                 for citation in citations]
                            )
                            plot_path = self.visualizer.plot_contributions(citations)

                            return response, citation_texts, plot_path

                        def display_dataset(self) -> str:
                            """ Load and return the dataset as a string """
                            try:
                                with open(self.data_path, "r") as file:
                                    data = json.load(file)
                                    return json.dumps(data[:10], indent=2)  # Display the first 5 items for brevity
                            except Exception as e:
                                return f"Error loading dataset: {str(e)}"

                        def create_interface(self) -> gr.Blocks:
                            with gr.Blocks() as ui:
                                ui.css = """
                                .centered-image {
                                    margin-left: auto;
                                    margin-right: auto;
                                    background: transparent;
                                    border-color: transparent;
                                    }
                                .spaced-textbox { margin-top: 30px;}
                                """
                                with gr.Row():
                                    gr.Image("Rag Attribution 1.png", elem_classes="centered-image", scale=0.5, show_label=False, show_download_button=False, show_fullscreen_button=False)
                                    # gr.Markdown("<h1 style='text-align:center; width: 90%;'>RAG--ATTRIBUTION</h1>")
                                with gr.Row():
                                    input_box = gr.Textbox(label="Enter your question",elem_classes="spaced-textbox",placeholder="E.g., Enter your Prompt")

                                with gr.Row():
                                    response_box = gr.Textbox(label="Response", placeholder="Model's Response", interactive=False)

                                with gr.Row():
                                    citation_box = gr.Textbox(
                                        label="Top 3 Citations with Weights",
                                        interactive=False
                                    )

                                with gr.Row():
                                    plot_box = gr.Image(label="Contribution Bar Graph", show_download_button=False, show_fullscreen_button=False)

                                with gr.Row():
                                    submit_btn = gr.Button("Submit", variant="primary")
                                    dataset_btn = gr.Button("Show Dataset", variant="secondary")

                                submit_btn.click(
                                    self.handle_query,
                                    inputs=[input_box],
                                    outputs=[response_box, citation_box, plot_box]
                                )

                                with gr.Row():
                                    dataset_display = gr.Textbox(label="Dataset", interactive=False, max_lines=20)
                                    # dataset_btn = gr.Button("Show Dataset", variant="secondary")
                                    dataset_btn.click(
                                        self.display_dataset,
                                        inputs=[],
                                        outputs=[dataset_display]
                                    )

                            return ui
                            from typing import Tuple, List, Dict
                            from openai import OpenAI

                            class QueryProcessor:
                                def __init__(self, index_manager, config):
                                    self.index_manager = index_manager
                                    self.config = config
                                    self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

                                def process_query(self, query: str) -> Tuple[str, List[Dict]]:
                                    """Process user query and return response with citations"""
                                    # Search for relevant documents
                                    citations = self.index_manager.search(query, limit=3)
                                    # Prepare context from citations
                                    context = "\n\n".join([f"Source {i+1}:\n{citation['text']}"
                                                          for i, citation in enumerate(citations)])

                                    response = self.openai_client.chat.completions.create(
                                        model=self.config.MODEL_NAME,
                                        messages=[
                                            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided sources."},
                                            {"role": "user", "content": f"Based on the following weighted sources, please answer: {query}\n\nSources:\n{context}"}
                                        ]
                                    )
                                    return response.choices[0].message.content, citations

import matplotlib.pyplot as plt
from typing import List, Dict
import re
class Visualizer:
    @staticmethod
    def plot_contributions(citations: List[Dict[str, float]]) -> str:
        """Create a bar plot of contribution weights"""
        contributor_names = []
        for citation in citations:
            text = citation["text"]
            user_match = re.search(r"User: (\d+)", text)
            channel_match = re.search(r"Channel: ([^\n]+)", text)

            user = user_match.group(1) if user_match else "Unknown"
            channel = channel_match.group(1) if channel_match else "Unknown"

            contributor_names.append(f"channel : {channel}\nUser : {user}")

        weights = [citation["weight"] for citation in citations]

        plt.figure(figsize=(8, 5))
        plt.bar(contributor_names, weights, color='Orange')
        plt.title("Top Contributors", fontsize=16,pad=15)
        plt.xlabel("Contributors", fontsize=12, labelpad=20)
        plt.ylabel("Weight (%)", fontsize=12)
        plt.ylim(0, 100)

        for i, weight in enumerate(weights):
            plt.text(i, weight + 1, f"{weight:.2f}%", ha='center', fontsize=10)

        # plt.xticks(rotation=45, ha='center')
        plt.tight_layout(pad=1.5)
        plt.savefig("contributions_plot.png", bbox_inches='tight')
        plt.close()

        return "contributions_plot.png"
