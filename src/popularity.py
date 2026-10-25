"""인기 점수 실험(H1, H2)에 같이 쓰는 데이터 준비와 평가 (report/실험설계.md 4, 5절).

아티스트는 순위 대상 집합(catalog) 안의 번호로 다룬다.
catalog = 학습 사용자가 한 번이라도 들은 아티스트, artist_id 순으로 정렬.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import N_SHOWN_ARTISTS, PROCESSED_DIR
from load_lastfm import load_plays
from metrics import ndcg_at_k, recall_at_k, top_k


@dataclass
class PopularityData:
    catalog: np.ndarray  # artist_id, 정렬됨
    country_listeners: dict  # iso3 -> 아티스트별 학습 청취자 수 (catalog 길이 배열)
    country_plays: dict  # iso3 -> 아티스트별 학습 재생 수 합
    country_train_users: dict  # iso3 -> 학습 사용자 수
    eval_users: pd.DataFrame  # user_id, iso3, split (검증·시험 사용자만)
    shown_index: dict  # user_id -> 보여준 아티스트의 catalog 번호 (catalog에 없는 것은 빠짐)
    relevant: dict  # user_id -> 정답 artist_id 집합 (catalog에 없는 것도 포함)


def load_popularity_data():
    """나누기 결과(split_users.py)와 재생 기록으로 실험 자료를 만든다."""
    split = pd.read_csv(PROCESSED_DIR / "user_split.csv", dtype=str, keep_default_na=False)
    shown = pd.read_csv(PROCESSED_DIR / "shown_artists.csv", dtype=str, keep_default_na=False)

    plays = load_plays()[["user_id", "artist_id", "plays"]]
    plays = plays.merge(split[["user_id", "iso3", "split"]], on="user_id", how="inner")

    # ---------- 학습 사용자로만 인기 점수 재료를 만든다 ----------
    train = plays[plays["split"] == "train"]
    catalog = np.sort(train["artist_id"].unique())
    train = train.assign(artist_index=np.searchsorted(catalog, train["artist_id"].to_numpy()))

    country_listeners, country_plays = {}, {}
    for iso3, rows in train.groupby("iso3", sort=True):
        index = rows["artist_index"].to_numpy()
        country_listeners[iso3] = np.bincount(index, minlength=len(catalog))
        country_plays[iso3] = np.bincount(
            index, weights=rows["plays"].to_numpy(dtype=float), minlength=len(catalog)
        )
    train_users = split[split["split"] == "train"]
    country_train_users = train_users.groupby("iso3").size().to_dict()

    # ---------- 평가 사용자: 보여준 것과 정답 ----------
    eval_users = split.loc[split["split"] != "train", ["user_id", "iso3", "split"]].reset_index(
        drop=True
    )
    eval_plays = plays.loc[plays["split"] != "train", ["user_id", "artist_id"]]
    shown_pairs = set(zip(shown["user_id"], shown["artist_id"]))
    is_shown = np.fromiter(
        (pair in shown_pairs for pair in zip(eval_plays["user_id"], eval_plays["artist_id"])),
        dtype=bool,
        count=len(eval_plays),
    )
    relevant = eval_plays[~is_shown].groupby("user_id")["artist_id"].agg(set).to_dict()

    shown_position = np.searchsorted(catalog, shown["artist_id"].to_numpy())
    shown_position = np.minimum(shown_position, len(catalog) - 1)
    in_catalog = catalog[shown_position] == shown["artist_id"].to_numpy()
    shown_in_catalog = shown[in_catalog].assign(artist_index=shown_position[in_catalog])
    shown_index = shown_in_catalog.groupby("user_id")["artist_index"].agg(np.array).to_dict()

    return PopularityData(
        catalog=catalog,
        country_listeners=country_listeners,
        country_plays=country_plays,
        country_train_users=country_train_users,
        eval_users=eval_users,
        shown_index=shown_index,
        relevant=relevant,
    )


def popularity_share(data, countries, measure):
    """주어진 나라들의 학습 사용자로 만든 인기 점수 (0~1).

    listeners: 들은 학습 사용자 비율. plays: 전체 재생 수 중 그 아티스트의 비율.
    """
    if measure == "listeners":
        counts = sum(data.country_listeners[iso3] for iso3 in countries)
        total = sum(data.country_train_users[iso3] for iso3 in countries)
    elif measure == "plays":
        counts = sum(data.country_plays[iso3] for iso3 in countries)
        total = counts.sum()
    else:
        raise ValueError(f"알 수 없는 인기 기준: {measure}")
    return counts / total


def listener_counts(data, countries):
    """동점 처리용 청취자 수. 주어진 나라들의 학습 사용자로만 센다."""
    return sum(data.country_listeners[iso3] for iso3 in countries)


def recommend_from_head(head, shown_index, k):
    """모두에게 같은 순위(head)에서 그 사용자에게 보여준 아티스트를 빼고 k개."""
    shown = set(int(index) for index in shown_index)
    return [int(index) for index in head if int(index) not in shown][:k]


def evaluate_shared_scores(data, scores, tie_listeners, user_ids, k):
    """같은 점수를 쓰는 사용자들(예: 한 나라)을 평가한다.

    점수가 모두에게 같으므로 순위는 한 번만 매긴다.
    사용자마다 빼는 아티스트가 최대 N_SHOWN_ARTISTS개라서 상위 k + N_SHOWN_ARTISTS개면 충분하다.
    돌려주는 값: 사용자별 NDCG, Recall 배열과 추천된 catalog 번호 집합.
    """
    head = top_k(scores, tie_listeners, exclude=[], k=k + N_SHOWN_ARTISTS)
    empty = np.array([], dtype=int)
    ndcg, recall, recommended_items = [], [], set()
    for user_id in user_ids:
        recommended = recommend_from_head(head, data.shown_index.get(user_id, empty), k)
        recommended_items.update(recommended)
        recommended_ids = list(data.catalog[recommended])
        relevant = data.relevant[user_id]
        ndcg.append(ndcg_at_k(recommended_ids, relevant, k))
        recall.append(recall_at_k(recommended_ids, relevant, k))
    return np.array(ndcg), np.array(recall), recommended_items
