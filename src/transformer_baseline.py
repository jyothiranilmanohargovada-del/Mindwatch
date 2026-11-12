"""OPTIONAL: fine-tune DistilBERT as a stronger baseline.

NOT executed in the environment this project was built in (no GPU/network there) - treat as a
starting point.  Requires:  pip install torch transformers datasets
Usage:  python -m src.transformer_baseline --data my.csv --text-col text --label-col label
Compare its metrics with reports/metrics.json; keep the linear model if the gain is small,
because it is explainable and far cheaper to run.
"""
import argparse


def main():
    try:
        import numpy as np
        import pandas as pd
        from datasets import Dataset
        from sklearn.metrics import f1_score
        from transformers import (AutoModelForSequenceClassification, AutoTokenizer, Trainer,
                                  TrainingArguments)
    except ImportError:
        raise SystemExit("Install optional deps first: pip install torch transformers datasets")

    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--text-col", default="text")
    ap.add_argument("--label-col", default="label"); ap.add_argument("--split-col", default="split")
    ap.add_argument("--model", default="distilbert-base-uncased"); ap.add_argument("--epochs", type=int, default=3)
    a = ap.parse_args()

    df = pd.read_csv(a.data).rename(columns={a.text_col: "text", a.label_col: "label"})
    if a.split_col in df.columns:
        train, test = df[df[a.split_col] == "train"], df[df[a.split_col] != "train"]
    else:
        test = df.sample(frac=0.2, random_state=42); train = df.drop(test.index)
    tok = AutoTokenizer.from_pretrained(a.model)
    enc = lambda b: tok(b["text"], truncation=True, padding="max_length", max_length=128)
    ds_tr = Dataset.from_pandas(train[["text", "label"]]).map(enc, batched=True)
    ds_te = Dataset.from_pandas(test[["text", "label"]]).map(enc, batched=True)
    model = AutoModelForSequenceClassification.from_pretrained(a.model, num_labels=2)

    def metrics(p):
        return {"f1": f1_score(p.label_ids, np.argmax(p.predictions, axis=1))}

    trainer = Trainer(model=model, args=TrainingArguments("models/transformer", num_train_epochs=a.epochs,
                      per_device_train_batch_size=16, eval_strategy="epoch", save_strategy="no", report_to=[]),
                      train_dataset=ds_tr, eval_dataset=ds_te, compute_metrics=metrics)
    trainer.train()
    print(trainer.evaluate())


if __name__ == "__main__":
    main()
