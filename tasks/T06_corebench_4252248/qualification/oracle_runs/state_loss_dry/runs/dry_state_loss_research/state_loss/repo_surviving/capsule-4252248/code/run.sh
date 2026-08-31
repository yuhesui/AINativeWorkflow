#!/bin/bash
set -ex
ln -s ../results output
ln -s ../data Data
Rscript main-ctrpv.R
Rscript main-nci.R
Rscript main-network-generation.R