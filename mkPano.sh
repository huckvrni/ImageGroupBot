pto_gen -o %outPto %imgs
pano_modify --hdr-file=TIF --ldr-file=JPG -o %outPto %outPto
hugin_executor -a %outPto
hugin_executor -p %outImg -s %outPto
