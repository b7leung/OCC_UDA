#!/bin/bash

cp /home/svcl-oowl/brandon/research/occ_uda/nautilus_prep/functional.py /opt/conda/envs/mesh_funcspace/lib/python3.6/site-packages/torchvision/transforms

cd ~
git clone https://github.com/b7leung/occ_uda.git
cd occ_uda
python setup.py build_ext --inplace
bash nautilus_prep/nautilus_prep.sh

python -u train.py configs/domain_adaptation/chair_DA_DANN.yaml
cp -r out/ /home/svcl-oowl/brandon/research/occ_uda
