class LogicTest:
    def __init__(self, scenarios=[]):
        self._scenarios = scenarios

    def get_results(self):
        results = self._evaluate()

        return results

    def _evaluate(self):
        results = []

        if len(self._scenarios) > 0:

            for scenario in self._scenarios:
                N = scenario['N']
                M = scenario['M']

                if N == M or M > N:

                    if N % 2 == 0:
                        results.append("L")
                    else:
                        results.append("R")

                elif N > M:

                    if M % 2 == 0:
                        results.append("U")
                    else:
                        results.append("D")

        return results
