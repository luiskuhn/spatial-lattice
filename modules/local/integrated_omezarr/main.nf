process INTEGRATED_OMEZARR {
    tag "$meta.id"
    label 'process_medium'
    container 'quay.io/spatial-lattice-omezarr:dev'
    input:
    tuple val(meta), path(macsima), path(mask), path(hne), path(native_hne), path(transform), path(metrics), path(markers)
    output:
    tuple val(meta), path("*.ome.zarr"), emit: store
    path("integrated_omezarr_mqc.json"), emit: qc
    script:
    """
    export XDG_CACHE_HOME=/tmp/ngff-cache
    integrate_omezarr.py --macsima '$macsima' --mask '$mask' --hne '$hne' \
        --native-hne '$native_hne' --transform '$transform' --metrics '$metrics' \
        --markers '$markers' --output '${meta.id}.ome.zarr'
    """
}
