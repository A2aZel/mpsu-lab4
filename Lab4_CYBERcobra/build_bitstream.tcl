# Usage: vivado -mode batch -nojournal -nolog -source build_bitstream.tcl -tclargs default
set script_dir [file dirname [file normalize [info script]]]
source [file join $script_dir lab4_common.tcl]
set program_mode default
if {$argc > 0} { set program_mode [lindex $argv 0] }
if {$argc > 1} { error "Usage: build_bitstream.tcl default|low16|operations" }
set build_dir [lab4::prepare bit $program_mode]
set board_sv [file join $script_dir {board files} nexys_cybercobra.sv]
set board_xdc [file join $script_dir {board files} nexys_a7_100t.xdc]
foreach input [list $board_sv $board_xdc] {
    if {![file isfile $input]} { error "Missing board input: $input" }
}
add_files -norecurse [list $board_sv]
add_files -fileset constrs_1 -norecurse [list $board_xdc]
set_property top nexys_CYBERcobra [get_filesets sources_1]
update_compile_order -fileset sources_1
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {
    error "Synthesis incomplete: [get_property STATUS [get_runs synth_1]]"
}
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
set impl_status [get_property STATUS [get_runs impl_1]]
if {![string match {*write_bitstream Complete*} $impl_status]} {
    error "Implementation/bitstream incomplete: $impl_status"
}
set generated_bit [file join $lab4::project_dir lab4.runs impl_1 nexys_CYBERcobra.bit]
if {![file isfile $generated_bit]} { error "Bitstream missing: $generated_bit" }
open_run impl_1
report_timing_summary -file [file join $build_dir timing_summary.rpt]
report_utilization -file [file join $build_dir utilization.rpt]
set paths [get_timing_paths -quiet -delay_type max -max_paths 1]
if {[llength $paths] == 0} { error "No timing path found. Inspect timing_summary.rpt before using this build." }
set slack [get_property SLACK [lindex $paths 0]]
if {$slack < 0} { error "Timing not met (worst setup slack $slack ns). Inspect timing_summary.rpt." }
set result_bit [file join $build_dir nexys_CYBERcobra.bit]
file copy $generated_bit $result_bit
puts "LAB4_BITSTREAM=$result_bit"
puts "LAB4_WORST_SETUP_SLACK_NS=$slack"
puts "Bitstream generated; physical board programming has not been performed."
close_project
