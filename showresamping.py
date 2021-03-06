# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 18:34:24 2017

@author: christian
"""

import numpy as np
import matplotlib
from matplotlib import pylab as plt
from argparse import ArgumentParser
import nibabel as nib


parser = ArgumentParser(description="show image resampled")
parser.add_argument("-PETraw", dest="PETraw_PATH", required=True,
    help="PET raw input file path", metavar="FILE")
args = parser.parse_args()

A = np.fromfile(args.PETraw_PATH, dtype='float64', sep="")
A = A.reshape([int(np.sqrt(len(A))), int(np.sqrt(len(A)))])


# show PET in CSI
plt.figure()
plt.title("Resampled PET in CSI space")
imgplot =plt.imshow(A, interpolation='none', cmap="hot")#,norm=mc.Normalize(vmin=np.min(A),vmax=np.max(A)))
clb = plt.colorbar()
clb.ax.set_title('Bq/ml')
plt.show()





