pto_gen -o %outPto %imgs
cpfind --celeste -o %outPto %outPto
cpclean --output=%outPto %outPto
linefind -o %outPto %outPto
pto_var --opt="y,p,r,TrX,TrY,TrZ,v,a,b,c,d" --output=%outPto %outPto
autooptimiser -n -l -m -s -o %outPto %outPto
vig_optimize -o %outPto %outPto
pano_modify --fov=AUTO -s -c --canvas=80% --crop=AUTO --output-type=N --ldr-file=JPG -o %outPto %outPto
hugin_executor -p %outImg -s %outPto
