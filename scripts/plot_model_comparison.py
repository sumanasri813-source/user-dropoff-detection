import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

results_dir = Path('results')
plots_dir = results_dir / 'plots'
plots_dir.mkdir(parents=True, exist_ok=True)

csv_path = results_dir / 'model_comparison.csv'
if not csv_path.exists():
    raise SystemExit(f'Missing {csv_path}. Run training first.')

df = pd.read_csv(csv_path)

metrics = ['roc_auc','precision','recall','f1']

x = range(len(df))
labels = df['model'].tolist()

plt.figure(figsize=(10,6))
width = 0.18
for i, m in enumerate(metrics):
    vals = df[m].values
    plt.bar([xi + i*width for xi in x], vals, width=width, label=m)

plt.xticks([xi + width*(len(metrics)-1)/2 for xi in x], labels)
plt.ylim(0,1.05)
plt.ylabel('Value')
plt.title('Model Comparison Metrics')
plt.legend()
plt.tight_layout()
plt.savefig(plots_dir / 'model_comparison.png')
print('Saved', plots_dir / 'model_comparison.png')

# Also save individual metric plots
for m in metrics:
    plt.figure(figsize=(6,4))
    plt.bar(labels, df[m].values, color='C0')
    plt.ylim(0,1.05)
    plt.title(m)
    plt.ylabel('Value')
    plt.tight_layout()
    out = plots_dir / f'{m}.png'
    plt.savefig(out)
    print('Saved', out)
