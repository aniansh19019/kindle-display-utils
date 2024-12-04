#!/bin/bash



docker run --rm -v $(pwd):/work -w /work arm32v7/debian     bash -c "
    apt-get update &&
    apt-get install -y gcc g++ libjpeg62-turbo-dev libpng-dev &&
    g++ -std=c++11 image_processor.cpp -o image_processor -lpng -ljpeg -static-libstdc++ -static-libgcc
    "