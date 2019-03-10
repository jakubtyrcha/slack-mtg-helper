from random import shuffle
# D - deck size
# X - count of a specific card
# ?: chance that we get K cards in the first K
# choose(K, X) * permutations(K) * permutations(D-K) * choose(X-K, X) * choose(1)

def prob_of_encountering_x_at_least_K_times_MC(deck_size, cards_seen, x_num_in_deck, K, samples):
    D = deck_size
    S = cards_seen
    X = x_num_in_deck
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

def expected_lands_num_MC(deck_size, lands_num, cards_seen, samples):
    D = deck_size
    X = lands_num
    S = cards_seen
    l = [0] * X + [1] * (D - X)

    e = 0
    for _ in range(samples):
        shuffle(l)
        e += len([x for x in l[:S] if x == 0])

    return e / samples

if __name__ == "__main__":

    for x in range(20):
        print("{}(T+{}): {}".format(x, x - 7, expected_lands_num_MC(40, 17, x, 100)))
