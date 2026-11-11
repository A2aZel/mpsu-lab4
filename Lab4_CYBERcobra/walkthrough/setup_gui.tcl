# Run in a fresh Vivado GUI: source /path/to/walkthrough/setup_gui.tcl
if {[current_project -quiet] ne ""} {
    error "A project is already open. Open a fresh Vivado instance before running setup_gui.tcl."
}

set walkthrough_dir [file dirname [file normalize [info script]]]
set source_root ""
if {[info exists ::lab4_walkthrough_source_root] && $::lab4_walkthrough_source_root ne ""} {
    set source_root [file normalize $::lab4_walkthrough_source_root]
} else {
    foreach candidate [list [file join $walkthrough_dir .. project] [file join $walkthrough_dir ..]] {
        if {[file isfile [file join $candidate CYBERcobra.sv]]} {
            set source_root [file normalize $candidate]
            break
        }
    }
}
if {$source_root eq ""} {
    error "Cannot locate the project sources beside walkthrough or in ../project."
}

set walkthrough_program_mode default
if {[info exists ::lab4_walkthrough_program_mode]} {
    set walkthrough_program_mode $::lab4_walkthrough_program_mode
}
if {$walkthrough_program_mode ni {default operations}} {
    error "GUI program must be default or operations. Set ::lab4_walkthrough_program_mode before sourcing this script."
}
set program_name [expr {$walkthrough_program_mode eq "operations" ? "program_operations.mem" : "program.mem"}]

set rtl_sources [list memory_pkg.sv alu_opcodes_pkg.sv fulladder.sv fulladder4.sv fulladder32.sv alu.sv instr_mem.sv register_file.sv CYBERcobra.sv]
set board_sv [file join $source_root {board files} nexys_cybercobra.sv]
set board_xdc [file join $source_root {board files} nexys_a7_100t.xdc]
set program_source [file join $source_root $program_name]
set demo_tb [file join $walkthrough_dir tb_lab4_demo.sv]
set wave_script [file join $walkthrough_dir wave_demo.tcl]
set required [list $board_sv $board_xdc $program_source $demo_tb $wave_script]
foreach name $rtl_sources { lappend required [file join $source_root $name] }
foreach input $required {
    if {![file isfile $input]} { error "Missing walkthrough input: $input" }
}

set tag "demo_${walkthrough_program_mode}_[clock format [clock seconds] -format %Y%m%d_%H%M%S]_[pid]_[clock clicks]"
set walkthrough_build [file join $walkthrough_dir gui_build $tag]
if {[file exists $walkthrough_build]} { error "Build directory already exists: $walkthrough_build" }
file mkdir $walkthrough_build
set staged_program [file join $walkthrough_build program.mem]
file copy $program_source $staged_program
cd $walkthrough_build
set walkthrough_project_dir [file join $walkthrough_build vivado]
create_project lab4_walkthrough $walkthrough_project_dir -part xc7a100tcsg324-1
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
foreach name $rtl_sources { add_files -norecurse [list [file join $source_root $name]] }
add_files -norecurse [list $staged_program]
set_property file_type {Memory Initialization Files} [get_files [list $staged_program]]
add_files -norecurse [list $board_sv]
add_files -fileset constrs_1 -norecurse [list $board_xdc]
add_files -fileset sim_1 -norecurse [list $demo_tb]
set_property top nexys_CYBERcobra [get_filesets sources_1]
set_property top tb_lab4_demo [get_filesets sim_1]
set_property xsim.elaborate.debug_level typical [get_filesets sim_1]
set_property xsim.simulate.runtime 0ns [get_filesets sim_1]
if {$walkthrough_program_mode eq "operations"} {
    set_property xsim.simulate.xsim.more_options [list -testplusarg OPERATIONS=1] [get_filesets sim_1]
}
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1

puts "WALKTHROUGH_PROJECT=[file join $walkthrough_project_dir lab4_walkthrough.xpr]"
puts "WALKTHROUGH_PROGRAM=$walkthrough_program_mode"
puts "WALKTHROUGH_WAVE_SCRIPT=$wave_script"
puts "Ready: click Run Behavioral Simulation, then source the wave script in the Vivado Tcl Console."
