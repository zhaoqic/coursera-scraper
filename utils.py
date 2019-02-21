# https://stackoverflow.com/a/16464305
class AllEC(object):
    def __init__(self, *args):
        self.ecs = args

    def __call__(self, driver):
        for fn in self.ecs:
            try:
                if not fn(driver):
                    return False
            except:
                return False
        return True
