# * encoding: utf-8 *
def Enum(name, option_pairs):
    code = """
class {}(object):
    @classmethod
    def pretty_print(cls, ob):
        return dict(SRIStatus.__OPTIONS__)[ob]
""".format(name)
    exec(code)
    cls = locals()[name]

    class options(object):
        pass
    cls.options = options
    for k, v in option_pairs:
        setattr(options, k, k)
    cls.__OPTIONS__ = option_pairs
    return cls
