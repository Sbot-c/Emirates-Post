"""
data_check.py - Data Lead checks for the Emirates Post Network Audit.

Usage:
    python data_check.py EmiratesPost_Network_Data.xlsx            # threshold table only
    python data_check.py EmiratesPost_Network_Data.xlsx --x 30     # full check at X = 30

Reads the LOW / HIGH typical times you typed in the Time_Matrix sheet,
computes Minutes = round((LOW + HIGH) / 2) exactly like the workbook,
then:
  1. validates all 21 pairs,
  2. prints routes + connectivity for every X from 10 to 60,
  3. at your chosen X: DFS visit order from HUB, unreachable branches,
     single points of failure (branches whose loss disconnects the network),
  4. writes times.csv (all 21) and routes.csv (only routes under X)
     in the From, To, Minutes format the analysts load.
"""
import argparse, csv, sys
from decimal import Decimal, ROUND_HALF_UP
from openpyxl import load_workbook

def load(path):
    wb = load_workbook(path, data_only=False)
    br = wb["Branches"]; tm = wb["Time_Matrix"]
    nodes = [br.cell(r, 1).value for r in range(2, 9)]
    names = {br.cell(r, 1).value: br.cell(r, 2).value for r in range(2, 9)}
    times, problems = {}, []
    for r in range(2, 23):
        a, b, lo, hi = tm.cell(r, 2).value, tm.cell(r, 4).value, tm.cell(r, 7).value, tm.cell(r, 8).value
        if lo is None or hi is None:
            problems.append(f"row {r}: {a}-{b} missing LOW/HIGH"); continue
        try: lo, hi = float(lo), float(hi)
        except (TypeError, ValueError):
            problems.append(f"row {r}: {a}-{b} LOW/HIGH not numbers"); continue
        if lo > hi: problems.append(f"row {r}: {a}-{b} LOW {lo} > HIGH {hi}")
        if not (1 <= lo <= 240 and 1 <= hi <= 240): problems.append(f"row {r}: {a}-{b} outside 1-240 min")
        # Excel ROUND = half away from zero (Python round() would do banker's rounding)
        m = int(Decimal(str((lo + hi) / 2)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        times[frozenset((a, b))] = (a, b, m)
    if len(times) != 21 and not problems:
        problems.append(f"expected 21 distinct pairs, found {len(times)}")
    return nodes, names, times, problems

def adjacency(nodes, times, x, removed=None):
    adj = {n: [] for n in nodes if n != removed}
    for a, b, m in times.values():
        if m < x and a != removed and b != removed:
            adj[a].append(b); adj[b].append(a)
    for n in adj: adj[n].sort(key=nodes.index)   # matrix order: HUB, KAR, QUS, UMS, JAF, SHJ, AJM
    return adj

def dfs(adj, start):
    """Classic depth-first search (recursive), neighbours tried in matrix order (HUB, KAR, QUS, UMS, JAF, SHJ, AJM).
    Returns visit order, visited set, a step trace and the DFS tree edges."""
    visited, order, trace, tree = set(), [], [], []
    path = []
    def go(node, parent):
        visited.add(node); order.append(node); path.append(node)
        trace.append(("visit", node, parent, list(path)))
        if parent: tree.append((parent, node))
        for n in adj[node]:
            if n not in visited:
                go(n, node)
        path.pop()
        trace.append(("back", node, None, list(path)))
    go(start, None)
    return order, visited, trace, tree

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx"); ap.add_argument("--x", type=int); ap.add_argument("--start", default="HUB")
    a = ap.parse_args()
    nodes, names, times, problems = load(a.xlsx)
    print(f"Branches: {', '.join(nodes)}")
    if problems:
        print("\nDATA NOT READY:"); [print("  -", p) for p in problems]; sys.exit(1)
    print(f"All 21 pairs valid. Min {min(t[2] for t in times.values())} min, max {max(t[2] for t in times.values())} min.\n")

    print(" X | routes | in 10-14 | connected | cut off")
    print("---+--------+----------+-----------+--------")
    good = []
    for x in range(10, 61):
        adj = adjacency(nodes, times, x)
        n_routes = sum(len(v) for v in adj.values()) // 2
        _, vis, _, _ = dfs(adj, a.start)
        conn = len(vis) == len(nodes)
        cut = ",".join(sorted(set(nodes) - vis)) or "-"
        ok = 10 <= n_routes <= 14
        if ok and conn: good.append(x)
        print(f"{x:>2} | {n_routes:>6} | {'yes' if ok else '':>8} | {'YES' if conn else 'no':>9} | {cut}")
    print(f"\nX values with 10-14 routes AND connected: {good if good else 'NONE - see FAQ: raise X and report the weak branch'}")

    if a.x is None:
        print("\nRun again with --x <your X> for the DFS order, weak points and CSV export."); return
    x = a.x
    adj = adjacency(nodes, times, x)
    n_routes = sum(len(v) for v in adj.values()) // 2
    order, vis, trace, tree = dfs(adj, a.start)
    print(f"\n=== Chosen X = {x} min: {n_routes} routes ===")
    print("DFS from", a.start, "(neighbours in matrix order HUB, KAR, QUS, UMS, JAF, SHJ, AJM; compare with your paper trace):")
    for i, (kind, node, parent, path) in enumerate(trace, 1):
        if kind == "visit":
            print(f"{i:>3}. visit {node:<4}" + (f"(from {parent})" if parent else "(start)    ") + f"  path: {' > '.join(path)}")
        else:
            print(f"{i:>3}. done  {node:<4}  no unvisited neighbours, back to {path[-1] if path else '-'}")
    print("Visit order:", " > ".join(order))
    print("DFS tree edges:", ", ".join(f"{p}-{c}" for p, c in tree))
    if len(vis) == len(nodes):
        print("CONNECTED: every branch reachable.")
    else:
        print("NOT CONNECTED. Cut off:", ", ".join(sorted(set(nodes) - vis)))
    leaves = [n for n in nodes if len(adj[n]) == 1]
    print("Branches with only ONE route (lose that road, they are cut off):", ", ".join(leaves) or "none")
    if len(vis) == len(nodes):
        # single point of failure = a branch whose closure splits the remaining network
        spof = []
        for n in nodes:
            sub = adjacency(nodes, times, x, removed=n)
            _, v2, _, _ = dfs(sub, next(iter(sub)))
            if len(v2) < len(sub): spof.append((n, sorted(set(sub) - v2)))
        for n, lost in spof:
            print(f"Single point of failure: if {n} closes, {', '.join(lost)} become unreachable from the rest.")
        if not spof: print("No single point of failure: any one branch can close and the rest stay connected.")
    else:
        print("(Single-point-of-failure check skipped: network is already disconnected at this X.)")
    lower = adjacency(nodes, times, x - 5)
    _, v5, _, _ = dfs(lower, a.start)
    print(f"At X-5 = {x-5}: {sum(len(v) for v in lower.values())//2} routes, "
          f"{'connected' if len(v5)==len(nodes) else 'cut off: ' + ', '.join(sorted(set(nodes)-v5))}")
    try:
        import networkx as nx
        G = nx.Graph(); G.add_nodes_from(nodes)
        G.add_weighted_edges_from([(p, q, m) for p, q, m in times.values() if m < x])
        print("networkx cross-check is_connected():", nx.is_connected(G))
    except ImportError:
        pass

    with open("times.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["From", "To", "Minutes"])
        for p, q, m in times.values(): w.writerow([p, q, m])
    with open("routes.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["From", "To", "Minutes"])
        for p, q, m in sorted(times.values(), key=lambda t: t[2]):
            if m < x: w.writerow([p, q, m])
    print("\nWrote times.csv (21 pairs) and routes.csv (routes under X) for the analysts.")

if __name__ == "__main__":
    main()
