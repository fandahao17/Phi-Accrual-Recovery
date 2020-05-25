from weibull import WeibullWindow
from phi_accrual_failure_detector import PhiAccrualFailureDetector


class ColdStartFD:
    def __init__(self):
        self.weibull = WeibullWindow()
        self.phi_accrual = PhiAccrualFailureDetector()
        self.stable = False
        self.is_on = False

    def heartbeat(self, time):
        self.is_on = True

        if not self.weibull.is_on:
            print('Detected heartbeat!')
            self.weibull.started(time)

        self.phi_accrual.heartbeat(time)

    def is_available(self, time):
        if not self.is_on:
            return False

        if self.stable:
            if self.phi_accrual.is_available(time):
                return True
            else:
                # Must have crashed
                # print('Crash on stable!')
                self.phi_accrual.reinit()
                self.is_on = False
                self.stable = False
                self.weibull.failed(time)
        else:
            # Not stable yet
            if self.phi_accrual.is_available(time):
                if self.weibull.is_stable(time):
                    print('Turns stable!')
                    self.stable = True
            else:
                # Must have crashed
                # print('Crash unstable!')
                self.phi_accrual.reinit()
                self.is_on = False
                self.weibull.failed(time)

        return False
