from random import shuffle
from functools import reduce
import operator

def C(n, r):
    r = min(r, n-r)
    numer = reduce(operator.mul, range(n, n-r, -1), 1)
    denom = reduce(operator.mul, range(1, r+1), 1)
    return numer / denom

def prob_seeing_the_card_K_times_MC(deck_size, cards_seen, in_deck, K, samples):
    D = deck_size
    S = cards_seen
    X = in_deck
    if S < K:
        return 0
    if K > X:
        return 0
    assert X <= D

    l = [0] * X + [1] * (D - X)

    s = 0
    c = 0
    for _ in range(samples):
        shuffle(l)
        s += len([x for x in l[:S] if x == 0]) == K
        c += 1
    return s / c

def prob_seeing_the_card_Kplus_times_MC(deck_size, cards_seen, in_deck, K, samples):
    D = deck_size
    S = cards_seen
    X = in_deck
    if S < K:
        return 0
    if K > X:
        return 0
    assert X <= D

    l = [0] * X + [1] * (D - X)

    s = 0
    c = 0
    for _ in range(samples):
        shuffle(l)
        s += len([x for x in l[:S] if x == 0]) >= K
        c += 1
    return s / c

def prob_seeing_the_card_K_times(deck_size, cards_seen, in_deck, K):
    D = deck_size
    X = in_deck
    H = cards_seen
    # C(X, K) * C(D - X, H - K) * H! * (D-H)!
    # D! - outcomes
    assert(K <= min(X, H))
    if H - K > D - X:
        return 0
    x = C(X, K) * C(D-X, H-K)
    y = C(D, H)
    return x / y

def prob_seeing_the_card_Kplus_times(deck_size, cards_seen, in_deck, K):
    D = deck_size
    X = in_deck
    H = cards_seen
    p = 0
    for k in range(K, min(X, H) + 1):
        p += prob_seeing_the_card_K_times(D, H, X, k)
    return p

def the_card_seen_expected_value(deck_size, cards_seen, in_deck):
    ev = 0
    for K in range(1, min(cards_seen, in_deck)):
        ev += K * prob_seeing_the_card_K_times(deck_size, cards_seen, in_deck, K)
    return ev

if __name__ == "__main__":

    x = 20 * 19 * reduce(operator.mul, range(36,41)) * 7 * 6
    y = 2 * reduce(operator.mul, range(54, 61))
    print(x / y)
    print(prob_seeing_the_card_K_times_MC(60, 7, 20, 2, 1000))
    print(prob_seeing_the_card_K_times(60, 7, 20, 2))

    for i in range(5, 40):
        print("{}, {} {}".format(i,prob_seeing_the_card_K_times(40, i, 17, 5),prob_seeing_the_card_K_times_MC(40, i, 17, 5, 1000)))
        print("{}, {} {}".format(i,prob_seeing_the_card_Kplus_times(40, i, 17, 5),prob_seeing_the_card_Kplus_times_MC(40, i, 17, 5, 1000)))


