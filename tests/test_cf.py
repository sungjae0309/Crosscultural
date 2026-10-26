"""src/cf.py 확인용 테스트 (가짜 데이터).

빠른 계산(후보 안에서 순위)이 정의대로 전체를 계산한 결과와 같은지 본다.
실행: python tests/test_cf.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cf  # noqa: E402
from config import N_SHOWN_ARTISTS  # noqa: E402
from metrics import ndcg_at_k, recall_at_k, top_k  # noqa: E402
from popularity import build_popularity_data, listener_counts, user_listener_counts  # noqa: E402


def _frames(rng, n_artists=60, n_train=80, n_eval=30):
    artists = [f"art{index:03d}" for index in range(n_artists)]
    split_rows, play_rows, shown_rows = [], [], []
    for index in range(n_train):
        user = f"tr{index:03d}"
        split_rows.append((user, ["AAA", "BBB", "CCC"][index % 3], "train"))
        # 학습 사용자는 앞쪽 45개만 들어서 뒤쪽은 학습 자료 밖이 된다
        for artist in rng.choice(artists[:45], size=int(rng.integers(2, 15)), replace=False):
            play_rows.append((user, artist, 1))
    for index in range(n_eval):
        user = f"ev{index:03d}"
        split_rows.append((user, "AAA", "valid"))
        if index == 0:
            # fold-in에 쓸 아티스트가 없는 사용자: 보여준 5개가 모두 학습 자료 밖
            listened = list(artists[50:58])
        else:
            listened = list(rng.choice(artists, size=int(rng.integers(N_SHOWN_ARTISTS + 1, 25)), replace=False))
        play_rows.extend((user, artist, 1) for artist in listened)
        shown_rows.extend((user, artist) for artist in listened[:N_SHOWN_ARTISTS])
    return (
        pd.DataFrame(split_rows, columns=["user_id", "iso3", "split"]),
        pd.DataFrame(shown_rows, columns=["user_id", "artist_id"]),
        pd.DataFrame(play_rows, columns=["user_id", "artist_id", "plays"]),
    )


def _reference(data, model, users, weight, country_share, global_share, tie, mask, k):
    """정의대로: 사용자마다 순위 대상 전체에 섞은 점수를 매기고 metrics.py로 평가."""
    country_norm = cf._share_norm(country_share, mask)
    global_norm = cf._share_norm(global_share, mask)
    candidates = np.flatnonzero(mask)
    ndcg, recall, items = [], [], set()
    users_by_row = data.eval_users.set_index("row")["user_id"]
    for position, row in enumerate(users.rows):
        if users.usable[position]:
            raw = model.item_factors64 @ users.factors[position]
            model_raw = raw[model.in_model]
            span = model_raw.max() - model_raw.min()
            cf_norm = (raw - model_raw.min()) / span if span > 0 else np.zeros_like(raw)
            cf_norm = np.where(model.in_model, cf_norm, 0.0)
        else:
            cf_norm = global_norm
        scores = (1 - weight) * cf_norm + weight * country_norm
        shown = data.shown_matrix[row].indices
        exclude = np.flatnonzero(np.isin(candidates, shown))
        best = candidates[top_k(scores[candidates], tie[candidates], exclude, k)]
        items.update(best.tolist())
        relevant = set(data.relevant_matrix[row].indices.tolist())
        # 학습 자료 밖 정답은 행렬에 없으니 개수만 맞춘 가짜 번호로 채운다
        relevant |= {-1 - extra for extra in range(data.n_relevant[row] - len(relevant))}
        ndcg.append(ndcg_at_k(list(best), relevant, k))
        recall.append(recall_at_k(list(best), relevant, k))
        assert users_by_row[row]  # 행 번호가 실제 사용자와 맞는지
    return np.array(ndcg), np.array(recall), items


def test_fast_ranking_matches_reference():
    rng = np.random.default_rng(3)
    original = cf.CANDIDATES_PER_SOURCE
    exact_counts = []
    try:
        for trial in range(4):
            split, shown, plays = _frames(rng)
            data = build_popularity_data(split, shown, plays, "valid")
            model = cf.train_cf(data, ["BBB", "CCC"], factors=8, regularization=0.1)
            early = data.train_users["AAA"][:5]
            country_share = user_listener_counts(data, early) / len(early)
            listeners = listener_counts(data, ["BBB", "CCC"])
            global_share = listeners / sum(data.country_train_users[c] for c in ["BBB", "CCC"])
            tie = listeners + user_listener_counts(data, early)
            mask = tie > 0
            # 후보 수를 작게 하면 상한 확인에 걸려 전체 계산으로 가는 사용자가 생긴다
            for candidates in [3, 11, 12, 15, 100]:
                cf.CANDIDATES_PER_SOURCE = candidates
                users = cf.prepare_users(data, model, "AAA", candidates=candidates)
                assert not users.usable[0]  # 첫 사용자는 대체 규칙을 탄다
                for weight in [0.0, 0.3, 0.7, 1.0]:
                    got = cf.evaluate_mix(data, model, users, weight, country_share, global_share, tie, mask, "AAA", 10)
                    expected = _reference(data, model, users, weight, country_share, global_share, tie, mask, 10)
                    assert np.allclose(got[0], expected[0], atol=1e-12), (trial, candidates, weight)
                    assert np.allclose(got[1], expected[1], atol=1e-12), (trial, candidates, weight)
                    assert got[2] == expected[2], (trial, candidates, weight)
                    if weight < 1.0:
                        exact_counts.append(got[3])
    finally:
        cf.CANDIDATES_PER_SOURCE = original
    # 빠른 계산과 전체 계산이 둘 다 실제로 쓰였는지 (사용자 30명 중 전체 계산 인원)
    # 대체 규칙 사용자 1명은 늘 전체 계산이고, 한 번의 평가 안에서 두 경로가 섞인 경우도 있어야 한다
    assert min(exact_counts) >= 1
    assert any(1 < count < 30 for count in exact_counts)
    assert exact_counts.count(1) > 0


def test_train_matrix_and_in_model():
    rng = np.random.default_rng(0)
    split, shown, plays = _frames(rng)
    data = build_popularity_data(split, shown, plays, "valid")
    matrix = cf.train_matrix(data, ["BBB"])
    assert matrix.shape == (len(data.train_users["BBB"]), len(data.universe))
    assert matrix.nnz == sum(len(data.train_items[user]) for user in data.train_users["BBB"])
    model = cf.train_cf(data, ["BBB"], factors=4, regularization=0.1)
    assert np.array_equal(model.in_model, np.asarray(matrix.getnnz(axis=0)).ravel() > 0)


def test_model_save_and_load(tmp_dir=Path(__file__).resolve().parent):
    rng = np.random.default_rng(1)
    split, shown, plays = _frames(rng)
    data = build_popularity_data(split, shown, plays, "valid")
    model = cf.train_cf(data, ["BBB"], factors=4, regularization=0.1)
    path = tmp_dir / "_cf_model_test.npz"
    try:
        model.save(path)
        loaded = cf.CFModel.load(path)
        assert np.array_equal(loaded.item_factors, model.item_factors)
        assert np.array_equal(loaded.in_model, model.in_model)
        assert loaded.regularization == model.regularization
    finally:
        path.unlink(missing_ok=True)


def test_cross_fit_groups_and_models():
    from config import N_CF_GROUPS
    from run_h3 import all_model_keys, country_groups, model_key

    targets = [f"C{index:02d}" for index in range(42)]
    groups = country_groups(targets)
    # 사용자 수 순서대로 돌려 넣으므로 묶음마다 같은 수
    assert sorted(np.bincount(list(groups.values()))) == [42 // N_CF_GROUPS] * N_CF_GROUPS
    assert groups["C00"] == 0 and groups["C01"] == 1 and groups[f"C{N_CF_GROUPS:02d}"] == 0
    keys = all_model_keys()
    assert len(keys) == N_CF_GROUPS + N_CF_GROUPS * (N_CF_GROUPS - 1) // 2
    # 어떤 (t, c) 조합이든 쓸 ALS가 있고, 그 ALS는 t와 c의 묶음을 모두 뺀다
    for t in targets:
        for c in targets:
            key = model_key([groups[t], groups[c]])
            assert key in keys
            removed = {int(part[1:]) for part in key.split("_")}
            assert groups[t] in removed and groups[c] in removed


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"통과: {test.__name__}")
    print(f"{len(tests)}개 모두 통과")
