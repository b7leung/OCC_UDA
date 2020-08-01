# prep datasets for nautilus jobs. This is supposed to be run in the base directory of the project
# in the pod's home directory

mkdir data
cd data

mkdir ShapeNet
cp /home/svcl-oowl/brandon/research/occ_uda/data/compressed_datasets/03001627.tar.gz ShapeNet
cd ShapeNet
tar -xzvf 03001627.tar.gz
rm 03001627.tar.gz
cd ..

cp /home/svcl-oowl/brandon/research/occ_uda/data/compressed_datasets/pix3d_processed.tar.gz .
tar -xzvf pix3d_processed.tar.gz
rm pix3d_processed.tar.gz

cp /home/svcl-oowl/brandon/research/occ_uda/data/compressed_datasets/target_domain.tar.gz .
tar -xzvf target_domain.tar.gz
rm target_domain.tar.gz

cd ..
