"""
Standardized Evaluation and Benchmark Script for PulseTalk Sentiment Analysis
Evaluates and compares:
  Model A: DistilBERT SST-2 (Binary classifier with threshold calibration)
  Model B: Twitter-RoBERTa (Native 3-class sentiment classifier)
Calculates Accuracy, Precision, Recall, F1-score, and Confusion Matrices.
"""

import argparse
from typing import List, Tuple, Dict, Any
from transformers import pipeline

from app.services.preprocessor import TextPreprocessor

# Curated benchmark dataset of unambiguous samples covering diverse domains:
# Product reviews, movie reviews, customer service, negations, emojis, and neutral facts.
BENCHMARK_DATA: List[Tuple[str, str]] = [
    # Positive samples (18)
    ("I love this product, it works brilliantly!", "positive"),
    ("Absolutely fantastic customer service, highly recommended.", "positive"),
    ("One of the best movies I have ever watched in my life.", "positive"),
    ("Delighted with the speed and reliability of this service.", "positive"),
    ("Super easy to set up and very intuitive interface.", "positive"),
    ("Great performance! It exceeded all my expectations.", "positive"),
    ("Awesome build quality and fast shipping. ❤️👍", "positive"),
    ("Not bad at all, actually quite good and impressive.", "positive"),
    ("Exceptional clarity and stunning sound quality.", "positive"),
    ("I am thrilled with this purchase and would buy again.", "positive"),
    ("Extremely pleased with the outstanding outcome.", "positive"),
    ("This phone is a masterpiece of modern engineering.", "positive"),
    ("Wonderful experience from start to finish.", "positive"),
    ("Highly efficient, durable, and affordable.", "positive"),
    ("Totally in love with this! 🎉🔥", "positive"),
    ("A joy to use, saves me hours every single day.", "positive"),
    ("Superb battery life and breathtaking display.", "positive"),
    ("Remarkable achievement, truly well done.", "positive"),

    # Negative samples (18)
    ("Terrible quality, broke on the first day of use.", "negative"),
    ("I hate this app, it crashes every few minutes.", "negative"),
    ("Awful customer service, nobody responded to my ticket.", "negative"),
    ("Do not waste your money on this piece of junk.", "negative"),
    ("Completely unacceptable delay and rude staff.", "negative"),
    ("Extremely disappointing performance and sluggish speed.", "negative"),
    ("I do not like this device at all, it is very bad.", "negative"),
    ("Defective item received, total rip off. 😡👎", "negative"),
    ("Worst purchase I have made all year.", "negative"),
    ("Utter waste of time, failed to deliver what was promised.", "negative"),
    ("Horrible user experience, cluttered and confusing.", "negative"),
    ("The battery drains in two hours, absolutely useless.", "negative"),
    ("Customer support was unhelpful and dismissive.", "negative"),
    ("Very frustrating bugs that make it impossible to use.", "negative"),
    ("Disastrous update, ruined all my saved files.", "negative"),
    ("Nothing works as advertised, completely broken.", "negative"),
    ("Regret buying this, full of flaws.", "negative"),
    ("Inferior materials and terrible build.", "negative"),

    # Neutral / Factual / Objective samples (14)
    ("The package was delivered on Tuesday afternoon.", "neutral"),
    ("The table is made of pine wood with four legs.", "neutral"),
    ("The meeting is scheduled for 3:00 PM in room 204.", "neutral"),
    ("Water boils at 100 degrees Celsius at sea level.", "neutral"),
    ("The store opens at 9 AM and closes at 8 PM.", "neutral"),
    ("The document contains five pages with black ink.", "neutral"),
    ("The car has four wheels and runs on diesel fuel.", "neutral"),
    ("There are sixty minutes in one hour.", "neutral"),
    ("The train departs from platform 3 every hour.", "neutral"),
    ("The temperature outside is currently 22 degrees.", "neutral"),
    ("The laptop weighs approximately 1.5 kilograms.", "neutral"),
    ("The book has 320 pages and was published in 2021.", "neutral"),
    ("He took the keys from the counter and left.", "neutral"),
    ("The item arrived in a standard cardboard carton.", "neutral")
]

CLASSES = ["positive", "negative", "neutral"]


def evaluate_pipeline(name: str, pipe, is_binary: bool, neutral_margin: float = 0.15) -> Dict[str, Any]:
    """Evaluate a pipeline on the benchmark dataset"""
    conf_matrix = {c_true: {c_pred: 0 for c_pred in CLASSES} for c_true in CLASSES}
    y_true = []
    y_pred = []

    for raw_text, expected in BENCHMARK_DATA:
        # Preprocess text
        prepared = TextPreprocessor.prepare_for_transformer(raw_text)
        results = pipe(prepared, truncation=True, max_length=512)

        items = results[0] if (isinstance(results, list) and len(results) > 0 and isinstance(results[0], list)) else results
        if isinstance(items, list) and len(items) > 0 and isinstance(items[0], dict):
            scores_by_label = {}
            for item in items:
                lbl = item["label"].lower().strip()
                if lbl in ["positive", "pos", "1"]:
                    lbl = "positive"
                elif lbl in ["negative", "neg", "0"]:
                    lbl = "negative"
                else:
                    lbl = "neutral"
                scores_by_label[lbl] = float(item["score"])
        else:
            scores_by_label = {"neutral": 1.0}

        if is_binary:
            pos = scores_by_label.get("positive", 0.0)
            neg = scores_by_label.get("negative", 0.0)
            margin = abs(pos - neg)
            if margin < neutral_margin:
                predicted = "neutral"
            elif pos >= neg:
                predicted = "positive"
            else:
                predicted = "negative"
        else:
            # Native 3-class: pick max probability
            predicted = max(scores_by_label.keys(), key=lambda k: scores_by_label[k])

        y_true.append(expected)
        y_pred.append(predicted)
        conf_matrix[expected][predicted] += 1

    total = len(y_true)
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / total

    class_metrics = {}
    for c in CLASSES:
        tp = conf_matrix[c][c]
        fp = sum(conf_matrix[other][c] for other in CLASSES if other != c)
        fn = sum(conf_matrix[c][other] for other in CLASSES if other != c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        support = sum(conf_matrix[c].values())
        class_metrics[c] = {"precision": precision, "recall": recall, "f1": f1, "support": support}

    macro_precision = sum(m["precision"] for m in class_metrics.values()) / len(CLASSES)
    macro_recall = sum(m["recall"] for m in class_metrics.values()) / len(CLASSES)
    macro_f1 = sum(m["f1"] for m in class_metrics.values()) / len(CLASSES)

    return {
        "name": name,
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "class_metrics": class_metrics,
        "confusion_matrix": conf_matrix
    }


def print_report(res: Dict[str, Any]):
    print("=" * 65)
    print(f"BENCHMARK RESULTS: {res['name']}")
    print("=" * 65)
    print(f"Overall Accuracy: {res['accuracy'] * 100:.2f}% ({res['correct']}/{res['total']})")
    print(f"Macro Precision : {res['macro_precision']:.4f}")
    print(f"Macro Recall    : {res['macro_recall']:.4f}")
    print(f"Macro F1-Score  : {res['macro_f1']:.4f}\n")

    print(f"{'Class':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
    print("-" * 58)
    for c in CLASSES:
        m = res["class_metrics"][c]
        print(f"{c:<12} {m['precision']:<12.4f} {m['recall']:<12.4f} {m['f1']:<12.4f} {m['support']:<10}")
    print("-" * 58)

    print("\nConfusion Matrix:")
    print(f"{'True \\ Pred':<15} {'positive':<12} {'negative':<12} {'neutral':<12}")
    print("-" * 51)
    for c in CLASSES:
        cm = res["confusion_matrix"][c]
        print(f"{c:<15} {cm['positive']:<12} {cm['negative']:<12} {cm['neutral']:<12}")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate PulseTalk Sentiment Models")
    parser.add_argument("--model", choices=["distilbert", "roberta", "both"], default="both",
                        help="Model to benchmark (distilbert, roberta, or both)")
    args = parser.parse_args()

    results = []

    if args.model in ["distilbert", "both"]:
        print("\nLoading Model A (DistilBERT SST-2 Binary)...")
        pipe_distilbert = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", top_k=None)
        res_a = evaluate_pipeline("DistilBERT SST-2 (Binary + Threshold)", pipe_distilbert, is_binary=True)
        results.append(res_a)
        print_report(res_a)

    if args.model in ["roberta", "both"]:
        print("\nLoading Model B (Twitter-RoBERTa Native 3-Class)...")
        pipe_roberta = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest", top_k=None)
        res_b = evaluate_pipeline("Twitter-RoBERTa (Native 3-Class)", pipe_roberta, is_binary=False)
        results.append(res_b)
        print_report(res_b)

    if len(results) == 2:
        print("=" * 65)
        print("HEAD-TO-HEAD MODEL COMPARISON")
        print("=" * 65)
        print(f"{'Metric':<25} {'DistilBERT SST-2':<20} {'Twitter-RoBERTa':<20}")
        print("-" * 65)
        print(f"{'Overall Accuracy':<25} {results[0]['accuracy']*100:.2f}%{'':<13} {results[1]['accuracy']*100:.2f}%")
        print(f"{'Macro F1-Score':<25} {results[0]['macro_f1']:.4f}{'':<14} {results[1]['macro_f1']:.4f}")
        print(f"{'Positive F1':<25} {results[0]['class_metrics']['positive']['f1']:.4f}{'':<14} {results[1]['class_metrics']['positive']['f1']:.4f}")
        print(f"{'Negative F1':<25} {results[0]['class_metrics']['negative']['f1']:.4f}{'':<14} {results[1]['class_metrics']['negative']['f1']:.4f}")
        print(f"{'Neutral Recall':<25} {results[0]['class_metrics']['neutral']['recall']*100:.1f}%{'':<14} {results[1]['class_metrics']['neutral']['recall']*100:.1f}%")
        print(f"{'Neutral F1':<25} {results[0]['class_metrics']['neutral']['f1']:.4f}{'':<14} {results[1]['class_metrics']['neutral']['f1']:.4f}")
        print("=" * 65)


if __name__ == "__main__":
    main()
