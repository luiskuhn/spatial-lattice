process CELLPOSE3 {
    tag "$meta.id"
    label 'process_low'

    container "docker.io/biocontainers/cellpose:3.0.1_cv1"

    input:
    tuple val(meta), path(image)
    path(model)

    output:
    tuple val(meta), path("*masks.tif") ,   emit: mask
    tuple val(meta), path("*flows.tif") ,   emit: flows, optional: true
    tuple val("${task.process}"), val('cellpose'), eval("cellpose --version | sed -n 's/cellpose version:[[:space:]]*//p' | tr -d '[:space:]'"), topic: versions, emit: versions_cellpose

    when:
    task.ext.when == null || task.ext.when

    script:
    // Exit if running this module with -profile conda / -profile mamba
    if (workflow.profile.tokenize(',').intersect(['conda', 'mamba']).size() >= 1) {
        error "I did not manage to create a cellpose module in Conda that works in all OSes. Please use Docker / Singularity / Podman instead."
    }
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    def model_command = model ? "--pretrained_model $model" : ""
    """
    export OMP_NUM_THREADS=${task.cpus}
    export MKL_NUM_THREADS=${task.cpus}
    export HOME=\$PWD
    export NUMBA_CACHE_DIR=\$PWD

    cellpose \\
        --image_path $image \\
        --save_tif \\
        $model_command \\
        $args
    """
    stub:
    // Exit if running this module with -profile conda / -profile mamba
    if (workflow.profile.tokenize(',').intersect(['conda', 'mamba']).size() >= 1) {
        error "I did not manage to create a cellpose module in Conda that works in all OSes. Please use Docker / Singularity / Podman instead."
    }
    def prefix = task.ext.prefix ?: "${meta.id}"
    def name = image.name
    def base = name.lastIndexOf('.') != -1 ? name[0..name.lastIndexOf('.') - 1] : name
    """
    touch ${base}_cp_masks.tif
    """
}
