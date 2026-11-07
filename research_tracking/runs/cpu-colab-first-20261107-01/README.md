# Colab trước Modal — kiểm notebook local

Theo user07/11, ưu tiênColabfree cho kiểmCUDA dùng chung trước tiêuModalcredits. SửaCPUtimeout300→600vì current suite từng375s, JUnitnonempty/noerrors/noskips, CPUflag và sourcehash guard trướcGPU. Gói400targets/1step không tăng.

Guardchecks dùng fake subprocess/JUnit,8cases, không chạyCUDA/Colab. test_bundle làpytest thực để kiểmpackaging; sourceGate401binding kiểmriêng, khôngclaimrerunfullsuite. v10ZIP giữnguyênsource; notebooktemplate không thuộcZIP. Mid-epochCUDAresume và actualModalVolume vẫnchưakiểm.
