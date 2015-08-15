from Cython.Compiler import Pipeline, Visitor, ExprNodes, StringEncoding

import imp
import os

# Load the DAAP data. Cannot use normal import because setup.py will install
# dependencies after this file is imported.
daap_data = imp.load_source("daap_data", os.path.join(
    os.path.dirname(__file__), "../daapserver/daap_data.py"))


class DAAPObjectTransformer(Visitor.CythonTransform):
    """
    Convert all DAAPObject(x, y) into SpeedyDAAPObject(code[x], type[x], y).
    """

    def visit_CallNode(self, node):
        if isinstance(node.function, ExprNodes.NameNode) and \
                node.function.name == u"DAAPObject":

            # Make sure we only convert DAAPObject(x, y) calls, nothing more.
            if len(node.args) == 2:
                code = daap_data.dmap_names[node.args[0].value]
                itype = daap_data.dmap_code_types[code][1]

                node.function.name = self.context.intern_ustring(
                    u"SpeedyDAAPObject")
                node.args[0] = ExprNodes.StringNode(
                    node.pos, value=StringEncoding.BytesLiteral(code))
                node.args.insert(1, ExprNodes.IntNode(
                    node.pos, value=str(itype)))

        # Visit method body.
        self.visitchildren(node)

        return node


def install_new_pipeline():
    """
    Install above transformer into the existing pipeline creator.
    """

    def new_create_pipeline(context, *args, **kwargs):
        result = old_create_pipeline(context, *args, **kwargs)
        result.insert(1, DAAPObjectTransformer(context))

        return result

    old_create_pipeline = Pipeline.create_pipeline
    Pipeline.create_pipeline = new_create_pipeline
