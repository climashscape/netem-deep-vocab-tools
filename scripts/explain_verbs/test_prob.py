
import math

def original_algo(freq):
    if freq <= 0: return 0
    log_freq = math.log(freq)
    max_log = math.log(55000)
    return min(99.9, (log_freq / max_log) * 100)

def new_algo(freq, saturation_threshold=4000):
    if freq <= 0: return 0
    # 饱和阈值：超过这个频次的都认为是 99% 以上的必考词
    # 比如设为 4000，因为 make(3882) 这种词绝对是必考的
    
    log_freq = math.log(freq)
    max_log = math.log(saturation_threshold)
    
    prob = (log_freq / max_log) * 100
    return min(99.9, max(1, prob))

test_cases = [
    ("be", 54093),
    ("have", 15599),
    ("make", 3882),
    ("find", 2000),  # 假设
    ("help", 1000),  # 假设
    ("common", 500), # 假设
    ("rare", 50),
    ("once", 1)
]

print(f"{'Word':<10} {'Freq':<8} {'Original':<10} {'New(4000)':<10} {'New(3000)':<10}")
print("-" * 60)

for word, freq in test_cases:
    p_orig = original_algo(freq)
    p_new_4000 = new_algo(freq, 4000)
    p_new_3000 = new_algo(freq, 3000)
    print(f"{word:<10} {freq:<8} {p_orig:<10.1f} {p_new_4000:<10.1f} {p_new_3000:<10.1f}")
