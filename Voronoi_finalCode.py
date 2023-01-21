from tkinter import HORIZONTAL
from PySide2 import QtCore,QtGui,QtWidgets
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
import random as random
import math as math


def maya_main_window():
    main_window_ptr= omui.MQtUtil.mainWindow()
    return wrapInstance (int(main_window_ptr), QtWidgets.QWidget)
    
class VoronoiDialog(QtWidgets.QDialog):
 
    def __init__(self,parent=maya_main_window()):
        super().__init__(parent)
        self.setWindowTitle('Voronoi Fractures')
        self.setMinimumWidth(400)
        self.setMinimumHeight(100)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.create_widgets()
        self.create_layout()
        self.connections()
        
    def create_widgets(self):
       
        self.apply_btn = QtWidgets.QPushButton('Apply')
        self.close_btn = QtWidgets.QPushButton('Close')
        self.distribution = QtWidgets.QComboBox()
        self.distribution.addItems(['Random Distribution', 'Impact Based Distribution'])
        # self.density_slider = QtWidgets.QSlider()
        self.density = QtWidgets.QSpinBox()
        self.density.setFixedWidth(80)
        self.density.setMinimum(0)
        self.density.setMaximum(100)
        
        
    def create_layout(self):
        
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow('Distribution: ', self.distribution)
        form_layout.addRow ('Density', self.density)

        
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.close_btn)
        
        
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout) 
        
    def connections(self):
        pass
        self.apply_btn.clicked.connect(self.combo_selection)
        self.close_btn.clicked.connect(self.close) 

    
    def combo_selection(self):
        if self.distribution.currentText == 'Random Distribution':
            self.voroBasic()
            
        else:
            self.voroLocal()
            
    #basic voronio fracture
    def voroBasic(self):

        density = self.density.value()
        selection = cmds.ls( selection = True )
        seeds = []        

        if len( selection ) == 1:
            shape = selection[0]
            bbox = cmds.exactWorldBoundingBox( shape )

            for i in range(density):
                seed = cmds.spaceLocator( p = ( 0, 0, 0), a = True )[0]
                cmds.move( random.uniform( bbox[0], bbox[3] ), random.uniform( bbox[1], bbox[4] ), random.uniform( bbox[2], bbox[5] ), a = True )
                cmds.scale( 0.1, 0.1, 0.1, a = True, ocp = True )
                seeds.append( seed )

            for i in range ( 0, len(seeds)):

                shapeCopy = cmds.duplicate( shape ) 

                for j in range ( 0, len(seeds)):

                    if i != j:

                        self.voronoiFracture( i, j, seeds, shapeCopy )

            cmds.select( shape )
            cmds.delete()

            cmds.select( *seeds )
            cmds.delete()

        elif( len( selection ) > 1 ):
            print( 'error: please select only 1 object' )

        else:
            print( 'error: please select an object' )   

    #voronoi fracture around a vertex
    def voroLocal(self):
        
        density = self.density.value()
        density = density * 10
        selectedVerts = cmds.ls( sl = True )
        selectedMesh = selectedVerts[0].split('.')
        seeds = []        
         
        if len( selectedVerts ) == 1:
            shape = selectedVerts[0]
            bbox = cmds.exactWorldBoundingBox( selectedMesh[0] )
            
            for i in range( density ):
                vtx = cmds.xform( selectedVerts[0], q = True, ws = True, t = True )
                seed = cmds.spaceLocator( p = ( 0, 0, 0), a = True )[0]
                cmds.move( random.uniform( vtx[0] - 0.1, vtx[0] + 0.1 ), random.uniform( vtx[1] - 0.1, vtx[1] + 0.1 ), random.uniform( vtx[2] - 0.1, vtx[2] + 0.1 ), a = True )
                cmds.scale( 0.1, 0.1, 0.1, a = True, ocp = True )
                
                seedL = cmds.xform( seed, q = True, ws = True, t = True )
                
                if( seedL[0] > bbox[0] and seedL[0] < bbox[3] and seedL[1] > bbox[1] and seedL[1] < bbox[4] and seedL[2] > bbox[2] and seedL[2] < bbox[5] ): 
                    seeds.append( seed )
                
                else:
                    cmds.select( seed )
                    cmds.delete()
            
            
            print(len(seeds))    
            for i in range ( 0, len(seeds)):
                
                meshCopy = cmds.duplicate( selectedMesh[0] ) 
                
                for j in range ( 0, len(seeds)):
                        
                    if i != j:
                        
                        self.voronoiFracture( i, j, seeds, meshCopy )
                        
            cmds.select( selectedMesh[0] )
            cmds.delete()
            
            cmds.select( *seeds )
            cmds.delete()
            
        elif( len( selection ) > 1 ):
            print( 'error: please select only 1 vertex' )
            
        else:
            print( 'error: please select a vertex' )

    def voronoiFracture( self, i, j, seeds, shapeCopy ):

        p1 = cmds.xform( seeds[j], q = True, ws = True, t = True )
        p2 = cmds.xform( seeds[i], q = True, ws = True, t = True )   

        #cutting position
        planePos = self.getVecPoint( p1, p2, 0.5 )

        #calculate unit vector
        vec = self.getVector( p1, p2 )
        vecMag = self.magnitude( vec )

        vecNorm = [ 0, 0, 0 ]
        vecNorm[0] = vec[0] / vecMag 
        vecNorm[1] = vec[1] / vecMag 
        vecNorm[2] = vec[2] / vecMag 

        #calculate cutting angles
        rX = -math.degrees( math.asin( vecNorm[1]))
        rY = math.degrees( math.atan2( vecNorm[0], vecNorm[2] ))

        #cut the shape
        cmds.select( shapeCopy )    
        cmds.polyCut( constructionHistory = False, deleteFaces = True, pc = planePos, ro = ( rX, rY, 0 ) )
        cmds.polyCloseBorder( constructionHistory = False )

    #calculate a vector from two points    
    def getVector(self,  pointA, pointB ):
    
        vec = [0, 0, 0]
    
        vec[0] = pointB[0] - pointA[0]
        vec[1] = pointB[1] - pointA[1]
        vec[2] = pointB[2] - pointA[2]
    
        return vec
    
    #calculate the magnitude of a vector
    def magnitude(self, vec ):
    
        mag = ( vec[0] ** 2 ) + ( vec[1] ** 2 ) + ( vec[2] ** 2 )
        mag = mag ** 0.5
    
        return mag
    
    #calculate a point on a line
    def getVecPoint(self, pointA, pointB, pos ):
    
        point = [ 0, 0, 0 ]
    
        point[0] = pointA[0] + ( pos * ( pointB[0] - pointA[0] ))
        point[1] = pointA[1] + ( pos * ( pointB[1] - pointA[1] ))
        point[2] = pointA[2] + ( pos * ( pointB[2] - pointA[2] ))
    
        return point  
    

    

if __name__ == '__main__':
    try:
        voronoi_fractures.close()
        voronoi_fractures.Deletelater()
    except:
        pass
            
    voronoi_fractures = VoronoiDialog()
    voronoi_fractures.show()