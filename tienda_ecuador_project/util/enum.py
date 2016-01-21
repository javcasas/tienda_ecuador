# * encoding: utf-8 *
def Enum(name, option_pairs):
    code = """
class {clsname}(object):
    @classmethod
    def pretty_print(cls, ob):
        return dict(cls.__OPTIONS__)[ob]
""".format(clsname=name)
    exec(code)
    cls = locals()[name]

    class options(object):
        pass
    cls.options = options
    for k, v in option_pairs:
        try:
            setattr(options, k, k)
        except:
            pass
    cls.__OPTIONS__ = option_pairs
    return cls
