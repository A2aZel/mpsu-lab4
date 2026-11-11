# Usage: vivado -mode batch -nojournal -nolog -source build_sim.tcl -tclargs default directed
set script_dir [file dirname [file normalize [info script]]]
source [file join $script_dir lab4_common.tcl]
set program_mode default
set coverage_mode directed
if {$argc > 0} { set program_mode [lindex $argv 0] }
if {$argc > 1} { set coverage_mode [lindex $argv 1] }
if {$argc > 2 || $program_mode ni {default low16} || $coverage_mode ni {directed exhaustive}} {
    error "Usage: build_sim.tcl default|low16 directed|exhaustive"
}
set build_dir [lab4::prepare sim $program_mode]
set testbench [file join $script_dir tests tb_lab4_selfcheck.sv]
if {![file isfile $testbench]} { error "Missing testbench: $testbench" }
add_files -fileset sim_1 -norecurse [list $testbench]
set_property top CYBERcobra [get_filesets sources_1]
set_property top tb_lab4_selfcheck [get_filesets sim_1]
set_property xsim.elaborate.debug_level typical [get_filesets sim_1]
set_property xsim.simulate.runtime 0ns [get_filesets sim_1]
set plusargs {}
if {$program_mode eq "low16"} { lappend plusargs -testplusarg LOW16=1 }
if {$coverage_mode eq "exhaustive"} { lappend plusargs -testplusarg EXHAUSTIVE=1 }
set_property -dict [list xsim.simulate.xsim.more_options $plusargs] [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation -simset sim_1 -mode behavioral
run all
set passed [get_value -radix unsigned /tb_lab4_selfcheck/test_pass]
if {$passed ne "1"} { error "Self-check did not report test_pass=1. Inspect xsim.log and waveform." }
puts "LAB4_SELF_CHECK=PASS"
puts "LAB4_SIMULATION_DIRECTORY=$build_dir"
# Only the project/simulation created by this script is closed.
close_sim
close_project
