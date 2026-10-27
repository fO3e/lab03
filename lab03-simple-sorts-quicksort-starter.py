#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 3. Простые сортировки и QuickSort с рандомизацией.

Реализация, самопроверка, замеры и построение графика по требованиям КИМ-03.

Запуск: python lab03-simple-sorts-quicksort-starter.py --variant N
"""
from __future__ import annotations

import argparse
import collections
import math
from pathlib import Path
import random
import statistics
import sys
import time
import traceback

# ---------------------------------------------------------------------------
# 1. Простые сортировки со счётчиками (сортируют КОПИЮ входа, вход не меняют)
#    Каждая функция возвращает кортеж: (отсортированный список,
#    число сравнений ключей, число обменов/перемещений элементов).
# ---------------------------------------------------------------------------


def _identity(value):
    """Ключ сортировки по умолчанию."""
    return value


def bubble_sort(a: list, key=_identity) -> tuple[list, int, int]:
    """Стабильная сортировка пузырьком: O(n) в лучшем, O(n^2) в худшем случае.

    Подсказка: досрочный выход, если за проход не было ни одного обмена, —
    именно он даёт лучший случай на упорядоченном входе.
    """
    result = list(a)
    comparisons = 0
    swaps = 0

    for end in range(len(result) - 1, 0, -1):
        changed = False
        for index in range(end):
            comparisons += 1
            if key(result[index]) > key(result[index + 1]):
                result[index], result[index + 1] = result[index + 1], result[index]
                swaps += 1
                changed = True
        if not changed:
            break

    return result, comparisons, swaps


def insertion_sort(a: list, key=_identity) -> tuple[list, int, int]:
    """Стабильная сортировка вставками: O(n) в лучшем, O(n^2) в худшем случае."""
    result = list(a)
    comparisons = 0
    moves = 0

    for index in range(1, len(result)):
        value = result[index]
        value_key = key(value)
        position = index - 1

        while position >= 0:
            comparisons += 1
            if key(result[position]) <= value_key:
                break
            result[position + 1] = result[position]
            moves += 1
            position -= 1

        if position + 1 != index:
            result[position + 1] = value
            moves += 1

    return result, comparisons, moves


def selection_sort(a: list, key=_identity) -> tuple[list, int, int]:
    """Нестабильная сортировка выбором с Theta(n^2) сравнений на любом входе."""
    result = list(a)
    comparisons = 0
    swaps = 0

    for start in range(len(result) - 1):
        minimum = start
        for index in range(start + 1, len(result)):
            comparisons += 1
            if key(result[index]) < key(result[minimum]):
                minimum = index
        if minimum != start:
            result[start], result[minimum] = result[minimum], result[start]
            swaps += 1

    return result, comparisons, swaps


# ---------------------------------------------------------------------------
# 2. QuickSort с рандомизированным опорным элементом
# ---------------------------------------------------------------------------


def quick_sort(a: list, rng: random.Random | None = None, key=_identity) -> list:
    """QuickSort с выбором опорного через rng.randrange. Возвращает новый список.

    Ожидаемая сложность: в среднем O(n log n), в худшем случае O(n^2)
    в отчёте, объяснить роль рандомизации). rng передаётся снаружи, чтобы
    запуск был воспроизводим по seed варианта.
    """
    if rng is None:
        rng = random.Random()
    result = list(a)
    if len(result) < 2:
        return result

    # Итеративная трёхчастная схема: элементы меньше, равны и больше pivot.
    # Третья часть особенно важна для входов с большим числом повторов.
    stack = [(0, len(result))]
    while stack:
        lo, hi = stack.pop()
        if hi - lo < 2:
            continue

        pivot_key = key(result[rng.randrange(lo, hi)])
        less = lo
        current = lo
        greater = hi
        while current < greater:
            current_key = key(result[current])
            if current_key < pivot_key:
                result[less], result[current] = result[current], result[less]
                less += 1
                current += 1
            elif current_key > pivot_key:
                greater -= 1
                result[current], result[greater] = result[greater], result[current]
            else:
                current += 1

        left = (lo, less)
        right = (greater, hi)
        # Большую часть кладём первой: меньшая обрабатывается следующей,
        # поэтому явный стек занимает O(log n) при сбалансированных разбиениях.
        if left[1] - left[0] < right[1] - right[0]:
            stack.append(right)
            stack.append(left)
        else:
            stack.append(left)
            stack.append(right)

    return result


# ---------------------------------------------------------------------------
# 3. Демонстрация стабильности на парах (ключ, метка)
# ---------------------------------------------------------------------------


def stability_demo() -> None:
    """Показать, какие из четырёх сортировок стабильны.

    План: взять массив пар (ключ, метка) с повторяющимися ключами, например
    [(2, "a"), (1, "b"), (2, "c"), (1, "d")], отсортировать каждой сортировкой
    по ключу (сравнение только по p[0]!) и напечатать порядок меток при равных
    ключах. Вывод о стабильности каждой сортировки включить в отчёт.
    """
    pairs = [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
    key = lambda pair: pair[0]
    algorithms = (
        ("bubble_sort", lambda values: bubble_sort(values, key)[0]),
        ("insertion_sort", lambda values: insertion_sort(values, key)[0]),
        ("selection_sort", lambda values: selection_sort(values, key)[0]),
        ("quick_sort", lambda values: quick_sort(values, random.Random(0), key)),
    )

    print("\nСтабильность на парах (ключ, метка):")
    print(f"  вход: {pairs}")
    for name, sort in algorithms:
        result = sort(pairs)
        stable = preserves_equal_order(pairs, result, key)
        print(f"  {name:16s} {result}  стабилен на примере: {'да' if stable else 'нет'}")


# ---------------------------------------------------------------------------
# 4. Классы входов (данные по варианту, детерминированно по seed)
# ---------------------------------------------------------------------------


def make_inputs(n: int, seed: int) -> dict[str, list[int]]:
    """Три класса входов размера n: упорядоченный, случайный, обратный."""
    rng = random.Random(seed + n)  # свой поток для каждого размера
    data = [rng.randint(-1_000_000, 1_000_000) for _ in range(n)]
    return {
        "упорядоченный": sorted(data),
        "случайный": data,
        "обратный": sorted(data, reverse=True),
    }


# ---------------------------------------------------------------------------
# 5. Верификация (шаги 1–3 методики docs/ai-verification.md)
# ---------------------------------------------------------------------------

ALGORITHMS = {
    "bubble_sort": lambda a: bubble_sort(a)[0],
    "insertion_sort": lambda a: insertion_sort(a)[0],
    "selection_sort": lambda a: selection_sort(a)[0],
    "quick_sort": lambda a: quick_sort(a, random.Random(0)),
}


def is_sorted(a: list) -> bool:
    """Инвариант 1: неубывающий порядок элементов."""
    return all(a[i] <= a[i + 1] for i in range(len(a) - 1))


def preserves_equal_order(before: list, after: list, key=_identity) -> bool:
    """Сохранён ли взаимный порядок элементов с одинаковым ключом."""
    before_groups: dict[object, list] = collections.defaultdict(list)
    after_groups: dict[object, list] = collections.defaultdict(list)
    for value in before:
        before_groups[key(value)].append(value)
    for value in after:
        after_groups[key(value)].append(value)
    return dict(before_groups) == dict(after_groups)


class SelfCheckError(Exception):
    """Нарушен контракт или инвариант реализации."""


def expect(condition: bool, message: str) -> None:
    """Явная проверка вместо assert: assert-ы исчезают при запуске python -O."""
    if not condition:
        raise SelfCheckError(message)


def check_algorithm(fn) -> None:
    """Граничные случаи, инварианты сортировки и сверка с эталоном sorted()."""
    boundary = [
        [],                    # пустой массив
        [7],                   # один элемент
        [5, 5, 5, 5],          # все элементы равны
        [1, 2, 3, 4, 5],       # уже отсортирован
        [5, 4, 3, 2, 1],       # обратный порядок
    ]
    for a in boundary:
        argument = list(a)
        res = fn(argument)
        expect(argument == a, f"изменён входной массив {a}: стало {argument}")
        expect(isinstance(res, list), f"на {a} возвращён {type(res).__name__}, а не список")
        expect(is_sorted(res), f"нарушен порядок на {a}: получено {res}")
        expect(sorted(res) == sorted(a), f"не перестановка входа {a}: получено {res}")

    # Сверка с эталоном из стандартной библиотеки на сотнях случайных входов.
    rng = random.Random(0)
    for _ in range(300):
        a = [rng.randint(-100, 100) for _ in range(rng.randint(0, 80))]
        argument = list(a)
        res = fn(argument)
        expect(argument == a, f"изменён случайный вход {a}: стало {argument}")
        expect(res == sorted(a), f"расходится с sorted() на {a}: получено {res}")


def check_counters() -> None:
    """Проверить счётчики простых сортировок на входах с известным ответом."""
    _, comparisons, _ = selection_sort([3, 1, 2, 5, 4])
    expect(comparisons == 10,
           f"selection_sort: неверный счётчик сравнений — {comparisons}, ожидалось 10")

    _, comparisons, swaps = bubble_sort([1, 2, 3, 4])
    expect((comparisons, swaps) == (3, 0),
           f"bubble_sort на упорядоченном входе: {(comparisons, swaps)}, ожидалось (3, 0)")
    _, comparisons, swaps = bubble_sort([4, 3, 2, 1])
    expect((comparisons, swaps) == (6, 6),
           f"bubble_sort на обратном входе: {(comparisons, swaps)}, ожидалось (6, 6)")

    _, comparisons, moves = insertion_sort([1, 2, 3, 4])
    expect((comparisons, moves) == (3, 0),
           f"insertion_sort на упорядоченном входе: {(comparisons, moves)}, ожидалось (3, 0)")
    _, comparisons, moves = insertion_sort([4, 3, 2, 1])
    expect((comparisons, moves) == (6, 9),
           f"insertion_sort на обратном входе: {(comparisons, moves)}, ожидалось (6, 9)")


def check_stability() -> None:
    """Проверить стабильные сортировки и показать контрпример нестабильных."""
    pairs = [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
    key = lambda pair: pair[0]
    bubble = bubble_sort(pairs, key)[0]
    insertion = insertion_sort(pairs, key)[0]
    selection = selection_sort(pairs, key)[0]
    quick = quick_sort(pairs, random.Random(0), key)

    expect(preserves_equal_order(pairs, bubble, key), "bubble_sort потерял стабильность")
    expect(preserves_equal_order(pairs, insertion, key), "insertion_sort потерял стабильность")
    expect(not preserves_equal_order(pairs, selection, key),
           "для selection_sort не сработал выбранный контрпример нестабильности")
    expect(not preserves_equal_order(pairs, quick, key),
           "для quick_sort не сработал выбранный контрпример нестабильности")


def self_check() -> None:
    """Все проверки по разделам; при любой ошибке замеры не выполняются."""
    # fn=fn фиксирует функцию текущего шага цикла (иначе все лямбды увидят последнюю)
    checks = [(name, lambda fn=fn: check_algorithm(fn)) for name, fn in ALGORITHMS.items()]
    checks.append(("счётчики", check_counters))
    checks.append(("стабильность", check_stability))
    failed = 0
    print("self_check:")
    for name, check in checks:
        try:
            check()
        except NotImplementedError as err:
            where = traceback.extract_tb(err.__traceback__)[-1].name
            print(f"  {name}: не реализовано — {where} (TODO)")
            failed += 1
        except SelfCheckError as err:
            print(f"  {name}: ОШИБКА — {err}")
            failed += 1
        except Exception:  # noqa: BLE001 — падение реализации тоже результат проверки
            print(f"  {name}: ИСКЛЮЧЕНИЕ")
            traceback.print_exc(file=sys.stdout)
            failed += 1
        else:
            print(f"  {name}: OK")
    if failed:
        raise SystemExit(f"self_check: не пройдено разделов — {failed}; "
                         f"замеры выполняются только после всех проверок.")
    print("self_check: OK")


# ---------------------------------------------------------------------------
# 6. Бенчмарк (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES_QUADRATIC = [500, 1_000, 2_000, 4_000, 8_000]     # для простых сортировок
SIZES_QUICK = [1_000, 3_000, 10_000, 30_000, 100_000]   # для QuickSort
REPEATS = 5


def bench(fn, data: list) -> float:
    """Медиана времени выполнения fn(копия data) по REPEATS запускам, с прогревом."""
    fn(list(data))  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        arg = list(data)  # свежая копия: сортировка не должна получать свой результат
        t0 = time.perf_counter()
        fn(arg)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def log_log_slope(points: list[tuple[int, float]]) -> float:
    """Оценить показатель степени по наклону прямой в координатах log-log."""
    xs = [math.log10(n) for n, _ in points]
    ys = [math.log10(elapsed) for _, elapsed in points]
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = sum((x - mean_x) ** 2 for x in xs)
    return numerator / denominator


def print_counter_table(seed: int, n: int = 1_000) -> None:
    """Вывести сравнения и обмены/перемещения на трёх классах входов."""
    algorithms = (
        ("bubble_sort", bubble_sort),
        ("insertion_sort", insertion_sort),
        ("selection_sort", selection_sort),
    )
    print(f"\nСчётчики простых сортировок при n={n}:")
    for name, sort in algorithms:
        for input_class, data in make_inputs(n, seed).items():
            result, comparisons, movements = sort(data)
            expect(result == sorted(data), f"{name}: ошибка перед выводом счётчиков")
            print(f"  {name:16s} вход={input_class:<13} "
                  f"сравнения={comparisons:>9}  обмены/перемещения={movements:>9}")


def run_benchmarks(seed: int) -> dict:
    """Замеры всех алгоритмов на трёх классах входов; вернуть данные графиков."""
    plans = [
        ("bubble_sort", ALGORITHMS["bubble_sort"], SIZES_QUADRATIC),
        ("insertion_sort", ALGORITHMS["insertion_sort"], SIZES_QUADRATIC),
        ("selection_sort", ALGORITHMS["selection_sort"], SIZES_QUADRATIC),
        ("quick_sort", lambda a: quick_sort(a, random.Random(seed)), SIZES_QUICK),
    ]
    results: dict = {}
    for name, fn, sizes in plans:
        print(f"\n{name}:")
        results[name] = collections.defaultdict(list)
        for n in sizes:
            for cls, data in make_inputs(n, seed).items():
                elapsed = bench(fn, data)
                results[name][cls].append((n, elapsed))
                print(f"  n={n:>7}  вход={cls:<13} t={elapsed:.6f} c")
        for cls, points in results[name].items():
            print(f"  наклон log-log, вход={cls:<13}: {log_log_slope(points):.2f}")
    return results


def plot_results(results: dict, out_dir: Path) -> None:
    """Построить log-log графики времени для четырёх сортировок."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib не установлен — графики пропущены")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    for ax, (algorithm, classes) in zip(axes.flat, results.items()):
        for input_class, points in classes.items():
            slope = log_log_slope(points)
            ax.plot([n for n, _ in points], [t for _, t in points], marker="o",
                    label=f"{input_class}, наклон {slope:.2f}")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(algorithm)
        ax.set_xlabel("размер входа n")
        ax.set_ylabel("время, с")
        ax.grid(True, which="both", linewidth=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    path = out_dir / "lab03_sorts_loglog.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\nГрафик сохранён: {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    ap.add_argument("--out", type=Path, default=Path.cwd(),
                    help="каталог для графика (по умолчанию текущий)")
    args = ap.parse_args()
    seed = 30 + args.variant
    random.seed(seed)
    args.out.mkdir(parents=True, exist_ok=True)
    self_check()
    stability_demo()
    print_counter_table(seed)
    results = run_benchmarks(seed)
    plot_results(results, args.out)


if __name__ == "__main__":
    main()
