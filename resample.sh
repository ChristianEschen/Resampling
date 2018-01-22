#!/bin/bash
#insert

# Iterate through input lines in text file
echo "Showing txt file by looping:"

IFS=","
echo "begin for"
for ((i=1;; i++)); do
    read "d$i" || break;
done < "$1"


#$d1=PET
#$d2=MRI at CSI time: 2D
#$d3= CSI img file (.dcm)
#$d4=interpolation (tricubic)

echo "d1"
echo "$d1"
echo "d2"
echo "$d2"
echo "d3"
echo "$d3"
echo "d4"
echo "$d4"



##################################### create valid CSI.dcm  header ###########################
CSIdicom="CSI_pseudo_dicom.dcm"
python CSI2DICOM_v2.py -MRIdicom $d2 -CSIdicom $d3 -CSIname $CSIdicom


########################################### Convert minc files ###########################################################
name=.mnc
echo "Convert PET DICOM header to MINC:"
# Converting PET dicom to minc
PET="PET"
dcm2mnc $d1  -dname '' -fname $PET . -usecoordinates -clobber
namePETminc=$PET$name


# Convert CSI header to MINC
echo "Convert pseudo CSI dicom header to MINC:"
CSI="CSI"
dcm2mnc $CSIdicom  -dname '' -fname $CSI . -usecoordinates -clobber
nameCSI=$CSI$name

############################################ Resampling ###################################################
# Resample PET to CSI
PET_resample_CSI="PET_resampled_CSI.mnc"
mincresample $namePETminc -like $nameCSI $PET_resample_CSI -$d4

########## Convert PET in CSI space to .raw #####################
PET_resampled_CSI_raw="PET_resampled_CSI_raw.raw"
minctoraw $PET_resample_CSI -nonormalize -double > $PET_resampled_CSI_raw

######### show resampling
python showresamping.py -PETraw $PET_resampled_CSI_raw