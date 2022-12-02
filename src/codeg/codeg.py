import abc
import collections.abc
import linecache
from typing import Any, Callable, List, Type, Union  # noqa: TYP001

import attr
import black

from .exceptions import CodegSyntaxError


def _attr_nothing_factory():
    """Since attr already use attr.NOTHING for no default args,
    we use the hack as factory so that we can use nothing as default"""
    return attr.NOTHING


def format_string_with_black(string: str, stub: bool = False) -> str:
    """Format python code with PEP8 using black"""
    return black.format_str(string, mode=black.FileMode(is_pyi=stub))


def annotation_to_str(annotation) -> str:
    """Convert an annotation to an str"""
    if hasattr(annotation, "__name__"):
        return f"{annotation.__name__}"
    else:
        return f"{annotation}"


@attr.s
class Parameter:
    """Data class used to handle attribute information"""

    name = attr.ib()
    annotation = attr.ib(default=None, kw_only=True)
    default = attr.ib(factory=_attr_nothing_factory, kw_only=True)
    kw_only = attr.ib(default=False, kw_only=True)


def parameter(*args, **kwargs):
    return Parameter(*args, **kwargs)


p = param = parameter


def build(source: str, globals=None, locals=None, filename=None) -> Any:
    """Compile the script and return the objects in a dict
    Subclass can return specific objects (not always dict)
    """
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

    # Adding linecache to facilitate debuging and show lines of errors
    linecache.cache[filename] = (len(source), None, source.splitlines(True), filename)

    c = compile(source, filename, "exec")
    eval(c, globals, locals)
    return locals


# Used to generate unique filename when compiling python code
_counter_filename = 0


class BasePiece(abc.ABC):
    def __init__(self):
        """Base class used to generate a script dynamically and execute it

        Algorithme:
            Every python instruction or block is a piece (condition, loops, ...)
            Each pieces have a list of pieces (child pieces):
                Example: all instructions inside a 'for' loop are included in the 'pieces' list
            Each piece have a list of sibling_pieces
                Example: an 'if' piece can have 'else' piece or 'elif' piece in the same level (siblings)
            generate_code is the main function that will generate the script recursively
                generate_code will call generate_atomic_script of each piece
        """
        self.pieces = []
        self.sibling_pieces = []
        self.tab = "    "

    def __str__(self):
        return f"<{self.__class__.__name__}>"

    def __repr__(self):
        return self.__str__()

    def generate_atomic_script(self) -> Union[str, List[str]]:
        """Generate the 'important part' of script of the current cls piece (without the siblings and childs pieces)

        This function should be reimplemented in all subclasses"""
        return ""

    def generate_code(
        self, format_with_black=True, *, _indent=0, _aslist=False, stub=False
    ):
        """Recursive function to generate the script(str) from the picies and siblings_pieces"""
        # use list instead of str to optimize, 'str +=' have O(n) complexity
        script_as_list = []

        for sibling_piece in [self] + self.sibling_pieces:
            _atomic_script = sibling_piece.generate_atomic_script()
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

                _atomic_script = self.tab * _indent + ("\n" + self.tab * _indent).join(
                    _atomic_script
                )
                # all blocks ends with ":"
                if isinstance(sibling_piece, BaseIndentPiece):
                    _atomic_script += ":"

                script_as_list.append(_atomic_script)

                # add pass if no blocks inside
                if (
                    isinstance(sibling_piece, BaseIndentPiece)
                    and not sibling_piece.pieces
                ):
                    # Fixme: if we have only comments also add blocks!
                    if stub:
                        pass_or_elips = "..."
                    else:
                        pass_or_elips = "pass"
                    script_as_list.append(self.tab * (_indent + 1) + pass_or_elips)

            # Recursively generate sub blocks
            if sibling_piece.pieces:
                _new_indent = _indent
                if isinstance(sibling_piece, BaseIndentPiece):
                    _new_indent += 1
                for block in sibling_piece.pieces:
                    if isinstance(block, str):
                        script_as_list.append((_new_indent * self.tab) + block)
                        continue
                    elif not isinstance(block, BasePiece):
                        raise ValueError(f"Type {type(block)!r} unhandled")

                    script_as_list.extend(
                        block.generate_code(
                            _indent=_new_indent,
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
                import coloring

                coloring.print_red(script)
                coloring.print_red("========== ERORR ===========")
                raise e

        return script

    def generate_stubcode(self) -> str:
        """Generate the stubfile code (file containing class names, annotations, function signature, ...)"""
        stubcodde = script()
        for piece in self.pieces:
            if isinstance(piece, (ImportPiece, AnnotationPiece)):
                stubcodde.pieces.append(piece)

            elif isinstance(piece, ClassBlock):
                stubcls = stubcodde.cls(piece.name, piece.bases)
                for cls_piece in piece.pieces:
                    if isinstance(cls_piece, AnnotationPiece):
                        stubcls.pieces.append(cls_piece)

                    if isinstance(cls_piece, FunctionBlock):
                        stubcls.function(
                            cls_piece.name,
                            parameters=cls_piece.parameters,
                            add_self=cls_piece.add_self,
                            replace_defaults_with_none=cls_piece.replace_defaults_with_none,
                        )

        return stubcodde.generate_code(stub=True)

    def build(self, globals=None, locals=None, filename=None) -> Any:
        """Compile the current script and return the objects in a dict
        Subclass can return specific objects (not always dict)
        Example: FunctionPiece return a function and not a dict
        """
        source = self.generate_code()
        return build(source, globals=globals, locals=locals, filename=filename)

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

    def parameter(self, *args, **kwargs):
        return parameter(*args, **kwargs)

    p = param = parameter
    # ==================== #
    # INSTRUCTIONS METHODS #
    # ==================== #

    def if_(self, test):
        piece = if_(test)
        self.pieces.append(piece)
        return piece

    def while_(self, test):
        piece = while_(test)
        self.pieces.append(piece)
        return piece

    def for_(self, target, iter):
        piece = for_(target, iter)
        self.pieces.append(piece)
        return piece

    def try_(self):
        piece = try_()
        self.pieces.append(piece)
        return piece

    def line(self, line: str):
        if not isinstance(line, str):
            raise TypeError("line must be an str")
        self.pieces.append(line)
        return self

    def annotation(self, var, annotation):
        self.pieces.append(AnnotationPiece(var, annotation))
        return self

    def import_(self, *modules, frm=None):
        piece = import_(*modules, frm=frm)
        self.pieces.append(piece)
        return self

    def return_(self, value):
        return self.line(f"return {value}")

    ret = return_

    def comment(self, comment: str, title=None):
        self.pieces.append(CommentPiece(comment, title=title))
        return self

    def class_(self, name, bases=None):
        block = ClassBlock(name, bases=bases)
        self.pieces.append(block)
        return block

    cls = class_

    def function(
        self, name, parameters=None, *, add_self=None, replace_defaults_with_none=None
    ):
        block = FunctionBlock(
            name,
            parameters=parameters,
            add_self=add_self,
            replace_defaults_with_none=replace_defaults_with_none,
        )
        self.pieces.append(block)
        return block

    def method(self, name, parameters=None, *, replace_defaults_with_none=None):
        return self.function(
            name,
            parameters,
            add_self=True,
            replace_defaults_with_none=replace_defaults_with_none,
        )

    def block(self, name):
        block = GenericBlock(name)
        self.pieces.append(block)
        return block

    def condition(self, condition):
        block = If(condition)
        self.pieces.append(block)
        return block


# FIXME: handle the case where only comment are in block (must also add pass)
class BaseIndentPiece(BasePiece):
    pass


class CommentPiece(BasePiece):
    def __init__(self, comment, title=None):
        super().__init__()
        if not title:
            self.comments = [comment]
        else:
            wrap_comment = "#" * len(comment) + " #"
            comment += " #"
            self.comments = [wrap_comment, comment, wrap_comment]

    def generate_atomic_script(self):
        return [f"# {e}" for e in self.comments]


class DecoratorMixin:
    def __init__(self):
        self.decorators = []

    def decorator(self, name):
        self.decorators.append(name)
        return self


class ClassBlock(BaseIndentPiece, DecoratorMixin):
    def __init__(self, name, bases=None):
        BaseIndentPiece.__init__(self)
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


class FunctionBlock(BaseIndentPiece, DecoratorMixin):
    def __init__(
        self, name, parameters=None, add_self=None, replace_defaults_with_none=None
    ):
        BaseIndentPiece.__init__(self)
        DecoratorMixin.__init__(self)

        parameters = normalize_parameters(parameters)

        if add_self is None:
            add_self = False

        if replace_defaults_with_none is None:
            replace_defaults_with_none = False

        self.name = name
        self.parameters = parameters
        self.add_self = add_self
        self.replace_defaults_with_none = replace_defaults_with_none

    def generate_atomic_script(self):
        ret_list = [f"@{e}" for e in self.decorators]
        # f"({self.}):\n"
        signature = generate_function_signature(
            self.parameters,
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


class ImportPiece(BasePiece):
    def __init__(self, *libs, frm=None):
        super().__init__()
        normalized_libs = []
        for lib in libs:
            if isinstance(lib, tuple):
                lib_name = self._normalize_lib_element(lib[0])
                normalized_libs.append((lib_name, lib[1]))
            else:
                lib = self._normalize_lib_element(lib)
                normalized_libs.append(lib)

        self.frm = frm
        self.libs = normalized_libs
        # FIXME: handle cls when importing? and test it!

    def _normalize_lib_element(self, e):
        if hasattr(e, "__name__"):
            return e.__name__
        return str(e)

    def generate_atomic_script(self):
        libs = [f"{e[0]} as {e[1]}" if isinstance(e, tuple) else e for e in self.libs]
        libs = ", ".join(libs)
        if not self.frm:
            return f"import {libs}"
        return f"from {self.frm} import {libs}"


class AnnotationPiece(BasePiece):
    def __init__(self, variable, annotation):
        super().__init__()
        self.variable = variable
        self.annotation = annotation

    def generate_atomic_script(self):
        return f"{self.variable}: {annotation_to_str(self.annotation)}"


class GenericBlock(BaseIndentPiece):
    def __init__(self, text):
        BaseIndentPiece.__init__(self)
        self.text = text

    def generate_atomic_script(self):
        return self.text


class ElseMixin:
    def __init__(self):
        self._else_called = False

    def else_(self):
        if self._else_called:
            raise CodegSyntaxError("Can not have more than one else in same block")

        piece = Else()
        self.sibling_pieces.append(piece)
        self._else_called = True
        return piece


class If(BaseIndentPiece, ElseMixin):
    def __init__(self, condition):
        BaseIndentPiece.__init__(self)
        ElseMixin.__init__(self)
        # TODO: find better way of naming?
        self._condition = condition

    def elif_(self, test):
        if self._else_called:
            raise CodegSyntaxError("Can not have elif after else")

        piece = Elif(test)
        self.sibling_pieces.append(piece)
        return piece

    def generate_atomic_script(self):
        return f"if {self._condition}"


class Else(BaseIndentPiece):
    def generate_atomic_script(self):
        return f"else"


class Elif(BaseIndentPiece):
    def __init__(self, test):
        super().__init__()
        self.test = test

    def generate_atomic_script(self):
        return f"elif {self.test}"


class Try(BaseIndentPiece, ElseMixin):
    def __init__(self):
        BaseIndentPiece.__init__(self)
        ElseMixin.__init__(self)
        self._finally_called = False

    def generate_atomic_script(self):
        return f"try"

    def else_(self):
        if self._finally_called:
            raise CodegSyntaxError("else can not be called after finally")
        return super().else_()

    def except_(self, type=None, name=None):
        if self._else_called:
            raise CodegSyntaxError("except can not be called after else")
        if self._finally_called:
            raise CodegSyntaxError("except_ can not be called after finally")
        piece = Except(type, name)
        self.sibling_pieces.append(piece)
        return piece

    def finally_(self):
        if self._finally_called:
            raise CodegSyntaxError("finally can not be called twice")
        piece = Finally()
        self.sibling_pieces.append(piece)

        self._finally_called = True
        return piece


class Except(BaseIndentPiece):
    def __init__(self, type=None, name=None):
        if name is not None and type is None:
            raise ValueError("When name is present, type must be provided")

        BaseIndentPiece.__init__(self)
        self.type = type
        self.name = name

    def generate_atomic_script(self):
        string = "except"
        if self.type:
            string += f" {self.type}"
        if self.name:
            string += f" as {self.name}"
        return string


class Raise(BasePiece):
    def __init__(self, exception):
        super().__init__()
        self.exception = exception

    def generate_atomic_script(self):
        return f"raise {self.exception}"


class Finally(BaseIndentPiece):
    def generate_atomic_script(self):
        return f"finally"


class While(BaseIndentPiece, ElseMixin):
    def __init__(self, test: str):
        BaseIndentPiece.__init__(self)
        ElseMixin.__init__(self)
        self.test = test

    def generate_atomic_script(self):
        return f"while {self.test}"


class For(BaseIndentPiece, ElseMixin):
    def __init__(self, target, iter):
        BaseIndentPiece.__init__(self)
        ElseMixin.__init__(self)
        self.target = target
        self.iter = iter

    def generate_atomic_script(self):
        return f"for {self.target} in {self.iter}"


def normalize_parameters(parameters):
    if parameters is None:
        return []
    elif not isinstance(parameters, collections.abc.Iterable):
        parameters = [parameters]

    normalized_parameters = []
    for e in parameters:
        if isinstance(e, str):
            e = Parameter(e)
        normalized_parameters.append(e)
    return normalized_parameters


# ========= #
# FUNCTIONS #
# ========= #
def if_(test):
    return If(test)


def try_():
    return Try()


def while_(test):
    return While(test)


def for_(target, iter):
    return For(target, iter)


def import_(*modules, frm=None):
    return ImportPiece(*modules, frm=frm)


def cls(name, bases=None):
    # TODO: bases can be a real cls?
    return ClassBlock(name, bases=bases)


class_ = cls


def function(
    name: str,
    parameters: Union[str, List] = None,
    *,
    replace_defaults_with_none: bool = None,
    is_method=False,
):
    return FunctionBlock(
        name,
        parameters=parameters,
        add_self=is_method,
        replace_defaults_with_none=replace_defaults_with_none,
    )


def method(
    name: str,
    parameters: Union[str, List] = None,
    *,
    replace_defaults_with_none: bool = None,
):
    return function(
        name,
        parameters,
        is_method=True,
        replace_defaults_with_none=replace_defaults_with_none,
    )


def line(line):
    base = BasePiece()
    return base.line(line)


def script():
    return BasePiece()


def block(content):
    base = BasePiece()
    return base.block(content)


# todo: fixme
def comment(content, title=None):
    base = BasePiece()
    return base.comment(content, title=title)


def annotation(var, annotation):
    base = BasePiece()
    return base.annotation(var, annotation)


def generate_function_call(parameters: List[Parameter] = None, kw_only=False) -> str:
    # self._generic_new_entity("animals", name, age)
    script = ""
    str_parameters = []
    for attribute in parameters:
        if attribute.kw_only or kw_only:
            str_parameters.append(f"{attribute.name}={attribute.name}")
        else:
            str_parameters.append(attribute.name)

    script += ", ".join(str_parameters)
    return script


def generate_function_signature(
    parameters: List[Parameter] = None, add_self=False, replace_defaults_with_none=False
) -> str:
    """Create the function signature based on the attributes (name, annotation, default)"""
    parameters = normalize_parameters(parameters)

    script = ""
    if add_self:
        if parameters:
            script += "self, "
        else:
            script += "self"

    attributes_params = []
    kw_only = False
    for a in parameters:
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

# TODO: import from as
# TODO: test name of functions/classes are identifiers
