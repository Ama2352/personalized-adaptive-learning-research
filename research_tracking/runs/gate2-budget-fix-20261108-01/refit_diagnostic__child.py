from pathlib import Path
import json,os,sys,torch
out=Path(sys.argv[1])
(out/'process_metadata.json').write_text(json.dumps({'python':sys.version,'torch':torch.__version__,'threads':torch.get_num_threads(),'interop_threads':torch.get_num_interop_threads(),'cpu_count':os.cpu_count(),'cuda_available':torch.cuda.is_available(),'cuda_initialized':torch.cuda.is_initialized(),'environment':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES']}},indent=2)+'\\n')
import pytest
raise SystemExit(pytest.main(['tests/akt/test_refit_recovery.py::test_refit_recovery_matches_uninterrupted_weights_adam_rng','-q','-p','no:cacheprovider','--basetemp',str(out/'t'),'--junitxml',str(out/'pytest.xml')]))
