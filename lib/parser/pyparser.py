import time

import lxml.html

from lib.parser.errors import *


etree = lxml.html.etree

# Configures
ATTR_ID = 'id'
ATTR_TITLE = 'name'

ATTR_START = 'head'
ATTR_START_VALUE = 'head'

ATTR_UNIT = 'u'
ATTR_UNIT_VALUE_CON = 'constraints'
ATTR_UNIT_VALUE_ACT = 'activations'
ATTR_UNIT_VALUE_INT = 'initializers'
ATTR_UNIT_VALUE_REG = 'regularizers'

ATTR_ARG_CLS = 'c'
ATTR_ARG_CLS_VALUE_ID = 'id'
ATTR_ARG_CLS_VALUE_STR = 'str'
ATTR_ARG_CLS_VALUE_NUM = 'num'
ATTR_ARG_CLS_VALUE_SEQ = 'seq'
ATTR_ARG_CLS_VALUE_BOL = 'bool'

TAG_VNM = 'var'
TAG_CLS = 'class'
TAG_ARGS = 'args'
TAG_MODE = 'mode'
TAG_UNIT = 'unit'
TAG_MODEL = 'model'
TAG_LAYER = 'layer'
TAG_PLACEHOLDER = 'ph'

TAG_MODE_VALUE_IO = 'IO'
TAG_MODE_VALUE_CA = 'CA'  # Mode that accept other layer as its arg.
TAG_MODE_VALUE_AC = 'AC'  # Mode that can be accepted by Mode: CA.
TAG_MODEL_CLS_VALUE = 'Model'

L_TAG_INPUT = 'input'   # Layer's type input tag.
M_TAG_INPUT = 'inputs'  # Model's type input tag.
L_TAG_OUTPUT = 'output'
M_TAG_OUTPUT = 'outputs'

# The path of all the layers and models in Keras.
TAG_LAYER_SRC = 'layers'
TAG_MODEL_SRC = 'models'

IO_SPLIT = ';'
DEBUG = True


def debug(*msg):
    """ Debug mode. """
    if DEBUG:
        print(*msg)


class PlaceHolder(object):
    """ The super class of all the placeholders.

    Fill initializer with:
    @:param element: etree element.
    @:param src_id: which is the gain value, and is related to 'got_'.
    @:param dst_id: which is the key pass to placeholder manger.

    """

    def __init__(self, dst_id):
        self.dst_id = dst_id
        self.var_nm = None
        self.cls_nm = None
        self.ep_ipt = None
        self.ep_opt = None
        self.gt_ipt = []
        self.gt_opt = []

    def check(self):
        # Check self gt_ and ep_ whether ready to go.
        # Cannot use '==' directly, it will compare both
        # list item's content and position. In this case,
        # just focus on content comparing. Refer to cmp_cnt().
        pass

    def gain(self, src_id):
        # Gain the value to the gt_ipt or gt_opt.
        # The src_id could be single item or a list.
        if src_id in self.ep_ipt:
            self.gt_ipt.append(src_id)
        if src_id in self.ep_opt:
            self.gt_opt.append(src_id)

    @classmethod
    def cmp_cnt(cls, a: list, b: list):
        # Compare list without position factor.
        if len(a) == len(b):
            r = [True for c in a if c in b]
            return all(r)
        return False

    def __str__(self):
        txt = ""
        txt += f"[ep_ipt: {self.ep_ipt}"
        txt += f" ep_opt: {self.ep_opt}"
        txt += f" gt_ipt: {self.gt_ipt}"
        txt += f" gt_opt: {self.gt_opt}]"
        return txt


class ModelPlaceHolder(PlaceHolder):
    """ Placeholder for model. """

    # This placeholder only ready when its 'inputs'
    # and 'outputs' are finished preparing.

    def __init__(self, dst_id):
        super().__init__(dst_id)

    def check(self):
        return self.cmp_cnt(self.gt_ipt, self.ep_ipt) and\
               self.cmp_cnt(self.gt_opt, self.ep_opt)


class NodePlaceHolder(PlaceHolder):
    """ Placeholder for node.py. """

    # This placeholder only ready when its input
    # is finished preparing.
    # Then follow the output to find next clue.

    def __init__(self, dst_id):
        super().__init__(dst_id)

    def check(self):
        return self.cmp_cnt(self.gt_ipt, self.ep_ipt)


class PlaceHolderHub:
    """ The manger of placeholder. """

    def __init__(self):
        self.repo = {}

    def put(self, placeholder: PlaceHolder):
        self.repo[placeholder.dst_id] = placeholder

    def contains(self, key):
        return self.repo.__contains__(key)

    def get(self, key) -> PlaceHolder:
        return self.repo.get(key)


class ArgItem:
    """ That store in the attrs_dict. """

    def __init__(self, value, class_):
        self.value = value
        self.class_ = class_

    @property
    def v(self):
        return self.value

    @property
    def c(self):
        return self.class_

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class PyLines:
    """ Line pattern of .py:

    # <var> = <src>.<cls>(<args>)(<call>)

    The value of tag can be either None or string.

    """

    def __init__(self):
        self.lines = []

    def add(self,
            var=None, src=None,
            cls=None, args=None, call=None):
        line = ""
        if var:
            line += f'{var} = '
        if src:
            line += f'{src}.'
        if cls:
            line += f'{cls}({args})'
        if call:
            line += f'({call})'

        debug('[Line] +', line)
        self.lines.append(line)

    def get(self):
        # Make lines to a context.
        return self.lines


class PyParser:
    """ Parse XML file to PY lines. """

    def __init__(self, src_path: str):
        self.content = etree.parse(src_path)
        self.phs_hub = PlaceHolderHub()
        # This is the tag <ph>, not same as the one above.
        self.phs_tag = []
        self.rtn_mod = []
        self.src_dir = set()
        self.lines = PyLines()
        # May have multi-entrance.
        entrance = self.get_elm_by_attr(ATTR_START,
                                        ATTR_START_VALUE)
        # Entrance Error
        if not entrance:
            raise PyEntranceError()
        # Getting started.
        for cur_item in entrance:
            self.cur_item = cur_item
            self.line_handler()

    def commit(self):
        return self.lines.get(), self.phs_tag, self.src_dir, self.rtn_mod

    # ------------------------------------
    #           Basic Operation
    # ------------------------------------

    def get_elm_by_attr(self, attr, args, node=None):
        # Usually element only has two attributes:
        # one is id, the other is start. ID is one and only.
        # Making node.py optional, sometimes it's necessary to add constraint.
        if node is None:
            res = self.content.xpath(f'//*[@{attr}="{args}"]')
        else:
            res = self.content.xpath(f'//{node}[@{attr}="{args}"]')
        # Return the unpack the list.
        return res

    @classmethod
    def get_node_value_in_elm(cls, element, node, raw=False):
        # Return type has different forms:
        # Form 1: string
        # Form 2: ["string1", "string2", ...]
        # Form 3: [string] (raw)
        try:
            res = element.xpath(f'{node}/text()')[0]
        # If got nothing, return None.
        except IndexError:
            return None
        # Convert it from etree unicode to string.
        res = str(res)
        if len(res.split(IO_SPLIT)) != 1:
            return res.split(IO_SPLIT)
        else:
            return [res] if raw else res

    def get_batch_node_value(self, element, *nodes):
        # Get node.py value from element in batch,
        # but without raw format.
        results = []
        for node in nodes:
            results.append(self.get_node_value_in_elm(element, node))
        return results

    def get_node_value_by_id(self, id_: list, node):
        # First select node.py by id, then get node.py value.
        # But this function can do batch operation.
        res = []
        for i in id_:
            n = self.get_elm_by_attr(ATTR_ID, i)[0]
            r = self.get_node_value_in_elm(n, node)
            res.append(r)
        if len(res) == 1:
            return res[0]
        else:
            return "[" + ", ".join(t for t in res) + "]"

    @classmethod
    def get_args_by_elm(cls, element, passing=None):
        # Get all the <attrs> node.py that in element.
        attrs = {}
        attrs_n = element.xpath(f'{TAG_ARGS}//*')
        attrs_v = element.xpath(f'{TAG_ARGS}//*/text()')
        attrs_c = element.xpath(f'{TAG_ARGS}//*/@{ATTR_ARG_CLS}')
        for n, c, v in zip(attrs_n, attrs_c, attrs_v):
            if passing and v == passing:
                continue
            attrs[n.tag] = [ArgItem(item, c)
                            for item in v.split(IO_SPLIT)]
        # Some node.py don't have any attrs, so return a null string.
        return attrs if attrs else ''

    def get_args_by_id(self, id_):
        # First select the element by id.
        # Then get arguments from that element.
        elm = self.get_elm_by_attr(ATTR_ID, id_)[0]
        atr = self.get_args_by_elm(elm)
        return atr

    def get_tag_by_id(self, id_, value=False):
        # Get the tag name by its id. If the element
        # have single value, activate value to get it.
        elm = self.get_elm_by_attr(ATTR_ID, id_)[0]
        if value:
            val = elm.xpath('./text()')[0]
            return elm.tag, val
        return elm.tag

    # ------------------------------------
    #            Parser Handler
    # ------------------------------------

    def line_handler(self):
        """ Main handler. """

        # Those which node.py has attr 'head="true"' will be enter.
        # Also these node.py have null <input>, unlike CA mode.
        var_nm, cls_nm = self.get_batch_node_value(self.cur_item,
                                                   TAG_VNM, TAG_CLS)
        args = self.args_handler(self.cur_item)
        src = self.src_handler(self.cur_item)
        cur_id = self.cur_item.xpath(f'@{ATTR_ID}')[0]
        self.lines.add(var=var_nm,
                       src=src,
                       cls=cls_nm,
                       args=args)
        self.clue_handler(self.cur_item, var_nm, cur_id)

    def clue_handler(self, element, var_nm, cur_id):
        """ Parse the clue by DFS. """

        # Start with element, end with model.
        output_ids = self.get_node_value_in_elm(element, L_TAG_OUTPUT, raw=True)
        for output_id in output_ids:
            nxt_elm = self.get_elm_by_attr(ATTR_ID, output_id)[0]
            nxt_var, nxt_cls = self.get_batch_node_value(nxt_elm,
                                                         TAG_VNM, TAG_CLS)
            # Making attributes to a valid line.
            if nxt_cls == TAG_MODEL_CLS_VALUE:
                # Endpoint case.
                self.model_handler(cur_id, output_id)
            else:
                nxt_ipt = self.get_node_value_in_elm(nxt_elm, L_TAG_INPUT)
                nxt_arg = self.args_handler(nxt_elm)
                nxt_src = self.src_handler(nxt_elm)
                # One input case.
                if cur_id == nxt_ipt:
                    self.lines.add(var=nxt_var,
                                   src=nxt_src,
                                   cls=nxt_cls,
                                   args=nxt_arg,
                                   call=var_nm)
                    self.clue_handler(nxt_elm, nxt_var, output_id)
                # Multi-input case.
                elif cur_id in nxt_ipt:
                    ok = self.node_handler(cur_id, output_id)
                    if ok:
                        res_var_nm = self.get_node_value_by_id(ok, TAG_VNM)
                        self.lines.add(var=nxt_var,
                                       src=nxt_src,
                                       cls=nxt_cls,
                                       args=nxt_arg,
                                       call=res_var_nm)
                        self.clue_handler(nxt_elm, nxt_var, output_id)

    def node_handler(self, src_id, dst_id):
        """ Node handler: setup and check input to go. """

        element = self.get_elm_by_attr(ATTR_ID, dst_id)[0]

        if self.phs_hub.contains(dst_id):
            node = self.phs_hub.get(dst_id)
            node.gain(src_id)
            # Check to make sure can release.
            if node.check():
                return node.ep_ipt
        else:
            # Setup a new one and put into placeholder.
            ph = NodePlaceHolder(dst_id)
            ph.var_nm, ph.cls_nm, ph.ep_ipt, ph.ep_opt = \
                self.get_batch_node_value(element,
                                          TAG_VNM, TAG_CLS,
                                          L_TAG_INPUT, L_TAG_OUTPUT)
            ph.gain(src_id)
            self.phs_hub.put(ph)

    def model_handler(self, src_id, dst_id):
        """ Model handler: setup and check to go. """

        elem = self.get_elm_by_attr(ATTR_ID, dst_id)[0]
        args = self.get_args_by_elm(elem)

        if self.phs_hub.contains(dst_id):
            # Find out and check to make line.
            model = self.phs_hub.get(dst_id)
            model.gain(src_id)
            if model.check():
                res_src = self.src_handler(elem)
                res_args = self.args_handler(args)
                self.lines.add(var=model.var_nm,
                               cls=model.cls_nm,
                               src=res_src,
                               args=res_args)
                self.rtn_mod.append(model.var_nm)
        else:
            # Setup a new one and put into placeholder.
            ph = ModelPlaceHolder(dst_id)
            ph.var_nm, ph.cls_nm = self.get_batch_node_value(elem,
                                                             TAG_VNM, TAG_CLS)
            ph.ep_ipt, ph.ep_opt = [v.v for v in args[M_TAG_INPUT]],\
                                   [v.v for v in args[M_TAG_OUTPUT]]
            ph.gain(src_id)
            self.phs_hub.put(ph)

    def args_handler(self, argv):
        """ Arguments handler: make args to a valid string.

        @:param argv: could be an arg dict or element.

        """
        if isinstance(argv, dict):
            ad = argv
        else:
            ad = self.get_args_by_elm(argv)

        # null args element got nothing but blank space.
        if ad == '':
            return ad
        # for those element which has args.
        lines = []
        for k, vs in ad.items():
            line = self.type_handler(vs)
            if len(line) == 1:
                lines.append(f"{k}={line[0]}")
            else:
                lines.append(f"{k}=[" + ", ".join(
                         l for l in line) + "]")
        return ", ".join(l for l in lines)

    def type_handler(self, args: list):
        """ Handle the argument by its type. """
        lines = []

        for arg in args:
            # Now the special treat attr's type have:
            # [str, id, ]
            if arg.c == ATTR_ARG_CLS_VALUE_STR:
                lines.append(f'"{arg}"')
            elif arg.c == ATTR_ARG_CLS_VALUE_ID:
                # id may be the different element.
                tag = self.get_tag_by_id(arg)
                if tag == TAG_PLACEHOLDER:
                    self.ph_type_support(arg, lines)
                elif tag == TAG_LAYER:
                    self.layer_type_support(arg, lines)
                elif tag == TAG_UNIT:
                    self.unit_type_support(arg, lines)
            else:
                lines.append(f'{arg}')

        return lines

    def src_handler(self, elm):
        """ Handle the source of the element's class. """
        tag = elm.tag
        if tag == TAG_MODEL:
            res = TAG_MODEL_SRC
        elif tag == TAG_UNIT:
            res = elm.xpath(f'@{ATTR_UNIT}')[0]
        else:
            res = TAG_LAYER_SRC
        self.src_dir.add(res)
        return res

    # ------------------------------------
    #         Component & Support
    # ------------------------------------

    def gv_mv_cv(self, elm):
        """ This is a procedure that
        first Get var, if fail, return;
        if get, then Make line about var;
        finally return the var as a Callable obj.

        Will work only the element which has
        both <class> and <var>, also with <args>.

        """
        var = self.get_node_value_in_elm(elm, TAG_VNM)
        cls = self.get_node_value_in_elm(elm, TAG_CLS)
        arg = self.get_args_by_elm(elm)
        src = self.src_handler(elm)

        if arg != '':
            arg = self.args_handler(arg)
        if var is None:
            return f'{src}.{cls}({arg})'
        self.lines.add(var=var, src=src,
                       cls=cls, args=arg)
        return var

    def unit_type_support(self, id_, collector: list):
        """ Support for <unit> in type handler"""
        elm = self.get_elm_by_attr(ATTR_ID, id_)[0]
        collector.append(self.gv_mv_cv(elm))

    def ph_type_support(self, id_, collector: list):
        """ Support for <ph>(placeholder) in type handler. """

        # This <ph> is not same ph in this test_p, it's a tag.
        _, value = self.get_tag_by_id(id_, value=True)
        # The tag finally goes into test_p,
        # it will be parse to the attr of class.
        self.phs_tag.append(value)
        collector.append(f'self.{value}')

    def layer_type_support(self, id_, collector: list):
        """ Support for <layer> in type handler. """

        elm = self.get_elm_by_attr(ATTR_ID, id_)[0]
        mode = self.get_node_value_in_elm(elm, TAG_MODE)
        # Only IO, AC node will be added in lines.
        if mode in (TAG_MODE_VALUE_IO, TAG_MODE_VALUE_AC):
            var_nm = self.get_node_value_in_elm(elm, TAG_VNM)
            collector.append(f'{var_nm}')
        # For CA node just grab class name and args.
        elif mode == TAG_MODE_VALUE_CA:
            collector.append(self.gv_mv_cv(elm))
        # Besides IO and CA, is AC, the only one accept CA.
        else:
            pass


class PyHandler:
    """ Organize PY line to PY file. """

    TAB = 4
    SAFE = 80

    def __init__(self,
                 parser: PyParser,
                 model_name: str = 'Model',
                 author: str = None,
                 comment: str = None):
        self.parser = parser
        self.title = model_name.capitalize()
        self.author = author.capitalize()
        self.comment = comment
        self.time = time.strftime('%y/%m/%d',
                                  time.localtime(time.time()))

        (self.lines,
         self.phs,
         self.src,
         self.rtn) = self.parser.commit()
        # record .py code content.
        self.contents = []

    def brk(self, n=1):
        self.add(* [''] * n)

    def tab(self, weight):
        return self.TAB * weight * ' '

    def add(self, *args):
        self.contents += args

    def make_declare(self):
        self.add(
            "# -*- coding: utf-8 -*-",
            "# ",
            "# {}.py".format(self.title.lower()),
            "# Created by {} on {}".format(self.author, self.time),
            "# "
            "# Model: {} was built with Karken: KMB".format(self.title),
            "# A Keras Model Builder Tool.",
            "# "
        )
        self.brk()

    def make_import(self):
        for src in self.src:
            self.add(f'from keras import {src}')
        self.brk(2)

    def make_class(self):
        # Make the lines about class and __init__.
        self.add(f'class {self.title}:')
        self.brk()
        self.add(self.tab(1) +
                 f'def __init__(self, '
                 f'{ ", ".join(ph for ph in self.phs) }'
                 f'):')
        if len(self.phs):
            self.add(*[self.tab(2) +
                       f'self.{ph} = {ph}'
                       for ph in self.phs])
        else:
            self.add('pass')
        # Make a break line.
        self.brk()

    def make_build(self):
        # Make the build method for model.
        self.add(self.tab(1) +
                 'def build(self):')
        self.add(*[self.tab(2) + line
                   for line in self.lines])
        self.brk()
        self.add(self.tab(2) +
                 f"return {', '.join(m for m in self.rtn)}")

    def wrapper_lines(self):
        # Warp the line inside SAFE zone.
        for i, line in enumerate(self.contents):
            if len(line) <= self.SAFE:
                continue

    def organize(self):
        self.make_declare()
        self.make_import()
        self.make_class()
        self.make_build()
        # self.wrapper_lines()

    def export(self, dst):
        self.organize()
        with open(dst, 'w') as py:
            cnt = ''
            for line in self.contents:
                cnt += (line + '\n')
            py.write(cnt)


"""if __name__ == '__main__':
    parse = PyParser("test_save.xml")
    ctt = PyHandler(parse)
    ctt.export('test_sss.py')"""
