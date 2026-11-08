"""Offline-built one-shot resume cell; do not execute locally."""
EMBEDDED = {'connection_probe.py': {'sha256': '34e6a3a6b2e38e40f2ac778b44adcb3b265fa1ee2b19542af2c3cd056bbbc7af', 'base64': 'aW1wb3J0IGpzb24sIG9zLCBwbGF0Zm9ybSwgc2h1dGlsLCBzeXMKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoClJPT1QgPSBQYXRoKCcvY29udGVudC9LTFROX0dQVTA4XzIwMjYxMTA4XzAxJykKYXNzZXJ0IHBsYXRmb3JtLnN5c3RlbSgpID09ICdMaW51eCcgYW5kIHBsYXRmb3JtLm1hY2hpbmUoKSA9PSAneDg2XzY0Jwphc3NlcnQgc3lzLmltcGxlbWVudGF0aW9uLm5hbWUgPT0gJ2NweXRob24nIGFuZCBzeXMudmVyc2lvbl9pbmZvWzoyXSA9PSAoMywgMTMpClJPT1QubWtkaXIoZXhpc3Rfb2s9RmFsc2UpCmluZm8gPSB7J3N0YWdlJzonR1BVMDhfQ1BVX0NPTk5FQ1RJT05fT05MWScsJ3B5dGhvbic6c3lzLnZlcnNpb24sJ2V4ZWN1dGFibGUnOnN5cy5leGVjdXRhYmxlLAogICAgICAgICdwbGF0Zm9ybSc6cGxhdGZvcm0ucGxhdGZvcm0oKSwnbWFjaGluZSc6cGxhdGZvcm0ubWFjaGluZSgpLCdwcmVmaXgnOnN5cy5wcmVmaXgsCiAgICAgICAgJ2FjY2VsZXJhdG9yX2Vudmlyb25tZW50Jzpvcy5lbnZpcm9uLmdldCgnQ09MQUJfR1BVJyksJ2Rpc2tfZnJlZV9ieXRlcyc6c2h1dGlsLmRpc2tfdXNhZ2UoJy9jb250ZW50JykuZnJlZSwKICAgICAgICAncm9vdCc6c3RyKFJPT1QpLCdwYWNrYWdlc19pbnN0YWxsZWQnOjAsJ3RvcmNoX2ltcG9ydGVkJzpGYWxzZSwnZ3B1X21vZGVsX3N0ZXBzJzowLAogICAgICAgICdzY29wZSc6J3N0ZGxpYiBkaXNjb3Zlcnk7IG5vIHBhY2thZ2UgbXV0YXRpb24sIEdQVSBjYWxscyBvciBNb2RhbCd9CihST09ULydjb25uZWN0aW9uLmpzb24nKS53cml0ZV90ZXh0KGpzb24uZHVtcHMoaW5mbyxpbmRlbnQ9MikrJ1xuJykKcHJpbnQoanNvbi5kdW1wcyhpbmZvLGluZGVudD0yKSkK', 'bytes': 858}, 'venv_prepare.py': {'sha256': '99f834e26daf7647acb9f0b8716e35c0878536ee6ba4167376a6ae2cb6d1f991', 'base64': 'aW1wb3J0IGhhc2hsaWIsIGpzb24sIG9zLCBzdWJwcm9jZXNzLCBzeXMKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoClJPT1QgPSBQYXRoKCcvY29udGVudC9LTFROX0dQVTA4XzIwMjYxMTA4XzAxJykKYXNzZXJ0IChST09ULydjb25uZWN0aW9uLmpzb24nKS5pc19maWxlKCkKVkVOViA9IFJPT1QvJy52ZW52Jwphc3NlcnQgbm90IFZFTlYuZXhpc3RzKCkKY29tbWFuZD1bc3lzLmV4ZWN1dGFibGUsJy1tJywndmVudicsJy0td2l0aG91dC1waXAnLHN0cihWRU5WKV0KcmVzdWx0PXN1YnByb2Nlc3MucnVuKGNvbW1hbmQsY2FwdHVyZV9vdXRwdXQ9VHJ1ZSx0ZXh0PVRydWUsdGltZW91dD0zMCkKKFJPT1QvJ3ZlbnYtY3JlYXRlLnN0ZG91dCcpLndyaXRlX3RleHQocmVzdWx0LnN0ZG91dCkKKFJPT1QvJ3ZlbnYtY3JlYXRlLnN0ZGVycicpLndyaXRlX3RleHQocmVzdWx0LnN0ZGVycikKYXNzZXJ0IHJlc3VsdC5yZXR1cm5jb2RlPT0wLCByZXN1bHQuc3RkZXJyCmNvZGU9IiIiaW1wb3J0IGltcG9ydGxpYi51dGlsLGpzb24scGxhdGZvcm0sc3lzLHN5c2NvbmZpZwpwcmludChqc29uLmR1bXBzKHsnZXhlY3V0YWJsZSc6c3lzLmV4ZWN1dGFibGUsJ3ByZWZpeCc6c3lzLnByZWZpeCwnYmFzZV9wcmVmaXgnOnN5cy5iYXNlX3ByZWZpeCwKICdwdXJlbGliJzpzeXNjb25maWcuZ2V0X3BhdGgoJ3B1cmVsaWInKSwncHl0aG9uJzpzeXMudmVyc2lvbiwncGxhdGZvcm0nOnBsYXRmb3JtLnBsYXRmb3JtKCksCiAndG9yY2hfc3BlYyc6c3RyKGltcG9ydGxpYi51dGlsLmZpbmRfc3BlYygndG9yY2gnKSksJ251bXB5X3NwZWMnOnN0cihpbXBvcnRsaWIudXRpbC5maW5kX3NwZWMoJ251bXB5JykpLAogJ3BpcF9zcGVjJzpzdHIoaW1wb3J0bGliLnV0aWwuZmluZF9zcGVjKCdwaXAnKSl9KSkKIiIiCnRhcmdldD1WRU5WLydiaW4vcHl0aG9uJwpwcm9iZT1qc29uLmxvYWRzKHN1YnByb2Nlc3MuY2hlY2tfb3V0cHV0KFtzdHIodGFyZ2V0KSwnLUInLCctYycsY29kZV0sdGV4dD1UcnVlLHRpbWVvdXQ9MTUpKQphc3NlcnQgcHJvYmVbJ3ByZWZpeCddPT1zdHIoVkVOVikgYW5kIHByb2JlWydwcmVmaXgnXSE9cHJvYmVbJ2Jhc2VfcHJlZml4J10KYXNzZXJ0IFBhdGgocHJvYmVbJ3B1cmVsaWInXSkuaXNfcmVsYXRpdmVfdG8oVkVOVikKYXNzZXJ0IHByb2JlWyd0b3JjaF9zcGVjJ109PXByb2JlWydudW1weV9zcGVjJ109PXByb2JlWydwaXBfc3BlYyddPT0nTm9uZScKY2ZnPShWRU5WLydweXZlbnYuY2ZnJykucmVhZF90ZXh0KCkKYXNzZXJ0ICdpbmNsdWRlLXN5c3RlbS1zaXRlLXBhY2thZ2VzID0gZmFsc2UnIGluIGNmZy5sb3dlcigpCnBpcF9pbmZvPXN1YnByb2Nlc3MuY2hlY2tfb3V0cHV0KFtzeXMuZXhlY3V0YWJsZSwnLW0nLCdwaXAnLCctLXZlcnNpb24nXSx0ZXh0PVRydWUsdGltZW91dD0xNSkuc3RyaXAoKQp0YXJnZXRfcGlwPXN1YnByb2Nlc3MuY2hlY2tfb3V0cHV0KFtzeXMuZXhlY3V0YWJsZSwnLW0nLCdwaXAnLCctLXB5dGhvbicsc3RyKHRhcmdldCksJy0tdmVyc2lvbiddLHRleHQ9VHJ1ZSx0aW1lb3V0PTE1KS5zdHJpcCgpCnBheWxvYWQ9eydzdGFnZSc6J0dQVTA4X0lTT0xBVEVEX1ZFTlZfUFJFUEFSRUQnLCdyb290JzpzdHIoUk9PVCksJ3ZlbnYnOnN0cihWRU5WKSwncHJvYmUnOnByb2JlLAogJ3B5dmVudl9jZmdfc2hhMjU2JzpoYXNobGliLnNoYTI1NihjZmcuZW5jb2RlKCkpLmhleGRpZ2VzdCgpLCdiYXNlX3BpcF9yZWFkb25seSc6cGlwX2luZm8sCiAndGFyZ2V0X3BpcF9ib290c3RyYXBfdmVyc2lvbic6dGFyZ2V0X3BpcCwnYm9vdHN0cmFwJzonYmFzZSBwaXAgLS1weXRob24gdGFyZ2V0OyBubyBwYWNrYWdlcyBpbnN0YWxsZWQnLAogJ3N5c3RlbV9zaXRlX3BhY2thZ2VzJzpGYWxzZSwndG9yY2hfaW1wb3J0ZWQnOkZhbHNlLCdwYWNrYWdlc19pbnN0YWxsZWQnOjAsJ2dwdV9tb2RlbF9zdGVwcyc6MH0KKFJPT1QvJ3ZlbnYuanNvbicpLndyaXRlX3RleHQoanNvbi5kdW1wcyhwYXlsb2FkLGluZGVudD0yKSsnXG4nKQpwcmludChqc29uLmR1bXBzKHBheWxvYWQsaW5kZW50PTIpKQo=', 'bytes': 2039}, 'resolve_dependencies.py': {'sha256': '39c68ed7921ccd7660ab1e625ab5df6ca3d2cfd473339b2b9babc7de3665b861', 'base64': 'aW1wb3J0IGhhc2hsaWIsIGltcG9ydGxpYi51dGlsLCBqc29uLCBvcywgcGxhdGZvcm0sIHJlLCBzaWduYWwsIHN1YnByb2Nlc3MsIHN5cywgdGltZQpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKZnJvbSB1cmxsaWIucGFyc2UgaW1wb3J0IHVybHNwbGl0CgpTUEVDID0geydzb3VyY2VfbG9ja19zaGEyNTYnOiAnM2U3MjFmZGI0OTU0M2FkMDg4OGNmMDJhODYzODI2ZWJjNjE0NGMwZDFkZDY3MGYyNDkwZWJjYzBkNjliOGMwYScsICdyb290X3BpbnMnOiB7J2Nsb3VkcGlja2xlJzogJzMuMS4yJywgJ2NvbG9yYW1hJzogJzAuNC42JywgJ2R1Y2tkYic6ICcxLjUuNicsICdmaWxlbG9jayc6ICc0LjIuNScsICdmc3NwZWMnOiAnMjAyNi45LjAnLCAnaW5pY29uZmlnJzogJzIuMy4xJywgJ2ppbmphMic6ICczLjEuNicsICdqb2JsaWInOiAnMS42LjAnLCAnbWFya3Vwc2FmZSc6ICczLjAuNCcsICdtcG1hdGgnOiAnMS4zLjAnLCAnbmFyd2hhbHMnOiAnMi4yOC4wJywgJ25ldHdvcmt4JzogJzMuNycsICdudW1weSc6ICcyLjUuNCcsICdwYWNrYWdpbmcnOiAnMjYuMycsICdwYW5kYXMnOiAnMy4wLjYnLCAncGx1Z2d5JzogJzEuNy4wJywgJ3BzdXRpbCc6ICc3LjIuMicsICdweWdtZW50cyc6ICcyLjIxLjAnLCAncHl0ZXN0JzogJzkuMS4xJywgJ3B5dGhvbi1kYXRldXRpbCc6ICczLjAuMCcsICdzY2lraXQtbGVhcm4nOiAnMS45LjEnLCAnc2NpcHknOiAnMS4xOC4xJywgJ3NldHVwdG9vbHMnOiAnODQuMi4xJywgJ3NpeCc6ICcxLjE3LjAnLCAnc3ltcHknOiAnMS4xNC4wJywgJ3RocmVhZHBvb2xjdGwnOiAnMy43LjAnLCAndG9yY2gnOiAnMi43LjErY3UxMjYnLCAndHlwaW5nLWV4dGVuc2lvbnMnOiAnNC4xNi4wJywgJ3R6ZGF0YSc6ICcyMDI2LjYnfSwgJ2N1ZGFfcGlucyc6IHsnbnZpZGlhLWN1ZGEtbnZydGMtY3UxMic6ICcxMi42Ljc3JywgJ252aWRpYS1jdWRhLXJ1bnRpbWUtY3UxMic6ICcxMi42Ljc3JywgJ252aWRpYS1jdWRhLWN1cHRpLWN1MTInOiAnMTIuNi44MCcsICdudmlkaWEtY3Vkbm4tY3UxMic6ICc5LjUuMS4xNycsICdudmlkaWEtY3VibGFzLWN1MTInOiAnMTIuNi40LjEnLCAnbnZpZGlhLWN1ZmZ0LWN1MTInOiAnMTEuMy4wLjQnLCAnbnZpZGlhLWN1cmFuZC1jdTEyJzogJzEwLjMuNy43NycsICdudmlkaWEtY3Vzb2x2ZXItY3UxMic6ICcxMS43LjEuMicsICdudmlkaWEtY3VzcGFyc2UtY3UxMic6ICcxMi41LjQuMicsICdudmlkaWEtY3VzcGFyc2VsdC1jdTEyJzogJzAuNi4zJywgJ252aWRpYS1uY2NsLWN1MTInOiAnMi4yNi4yJywgJ252aWRpYS1udnR4LWN1MTInOiAnMTIuNi43NycsICdudmlkaWEtbnZqaXRsaW5rLWN1MTInOiAnMTIuNi44NScsICdudmlkaWEtY3VmaWxlLWN1MTInOiAnMS4xMS4xLjYnLCAndHJpdG9uJzogJzMuMy4xJ30sICdyZXF1aXJlbWVudHNfdGV4dCc6ICdjbG91ZHBpY2tsZT09My4xLjJcbmNvbG9yYW1hPT0wLjQuNlxuZHVja2RiPT0xLjUuNlxuZmlsZWxvY2s9PTQuMi41XG5mc3NwZWM9PTIwMjYuOS4wXG5pbmljb25maWc9PTIuMy4xXG5qaW5qYTI9PTMuMS42XG5qb2JsaWI9PTEuNi4wXG5tYXJrdXBzYWZlPT0zLjAuNFxubXBtYXRoPT0xLjMuMFxubmFyd2hhbHM9PTIuMjguMFxubmV0d29ya3g9PTMuN1xubnVtcHk9PTIuNS40XG5wYWNrYWdpbmc9PTI2LjNcbnBhbmRhcz09My4wLjZcbnBsdWdneT09MS43LjBcbnBzdXRpbD09Ny4yLjJcbnB5Z21lbnRzPT0yLjIxLjBcbnB5dGVzdD09OS4xLjFcbnB5dGhvbi1kYXRldXRpbD09My4wLjBcbnNjaWtpdC1sZWFybj09MS45LjFcbnNjaXB5PT0xLjE4LjFcbnNldHVwdG9vbHM9PTg0LjIuMVxuc2l4PT0xLjE3LjBcbnN5bXB5PT0xLjE0LjBcbnRocmVhZHBvb2xjdGw9PTMuNy4wXG50b3JjaD09Mi43LjErY3UxMjZcbnR5cGluZy1leHRlbnNpb25zPT00LjE2LjBcbnR6ZGF0YT09MjAyNi42XG4nLCAncmVxdWlyZW1lbnRzX3NoYTI1Nic6ICczOTVkYmE1MzEyYmMxOGVlNzVjOGNkZGE2ZmNmZWVhYzZiYTM0NGVlNzUxZjhmY2FkYjNlZmFiYTA2NGNlMjViJywgJ3RvcmNoX3NoYTI1Nic6ICdhMDVjMDAwMWZkMWQwY2VhZTljZGE4YzhjMWI4YTE2ZWQ1ZGVmODU4ZmU5OTZjOTIzN2EyODAxNjU1OWRhZDUyJywgJ3RyaXRvbl9zaGEyNTYnOiAnYjg5ZDg0NmI1YTQxOTgzMTdmZWMyN2E1ZDNhNjA5ZWE5NmI2ZDU1N2ZmNDRiNTZjMjMxNzY1NDYwMjNjNDI0MCd9ClJPT1Q9UGF0aCgnL2NvbnRlbnQvS0xUTl9HUFUwOF8yMDI2MTEwOF8wMScpClZFTlY9Uk9PVC8nLnZlbnYnO1RBUkdFVD1WRU5WLydiaW4vcHl0aG9uJwphc3NlcnQgaGFzaGxpYi5zaGEyNTYoUGF0aChfX2ZpbGVfXykucmVhZF9ieXRlcygpKS5oZXhkaWdlc3QoKT09RVhQRUNURURfU09VUkNFX1NIQTI1Ngphc3NlcnQgcGxhdGZvcm0uc3lzdGVtKCk9PSdMaW51eCcgYW5kIHBsYXRmb3JtLm1hY2hpbmUoKT09J3g4Nl82NCcgYW5kIHN5cy52ZXJzaW9uX2luZm9bOjJdPT0oMywxMykKYXNzZXJ0IChST09ULyd2ZW52Lmpzb24nKS5pc19maWxlKCkgYW5kICdpbmNsdWRlLXN5c3RlbS1zaXRlLXBhY2thZ2VzID0gZmFsc2UnIGluIChWRU5WLydweXZlbnYuY2ZnJykucmVhZF90ZXh0KCkubG93ZXIoKQphc3NlcnQgb3MuZW52aXJvbi5nZXQoJ0NPTEFCX0dQVScsJycpIGluICgnJywnMCcpLCAnQ1BVLW9ubHkgcHJlcGFyYXRpb24gc3RhZ2U7IG5vIEdQVSBydW50aW1lIHJlcXVlc3RlZCcKcHJvYmVfY29kZT0iIiJpbXBvcnQgaW1wb3J0bGliLnV0aWwsanNvbixzeXMsc3lzY29uZmlnCnByaW50KGpzb24uZHVtcHMoeydwcmVmaXgnOnN5cy5wcmVmaXgsJ2V4ZWN1dGFibGUnOnN5cy5leGVjdXRhYmxlLCdwdXJlbGliJzpzeXNjb25maWcuZ2V0X3BhdGgoJ3B1cmVsaWInKSwKICd0b3JjaCc6c3RyKGltcG9ydGxpYi51dGlsLmZpbmRfc3BlYygndG9yY2gnKSksJ251bXB5JzpzdHIoaW1wb3J0bGliLnV0aWwuZmluZF9zcGVjKCdudW1weScpKSwKICdwaXAnOnN0cihpbXBvcnRsaWIudXRpbC5maW5kX3NwZWMoJ3BpcCcpKX0pKQoiIiIKcHJvYmVfYmVmb3JlPWpzb24ubG9hZHMoc3VicHJvY2Vzcy5jaGVja19vdXRwdXQoW3N0cihUQVJHRVQpLCctQicsJy1jJyxwcm9iZV9jb2RlXSx0ZXh0PVRydWUsdGltZW91dD0xNSkpCmFzc2VydCBwcm9iZV9iZWZvcmVbJ3ByZWZpeCddPT1zdHIoVkVOVikgYW5kIFBhdGgocHJvYmVfYmVmb3JlWydwdXJlbGliJ10pLmlzX3JlbGF0aXZlX3RvKFZFTlYpCmFzc2VydCBwcm9iZV9iZWZvcmVbJ3RvcmNoJ109PXByb2JlX2JlZm9yZVsnbnVtcHknXT09cHJvYmVfYmVmb3JlWydwaXAnXT09J05vbmUnCnNpdGU9UGF0aChwcm9iZV9iZWZvcmVbJ3B1cmVsaWInXSkKYmVmb3JlX3NpdGU9c29ydGVkKHAucmVsYXRpdmVfdG8oc2l0ZSkuYXNfcG9zaXgoKSBmb3IgcCBpbiBzaXRlLnJnbG9iKCcqJykpCmF0dGVtcHQ9Uk9PVC8ncmVzb2x1dGlvbi1hdHRlbXB0MDEnO2F0dGVtcHQubWtkaXIoZXhpc3Rfb2s9RmFsc2UpCmZvciBuYW1lIGluICgndG1wJywnY2FjaGUnKTooYXR0ZW1wdC9uYW1lKS5ta2RpcigpCnJlcXVpcmVtZW50cz1hdHRlbXB0LydyZXF1aXJlbWVudHMtcHJvcG9zZWQudHh0JwpyZXF1aXJlbWVudHMud3JpdGVfYnl0ZXMoU1BFQ1sncmVxdWlyZW1lbnRzX3RleHQnXS5lbmNvZGUoKSkKYXNzZXJ0IGhhc2hsaWIuc2hhMjU2KHJlcXVpcmVtZW50cy5yZWFkX2J5dGVzKCkpLmhleGRpZ2VzdCgpPT1TUEVDWydyZXF1aXJlbWVudHNfc2hhMjU2J10KcmVwb3J0X3BhdGg9YXR0ZW1wdC8ncGlwLXJlcG9ydC5qc29uJwpjb21tYW5kPVtzeXMuZXhlY3V0YWJsZSwnLUInLCctbScsJ3BpcCcsJy0tcHl0aG9uJyxzdHIoVEFSR0VUKSwnaW5zdGFsbCcsJy0tZHJ5LXJ1bicsJy0taWdub3JlLWluc3RhbGxlZCcsCiAnLS1vbmx5LWJpbmFyeT06YWxsOicsJy0tbm8taW5wdXQnLCctLWRpc2FibGUtcGlwLXZlcnNpb24tY2hlY2snLCctLXByb2dyZXNzLWJhcicsJ29mZicsJy0tcmV0cmllcycsJzAnLCctLXRpbWVvdXQnLCcxMicsCiAnLS1jYWNoZS1kaXInLHN0cihhdHRlbXB0LydjYWNoZScpLCctLWluZGV4LXVybCcsJ2h0dHBzOi8vZG93bmxvYWQucHl0b3JjaC5vcmcvd2hsL2N1MTI2JywKICctLWV4dHJhLWluZGV4LXVybCcsJ2h0dHBzOi8vcHlwaS5vcmcvc2ltcGxlJywnLS1yZXBvcnQnLHN0cihyZXBvcnRfcGF0aCksJy1yJyxzdHIocmVxdWlyZW1lbnRzKV0KYXNzZXJ0ICctLWRyeS1ydW4nIGluIGNvbW1hbmQgYW5kICctLWlnbm9yZS1pbnN0YWxsZWQnIGluIGNvbW1hbmQgYW5kICctLW9ubHktYmluYXJ5PTphbGw6JyBpbiBjb21tYW5kCmVudj17azp2IGZvciBrLHYgaW4gb3MuZW52aXJvbi5pdGVtcygpIGlmIG5vdCBrLnN0YXJ0c3dpdGgoKCdQSVBfJywnVVZfJykpfQplbnYudXBkYXRlKFBJUF9DT05GSUdfRklMRT1vcy5kZXZudWxsLFBJUF9ESVNBQkxFX1BJUF9WRVJTSU9OX0NIRUNLPScxJyxQSVBfTk9fSU5QVVQ9JzEnLAogICAgICAgICAgIFBZVEhPTkRPTlRXUklURUJZVEVDT0RFPScxJyxUTVBESVI9c3RyKGF0dGVtcHQvJ3RtcCcpLENVREFfVklTSUJMRV9ERVZJQ0VTPScnKQpzdGFydD10aW1lLm1vbm90b25pYygpO3JlYXNvbj1Ob25lO3BlYWs9MApkZWYgbWF0ZXJpYWxpemVkX2J5dGVzKCk6CiAgICB0b3RhbD0wCiAgICBmb3IgcGF0aCBpbiBhdHRlbXB0LnJnbG9iKCcqJyk6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBpZiBwYXRoLmlzX2ZpbGUoKSBhbmQgbm90IHBhdGguaXNfc3ltbGluaygpOnRvdGFsKz1wYXRoLnN0YXQoKS5zdF9zaXplCiAgICAgICAgZXhjZXB0IEZpbGVOb3RGb3VuZEVycm9yOnBhc3MgICMgcGlwIGPDsyB0aOG7gyB24burYSBk4buNbiB0ZW1wIGZpbGUuCiAgICByZXR1cm4gdG90YWwKd2l0aCAoYXR0ZW1wdC8ncGlwLnN0ZG91dC5sb2cnKS5vcGVuKCd4YicpIGFzIHN0ZG91dCwoYXR0ZW1wdC8ncGlwLnN0ZGVyci5sb2cnKS5vcGVuKCd4YicpIGFzIHN0ZGVycjoKICAgIHByb2Nlc3M9c3VicHJvY2Vzcy5Qb3Blbihjb21tYW5kLGN3ZD1ST09ULGVudj1lbnYsc3Rkb3V0PXN0ZG91dCxzdGRlcnI9c3RkZXJyLHN0YXJ0X25ld19zZXNzaW9uPVRydWUpCiAgICB0cnk6CiAgICAgICAgd2hpbGUgcHJvY2Vzcy5wb2xsKCkgaXMgTm9uZToKICAgICAgICAgICAgc2l6ZT1tYXRlcmlhbGl6ZWRfYnl0ZXMoKTtwZWFrPW1heChwZWFrLHNpemUpCiAgICAgICAgICAgIGlmIHRpbWUubW9ub3RvbmljKCktc3RhcnQ+PTE4MDpyZWFzb249J3dhbGxfYnVkZ2V0XzE4MHMnCiAgICAgICAgICAgIGVsaWYgc2l6ZT4yNTYqMTAyNCoqMjpyZWFzb249J2Nvb3BlcmF0aXZlX3dvcmtzcGFjZV9idWRnZXRfMjU2TWlCJwogICAgICAgICAgICBpZiByZWFzb246YnJlYWsKICAgICAgICAgICAgdGltZS5zbGVlcCgxKQogICAgZmluYWxseToKICAgICAgICAjIC0tcHl0aG9uIGPDsyB0aOG7gyB04bqhbyBkZXNjZW5kYW50OiBk4buNbiBvd25lZCBncm91cCBr4buDIGPhuqMgbGVhZGVyIMSRw6MgZXhpdC4KICAgICAgICB0cnk6b3Mua2lsbHBnKHByb2Nlc3MucGlkLHNpZ25hbC5TSUdLSUxMKQogICAgICAgIGV4Y2VwdCBQcm9jZXNzTG9va3VwRXJyb3I6cGFzcwogICAgICAgIHJldHVybmNvZGU9cHJvY2Vzcy53YWl0KHRpbWVvdXQ9MTApCmVsYXBzZWQ9dGltZS5tb25vdG9uaWMoKS1zdGFydDtwZWFrPW1heChwZWFrLG1hdGVyaWFsaXplZF9ieXRlcygpKQppZiByZWFzb24gaXMgTm9uZSBhbmQgZWxhcHNlZD4xODA6cmVhc29uPSdwb3N0ZXhpdF93YWxsX2J1ZGdldF8xODBzJwppZiByZWFzb24gaXMgTm9uZSBhbmQgcGVhaz4yNTYqMTAyNCoqMjpyZWFzb249J3Bvc3RleGl0X2Nvb3BlcmF0aXZlX3dvcmtzcGFjZV9idWRnZXRfMjU2TWlCJwpwcm9iZV9hZnRlcj1qc29uLmxvYWRzKHN1YnByb2Nlc3MuY2hlY2tfb3V0cHV0KFtzdHIoVEFSR0VUKSwnLUInLCctYycscHJvYmVfY29kZV0sdGV4dD1UcnVlLHRpbWVvdXQ9MTUpKQphZnRlcl9zaXRlPXNvcnRlZChwLnJlbGF0aXZlX3RvKHNpdGUpLmFzX3Bvc2l4KCkgZm9yIHAgaW4gc2l0ZS5yZ2xvYignKicpKQpzdW1tYXJ5PXsnc3RhZ2UnOidHUFUwOF9BQ1RVQUxfTElOVVhfQk9VTkRFRF9SRVNPTFZFUicsJ3JldHVybmNvZGUnOnJldHVybmNvZGUsJ3N0b3BfcmVhc29uJzpyZWFzb24sCiAnZWxhcHNlZF9zZWNvbmRzJzplbGFwc2VkLCdwZWFrX29ic2VydmVkX3dvcmtzcGFjZV9ieXRlcyc6cGVhaywnd29ya3NwYWNlX2NhcF9pc19jb29wZXJhdGl2ZSc6VHJ1ZSwKICduZXR3b3JrX2J5dGVfY2FwJzpGYWxzZSwnd2hlZWxfZmV0Y2hfYWJzZW5jZV9wcm92ZW4nOkZhbHNlLCdwYWNrYWdlc19pbnN0YWxsZWQnOjAsCiAnaXNvbGF0ZWRfc2l0ZV91bmNoYW5nZWQnOnByb2JlX2FmdGVyPT1wcm9iZV9iZWZvcmUgYW5kIGJlZm9yZV9zaXRlPT1hZnRlcl9zaXRlLAogJ3B5dGhvbic6c3lzLnZlcnNpb24sJ3BsYXRmb3JtJzpwbGF0Zm9ybS5wbGF0Zm9ybSgpLCdwcm9iZV9iZWZvcmUnOnByb2JlX2JlZm9yZSwncHJvYmVfYWZ0ZXInOnByb2JlX2FmdGVyLAogJ2Jhc2VfcGlwX2NvbnRyb2xzX3RhcmdldF92ZW52JzpUcnVlLCdzb3VyY2VfbG9ja19zaGEyNTYnOlNQRUNbJ3NvdXJjZV9sb2NrX3NoYTI1NiddLAogJ3JlcXVpcmVtZW50c19zaGEyNTYnOlNQRUNbJ3JlcXVpcmVtZW50c19zaGEyNTYnXSwnZ3B1X21vZGVsX3N0ZXBzJzowLCdtb2RhbF9jYWxscyc6MCwKICdleGVjdXRlZF9zb3VyY2Vfc2hhMjU2JzpFWFBFQ1RFRF9TT1VSQ0VfU0hBMjU2LAogJ3NvdXJjZV9kb2NzJzpbJ2h0dHBzOi8vcGlwLnB5cGEuaW8vZW4vc3RhYmxlL3RvcGljcy9weXRob24tb3B0aW9uLycsCiAgICAgICAgICAgICAgICAnaHR0cHM6Ly9waXAucHlwYS5pby9lbi9zdGFibGUvY2xpL3BpcF9pbnN0YWxsLyddLAogJ2xpbWl0YXRpb25zJzpbJ1Jlc29sdmVyIG1heSBmZXRjaCB3aGVlbCBieXRlcyBmb3IgbWV0YWRhdGE7IHBvbGxpbmcgaXMgbm90IGEgaGFyZCBuZXR3b3JrL2Rpc2sgY2FwLicsCiAgICAgICAgICAgICAgICAnSW5kZXgtcHJvdmlkZWQgd2hlZWwgaGFzaGVzIG5vdCB2ZXJpZmllZCBhZ2FpbnN0IGFsbCB3aGVlbCBieXRlczsgbm8gaW5zdGFsbC9pbWFnZS9ydW50aW1lL0dQVSBhY2NlcHRhbmNlLiddfQphc3NlcnQgc3VtbWFyeVsnaXNvbGF0ZWRfc2l0ZV91bmNoYW5nZWQnXSwgJ3VuZXhwZWN0ZWQgdGFyZ2V0IHNpdGUtcGFja2FnZXMgbXV0YXRpb24nCmlmIHJldHVybmNvZGU9PTAgYW5kIHJlYXNvbiBpcyBOb25lOgogICAgcmVwb3J0PWpzb24ubG9hZHMocmVwb3J0X3BhdGgucmVhZF90ZXh0KCkpCiAgICBlbnZpcm9ubWVudD1yZXBvcnRbJ2Vudmlyb25tZW50J10KICAgIGFzc2VydCBlbnZpcm9ubWVudFsnc3lzX3BsYXRmb3JtJ109PSdsaW51eCcgYW5kIGVudmlyb25tZW50WydwbGF0Zm9ybV9tYWNoaW5lJ109PSd4ODZfNjQnCiAgICBhc3NlcnQgZW52aXJvbm1lbnRbJ3B5dGhvbl9mdWxsX3ZlcnNpb24nXT09cGxhdGZvcm0ucHl0aG9uX3ZlcnNpb24oKQogICAgc2VsZWN0ZWQ9e307bGluZXM9W10KICAgIGZvciBpdGVtIGluIHJlcG9ydFsnaW5zdGFsbCddOgogICAgICAgIG5hbWU9cmUuc3ViKHInWy1fLl0rJywnLScsaXRlbVsnbWV0YWRhdGEnXVsnbmFtZSddKS5sb3dlcigpCiAgICAgICAgYXNzZXJ0IG5hbWUgbm90IGluIHNlbGVjdGVkIGFuZCBub3QgaXRlbS5nZXQoJ2lzX3lhbmtlZCcsRmFsc2UpCiAgICAgICAgdmVyc2lvbj1pdGVtWydtZXRhZGF0YSddWyd2ZXJzaW9uJ107ZG93bmxvYWQ9aXRlbVsnZG93bmxvYWRfaW5mbyddO3VybD1kb3dubG9hZFsndXJsJ107cGFydHM9dXJsc3BsaXQodXJsKQogICAgICAgIGFzc2VydCBwYXJ0cy5zY2hlbWU9PSdodHRwcycgYW5kIHBhcnRzLmhvc3RuYW1lIGluIHsnZmlsZXMucHl0aG9uaG9zdGVkLm9yZycsJ2Rvd25sb2FkLnB5dG9yY2gub3JnJywnZG93bmxvYWQtcjIucHl0b3JjaC5vcmcnfQogICAgICAgIGFzc2VydCBwYXJ0cy51c2VybmFtZSBpcyBOb25lIGFuZCBwYXJ0cy5wYXNzd29yZCBpcyBOb25lIGFuZCBub3QgcGFydHMucXVlcnkgYW5kIG5vdCBwYXJ0cy5mcmFnbWVudAogICAgICAgIGFzc2VydCBwYXJ0cy5wYXRoLmVuZHN3aXRoKCcud2hsJykgYW5kICd3aW5fYW1kNjQnIG5vdCBpbiBwYXJ0cy5wYXRoIGFuZCAnbWFjb3N4JyBub3QgaW4gcGFydHMucGF0aAogICAgICAgIGRpZ2VzdD1kb3dubG9hZFsnYXJjaGl2ZV9pbmZvJ11bJ2hhc2hlcyddWydzaGEyNTYnXTthc3NlcnQgcmUuZnVsbG1hdGNoKCdbYS1mMC05XXs2NH0nLGRpZ2VzdCkKICAgICAgICBzZWxlY3RlZFtuYW1lXT17J3ZlcnNpb24nOnZlcnNpb24sJ3VybCc6dXJsLCdzaGEyNTZfZnJvbV9waXBfaW5kZXhfcmVwb3J0JzpkaWdlc3QsCiAgICAgICAgICAgICAgICAgICAgICAgICdyZXF1aXJlc19kaXN0JzppdGVtWydtZXRhZGF0YSddLmdldCgncmVxdWlyZXNfZGlzdCcsW10pfQogICAgZm9yIG5hbWUsdmVyc2lvbiBpbiBTUEVDWydyb290X3BpbnMnXS5pdGVtcygpOmFzc2VydCBzZWxlY3RlZFtuYW1lXVsndmVyc2lvbiddPT12ZXJzaW9uLChuYW1lLHZlcnNpb24pCiAgICBmb3IgbmFtZSx2ZXJzaW9uIGluIFNQRUNbJ2N1ZGFfcGlucyddLml0ZW1zKCk6YXNzZXJ0IHNlbGVjdGVkW25hbWVdWyd2ZXJzaW9uJ109PXZlcnNpb24sKG5hbWUsdmVyc2lvbikKICAgIGFzc2VydCBzZWxlY3RlZFsndG9yY2gnXVsnc2hhMjU2X2Zyb21fcGlwX2luZGV4X3JlcG9ydCddPT1TUEVDWyd0b3JjaF9zaGEyNTYnXQogICAgYXNzZXJ0IHNlbGVjdGVkWyd0cml0b24nXVsnc2hhMjU2X2Zyb21fcGlwX2luZGV4X3JlcG9ydCddPT1TUEVDWyd0cml0b25fc2hhMjU2J10KICAgIGZvciBuYW1lLHJvdyBpbiBzb3J0ZWQoc2VsZWN0ZWQuaXRlbXMoKSk6bGluZXMuYXBwZW5kKGYie25hbWV9IEAge3Jvd1sndXJsJ119IC0taGFzaD1zaGEyNTY6e3Jvd1snc2hhMjU2X2Zyb21fcGlwX2luZGV4X3JlcG9ydCddfSIpCiAgICBsb2NrPWF0dGVtcHQvJ2NhbmRpZGF0ZS1saW51eC1jdWRhLmxvY2sudHh0Jztsb2NrLndyaXRlX2J5dGVzKCgnXG4nLmpvaW4obGluZXMpKydcbicpLmVuY29kZSgpKQogICAgc3VtbWFyeS51cGRhdGUoc3RhdHVzPSdDQU5ESURBVEVfQ0xPU1VSRV9SRVNPTFZFRF9OT1RfSU5TVEFMTEVEJyxwaXBfdmVyc2lvbj1yZXBvcnRbJ3BpcF92ZXJzaW9uJ10sCiAgICAgICAgc2VsZWN0ZWRfcGFja2FnZXM9c2VsZWN0ZWQscGFja2FnZV9jb3VudD1sZW4oc2VsZWN0ZWQpLG52aWRpYV9wYWNrYWdlX2NvdW50PXN1bShuLnN0YXJ0c3dpdGgoJ252aWRpYS0nKSBmb3IgbiBpbiBzZWxlY3RlZCksCiAgICAgICAgcmVwb3J0X3NoYTI1Nj1oYXNobGliLnNoYTI1NihyZXBvcnRfcGF0aC5yZWFkX2J5dGVzKCkpLmhleGRpZ2VzdCgpLAogICAgICAgIGNhbmRpZGF0ZV9sb2NrX3NoYTI1Nj1oYXNobGliLnNoYTI1Nihsb2NrLnJlYWRfYnl0ZXMoKSkuaGV4ZGlnZXN0KCksZW52aXJvbm1lbnQ9ZW52aXJvbm1lbnQpCmVsc2U6c3VtbWFyeVsnc3RhdHVzJ109J1JFU09MVVRJT05fRkFJTEVEX05PX0FVVE9NQVRJQ19SRVRSWScKKGF0dGVtcHQvJ3Jlc29sdXRpb24uanNvbicpLndyaXRlX3RleHQoanNvbi5kdW1wcyhzdW1tYXJ5LGluZGVudD0yKSsnXG4nKQphc3NlcnQgaGFzaGxpYi5zaGEyNTYoUGF0aChfX2ZpbGVfXykucmVhZF9ieXRlcygpKS5oZXhkaWdlc3QoKT09RVhQRUNURURfU09VUkNFX1NIQTI1NgojIE91dHB1dCBuaOG7jzsgcmF3IHJlc29sdmVyIHJlcG9ydC9sb2dzIGzGsHUgcmnDqm5nIHbDoCBz4bq9IGV4cG9ydC9oYXNoIHRyxrDhu5tjIMSRw7NuZyBydW50aW1lLgpvdXRwdXQ9e2s6diBmb3Igayx2IGluIHN1bW1hcnkuaXRlbXMoKSBpZiBrIT0nc2VsZWN0ZWRfcGFja2FnZXMnfQpwcmludChqc29uLmR1bXBzKG91dHB1dCxpbmRlbnQ9MikpCg==', 'bytes': 9841}}

# One-shot CPU preparation cell. Local validation must use AST/bytes, not exec/import.
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys

ROOT = Path('/content/KLTN_GPU08_20261108_01')
VENV = ROOT / '.venv'
ATTEMPT = ROOT / 'resolution-attempt01'
EXPECTED_RESOLVER_SHA256 = '39c68ed7921ccd7660ab1e625ab5df6ca3d2cfd473339b2b9babc7de3665b861'
STAGES_ATTEMPTED = []
VERIFIED_PAYLOADS = {}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path, maximum=2 * 1024**2):
    require(path.is_file() and not path.is_symlink(), f'missing/nonregular evidence: {path.name}')
    with path.open('rb') as stream:
        value = stream.read(maximum + 1)
    require(len(value) <= maximum, f'evidence exceeds byte bound: {path.name}')
    return value


def read_json(path):
    value = json.loads(read_bytes(path))
    require(type(value) is dict, f'expected JSON object: {path.name}')
    return value


def validate_payloads():
    require(set(EMBEDDED) == {'connection_probe.py', 'venv_prepare.py', 'resolve_dependencies.py'},
            'unexpected embedded source set')
    for name, record in EMBEDDED.items():
        payload = base64.b64decode(record['base64'], validate=True)
        require(len(payload) == record['bytes'] and sha(payload) == record['sha256'],
                f'embedded source byte/SHA mismatch: {name}')
        VERIFIED_PAYLOADS[name] = payload
    require(EMBEDDED['resolve_dependencies.py']['sha256'] == EXPECTED_RESOLVER_SHA256,
            'resolver differs from approved source')


def verify_or_materialize(name, create):
    path = ROOT / name
    payload = VERIFIED_PAYLOADS[name]
    require(not path.is_symlink(), f'source symlink forbidden: {name}')
    if path.exists():
        require(read_bytes(path, 65536) == payload, f'existing source differs: {name}')
    elif create:
        with path.open('xb') as stream:
            stream.write(payload)
        require(sha(read_bytes(path, 65536)) == EMBEDDED[name]['sha256'], f'written source SHA mismatch: {name}')
    return path


def validate_connection():
    require(ROOT.is_dir() and not ROOT.is_symlink() and ROOT.resolve() == ROOT,
            'workspace root must be the exact physical approved directory')
    value = read_json(ROOT / 'connection.json')
    require(value.get('stage') == 'GPU08_CPU_CONNECTION_ONLY' and value.get('root') == str(ROOT),
            'existing workspace lacks approved connection identity')
    require(value.get('accelerator_environment') in (None, '', '0'), 'connection is not CPU-only')
    require(type(value.get('packages_installed')) is int and value['packages_installed'] == 0,
            'unexpected connection mutation claim')


def validate_venv():
    require(VENV.is_dir() and not VENV.is_symlink() and VENV.resolve() == VENV,
            'partial/missing/redirected venv; no automatic recreation')
    value = read_json(ROOT / 'venv.json')
    require(value.get('stage') == 'GPU08_ISOLATED_VENV_PREPARED'
            and value.get('root') == str(ROOT) and value.get('venv') == str(VENV)
            and value.get('system_site_packages') is False,
            'missing/invalid isolated venv completion proof')
    cfg = read_bytes(VENV / 'pyvenv.cfg', 65536)
    flags = [line.split('=', 1)[1].strip().lower() for line in cfg.decode().splitlines()
             if '=' in line and line.split('=', 1)[0].strip().lower() == 'include-system-site-packages']
    require(flags == ['false'] and sha(cfg) == value.get('pyvenv_cfg_sha256'), 'venv cfg identity changed')
    probe = value.get('probe', {})
    require(type(probe) is dict and probe.get('prefix') == str(VENV)
            and probe.get('base_prefix') != str(VENV)
            and probe.get('executable') == str(VENV / 'bin/python')
            and probe.get('torch_spec') == probe.get('numpy_spec') == probe.get('pip_spec') == 'None',
            'venv proof is not the approved empty isolated target')
    purelib = Path(probe.get('purelib', ''))
    require(purelib.is_absolute() and purelib.resolve().is_relative_to(VENV)
            and (VENV / 'bin/python').is_file(), 'venv entry/purelib invalid')
    # bin/python may legitimately be a symlink to the base interpreter.


def failure_markers():
    return sorted(path.name for path in ROOT.glob('venv*')
                  if 'failure' in path.name.lower() or 'failed' in path.name.lower())


def execute_stage(name):
    payload = VERIFIED_PAYLOADS[name]
    STAGES_ATTEMPTED.append(name)
    captured = io.StringIO()
    # Restore only touched environment keys; no global dependency/config mutation.
    updates = {'PYTHONDONTWRITEBYTECODE': '1', 'PIP_CONFIG_FILE': os.devnull,
               'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'PIP_NO_INPUT': '1', 'PIP_NO_CACHE_DIR': '1'}
    if name == 'venv_prepare.py':
        temporary = ROOT / 'bootstrap-tmp'
        require(not temporary.is_symlink(), 'bootstrap temp directory cannot be redirected')
        temporary.mkdir(exist_ok=True)
        require(temporary.resolve().is_relative_to(ROOT), 'bootstrap temp escapes root')
        updates.update(TMPDIR=str(temporary), TEMP=str(temporary), TMP=str(temporary))
    touched = {key for key in os.environ if key.startswith(('PIP_', 'UV_'))} | set(updates)
    saved = {key: os.environ.get(key) for key in touched}
    try:
        for key in touched:
            os.environ.pop(key, None)
        os.environ.update(updates)
        with contextlib.redirect_stdout(captured):
            exec(compile(payload, str(ROOT / name), 'exec'),
                 {'__name__': '__main__', '__file__': str(ROOT / name),
                  'EXPECTED_SOURCE_SHA256': EMBEDDED[name]['sha256']})
    except Exception as error:
        if name == 'venv_prepare.py':
            marker = ROOT / 'venv-resume-failure.json'
            if not marker.exists():
                with marker.open('x', encoding='utf-8') as stream:
                    json.dump({'status': 'VENV_PREPARATION_FAILED_NO_AUTOMATIC_RETRY',
                               'source_sha256': EMBEDDED[name]['sha256'],
                               'error_type': type(error).__name__, 'error': str(error)[:2048]}, stream)
        raise
    finally:
        for key in touched | {key for key in os.environ if key.startswith(('PIP_', 'UV_'))}:
            os.environ.pop(key, None)
        for key, value in saved.items():
            if value is not None:
                os.environ[key] = value
    output = json.loads(captured.getvalue())
    require(type(output) is dict, f'non-JSON stage output: {name}')
    return output


def result_summary(action):
    value = read_json(ATTEMPT / 'resolution.json')
    require(value.get('executed_source_sha256') == EXPECTED_RESOLVER_SHA256,
            'stored result belongs to another resolver source')
    require(value.get('stage') == 'GPU08_ACTUAL_LINUX_BOUNDED_RESOLVER'
            and value.get('status') in {'CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED',
                                        'RESOLUTION_FAILED_NO_AUTOMATIC_RETRY'}, 'unknown stored resolution status')
    if value['status'] == 'CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED':
        require(sha(read_bytes(ATTEMPT / 'pip-report.json', 8 * 1024**2)) == value.get('report_sha256')
                and sha(read_bytes(ATTEMPT / 'candidate-linux-cuda.lock.txt')) == value.get('candidate_lock_sha256'),
                'stored report/candidate lock bytes changed or missing')
    output = {key: item for key, item in value.items() if key != 'selected_packages'}
    output.update(resume_action=action, resolver_invoked_this_call='resolve_dependencies.py' in STAGES_ATTEMPTED,
                  resume_stages_attempted=list(STAGES_ATTEMPTED),
                  resume_embedded_source_sha256={name: record['sha256'] for name, record in EMBEDDED.items()})
    return output


def main():
    validate_payloads()
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64'
            and sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 13),
            'only approved Linux x86_64 CPython3.13 CPU preparation is supported')
    require(os.environ.get('COLAB_GPU', '') in ('', '0'), 'GPU runtime is outside this resume stage')
    if not ROOT.exists():
        require(not ROOT.is_symlink(), 'broken workspace link is not an empty runtime')
        execute_stage('connection_probe.py')
    validate_connection()
    if ATTEMPT.exists() or ATTEMPT.is_symlink():
        require(ATTEMPT.is_dir() and not ATTEMPT.is_symlink(), 'invalid existing resolver attempt')
        validate_venv()
        for name in EMBEDDED:
            verify_or_materialize(name, create=False)
        if (ATTEMPT / 'resolution.json').exists():
            return result_summary('existing_final_result_no_rerun')
        return {'stage': 'GPU08_RESUME_RESOLVER', 'status': 'PENDING_EXISTING_ATTEMPT_NO_RESULT',
                'root': str(ROOT), 'attempt': str(ATTEMPT), 'resolver_invoked_this_call': False,
                'resume_stages_attempted': list(STAGES_ATTEMPTED),
                'reason': 'Existing attempt may be running or failed; inspect/preserve it, never duplicate automatically.'}
    require(not failure_markers(), 'prior venv failure marker; manual review required')
    if VENV.exists() or VENV.is_symlink():
        validate_venv()
    else:
        prior = [path.name for path in ROOT.glob('venv*') if path.name not in EMBEDDED]
        require(not prior, 'venv absent but prior proof/logs exist; no automatic recreation')
        for name in EMBEDDED:
            verify_or_materialize(name, create=True)
        with (ROOT / 'venv-resume-started.json').open('x', encoding='utf-8') as stream:
            json.dump({'stage': 'VENV_SETUP_RESERVED_NO_AUTOMATIC_RETRY',
                       'source_sha256': EMBEDDED['venv_prepare.py']['sha256']}, stream)
        execute_stage('venv_prepare.py')
        validate_venv()
    for name in EMBEDDED:
        verify_or_materialize(name, create=True)
    observed = execute_stage('resolve_dependencies.py')
    saved = result_summary('approved_resolver_executed_once')
    require(all(saved.get(key) == item for key, item in observed.items()), 'resolver stdout/stored result mismatch')
    return saved


try:
    _result = main()
except Exception as _error:
    _result = {'stage': 'GPU08_RESUME_RESOLVER', 'status': 'STOP_FAIL_CLOSED',
               'error_type': type(_error).__name__, 'error': str(_error)[:2048],
               'resolver_invoked_this_call': 'resolve_dependencies.py' in STAGES_ATTEMPTED,
               'resume_stages_attempted': list(STAGES_ATTEMPTED),
               'automatic_retry': False, 'existing_evidence_overwritten': False}
print(json.dumps(_result, indent=2))
