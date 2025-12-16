class BaseStrategy:
    name = "base"

    def apply(self, df):
        raise NotImplementedError
