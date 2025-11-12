import asyncio
import logging
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from constants import CATEGORY_MAP, MIN_CATEGORY_PERCENTAGE, NO_DATA_GRAPH_VALUE

logger = logging.getLogger(__name__)

mpl.use("Agg")

_executor = ThreadPoolExecutor(max_workers=3)


def transform_to_1d_list(x):
    if np.isscalar(x):
        return [float(x)]
    arr = np.asarray(x).ravel()
    return arr.tolist()


def _remove_emoji(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)
    return text.strip()


def create_graph_sync(
    categories: list[str], values: list[float], graph_name: str
) -> str:
    graph_path = f"graphs/{graph_name}"
    os.makedirs("graphs", exist_ok=True)

    logger.info(f"Creating graph: {graph_name} with {len(categories)} categories")

    cats = [_remove_emoji(cat) for cat in transform_to_1d_list(categories)]
    vals = transform_to_1d_list(values)

    try:
        if len(cats) != len(vals):
            if len(cats) >= len(vals):
                cats = cats[: len(vals)]
            else:
                cats = cats + [""] * (len(vals) - len(cats))

        fig = plt.figure(figsize=(10, 8))

        colors = plt.cm.Set3(range(len(vals)))

        wedges, texts, autotexts = plt.pie(
            vals,
            labels=None,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            wedgeprops={"width": 0.5},
            pctdistance=1.15,
        )

        for autotext in autotexts:
            autotext.set_color("black")
            autotext.set_weight("bold")
            autotext.set_fontsize("10")

        legend_labels = [f"{cat}: {val:.2f}€" for cat, val in zip(cats, vals)]
        plt.legend(
            wedges,
            legend_labels,
            title="Categories",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.05),
            ncol=3,
            fontsize=10,
            frameon=False,
        )

        plt.savefig(graph_path, dpi=200, bbox_inches="tight")
        plt.close(fig)

        return graph_path

    except Exception as e:
        logger.error(f"Error creating graph: {e}")
        raise


async def create_graph_async(categories: list[str], values: list[float]) -> str:
    graph_name = f"graph_{uuid.uuid4().hex[:8]}.png"

    logger.info(f"Starting async graph creation: {graph_name}")

    try:
        loop = asyncio.get_running_loop()
        graph_path = await loop.run_in_executor(
            _executor, create_graph_sync, categories, values, graph_name
        )
        logger.info(f"Async graph creation completed: {graph_name}")

        return graph_path

    except Exception as e:
        logger.error(f"Error starting async graph creation: {e}", exc_info=True)
        raise


async def call_graph_creator(all_values):
    categories = []
    values = []
    misc_total: float = 0

    logger.info("Calling graph creator.")
    try:
        total_sum = sum(value for _, value in all_values)

        if total_sum == 0:
            categories = ["No Data"]
            values = [NO_DATA_GRAPH_VALUE]
            result = await create_graph_async(categories, values)
            return result

        for category, value in all_values:
            if ((value / total_sum) * 100) > MIN_CATEGORY_PERCENTAGE:
                category = CATEGORY_MAP.get(category, category)
                categories.append(category)
                values.append(value)
                continue
            elif value != 0:
                misc_total += value

        if misc_total != 0:
            if "Miscellaneous" not in categories:
                categories.append("Miscellaneous")
                values.append(misc_total)
            else:
                values[categories.index("Miscellaneous")] += misc_total

        result = await create_graph_async(categories, values)
        logger.info("Graph creator completed.")

        return result

    except Exception as e:
        logger.error(f"Error in call_graph_creator: {e}")
        raise
