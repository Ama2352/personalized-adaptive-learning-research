# H100outercaller và worker, ngày17/11

Gói ngoàiKT, chưa gọicloud/GPU. Source7c/77file và codecache đang chạy giữ nguyên. Worker `scripts/akt/outer_gpu_worker.py` tái dùng `run_cuda_cached_numeric`, typedcache/admission và publicCUDAmodelbuilder; caller `scripts/akt/modal_junyi_outer.py` chỉ khai báo một functionH100, không CPUcloud/Secret/retry.

## Request và thứ tự nghiệm thu

Requestkind `JUNYI_OUTER_GPU_REQUEST_V1`, workspace2016, source7c, fullcohortapproval và reservation≤0,75USD/model. Exact72567records/72423windows/4137050targets/144OOV,39616learners/maxhistory21908/batch128. Tất cả4INDEX,4temperatureidentity/SHA và4compatibilityreceipt đều phải có pin hoàn chỉnh. Template cònUNAPPROVED/nullpins sẽ bị từ chối trước khi phát GPU.

Worker đọc cachemetadata, dựng fullouterview/refit90encoding, xác nhận mọiT/checkpoint/roles/vocab/bank/reference/domaincalibration và releaseD22→7c. Không fit/applyTtrênGPU. Chỉ windowcache/graphcache đi vào inference, không mởcanonical/assignments. Fullcache giữOOVeventmetadata cho rankcoverage; OOVbịskip, không đưa vào model, numericprobabilities chỉfittedknownwindows. CPUreplay sau đó xuấtnullOOV và applyfrozenT.

Scopedhook bọc `build_cuda_refit_predictor`, gọi builderthật, chuyểngraphphaseouter rồi `admit_outer`thật trướcforward. Contextmanager luôn restore trongfinally. Không giả modelsourceD22, không sửa oldbinding/calibrator. Admissionreceipt ghihai nguồn và SHAcompatibility. Core vẫn ghi receipt `JUNYI_CACHED_NUMERIC_INFERENCE_V1` đểCPUjoin reuse.

## Runtime, artifacts và chi phí

Factory nhận image/Volume do root chọn sau gate, không tự build/upload/launch. MộtH100!,CPU2/RAM8GiB đi kèm, timeoutfunction300s, childmonitor270s, numericcore240s, retries0/single_use. Reuse `run_gpu_monitored` thuNVML mỗi giây và thu hồi child trongfinally, authorization gắnrequestSHA/allocationID/reservedUSD. Coldstart/platformstartup nằmngoài numericcoretimer, root cần tính trong ngân sách thực và kiểm Appstopped khi xong.

Numericshards, config, MODEL_ADMISSION, HOST_TIMING và coreRECEIPT được commitVolume. Parent giữworkerlog/NVML/config/result/COMPLETE hoặcFAILED, committrongfinally. Không đóng ZIP/uploadDrive trongH100. CPUlocalstreamartifacts từVolume sangDrive sau khiGPUđã trả, giữ SHA và chỉ mục. Volume là durabilitytạm, chưa tự thành bằngchứng đãsao lưuDrive.

## Staging tối thiểu

`STAGING_PLAN01.json` liệt kê291file/632.754.832byte từcacheđãnghiệmthu và6scriptpins. DùngphysicalVolumeRoot `/__modal/volumes/vo-dv1975utRQbmagCjA0brSe`, tránhalias `/artifacts` trong requestpinnedpath. Giữ nguyênbyteCPUreceipt/manifest, Windowspathbêntrongkhôngrewrite. Requestlocations riêng chỉra vị tríwindows/admission/3graph trênVolume.

Tái dùng4exportsđã có trênVolume dướicalibration-inputs-20261117-01, gồmINDEX/SUPPORT/model.pt, không reuploadweights. Thêm4T+4compatmetadata đãnghiệmthu. Không chuyểnrawcanonical/assignments/Holdout/credentials. ShardSHA trongplan kếthừacompletedmanifest, uploaderphải hash/so sánh byte khi chuyển và đọc lại nhận.

Imagegatequantrọng: `im-FLsPV1Te1DGul7RBdUy5HH` làbase màfactorycalibrationcũ còn aptgit/cloneupstream/pip trướcGPU. Không coi baseID này tựđủruntime. Reuse FULLbuiltimage đãGPUđạt nếu tìm được, latefilemountguard/scripts đểidentity7c, giữupstreamgit/README/LICENSE/pinnedcommitclean. `AKTAdapter` bắt `verify_upstream` nên sourcepacketchỉakt.py không đủ. Workerexact77check bắt sai source trướcCUDA, nhưng root phải kiểm đủimageprovenance trước trảcredit.

## Kiểm đã chạy và phần còn thiếu

`green04.txt` ghi14PASS/0,17s, gồmstrictschemas/limits, nullpins/CPUcountmismatch, fakebuilderphase-before-admit/finallyrestore vàfakeModalsingleH100factory. Không importTorch/ModalSDK trong tests. `red01`/green01 giữ lỗi tênfixturepytestreserved đã đổi thànhouter_request. `red-pins01` ghi2FAIL trước thêmpin/countgates. FactoryAST đã parse. Chưa là nghiệm thu CUDA, modelthật hoặc cloudstage.

Root còn cần4metadata/compatpins thật, fullimageID/latefilemount, upload291files+readback, requestpervariant+allocation và actualsource/GPUadmission. Outputnumeric phảiCPUjoin/metrics/Driveverify sau đó. Gói này không mởthêm training hoặc thayprotocol/split/forward.
