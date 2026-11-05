//
// Segment stitched (and optionally background-subtracted) MACSima images
// with one or more segmentation tools selected via --segmentation
//

include { CELLPOSE3       } from '../../../modules/local/cellpose3/main'
include { CELLPOSE        } from '../../../modules/nf-core/cellpose/main'
include { DEEPCELL_MESMER } from '../../../modules/nf-core/deepcell/mesmer/main'

workflow MACSIMA_SEGMENTATION {

    take:
    ch_image        // channel: [ val(meta), path(image.ome.tif) ]
    val_methods     // list   : selected segmentation tools, e.g. [ 'cellpose3', 'cellpose4', 'mesmer' ]

    main:
    ch_masks = channel.empty()

    // Model selection for cellpose3 / cellpose4:
    //  - custom model file set -> the file is staged and passed to the module as path(model) input
    //  - no custom model       -> [] (no file); the pretrained model name (--cellpose*_pretrained_model)
    //                             is passed as '--pretrained_model <name>' via ext.args in conf/modules.config.
    //                             A name cannot go through path(model), Nextflow would try to stage it as a file.
    // A value channel is used so the model is reused for every image (a queue channel would be consumed after one task).

    if ( 'cellpose3' in val_methods ) {
        ch_cellpose3_model = params.cellpose3_custom_model
            ? channel.value( file(params.cellpose3_custom_model, checkIfExists: true) )
            : channel.value( [] )

        CELLPOSE3 ( ch_image, ch_cellpose3_model )
        ch_masks = ch_masks.mix(
            CELLPOSE3.out.mask.map { meta, mask -> [ meta + [ segmentation: 'cellpose3' ], mask ] }
        )
    }

    if ( 'cellpose4' in val_methods ) {
        ch_cellpose4_model = params.cellpose4_custom_model
            ? channel.value( file(params.cellpose4_custom_model, checkIfExists: true) )
            : channel.value( [] )

        CELLPOSE ( ch_image, ch_cellpose4_model )
        ch_masks = ch_masks.mix(
            CELLPOSE.out.mask.map { meta, mask -> [ meta + [ segmentation: 'cellpose4' ], mask ] }
        )
    }

    if ( 'mesmer' in val_methods ) {
        // nuclear and membrane channels are selected from the same multichannel image via ext.args,
        // so the separate membrane image input stays empty
        DEEPCELL_MESMER ( ch_image, [ [:], [] ] )
        ch_masks = ch_masks.mix(
            DEEPCELL_MESMER.out.mask.map { meta, mask -> [ meta + [ segmentation: 'mesmer' ], mask ] }
        )
    }

    emit:
    masks = ch_masks    // channel: [ val(meta + [ segmentation: tool ]), path(mask.tif) ]
}
