# utils/charts.py

import matplotlib.pyplot as plt

def plot_pie(data: dict[str, float], title: str, filename: str):
    fig, ax = plt.subplots()
    labels = list(data.keys())
    sizes  = list(data.values())
    ax.pie(sizes, labels=labels, autopct='%1.1f%%')
    ax.set_title(title)
    fig.savefig(filename, bbox_inches='tight')
    plt.close(fig)

def plot_bar(data: dict[str, float], title: str, filename: str):
    fig, ax = plt.subplots()
    x = list(data.keys())
    y = list(data.values())
    ax.bar(x, y)
    ax.set_title(title)
    plt.xticks(rotation=45)
    fig.savefig(filename, bbox_inches='tight')
    plt.close(fig)
