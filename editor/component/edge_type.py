import math

from PyQt5.QtGui import QPainterPath
from PyQt5.QtCore import QPointF

from cfg import DIRS
from editor.graphic.node_edge import KMBGraphicEdge


class KMBGraphicEdgeDirect(KMBGraphicEdge):

    def calc_path(self):
        path = QPainterPath(QPointF(self.pos_src[0], self.pos_src[1]))
        path.lineTo(self.pos_dst[0], self.pos_dst[1])
        return path


class KMBGraphicEdgeBezier(KMBGraphicEdge):

    EDGE_CP_ROUNDNESS = 100

    def calc_path(self):
        s = self.pos_src
        d = self.pos_dst
        dist = (d[0] - s[0]) * 0.5

        cpx_s = +dist
        cpx_d = -dist
        cpy_s = 0
        cpy_d = 0

        if self.edge.start_socket is not None:
            sspos = self.edge.start_socket.position

            if (s[0] > d[0] and sspos in (DIRS["rt"], DIRS["rb"])) or\
               (s[0] < d[0] and sspos in (DIRS["lb"], DIRS["lt"])):
                cpx_d *= -1
                cpx_s *= -1
                cpy_d = ((s[1] - d[1]) / math.fabs(
                    (s[1] - d[1]) if (s[1] - d[1]) != 0 else 0.00001
                )) * self.EDGE_CP_ROUNDNESS
                cpy_s = ((d[1] - s[1]) / math.fabs(
                    (d[1] - s[1]) if (d[1] - s[1]) != 0 else 0.00001
                )) * self.EDGE_CP_ROUNDNESS

        path = QPainterPath(QPointF(self.pos_src[0], self.pos_src[1]))
        path.cubicTo(s[0] + cpx_s, s[1] + cpy_s, d[0] + cpx_d, d[1] + cpy_d, self.pos_dst[0], self.pos_dst[1])
        return path
