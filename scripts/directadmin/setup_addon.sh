#!/bin/sh

mkdir addons
pushd addons

# ffmpeg
wget http://netcologne.dl.sourceforge.net/project/ffmpeg-php/ffmpeg-php/0.6.0/ffmpeg-php-0.6.0.tbz2
tar xjf ffmpeg-php-0.6.0.tbz2
pushd ffmpeg-php-0.6.0
    phpize
    ./configure --enable-skip-gd-check --enable-shared --with-php-config=/usr/local/bin/php-config
    sed -i 's/PIX_FMT_RGBA32/PIX_FMT_RGB32/g' ffmpeg_frame.c
    make install
popd
# extension=ffmpeg.so

# imagick
wget http://pecl.php.net/get/imagick-3.1.2.tgz
tar xzf imagick-3.1.2.tgz
pushd imagick-3.1.2
    phpize
    ./configure --enable-shared --with-php-config=/usr/local/bin/php-config
    make install
popd
# extension=imagick.so

# eaccelerator
# https://github.com/eaccelerator/eaccelerator
# https://github.com/eaccelerator/eaccelerator/tarball/master
wget https://codeload.github.com/eaccelerator/eaccelerator/legacy.tar.gz/master -O eaccelerator.tar.gz
tar 
pushd eaccelerator-eaccelerator-42067ac
    phpize
    ./configure --enable-shared --with-php-config=/usr/local/bin/php-config
    make install
popd

popd # addons
rm -rf addons
