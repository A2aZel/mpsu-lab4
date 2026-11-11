# Shared setup for batch-only, reproducible builds. No user projects are closed.
namespace eval lab4 {
    variable root [file dirname [file normalize [info script]]]
    variable build
    variable project_dir
    variable mode
    variable memory
}

proc lab4::prepare {kind requested_mode} {
    variable root
    variable build
    variable project_dir
    variable mode
    variable memory
    if {$requested_mode ni {default low16 operations}} {
        error "Program must be default, low16 or operations"
    }
    if {[current_project -quiet] ne ""} {
        error "An existing project is open. Run this script in a separate Vivado batch process."
    }
    set mode $requested_mode
    set mem_name [dict get [dict create default program.mem low16 program_low16.mem operations program_operations.mem] $mode]
    set sources [list memory_pkg.sv alu_opcodes_pkg.sv fulladder.sv fulladder4.sv fulladder32.sv alu.sv instr_mem.sv register_file.sv CYBERcobra.sv]
    foreach name [concat $sources [list $mem_name]] {
        if {![file isfile [file join $root $name]]} {
            error "Missing input: $name"
        }
    }
    set tag "${kind}_${mode}_[clock format [clock seconds] -format %Y%m%d_%H%M%S]_[pid]_[clock clicks]"
    set build [file join $root build $tag]
    if {[file exists $build]} { error "Build directory already exists: $build" }
    file mkdir $build
    set memory [file join $build program.mem]
    file copy [file join $root $mem_name] $memory
    cd $build
    set project_dir [file join $build vivado]
    create_project lab4 $project_dir -part xc7a100tcsg324-1
    set_property target_language Verilog [current_project]
    set_property simulator_language Mixed [current_project]
    foreach name $sources { add_files -norecurse [list [file join $root $name]] }
    add_files -norecurse [list $memory]
    set_property file_type {Memory Initialization Files} [get_files [list $memory]]
    update_compile_order -fileset sources_1
    puts "LAB4_BUILD_DIRECTORY=$build"
    puts "LAB4_PROGRAM=$mode"
    return $build
}
