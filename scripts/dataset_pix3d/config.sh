ROOT=..

export MESHFUSION_PATH=$ROOT/external/mesh-fusion
export HDF5_USE_FILE_LOCKING=FALSE # Workaround for NFS mounts

INPUT_PATH=$ROOT/data/external/pix3d/model
#CHOY2016_PATH=$ROOT/data/external/Choy2016
BUILD_PATH=$ROOT/data/pix3d_testttt.build
OUTPUT_PATH=$ROOT/data/pix3d_processed

NPROC=12
TIMEOUT=180
N_VAL=100
N_TEST=100
N_AUG=50

declare -a CLASSES=(
chair
)

# Utility functions
lsfilter() {
 folder=$1
 other_folder=$2
 ext=$3

 for f in $folder/*; do
   filename=$(basename $f)
   if [ ! -f $other_folder/$filename$ext ] && [ ! -d $other_folder/$filename$ext ]; then
    echo $filename
   fi
 done
}
