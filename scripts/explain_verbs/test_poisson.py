
import math

def poisson_prob(freq, k=100):
    if freq <= 0: return 0
    # P = 1 - e^(-freq/k)
    # k 是特征常数，代表"在该频次下，出现概率为 1 - 1/e ≈ 63.2%"
    prob = 1 - math.exp(-freq / k)
    return prob * 100

test_cases = [
    ("be", 54093),
    ("have", 15599),
    ("make", 3882),
    ("find", 2000),
    ("high", 500),
    ("mid", 200),
    ("core", 100),
    ("low", 50),
    ("rare", 20),
    ("once", 1)
]

print(f"{'Word':<10} {'Freq':<8} {'K=50':<10} {'K=100':<10} {'K=150':<10}")
print("-" * 60)

for word, freq in test_cases:
    p_50 = poisson_prob(freq, 50)
    p_100 = poisson_prob(freq, 100)
    p_150 = poisson_prob(freq, 150)
    print(f"{word:<10} {freq:<8} {p_50:<10.1f} {p_100:<10.1f} {p_150:<10.1f}")
