import attr

def parameter(
    name: str, *, annotation=None, default=attr.NOTHING, kw_only: bool = False
): ...
