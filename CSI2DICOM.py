# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 20:27:24 2017

@author: christian
"""
import numpy as np
import numpy.matlib
import re
import dicom
from operator import truediv
import copy
from argparse import ArgumentParser
import os.path
from dicom.UID import UID, generate_uid, pydicom_root_UID, InvalidUID

# Inputs
parser = ArgumentParser(description="ikjMatrix multiplication")
parser.add_argument("-CSIdicom", dest="CSI_PATH", required=True,
    help="CSI input file path", metavar="FILE")
parser.add_argument("-MRIdicom", dest="MRI_PATH", required=True,
    help="MRI input file path", metavar="FILE")
parser.add_argument("-CSIname", dest="CSI", required=True,
    help="MRI input file path", metavar="FILE")

args = parser.parse_args()

print "is CSI dicom header input file valid:"
print os.path.exists(args.CSI_PATH)
print "is MRI dicom header input file valid:"
print os.path.exists(args.MRI_PATH)


file=open(args.CSI_PATH, 'r')
a=file.read()


output=args.CSI
# Read image position patient

IPP_loc=a.find('ImagePositionPatient')
IPP=re.findall(r"[-+]?\d*\.\d+|\d+", a[IPP_loc:IPP_loc+300])
IPP=map(float,IPP)
IPP=IPP[0:3]


# read matrix size

matrix_size_1_loc =a.find('sSpecPara.lFinalMatrixSizePhase')
matrix_dim=re.findall(r"[-+]?\d*\.\d+|\d+", a[matrix_size_1_loc:matrix_size_1_loc+300])
matrix_dim=map(float,matrix_dim)
matrix_dim=matrix_dim[0:2]
print 'The matrix dimensions of the CSI image is:'
print matrix_dim

if matrix_dim[0]!=matrix_dim[1]:
    print 'warning matrix dimensions of CSI image does not agree'
    
MheaderORG = dicom.read_file(args.MRI_PATH)
CSIheaderORG = dicom.read_file(args.CSI_PATH)


Mheader=copy.copy(MheaderORG)

CSIheader=copy.copy(MheaderORG)

# Find phase encoding direction

phase_direction=MheaderORG.InplanePhaseEncodingDirection

if phase_direction== 'COL':
    FOV_loc2=a.find('sSpecPara.sVoI.dPhaseFOV')
    FOV_loc1=a.find('sSpecPara.sVoI.dReadoutFOV')
    print "Phase encoding direction is in column direction"
else:
    FOV_loc1=a.find('sSpecPara.sVoI.dPhaseFOV')
    FOV_loc2=a.find('sSpecPara.sVoI.dReadoutFOV')
    print "Phase encoding direction is in row direction"



# Localize FOV
#FOV_loc2=a.find('sSpecPara.sVoI.dPhaseFOV')
#FOV_loc1=a.find('sSpecPara.sVoI.dReadoutFOV')
FOV_loc3=a.find('sSpecPara.sVoI.dThickness')

FOV1=re.findall(r"[-+]?\d*\.\d+|\d+", a[FOV_loc1:FOV_loc1+300])
FOV1=map(float, FOV1)
FOV1=FOV1[0]
FOV2=re.findall(r"[-+]?\d*\.\d+|\d+", a[FOV_loc2:FOV_loc2+300])
FOV2=map(float, FOV2)
FOV2=FOV2[0]
FOV3=re.findall(r"[-+]?\d*\.\d+|\d+", a[FOV_loc3:FOV_loc3+300])
FOV3=map(float, FOV3)
FOV3=FOV3[0]

FOV=[FOV1,FOV2,FOV3]
print 'The field of view in CSI is:'
print FOV


# Add files from Mheader

fields=len(Mheader)
for iterator in range(fields):
    keynum=Mheader.keys()[iterator]
    mystring=Mheader[keynum]
    try:
        CSIheader[keynum]
    except KeyError:  
        CSIheader.add_new(mystring.tag, mystring.VR, mystring.value)

# add specific pixel spacing and slice thickness 
PixelSpacing=map(truediv,FOV[0:2],matrix_dim)
PixelSpacing=map(float,PixelSpacing)
CSIheader.PixelSpacing=PixelSpacing
CSIheader.SliceThickness=int(FOV3)
CSIheader.SeriesDescription='CSI_dicom'
#############################################33
#### Calculate IPP
############################################

## Calculate worlds coordinates
IoP_mat=np.matrix([[float(MheaderORG.ImageOrientationPatient[0]),float(MheaderORG.ImageOrientationPatient[3])],
[float(MheaderORG.ImageOrientationPatient[1]),float(MheaderORG.ImageOrientationPatient[4])],
[float(MheaderORG.ImageOrientationPatient[2]),float(MheaderORG.ImageOrientationPatient[5])]])
    
IOP=np.concatenate((IoP_mat, np.array([[0,0]])), axis=0)
IOP=np.concatenate((IOP, np.array([[0],[0],[0],[0]])), axis=1)
Vox_dim=np.concatenate((np.matlib.repmat(MheaderORG.PixelSpacing[0],3,1),np.matlib.repmat(MheaderORG.PixelSpacing[1],3,1)),axis=1)
Vox_dim=np.concatenate((Vox_dim,np.array([[0,0]])),axis=0)
Vox_dim=np.concatenate((Vox_dim, np.array([[0],[0],[0],[0]])), axis=1)
Matrix=np.concatenate((np.multiply(Vox_dim, IOP),np.array([[float(MheaderORG.ImagePositionPatient[0])],
                       [float(MheaderORG.ImagePositionPatient[1])],[float(MheaderORG.ImagePositionPatient[2])],[1]])),axis=1)

i=np.linspace(0, MheaderORG.Columns-1, num=MheaderORG.Columns)
j=np.linspace(0, MheaderORG.Rows-1, num=MheaderORG.Rows)
vec= np.row_stack((i,j,np.zeros((1,MheaderORG.Columns)),np.ones((1,MheaderORG.Rows))))
coords=np.dot(Matrix,vec)

center=np.array([coords[0,(MheaderORG.Columns-1)/2+1],coords[1,(MheaderORG.Columns-1)/2+1],coords[2,(MheaderORG.Columns-1)/2+1]])
## Extract FOV i world coordiantes
[Xq1,Yq1,Zq1]=np.meshgrid(np.linspace(center[0]-np.divide(FOV[0],2),center[0]+np.divide(FOV[0],2),matrix_dim[0]),
np.linspace(center[1]-np.divide(FOV[1],2),center[1]+np.divide(FOV[1],2),matrix_dim[1]),np.linspace(center[2]-np.divide(FOV[2],2),center[2]+np.divide(FOV[2],2),matrix_dim[1]))

# Calculate center of mass

xc=np.divide(np.sum(Xq1[1,:,1]),matrix_dim[0])
yc=np.divide(np.sum(Yq1[:,1,1]),matrix_dim[1])
zc=np.divide(np.sum(Zq1[1,1,:]),matrix_dim[1])

xt=np.transpose(Xq1[1,:,1])-xc
yt=np.transpose(Yq1[:,1,1])-yc
zt=np.transpose(Zq1[1,1,:])-zc


rota=np.dot(IOP[0:3,0:3],np.row_stack((xt,yt,zt)))
rota2=np.array([np.matlib.repmat(xc,int(matrix_dim[0]),1),
                np.matlib.repmat(yc,int(matrix_dim[1]),1),
np.matlib.repmat(zc,int(matrix_dim[1]),1)])

rota2=np.squeeze(rota2, axis=(2,))#.shape
rota2=rota+rota2

IPP_cal=np.array([rota2[0,0],rota2[1,0],rota2[2,0]])

result=np.allclose(IPP, IPP_cal)
if result is None:
    print "WARNING - No correspondence between calculated ImagePositioPatient and readed ImagePositionPaiten"
elif result:
    print "Correspondence calculated between ImagePositioPatient and readed ImagePositionPaitens"
else:
    print "WARNING - No correspondence between calculated ImagePositioPatient and readed ImagePositionPaiten"

CSIheader.ImagePositionPatient=IPP

CSIheader.Rows=int(matrix_dim[0])
CSIheader.Columns=int(matrix_dim[1])


new_img=np.zeros((int(matrix_dim[0]),int(matrix_dim[1]))).astype('uint16')
print 'create CSI dicom image with zeros'


CSIheader[0x0028,0x0107].value = 4095
CSIheader[0x0028,0x0106].value = 4095
CSIheader[0x0028,0x0107].VR = 'US'
CSIheader[0x0028,0x0106].VR = 'US'
CSIheader[0x7fe0,0x0010].VR = 'OW'


#  Generate UID

n2=9


UIDnr2=CSIheader[0x0020,0x00e].value#[0:30

groups = UIDnr2.split('.')
UID_gen_prefix='.'.join(groups[:n2])+'.'#, '.'.join(groups[n:])


uid_gen_series=generate_uid(prefix=UID_gen_prefix, truncate=True)
print 'Generated UID series:'
print uid_gen_series
CSIheader[0x0020,0x00e].value=uid_gen_series
CSIheader[0x008,0x060].value='MR'
CSIheader[0x008,0x103e].value='CSI metabolite image'



def write_dicom(ds,pixel_array,filename):
    """
    INPUTS:
    pixel_array: 2D numpy ndarray.  If pixel_array is larger than 2D, errors.
    filename: string name for the output file.
    Image array are stored as uint16
    """

    ## These are the necessary imaging components of the FileDataset object.
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.HighBit = 15 #63
    ds.BitsStored = 16 #64
    ds.BitsAllocated = 16 #64
    #ds.SmallestImagePixelValue = '\\x00\\x00'
    #ds.LargestImagePixelValue = '\\xff\\xff'
    ds.Columns = pixel_array.shape[0]
    ds.Rows = pixel_array.shape[1]
    if pixel_array.dtype != np.uint16:
        pixel_array = pixel_array.astype(np.uint16)
#    if pixel_array.dtype != np.float64:
#        pixel_array = pixel_array.astype(np.float64)
    ds.PixelData = pixel_array.tostring()

    ds.save_as(filename)
    return
write_dicom(CSIheader, new_img, output)
#CSIheader.save_as(args.outputFolder+args.output)

print "CSI header saved as"
print output

