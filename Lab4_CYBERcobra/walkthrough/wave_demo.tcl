# Source after Run Behavioral Simulation has loaded tb_lab4_demo at time 0.
set demo_scope /tb_lab4_demo
if {[catch {get_objects -quiet [list $demo_scope/clk]} clock_object] || [llength $clock_object] == 0} {
    error "Load the tb_lab4_demo behavioral simulation before sourcing wave_demo.tcl."
}
set demo_wave_sections [list \
    [list {1. Clock, reset and completed steps} [list \
        [list clk bin] [list rst bin] [list ordinary_step unsigned] [list test_pass bin]]] \
    [list {2. Instruction address and command} [list \
        [list sw hex] [list selected_op hex] [list input_a unsigned] [list input_b unsigned] \
        [list pc hex] [list instr hex] [list pc_next hex]]] \
    [list {3. Register operands and ALU} [list \
        [list RA1 unsigned] [list RA2 unsigned] [list rd1 hex] [list rd2 hex] \
        [list alu_op bin] [list alu_result hex] [list alu_flag bin]]] \
    [list {4. Register write and visible result} [list \
        [list WS bin] [list we bin] [list WA unsigned] [list write_data hex] \
        [list r1 hex] [list r2 hex] [list r4 unsigned] [list r6 hex] \
        [list expected_result hex] [list out hex]]]]

foreach section $demo_wave_sections {
    foreach spec [lindex $section 1] {
        set path $demo_scope/[lindex $spec 0]
        if {[llength [get_objects -quiet [list $path]]] == 0} {
            error "Missing demo waveform object: $path"
        }
    }
}

create_wave_config lab4_demo_[clock seconds]_[clock clicks]
foreach section $demo_wave_sections {
    add_wave_divider [lindex $section 0]
    foreach spec [lindex $section 1] {
        set path $demo_scope/[lindex $spec 0]
        add_wave -name [lindex $spec 0] -radix [lindex $spec 1] [get_objects [list $path]]
    }
}
puts "WALKTHROUGH_WAVES_READY: use Run For 100 ns for the first instructions, or Run All then Zoom Fit for the complete example."
