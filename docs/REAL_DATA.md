# Moving from synthetic to real data

The bundled dataset is synthetic. Before making any claim about real-world performance:

1. **Obtain an ethically approved dataset.** Examples (check each licence/access agreement; many need a signed
   data-use agreement and institutional ethics approval): the CLPsych 2015 Twitter shared-task data, the RSDD
   (Reddit Self-reported Depression Diagnosis) dataset, or other public mental-health text corpora.
2. **Never scrape private accounts.** Use only data you are permitted to use, de-identified, with ethics approval.
3. **Train on it:**
   ```bash
   python -m src.train --data path/to/data.csv --text-col post --label-col is_depressed [--split-col split]
   ```
   If the CSV has a `split` column containing `train` plus other values, each other value becomes a test set.
4. **Re-check everything:** metrics in `reports/EVALUATION.md`, the tuned thresholds (`models/thresholds.json`),
   the top features (look for artefacts), and subgroup performance (language variety, age, gender where available).
5. **Optional:** compare with `python -m src.transformer_baseline --data ...`.
6. **Validate the crisis detector separately** on a clinician-reviewed set; the bundled 40-example set was written
   by the authors and the rules were developed against it, so its perfect score is optimistic.
