"""무작위 단계에서 쓰는 난수 생성기."""

import numpy as np

from config import RANDOM_SEED


def seeded_rng(*keys):
    """RANDOM_SEED와 키들로 만든 난수 생성기. 같은 키면 항상 같은 결과.

    키마다 따로 만들어서, 다른 나라나 사용자가 추가·삭제되어도 결과가 바뀌지 않는다.
    """
    entropy = [RANDOM_SEED] + [int.from_bytes(str(key).encode("utf-8"), "big") for key in keys]
    return np.random.default_rng(np.random.SeedSequence(entropy))
