from collections import Counter
from math import log

from digestive.io import Sink


class Entropy(Sink):
    def __init__(self):
        super().__init__('entropy')
        self.length = 0
        self.counter = Counter()

    def process(self, data):
        self.length += len(data)
        self.counter.update(data)

    def digest(self):
        # calculate binary entropy as -Σ(1…n) p_i × log₂(p_i)
        entropy = -sum(count / self.length * log(count / self.length, 2) for count in self.counter.values())
        return '{:.8f}'.format(entropy)
