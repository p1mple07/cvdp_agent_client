
rename temp_dataset to temp_dataset1.jsonl
run_and_extract_errors.sh -> change dataset to temp_dataset1.jsonl
(cvdp_env) shashwat@Shashwat:~/btp/from_scratch/cvdp_benchmark$ ./run_all_problems.py -d dataset/temp_dataset1.jsonl 


  - cvdp_copilot_configurable_digital_low_pass_filter_0011
  - cvdp_copilot_interrupt_controller_0019
  - cvdp_copilot_ir_receiver_0001
  - cvdp_copilot_ir_receiver_0005
  - cvdp_copilot_kogge_stone_adder_0007
  - cvdp_copilot_line_buffer_0003


cvdp_copilot_sorter_0003
cvdp_copilot_sorter_0009
cvdp_copilot_sorter_0031
cvdp_copilot_sorter_0051
cvdp_copilot_sorter_0057
cvdp_copilot_sorter_0059
cvdp_copilot_sound_generator_0001
cvdp_copilot_sprite_0004
cvdp_copilot_sprite_0010
cvdp_copilot_static_branch_predict_0001
cvdp_copilot_static_branch_predict_0009
cvdp_copilot_static_branch_predict_0014
cvdp_copilot_swizzler_0009
cvdp_copilot_swizzler_0014
cvdp_copilot_sync_lifo_0010
cvdp_copilot_sync_serial_communication_0001
cvdp_copilot_sync_serial_communication_0014
cvdp_copilot_sync_serial_communication_0052
cvdp_copilot_thermostat_0001
cvdp_copilot_ttc_lite_0001
cvdp_copilot_vending_machine_0001
cvdp_copilot_virtual2physical_tlb_0001
cvdp_copilot_wb2ahb_0001
cvdp_copilot_word_change_detector_0001



rename temp_dataset to temp_dataset1.jsonl
run_and_extract_errors.sh -> change dataset to temp_dataset1.jsonl
(cvdp_env) shashwat@Shashwat:~/btp/from_scratch/cvdp_benchmark$ ./run_all_problems.py -d dataset/temp_dataset1.jsonl 

rename temp_dataset to temp_dataset2.jsonl
run_and_extract_errors.sh -> change dataset to temp_dataset2.jsonl
(cvdp_env) shashwat@Shashwat:~/btp/from_scratch/cvdp_benchmark$ ./run_all_problems.py -d dataset/temp_dataset2.jsonl --keep-failed


now temp_dataset will contain all the not passed problems


python merge_raw_results.py final_llm_nonagentic // this will create the final report



To Do:
    automate all the above steps
    save all the run logs
    investigate why some (6 problems) problems are not saved
