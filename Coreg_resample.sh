
# Iterate through input lines in text file
echo "Showing txt file by looping:"

IFS=","
echo "begin for"
for ((i=1;; i++)); do
    read "d$i" || break;
done < "$1"

#$d1=MRI at PET time
#$d2=PET
#$d3=MRI at CSI time: 3D
#$d4=MRI at CSI time: 2D
#$d5=interpolation (tricubic)
#$d6= optimizer (lsq6)
#$d7= CSI img file (.dcm)
echo "d1"
echo "$d1"
echo "d2"
echo "$d2"
echo "d3"
echo "$d3"
echo "d4"
echo "$d4"
echo "d5"
echo "$d5"
echo "d6"
echo "$d6"
echo "d7"
echo "$d7"

##### create valid CSI.dcm  header ###########
CSIdicom="CSI_pseudo_dicom.dcm"
python CSI2DICOM_v2.py -MRIdicom $d4 -CSIdicom $d7 -CSIname $CSIdicom


########################################### Convert minc files ###########################################################
echo "Convert MRI at PET DICOM header to MINC:"

# Initialize suffix name for minx files
name=.mnc
# Converting MRI dicom at PET stage to minc
MRI_at_PET="MRI_at_PET"

dcm2mnc $d1  -dname '' -fname $MRI_at_PET . -usecoordinates -clobber
nameMRI_at_PETminc=$MRI_at_PET$name


echo "Convert PET DICOM header to MINC:"

# Converting PET dicom to minc

PET="PET"
dcm2mnc $d2  -dname '' -fname $PET . -usecoordinates -clobber
namePETminc=$PET$name

# Converting MRI dicim at CSI stage

echo "Convert MRI 3D at CSI DICOM header to MINC:"


MRI_at_CSI_3D="MRI_at_CSI_3D"
dcm2mnc $d3  -dname '' -fname $MRI_at_CSI_3D . -usecoordinates -clobber
nameMRI_at_CSI_3D_minc=$MRI_at_CSI_3D$name

# Converting MRI 2D at CSI
echo "Convert MRI 2D at CSI DICOM header to MINC:"
MRI_at_CSI_2D="MRI_at_CSI_2D"
dcm2mnc $d4  -dname '' -fname $MRI_at_CSI_2D . -usecoordinates -clobber
nameMRI_at_CSI_2D_minc=$MRI_at_CSI_2D$name


# Convert CSI header to MINC
echo "Convert pseudo CSI dicom header to MINC:"
CSI="CSI"
dcm2mnc $CSIdicom  -dname '' -fname $CSI . -usecoordinates -clobber
nameCSI=$CSI$name

######################## Perform Initial coregistration and resampling ###################

matrix_trans="trans_mat"
# Register
echo "Computing Registration:"
minctracc $nameMRI_at_PETminc $nameMRI_at_CSI_3D_minc $matrix_trans -$d6 -identity -est_center -clobber


ext=.xfm
nameTransMat=$matrix_trans$ext

# Naming output
outputname="PET_coreg_MRI_CSI_2D.mnc"
out3Dname="PET_coreg_MRI_CSI_3D.mnc"
out3DMRIname="MRI_PET_coreg_MRI_CSI_3D.mnc"
out2DMRIname="MRI_PET_coreg_MRI_CSI_2D.mnc"
PET_resampled_COREG_CSI="PET_resampled_COREG_CSI.mnc"

echo "Resample:"
# Resample PET to MRI at CSI 3D
mincresample $namePETminc -transformation $nameTransMat -like $nameMRI_at_CSI_3D_minc $out3Dname -$d5 -clobber



# Resample MRI images (for check)
mincresample $nameMRI_at_PETminc -transformation $nameTransMat -like $nameMRI_at_CSI_3D_minc $out3DMRIname -$d5 -clobber

# Resample PET to MRI 2D at CSI
mincresample $out3Dname -like $nameMRI_at_CSI_2D_minc $outputname -$d5 -clobber

# Resample MRI to slice
mincresample $out3DMRIname -like $nameMRI_at_CSI_2D_minc $out2DMRIname -$d5 -clobber

#################### Resample PET to CSI space ########################

mincresample $outputname -like $nameCSI $PET_resampled_COREG_CSI -$d5 -clobber


########## Convert PET in CSI space to .raw #####################
PET_resampled_COREG_CSI_raw="PET_resampled_COREG_CSI_raw.raw"
minctoraw $PET_resampled_COREG_CSI -nonormalize -double > $PET_resampled_COREG_CSI_raw

######### Generate valid PET dicom ######################
output_PET_res_dicom="PET_resampled_to_CSI_DICOM.dcm"
echo "Generate dicom"
python generate_dicom_v2.py -ResampledPETrawpath $PET_resampled_COREG_CSI_raw -CSIdicom_path $CSIdicom -PETdicom $output_PET_res_dicom
######### show resampling
python showresamping.py -PETraw $PET_resampled_COREG_CSI_raw

