// Focused check using the original registration inputs; does not overwrite the old artifact.
include { STAINWARPY_REGISTER } from '../modules/local/stainwarpy/register/main'
workflow {
    STAINWARPY_REGISTER(Channel.of([
        [id:'SAMPLE_1_exp2'],
        file('/home/ubuntu/Caro/work/b8/f06ebd42316cc4037cdd65457e8089/SAMPLE_1_exp2_multiplexed_single_channel_img.ome.tif', checkIfExists:true),
        file('/home/ubuntu/Caro/hne_crop/20241031_CRC027_crop.ome.tif', checkIfExists:true)
    ]))
}
