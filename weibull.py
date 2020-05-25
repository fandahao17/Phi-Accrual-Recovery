import math


class WeibullWindow():
    def __init__(self, scale=20 * 60, inittime=100 * 60,
                 window_size=2, threshold=0.6):
        self.scale = scale
        self.k = scale / inittime
        self.window = []
        self.window_size = window_size
        self.threshold = threshold
        self.is_on = False

    def weibull(self, x):
        # print(x, self.scale, self.k)
        score = math.exp(-(x / self.scale) ** self.k)
        # print(f'WEIBULL SCORE: {score}')
        return score

    def started(self, time):
        self.ontime = time
        self.is_on = True

    def failed(self, time):
        self.window.append((time - self.ontime).total_seconds())
        if len(self.window) > self.window_size:
            self.window.remove(self.window[0])

        avg = sum(self.window) / len(self.window)
        self.k = self.scale / avg
        self.is_on = False

    def is_stable(self, time):
        return self.weibull((time - self.ontime).total_seconds()) < self.threshold
