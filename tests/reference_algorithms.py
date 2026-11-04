"""
Independent pure-Python reference implementations (the original hand-written DFS, Kruskal and
Dijkstra from the analyst packs / first integration). They are NOT used by the app — the app's graph
results come from NetworkX. They exist only so the tests can cross-check NetworkX's answers with a
second, transparent implementation.
"""
from math import inf


def adjacency(order, routes):
    adj = {n: [] for n in order}
    for a, b, m in routes[["From", "To", "Minutes"]].itertuples(index=False, name=None):
        adj[a].append((b, int(m)))
        adj[b].append((a, int(m)))
    for n in adj:
        adj[n].sort(key=lambda t: order.index(t[0]))
    return adj


def dfs(order, routes, start):
    adj = adjacency(order, routes)
    visited, visit_order, tree, stack, steps = {start}, [start], [], [start], 1
    while stack:
        u = stack[-1]
        nxt = next((v for v, _ in adj[u] if v not in visited), None)
        if nxt is not None:
            visited.add(nxt)
            visit_order.append(nxt)
            tree.append((u, nxt))
            stack.append(nxt)
        else:
            stack.pop()
        steps += 1
    return {"visit_order": visit_order, "tree": tree, "steps": steps,
            "unreachable": [n for n in order if n not in visited]}


def kruskal(order, routes):
    parent = {n: n for n in order}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    accepted = []
    for a, b, m in sorted(routes[["From", "To", "Minutes"]].itertuples(index=False, name=None), key=lambda e: e[2]):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            accepted.append((a, b, int(m)))
    return accepted, sum(m for *_, m in accepted)


def dijkstra(order, routes, source):
    adj = adjacency(order, routes)
    dist = {n: inf for n in order}
    dist[source] = 0
    settled = []
    while len(settled) < len(order):
        cands = [n for n in order if n not in settled and dist[n] < inf]
        if not cands:
            break
        u = min(cands, key=lambda n: (dist[n], order.index(n)))
        settled.append(u)
        for v, w in adj[u]:
            if v not in settled and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist
