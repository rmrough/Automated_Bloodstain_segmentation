from PyQt5 import QtCore, QtGui, QtWidgets


class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        self.highlight = QtWidgets.QGraphicsRectItem()
        self._scene.addItem(self.highlight)
        self.annotation_items = QtWidgets.QGraphicsItemGroup()

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if self.hasPhoto():
            factor = 1
            
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            elif event.angleDelta().y() < 0:
                factor = 0.8
                self._zoom -= 1

            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0


    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(QtCore.QPoint(event.pos()))
        super(PhotoViewer, self).mousePressEvent(event)

    def add_rectangle(self, x, y, width, height):
        self.highlight.setRect(x, y, width, height)
        penRectangle = QtGui.QPen(QtCore.Qt.blue)
        penRectangle.setWidth(3)
        self.highlight.setPen(penRectangle)
        
        self.fitInView()
        self._zoom = 5
        self.scale(5 * 1.25, 5*1.25)
        self.centerOn(x, y)

    def add_text(self, stain, text):
        text = QtWidgets.QGraphicsTextItem(str(text))
        font = QtGui.QFont()
        font.setPointSize(30)
        text.setFont(font)
        text.setDefaultTextColor(QtCore.Qt.yellow)
        text.setX(stain.position[0])
        text.setY(stain.position[1])
        return text

    def add_outline(self, stain):
        poly = QtGui.QPolygonF()
        for pt in stain.contour.tolist():
            poly.append(QtCore.QPointF(*pt[0]))
        outline = QtWidgets.QGraphicsPolygonItem(poly)
        pen = QtGui.QPen(QtCore.Qt.magenta)
        pen.setWidth(3)
        outline.setPen(pen)
        return outline

    def add_direction_line(self, stain):
        if stain.major_axis:
            poly = QtGui.QPolygonF()
            poly.append(QtCore.QPointF(*stain.major_axis[0]))
            poly.append(QtCore.QPointF(*stain.major_axis[1]))
            line = QtWidgets.QGraphicsPolygonItem(poly)
            pen = QtGui.QPen(QtCore.Qt.darkBlue)
            pen.setWidth(2)
            line.setPen(pen)
            return line

    def add_center(self, stain):
        center = QtWidgets.QGraphicsEllipseItem(stain.position[0], stain.position[1], 1, 1)
        pen = QtGui.QPen(QtCore.Qt.white)
        pen.setWidth(3)
        center.setPen(pen)
        return center

    def add_ellipse(self, stain):
        if stain.ellipse != None:
            ellipse = QtWidgets.QGraphicsEllipseItem(stain.x_ellipse - (stain.width / 2), stain.y_ellipse - (stain.height / 2), stain.width, stain.height)
            ellipse.setTransformOriginPoint(QtCore.QPointF(stain.x_ellipse, stain.y_ellipse ))
            ellipse.setRotation(stain.angle)
            pen = QtGui.QPen(QtCore.Qt.green)
            pen.setWidth(3)
            ellipse.setPen(pen)
            return ellipse

    def add_annotations(self, annotations, pattern):
        self._scene.removeItem(self.annotation_items)
        self._scene.update()

        items = []

        for stain in pattern.stains:
            text = ""
            if annotations['outline']:
                items.append(self.add_outline(stain))
            if annotations['ellipse']:
                items.append(self.add_ellipse(stain))
            if annotations['id']:
                text += str(stain.id)
            if annotations['directionality']:
                text += " " + str(stain.direction())
            if annotations['center']:
                items.append(self.add_center(stain))
            if annotations['gamma']:
                text += " " + str(stain.orientaton()[1])
            if annotations['direction_line']:
                items.append(self.add_direction_line(stain))

            items.append(self.add_text(stain, text))

        self.annotation_items = self._scene.createItemGroup(
                [item for item in items if item is not None])
