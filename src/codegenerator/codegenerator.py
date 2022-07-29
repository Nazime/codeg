import linecache
import typing
from typing import Any, Callable, List, Type, Union  # noqa: TYP001

import attr
import black


def _attr_nothing_factory():
    """Since attr already use attr.NOTHING for no default args,
    we use the hack as factory so that we can use nothing as default"""
    return attr.NOTHING


def format_string_with_black(string, stub=False):
    return black.format_str(string, mode=black.FileMode(is_pyi=stub))


def annotation_to_str(annotation):
    if hasattr(annotation, "__name__"):
        return f"{annotation.__name__}"
    else:
        return f"{annotation}"


@attr.s
class Attribute:
    name = attr.ib()
    annotation = attr.ib(default=None)
    default = attr.ib(factory=_attr_nothing_factory)
    kw_only = attr.ib(default=False)


_counter_filename = 0


class BaseBlock:
    indentable_block = False

    def __init__(self):
        self.blocks = []
        self.tab = "    "

    def __str__(self):
        return f"<{self.__class__.__name__}>"

    def __repr__(self):
        return self.__str__()

    def generate_atomic_script(self):
        return ""

    def line(self, line: str):
        if not isinstance(line, str):
            raise TypeError("line must be an str")
        self.blocks.append(line)
        return self

    def annotation(self, var, annotation):
        self.blocks.append(AnnotationBlock(var, annotation))
        return self

    def imports(self, modules, frm):
        self.blocks.append(ImportBlock(modules, frm=frm))
        return self

    def ret(self, value):
        return self.line(f"return {value}")

    def comment(self, comment: str):
        self.blocks.append(CommentBlock(comment))
        return self

    def cls(self, name, bases=None):
        block = ClassBlock(name, bases=bases)
        self.blocks.append(block)
        return block

    def function(
        self, name, attributes=None, add_self=None, replace_defaults_with_none=None
    ):
        block = FunctionBlock(
            name,
            attributes=attributes,
            add_self=add_self,
            replace_defaults_with_none=replace_defaults_with_none,
        )
        self.blocks.append(block)
        return block

    def method(self, name, attributes=None, replace_defaults_with_none=None):
        return self.function(
            name,
            attributes,
            add_self=True,
            replace_defaults_with_none=replace_defaults_with_none,
        )

    def block(self, name):
        block = GenericBlock(name)
        self.blocks.append(block)
        return block

    def condition(self, condition):
        block = ConditionBlock(condition)
        self.blocks.append(block)
        return block

    def generate_code(
        self, format_with_black=True, *, _indent=0, _aslist=False, stub=False
    ):
        # use list instead of str to optimize, str += have O(n) complexity
        script_as_list = []

        _atomic_script = self.generate_atomic_script()
        # If atomic script is empty string do nothing
        if _atomic_script:
            # Normalize script if it's str or list[str]
            if isinstance(_atomic_script, str):
                _atomic_script = [_atomic_script]
            elif not isinstance(_atomic_script, list):
                raise ValueError(
                    f"return of generate_atomic_script must be str or List[str]"
                    f"not {type(_atomic_script)}"
                )

            _atomic_script = self.tab * _indent + (self.tab * _indent + "\n").join(
                _atomic_script
            )
            # all blocks ends with ":"
            if isinstance(self, BaseIndentBlock):
                _atomic_script += ":"

            script_as_list.append(_atomic_script)

            # add pass if no blocks inside
            if isinstance(self, BaseIndentBlock) and not self.blocks:
                # Fixme: if we have only comments also add blocks!
                if stub:
                    pass_or_elips = "..."
                else:
                    pass_or_elips = "pass"
                script_as_list.append(self.tab * (_indent + 1) + pass_or_elips)

        # Recursively generate sub blocks
        if self.blocks:
            if isinstance(self, BaseIndentBlock):

                _indent += 1
            for block in self.blocks:
                if isinstance(block, str):
                    script_as_list.append((_indent * self.tab) + block)
                    continue
                elif not isinstance(block, BaseBlock):
                    raise ValueError(f"Type {type(block)!r} unhandled")

                script_as_list.extend(
                    block.generate_code(
                        _indent=_indent,
                        format_with_black=False,
                        _aslist=True,
                        stub=stub,
                    )
                )

        # Return
        if _aslist:
            return script_as_list

        script = "\n".join(script_as_list)
        if format_with_black:
            try:
                script = format_string_with_black(script, stub=stub)
            except Exception as e:
                # coloring.print_red(script)
                # coloring.print_red("========== ERORR ===========")
                raise e

        return script

    def build(self, globals=None, locals=None, filename=None) -> Any:
        if globals is None and locals is None:
            globals = {}
            locals = globals

        if globals is None:
            globals = {}

        if locals is None:
            locals = {}

        if not filename:
            global _counter_filename
            _counter_filename += 1
            filename = f"<generated with ScripBuilder {_counter_filename}>"

        source = self.generate_code()

        # Adding linecache to facilitate debuging and show lines of errors
        linecache.cache[filename] = (
            len(source),
            None,
            source.splitlines(True),
            filename,
        )

        c = compile(source, filename, "exec")
        eval(c, globals, locals)
        return locals

    def bound_to_class(self, cls, attribute_name=None):
        if attribute_name is None:
            attribute_name = self.name

        d = self.build()
        setattr(cls, attribute_name, d[attribute_name])

    bound_to_cls = bound_to_class

    def bound_to_instance(self, instance, attribute_name: str):
        # FIXME: limit to one build only?
        self.build(globals())
        setattr(instance, attribute_name, self.locals[attribute_name].__get__(instance))
        pass

    def print(self):
        """Used for debug purpose"""
        print(self.generate_code())

    def generate_stubcode(self):
        stubcodde = script()
        for piece in self.blocks:
            if isinstance(piece, (ImportBlock, AnnotationBlock)):
                stubcodde.blocks.append(piece)

            elif isinstance(piece, ClassBlock):
                stubcls = stubcodde.cls(piece.name, piece.bases)
                for cls_piece in piece.blocks:
                    if isinstance(cls_piece, AnnotationBlock):
                        stubcls.blocks.append(cls_piece)

                    if isinstance(cls_piece, FunctionBlock):
                        stubcls.function(
                            cls_piece.name,
                            attributes=cls_piece.attributes,
                            add_self=cls_piece.add_self,
                            replace_defaults_with_none=cls_piece.replace_defaults_with_none,
                        )

        return stubcodde.generate_code(stub=True)


# FIXME: handle the case where only comment are in block (must also add pass)
class BaseIndentBlock(BaseBlock):
    indentable_block = True


class CommentBlock(BaseBlock):
    def __init__(self, comment):
        super().__init__()
        self.comment = comment

    def generate_atomic_script(self):
        return f"# {self.comment}"


class DecoratorMixin:
    def __init__(self):
        self.decorators = []

    def decorator(self, name):
        self.decorators.append(name)
        return self


class ClassBlock(BaseIndentBlock, DecoratorMixin):
    def __init__(self, name, bases=None):
        BaseIndentBlock.__init__(self)
        DecoratorMixin.__init__(self)

        if bases is None:
            bases = []
        elif isinstance(bases, str):
            bases = [bases]

        self.name = name
        self.bases = bases

    def generate_atomic_script(self):
        ret_list = [f"@{e}" for e in self.decorators]
        if self.bases:
            bases = "(" + ", ".join(self.bases) + ")"
        else:
            bases = ""
        ret_list.append(f"class {self.name}{bases}")
        return ret_list

    def build(self, globals=None, locals=None, filename=None) -> Type:
        return super().build(globals, locals, filename)[self.name]


class FunctionBlock(BaseIndentBlock, DecoratorMixin):
    def __init__(
        self, name, attributes=None, add_self=None, replace_defaults_with_none=None
    ):
        BaseIndentBlock.__init__(self)
        DecoratorMixin.__init__(self)

        if attributes is None:
            attributes = []

        if add_self is None:
            add_self = False

        if replace_defaults_with_none is None:
            replace_defaults_with_none = False

        self.name = name
        self.attributes = attributes
        self.add_self = add_self
        self.replace_defaults_with_none = replace_defaults_with_none

    def generate_atomic_script(self):
        ret_list = [f"@{e}" for e in self.decorators]
        # f"({self.}):\n"
        signature = generate_function_signature(
            self.attributes,
            add_self=self.add_self,
            replace_defaults_with_none=self.replace_defaults_with_none,
        )
        ret_list.append(f"def {self.name}({signature})")
        return ret_list

    def bound_to_instance(self, instance, attribute_name: str = None):
        if attribute_name is None:
            attribute_name = self.name

        f = self.build()
        setattr(instance, attribute_name, f.__get__(instance))

    def bound_to_cls(
        self, cls, globals, locals=None, filename="", attribute_name: str = None
    ):
        # TODO: test and fixme
        if attribute_name is None:
            attribute_name = self.name

        locals = self.build(globals, locals=locals, filename=filename)
        setattr(cls, attribute_name, locals[self.name])

    def build(self, globals=None, locals=None, filename=None) -> Callable:
        return super().build(globals, locals, filename)[self.name]


class ImportBlock(BaseBlock):
    def __init__(self, libs, frm=None):
        super().__init__()
        if not isinstance(libs, typing.Sequence):
            libs = [libs]

        libs = [e.__name__ if hasattr(e, "__name__") else str(e) for e in libs]
        self.frm = frm
        self.libs = libs

    def generate_atomic_script(self):
        libs = ", ".join(self.libs)
        if not self.frm:
            return f"import {libs}"
        return f"from {self.frm} import {libs}"


class AnnotationBlock(BaseBlock):
    def __init__(self, variable, annotation):
        super().__init__()
        self.variable = variable
        self.annotation = annotation

    def generate_atomic_script(self):
        return f"{self.variable}: {annotation_to_str(self.annotation)}"


class GenericBlock(BaseIndentBlock):
    def __init__(self, text):
        BaseIndentBlock.__init__(self)
        self.text = text

    def generate_atomic_script(self):
        return self.text


class ConditionBlock(BaseIndentBlock):
    def __init__(self, condition):
        BaseIndentBlock.__init__(self)
        self.condition = condition

    def generate_atomic_script(self):
        return f"if {self.condition}"


def cls(name, bases=None):
    # TODO: bases can be a real cls?
    return ClassBlock(name, bases=bases)


def function(
    name: str,
    attributes: Union[str, List] = None,
    replace_defaults_with_none: bool = None,
    is_method=False,
):
    return FunctionBlock(
        name,
        attributes=attributes,
        add_self=is_method,
        replace_defaults_with_none=replace_defaults_with_none,
    )


def method(
    name: str,
    attributes: Union[str, List] = None,
    replace_defaults_with_none: bool = None,
):
    return function(
        name,
        attributes,
        is_method=True,
        replace_defaults_with_none=replace_defaults_with_none,
    )


def line(line):
    base = BaseBlock()
    return base.line(line)


def script():
    return BaseBlock()


def block(content):
    base = BaseBlock()
    return base.block(content)


# todo: fixme
def comment(content):
    base = BaseBlock()
    return base.comment(content)


def annotation(var, annotation):
    base = BaseBlock()
    return base.annotation(var, annotation)


def generate_function_call(attributes: List[Attribute] = None) -> str:
    # self._generic_new_entity("animals", name, age)
    script = ""
    str_attributes = []
    for attribute in attributes:
        if not attribute.kw_only:
            str_attributes.append(attribute.name)
        else:
            str_attributes.append(f"{attribute.name}={attribute.name}")

    script += ", ".join(str_attributes)
    return script


def generate_function_signature(
    attributes: List[Attribute] = None, add_self=False, replace_defaults_with_none=False
) -> str:
    """Create the function signature based on the attributes (name, annotation, default)"""
    if attributes is None:
        attributes = []

    script = ""
    if add_self:
        if attributes:
            script += "self, "
        else:
            script += "self"

    attributes_params = []
    kw_only = False
    for a in attributes:
        if kw_only is False and a.kw_only:
            kw_only = True
            attributes_params.append("*")

        a_param = a.name
        if a.annotation:
            a_param += f": {annotation_to_str(a.annotation)}"

        if replace_defaults_with_none:
            a_default = None
        else:
            a_default = a.default
        if a_default != attr.NOTHING:
            # To respect PEP8 if we have annotation we add spaces
            if a.annotation:
                a_param += f" = {a_default!r}"
            else:
                a_param += f"={a_default!r}"

        attributes_params.append(a_param)
    script += ", ".join(attributes_params)
    script += ""
    return script


# FIXME: there are mixing naming between generic block and indent block, block means indent block or piece of code?!
# TODO: create file when built to debug?
